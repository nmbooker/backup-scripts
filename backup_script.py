#! /usr/bin/env python

"""Implements the OS backup script.
"""

import backup_conf
import logging

class BackupScript(object):
    """Top-down implementation of backup operation.
    """

    def __init__(self, options):
        """
        options: The options generated by argparse.
        """
        self.options = options
        self._setup_logging()

    def _setup_logging(self):
        numeric_level = getattr(logging, self._log_level(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % self._log_level())
        logging.basicConfig(level=numeric_level)
        self.log = logging.getLogger(__name__)

    def _log_level(self):
        return self.options.log_level

    def run(self):
        """Run the script."""
        self._read_config()
        self._cleanup_last_time()
        try:
            self._prepare_for_backup()
            self._do_backup()
        finally:
            self._post_backup_cleanup()

    def _read_config(self):
        """Read the configuration.
        """
        self.conf = backup_conf.BackupConf(self.options)

    def _cleanup_last_time(self):
        """Clean up any left-overs from last time.
        """
        self.log.info("Cleanup from last time")

    def _prepare_for_backup(self):
        """Do any backup preparations.
        """
        self._make_lvm_snapshot()
        self._mount_lvm_snapshot()
        self._mount_binds()

    def _make_lvm_snapshot(self):
        """Make the LVM snapshot.
        """
        self.log.info("Make temporary LVM snapshot")

    def _mount_lvm_snapshot(self):
        """Mount the LVM snapshot
        """
        self.log.info("Mount temporary LVM snapshot")

    def _mount_binds(self):
        """Mount any bind mounts requested.
        """
        self.log.info("Mount any bind mounts")

    def _do_backup(self):
        """Perform the backup copying operation itself.
        """
        self.log.info("Do the backup copying operation")

    def _post_backup_cleanup(self):
        """Remove any temporary stuff from this backup.
        """
        self._unmount_binds()
        self._unmount_lvm_snapshot()
        self._remove_lvm_snapshot()

    def _unmount_binds(self):
        """Unmount any bind mounts.
        """
        self.log.info("Unmount any bind mounts")

    def _unmount_lvm_snapshot(self):
        """Unmount any LVM snapshots.
        """
        self.log.info("Unmount the temporary LVM snapshot")

    def _remove_lvm_snapshot(self):
        """Remove any LVM snapshots.
        """
        self.log.info("Remove the temporary LVM snapshot")
