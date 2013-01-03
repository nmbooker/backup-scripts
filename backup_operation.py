#! /usr/bin/env python

"""The actual backup copying operation.
"""
import datetime
import subprocess
import os.path
import logging
import errno

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
        self.options = options
        self.conf = config
        self._backup_source_root_override = backup_source_root
        self._setup_logging()
        self.backup_date = datetime.datetime.now()
        self._make_backup_set()

    def _setup_logging(self):
        numeric_level = getattr(logging, self._log_level(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % self._log_level())
        logging.basicConfig(level=numeric_level)
        self.log = logging.getLogger(__name__)

    def _log_level(self):
        return self.options.log_level

    def _noop(self):
        return self.options.noop

    def run(self):
        backup_strategy = self._get_backup_strategy()
        backup_strategy.run()

    def _get_backup_strategy(self):
        if self.is_full_backup():
            return FullBackupStrategy(self)
        else:
            return IncrementalBackupStrategy(self)

    def backup_prefix(self):
        return self.conf.backup_archive_prefix()

    def is_full_backup(self):
        return self.last_successful_backup_in_set() is None

    def backup_root(self):
        return self.conf.backup_target()

    def backup_set_root(self):
        return os.path.join(self.backup_root(), self.backup_set_name())

    def backup_set_name(self):
        return self.backup_date.strftime('%Y-%m')

    def last_successful_filename(self):
        return os.path.join(self.backup_set_root(), 'latest_successful')

    def deps_filename(self):
        return os.path.join(self.backup_set_root(), 'backup_deps')

    def last_successful_backup_in_set(self):
        """Return name of last successful backup in set.

        None if there are no suitable backups in the curren set.

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
        return self.backup_prefix() + self.backup_date.strftime('%Y-%m-%dT%H%M') + suffix

    def pre_backup(self):
        self.log.info('pre_backup() not implemented in this script')

    def get_backup_source_root(self):
        if self._backup_source_root_override is None:
            return self.conf.backup_source_root()
        else:
            return self._backup_source_root_override
        return self.backup.get_backup_source_root()

    def get_chosen_subdirs(self):
        return self.conf.backup_subdirs()

    def _make_backup_set(self):
        try:
            os.mkdir(self.backup_set_root())
        except OSError, exc:
            if exc.errno == errno.EEXIST:
                self.log.info('Directory %r already exists', self.backup_set_root())
            else:
                raise
        return self.backup_root()



class BaseBackupStrategy(object):
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
        for subdir in self._subdirs():
            dar_args.append('-g', subdir)
        return dar_args

    def _nocompress_patterns(self):
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
        return self.backup.get_chosen_subdirs()

    def get_archive_base_path(self):
        return os.path.join(self.backup.backup_set_root(), self.get_archive_name())

    def _print_run_cmd(self, cmd):
        self._print_cmd(cmd)
        self._run_cmd(cmd)

    def _print_cmd(self, cmd):
        self.backup.log.info("Command: %r", cmd)

    def _run_cmd(self, cmd):
        if not self.backup._noop():
            subprocess.check_call(cmd)

    def _set_successful_backup(self, archive_name, parent=None):
        return self.backup.set_successful_backup(archive_name, parent)



class FullBackupStrategy(BaseBackupStrategy):
    def get_archive_name(self):
        return self.backup.archive_basename('-FULL')

    def print_backup_type(self):
        print('Full backup: %s' % self.get_archive_name())

    def get_extra_dar_args(self):
        return []

    def set_successful_backup(self):
        self._set_successful_backup(self.get_archive_name())

class IncrementalBackupStrategy(BaseBackupStrategy):
    def get_archive_name(self):
        return self.backup.archive_basename('-INC')

    def print_backup_type(self):
        print('Incremental backup: %s' % self.get_archive_name())
        print('Based on parent: %s' % self._get_parent_archive_name())

    def get_extra_dar_args(self):
        return ['-A', self._parent_archive_path()]

    def _get_parent_archive_name(self):
        if not hasattr(self, '_parent_archive_name'):
            # cache to avoid repeated lookups from file
            self._parent = self.backup.last_successful_backup_in_set()
        return self._parent

    def _parent_archive_path(self):
        return os.path.join(self.backup.backup_set_root(), self._get_parent_archive_name())

    def set_successful_backup(self):
        archive_name = self.get_archive_name()
        parent = self._get_parent_archive_name()
        self._set_successful_backup(archive_name, parent)


class ArgList(list):
    """A slightly extended version of list, with an append method that
    can take more than one argument.

    When building lists of arguments, this is syntatically cleaner than
    using .extend(['--more', 'args']) or .append('--more') ; .append('args')
    """
    def append(self, *args):
        """Append the objects in the given args to the end of the list.
        """
        if not args:
            raise TypeError('append() takes at least one argument (0 given)')
        self.extend(args)
