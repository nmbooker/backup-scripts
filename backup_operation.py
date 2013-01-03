#! /usr/bin/env python

"""The actual backup copying operation.
"""
import datetime
import subprocess
import os.path
import logging
import errno
from arglist import ArgList

class BackupCopy(object):
    """This encapsulates the copy operation for the backup.

    It's an almost-direct port of my previous Ruby blah_backup.rb,
    but with configuration from a file rather than having to copy-and-edit
    each time.

    This implementation, however, doesn't currently do the rsync.
    That's best left to a wrapper script IMO, though the ability to run
    generic post_backup and pre_backup hooks may be added later.
    """
    def __init__(self, options, config, backup_source_root=None):
        """
        options: The script options namespace (usually returned from argparse)
        config: The BackupConf object for the current instance.
        backup_source_root: If provided, overrides the value in the config for get_backup_source_root()
        """
        self.options = options
        self.conf = config
        self._backup_source_root_override = backup_source_root
        self._setup_logging()
        self.backup_date = datetime.datetime.now()
        self._make_backup_set()

    def _setup_logging(self):
        """Sets up the logging interface at self.log
        """
        numeric_level = getattr(logging, self._log_level(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % self._log_level())
        logging.basicConfig(level=numeric_level)
        self.log = logging.getLogger(__name__)

    def _log_level(self):
        """Get the log level (DEBUG etc) from the script options."""
        return self.options.log_level

    def _noop(self):
        """Return True if command line switch instructed the script to skip any real filesystem-changing operations.
        """
        return self.options.noop

    def run(self):
        """Select and run a backup strategy (full or incremental)
        """
        backup_strategy = self._get_backup_strategy()
        backup_strategy.run()

    def _get_backup_strategy(self):
        """Return the appropriate backup strategy for this backup operation.
        """
        if self.is_full_backup():
            return FullBackupStrategy(self)
        else:
            return IncrementalBackupStrategy(self)

    def backup_prefix(self):
        """The configured string to append to the start of each backup's filename.

        It's best if this is configured in the .ini file to end with some
        sort of separator like underscore (_) or hyphen (-), to make the
        resulting filenames easier to read.
        """
        return self.conf.backup_archive_prefix()

    def is_full_backup(self):
        """Return True if this will be a full backup, else False.
        """
        return self.last_successful_backup_in_set() is None

    def backup_root(self):
        """The base directory for all backup sets for the current configuration.

        Typically, a directory for each month is created underneath this
        directory, and backup files are put inside there.
        """
        return self.conf.backup_target()

    def backup_set_root(self):
        """The full path to the directory containing this month's backup set.
        """
        return os.path.join(self.backup_root(), self.backup_set_name())

    def backup_set_name(self):
        """The basename of the directory containing this month's backup set.
        """
        return self.backup_date.strftime('%Y-%m')

    def last_successful_filename(self):
        """The full path to the file that will contain the name of the last
        successful backup in the current set.
        """
        return os.path.join(self.backup_set_root(), 'latest_successful')

    def deps_filename(self):
        """The full path to the file that documents the parent-child
        relationship between backups in the current set.
        """
        return os.path.join(self.backup_set_root(), 'backup_deps')

    def last_successful_backup_in_set(self):
        """Return name of last successful backup in set.

        None if there are no suitable backups in the current set.
        Typically, this means this is the first backup of the month.

        This is only looked up from disk on first call, and remembered
        thereafter, so don't worry about calling this multiple times.
        """
        if hasattr(self, '_parent_memo'):
            self.log.debug("getting last successful backup from _parent_memo")
            # Memoize to avoid hitting the filesystem every time
            # or getting inconsistent results.
            return self._parent_memo

        self.log.debug("getting last successful backup from file")
        try:
            lsf = open(self.last_successful_filename())
        except IOError, exc:
            if exc.errno == errno.ENOENT:
                self.log.debug("Last Successful file %r not found", self.last_successful_filename())
                return None
            else:
                raise

        try:
            result = lsf.readline().rstrip()
        finally:
            lsf.close()
        if not result:
            # coerce empty string to None
            result = None
        self.log.debug("Last Successful backup was %r", result)
        self._parent_memo = result
        return result

    def set_successful_backup(self, backup_name, parent_backup=''):
        """Record the backup of the given name as the latest successful
        backup, and record its name and the name of its parent in the
        dependencies file.
        """
        # Record latest successful backup as this one
        lsf_name = self.last_successful_filename()
        self.log.debug('Setting last successful backup name in %r', lsf_name)
        if not self._noop():
            with open(lsf_name, 'w') as lsf:
                lsf.write(backup_name + '\n')

        # Record backup dependency in dependencies file
        depf_name = self.deps_filename()
        self.log.debug('Logging backup dependency to %r...', depf_name)
        if not self._noop():
            with open(depf_name, 'a') as depf:
                depf.write("%s:%s\n" % (backup_name, parent_backup))

    def archive_basename(self, suffix):
        """The full path and basename of the current backup.

        This is the dar archive name.  dar itself automatically adds the
        .N.dar suffixes to this, so you should not include this.

        suffix: A string, usually beginning with a dash (-) specifying the type of backup.  Usully either '-FULL' or '-INC'.

        If we produce an rsync backup type, suffix may well be blank.
        """
        return self.backup_prefix() + self.backup_date.strftime('%Y-%m-%dT%H%M') + suffix

    def pre_backup(self):
        """Might eventually run a configurable pre-backup script.
        Currently just warns at INFO level that it's not implemented.
        """
        self.log.info('pre_backup() not implemented in this script')

    def get_backup_source_root(self):
        """Return the path to the directory to be backed up.

        This is taken from the backup/source_root setting in the config
        file, unless backup_source_root was provided in __init__,
        in which case that value overrides that in the file.
        """
        if self._backup_source_root_override is None:
            return self.conf.backup_source_root()
        else:
            return self._backup_source_root_override
        return self.backup.get_backup_source_root()

    def get_chosen_subdirs(self):
        """Return the set of subdirectories of get_backup_source_root()
        that should be backed up.

        NOTE: an empty list or None value should be interpreted as meaning
        'no restriction'.
        This reflects the way the '-g' option to dar works.
        """
        return self.conf.backup_subdirs()

    def _make_backup_set(self):
        """Make the directory for the current backup set if it does not
        exist.
        """
        try:
            os.mkdir(self.backup_set_root())
        except OSError, exc:
            if exc.errno == errno.EEXIST:
                self.log.info('Directory %r already exists', self.backup_set_root())
            else:
                raise
        return



class BaseBackupStrategy(object):
    """Base backup strategy.

    Runs dar to actually perform the backup.

    Subclasses must implement:
     print_backup_type() - print the type (full or incremental) of backup
                           and the name of the backup archive.
                           It might also print the parent backup name.
     get_extra_dar_args() - return any additional arguments to append to
                            the usual dar command line.
     get_archive_name() - return the full basename, with -FULL or -INC suffix.  Should usually use self.backup.archive_basename(suffix) for this.
     set_successful_backup() - call self._set_successful_backup() with appropriate arguments.

    You should instantiate a child class (concrete implementation) of this
    and call its .run() method.
    """
    def __init__(self, backup):
        self.backup = backup

    def run(self):
        self.backup.pre_backup()
        self.print_backup_type()
        dar_cmd = self.base_dar_cmdline()
        dar_cmd.extend(self.get_extra_dar_args())
        self._print_run_cmd(dar_cmd)
        self.set_successful_backup()

    def base_dar_cmdline(self):
        basename = self.get_archive_base_path()
        dar_args = ArgList(['dar'])
        # dar_args.append('-v')
        dar_args.append('-c', basename)
        dar_args.append('-R', self.backup.get_backup_source_root())
        # Don't warn before overwriting a file or slice
        dar_args.append('-w')
        # Split into < 2GB slices so they can go on ISO9660 DVDs
        dar_args.append('-s', '1875000000')
        # Make excluded directories as empty
        dar_args.append('-D')
        # Use maximum gzip compression when compressing files
        dar_args.append('-z9')
        # Don't compress files smaller than 150 bytes
        dar_args.append('-m', '150')
        # Don't compress the files matching the following patterns:
        for pattern in self._nocompress_patterns():
            dar_args.append('-Z', pattern)
        # -g arguments restrict the subdirectories to be backed up.
        # if there are no -g arguments, all subdirectories are backed up.
        for subdir in self._subdirs():
            dar_args.append('-g', subdir)
        return dar_args

    def _nocompress_patterns(self):
        """Return the list of filename patterns to avoid compressing.

        If empty, assume all files must be compressed.
        """
        nocompress = [
                '*.avi',
                '*.bz2',
                '*.gif',
                '*.gz',
                '*.jpg',
                '*.mov',
                '*.mpg',
                '*.mp3',
                '*.pbm',
                '*.pdf',
                '*.png',
                '*.Z',
                '*.zip',
                ]
        return nocompress

    def _subdirs(self):
        """Return the list of subdirectories to backup.

        An empty list must be taken to mean 'backup all subdirectories'.
        """
        return self.backup.get_chosen_subdirs()

    def get_archive_base_path(self):
        """Return the full path to the new archive, to be passed to dar."""
        return os.path.join(self.backup.backup_set_root(), self.get_archive_name())

    def _print_run_cmd(self, cmd):
        """Print and perhaps run the given cmd.  cmd must be a list of args"""
        self._print_cmd(cmd)
        self._run_cmd(cmd)

    def _print_cmd(self, cmd):
        """Log the command at info level."""
        self.backup.log.info("Command: %r", cmd)

    def _run_cmd(self, cmd):
        """Run the argument list cmd with check_call, unless --noop is set."""
        if not self.backup._noop():
            subprocess.check_call(cmd)

    def _set_successful_backup(self, archive_name, parent=''):
        """Save the successful backup.

        archive_name: The name of the archive that's just been made.
        parent: The name of the parent archive if applicable, else the empty string.
        """
        return self.backup.set_successful_backup(archive_name, parent)



class FullBackupStrategy(BaseBackupStrategy):
    """Bits of backup specific to a full backup.

    See BaseBackupStrategy for invocation instructions.
    """
    def get_archive_name(self):
        """archive_basename + '-FULL'"""
        return self.backup.archive_basename('-FULL')

    def print_backup_type(self):
        """Appropriate output information for a full backup."""
        print('Full backup: %s' % self.get_archive_name())

    def get_extra_dar_args(self):
        """No extra args required for a full backup."""
        return []

    def set_successful_backup(self):
        """Set successful backup with no parent"""
        self._set_successful_backup(self.get_archive_name())

class IncrementalBackupStrategy(BaseBackupStrategy):
    """Bits of backup specific to an incremental backup.

    See BaseBackupStrategy for invocation instructions.
    """
    def get_archive_name(self):
        """archive_basename + '-INC'"""
        return self.backup.archive_basename('-INC')

    def print_backup_type(self):
        """Outputs info for incremental backup, and name of parent."""
        print('Incremental backup: %s' % self.get_archive_name())
        print('Based on parent: %s' % self._get_parent_archive_name())

    def get_extra_dar_args(self):
        """Arguments to specify the parent archive."""
        return ['-A', self._parent_archive_path()]

    def _get_parent_archive_name(self):
        if not hasattr(self, '_parent_archive_name'):
            # cache to avoid repeated lookups from file
            self._parent = self.backup.last_successful_backup_in_set()
        return self._parent

    def _parent_archive_path(self):
        return os.path.join(self.backup.backup_set_root(), self._get_parent_archive_name())

    def set_successful_backup(self):
        """Set successful backup with parent."""
        archive_name = self.get_archive_name()
        parent = self._get_parent_archive_name()
        self._set_successful_backup(archive_name, parent)
