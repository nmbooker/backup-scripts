#! /usr/bin/env python

"""Help to read and interpret the config file.
"""

import ConfigParser
import shlex

class BackupConf(object):
    """Backup configuration.

    Unless otherwise noted, ConfigParser.NoOptionError is raised if the
    appropriate option is not present in the config file.
    """
    def __init__(self, options):
        self.options = options
        self.conf = ConfigParser.ConfigParser()
        self._read_config()

    def _read_config(self):
        self.conf.read([self.options.specfile])

    def backup_source_type(self):
        """Currently supported: lvm

        [backup]
        source_type = lvm
        """
        return self.conf.get('backup', 'source_type')

    def backup_source_root(self):
        """For non-LVM backups, the directory whose contents will be backed up.

        Not currently used by the current version of 'backup' script, but
        ready for when it does.
        """
        return self.conf.get('backup', 'source_root')

    def source_is_lvm(self):
        """Returns True if the source_type is lvm

        Depends on [backup] source_type
        """
        return self.backup_source_type() == 'lvm'

    def should_snapshot_source(self):
        """Returns True if we should take an LVM snapshot, mount it and
        back that up.

        Depends on [backup] source_type
        """
        return self.source_is_lvm()

    def lvm_snapshot_size(self):
        """The size of the snapshot space to use.

        Can be any size string accepted by the lvcreate command.

        [lvm]
        snapshot_size = 2G
        """
        return self.conf.get('lvm', 'snapshot_size')

    def lvm_snapshot_lv_name(self):
        """The name of the logical volume snapshot to create for backing up.

        [lvm]
        snapshot_lv_name = name-of-volume-backup-snapshot
        """
        return self.conf.get('lvm', 'snapshot_lv_name')

    def lvm_vg(self):
        """The name of the LVM volume group containing the logical volume to back up.

        [lvm]
        volume_group = data
        """
        return self.conf.get('lvm', 'volume_group')

    def lvm_lv(self):
        """The name of the LVM logical volume to back up.

        [lvm]
        logical_volume = name-of-volume
        """
        return self.conf.get('lvm', 'logical_volume')

    def backup_target(self):
        """The path to the base directory for backups taken with this configuration.

        Backups are placed in per-month directories underneath the directory
        specified here.

        [backup]
        target = /net/someserver/backups/somedir
        """
        return self.conf.get('backup', 'target')

    def backup_archive_prefix(self):
        """The start of the name to give each archive file.

        Typically, for readability of the resulting filenames,
        this should end with a hyphen (-) or underscore (_).  e.g.

        [backup]
        archive_prefix = os-mypc-xub-precise-
        """
        return self.conf.get('backup', 'archive_prefix')

    def backup_subdirs(self):
        """Return the subdirectories to restrict to.
        If the subdirs line is not present in the config, the empty list
        [] is returned, which means NO RESTRICTION on subdirectories.

        Returns empty list to mean 'backup all of them'.

        I repeat, if no subdirs option is provided, ALL subdirectories are
        backed up.

        If provided, they're parsed like a shell command, so separate them
        with spaces and put quotes round any path that itself contains
        spaces.

        This example will only backup the etc, var/lib, usr/local and opt
        directories under the source filesystem:

        [backup]
        subdirs = etc var/lib usr/local opt
        """
        try:
            return shlex.split(self.conf.get('backup', 'subdirs'))
        except ConfigParser.NoOptionError:
            return []

    def bindmounts_equals(self):
        """Return the subdirectories that should be bind-mounted to the current root filesystem.

        Each item listed (separated by spaces) is bind-mounted to the same
        directory in the current root filesystem (/).

        For example:
         [bindmounts]
         equals = /boot

        in the above example, if the filesystem being backed up is mounted
        at /tmp/backupfs, then before backup /boot will be bind-mounted on
        /tmp/backupfs/boot.

        This is primarily to allow backups of the Linux operating system
        where most of the root filesystem is on LVM but /boot is still on
        a regular disk partition.  The result is that the /boot from the
        running system is included in the backup.
        """
        if not (self.conf.has_option('bindmounts', 'equals')):
            return []
        return shlex.split(self.conf.get('bindmounts', 'equals'))

    def rsync_enabled(self):
        """Whether or not to do an rsync after the backup.

        If this config option or [rsync] is not present, it is assumed False.

        [rsync]
        enabled = true
        """
        try:
            return self.conf.getboolean('rsync', 'enabled')
        except ConfigParser.NoOptionError:
            return False
        except ConfigParser.NoSectionError:
            return False

    def rsync_target_dir(self):
        """Specify where any rsync job should synchronise to.

        The specified directory will be a mirror of the directory
        specified by [backup]/target.

        --delete is not used in rsync, so accidental deletion on the
        source side won't get passed through to the remote side.

        [rsync]
        target_dir = /some/remote/directory
        """
        path = self.conf.get('rsync', 'target_dir')
        if not path.endswith('/'):
            path += '/'
        return path

    def rsync_even_if_backup_failed(self):
        """Specify whether the rsync should still happen even if the backup itself failed.

        This is handy if a previous rsync could have failed for other reasons
        and you want previous backups to be synced even if this one failed.

        NOT YET IMPLEMENTED
        """
        return self.conf.getboolean('rsync', 'even_if_backup_failed')

    def rsync_touch_file(self):
        """Specify a file to touch before attempting a sync.

        It's a way of making sure some remote filesystems, particularly
        NFS ones automounted with autofs, are present and responding
        before exiting.

        If blank or missing, None is returned, which should be interpreted
        as meaning that no file needs touching before commencing the sync.

        If specified, and the touch_file could not be touched due to
        'No such file or directory' (ENOENT), then the script will wait
        a further 15 seconds before attempting to do the rsync.

        NOT YET IMPLEMENTED
        """
        try:
            value = self.conf.get('rsync', 'touch_file')
            if value:
                return value
            else:
                return None
        except NoOptionError:
            return None
