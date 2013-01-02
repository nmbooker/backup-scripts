#! /usr/bin/env python

"""DESCRIPTION
"""

import sys
import argparse
import backup_conf

def main(options):
    """Main program."""
    script = BackupScript(options)
    script.run()
    return

class BackupScript(object):
    """Top-down implementation of backup operation.
    """

    def __init__(self, options):
        self.options = options

    def run(self):
        self._read_config()
        self._cleanup_last_time()
        self._prepare_for_backup()
        self._do_backup()
        self._post_backup_cleanup()

    def _read_config(self):
        """Read the configuration.
        """
        self.conf = backup_conf.BackupConf(self.options)

    def _cleanup_last_time(self):
        """Clean up any left-overs from last time.
        """
        print "Cleanup from last time"

    def _prepare_for_backup(self):
        """Do any backup preparations.
        """
        self._make_lvm_snapshot()
        self._mount_lvm_snapshot()
        self._mount_binds()

    def _make_lvm_snapshot(self):
        """Make the LVM snapshot.
        """
        print "Make LVM snapshot"

    def _mount_lvm_snapshot(self):
        """Mount the LVM snapshot
        """
        print "Mount LVM snapshot"

    def _mount_binds(self):
        """Mount any bind mounts requested.
        """
        print "Mount any bind mounts"

    def _do_backup(self):
        """Perform the backup copying operation itself.
        """
        print "Do the backup copying operation"

    def _post_backup_cleanup(self):
        """Remove any temporary stuff from this backup.
        """
        self._unmount_binds()
        self._unmount_lvm_snapshot()
        self._remove_lvm_snapshot()

    def _unmount_binds(self):
        """Unmount any bind mounts.
        """
        print "Unmount any bind mounts"

    def _unmount_lvm_snapshot(self):
        """Unmount any LVM snapshots.
        """
        print "Unmount any LVM snapshots used"

    def _remove_lvm_snapshot(self):
        """Remove any LVM snapshots.
        """
        print "Remove the LVM snapshots we used"



def get_options():
    """Get options for the script."""
    parser = argparse.ArgumentParser(
               description="DESCRIPTION",
             )
    # parser.add_argument() calls here
    parser.add_argument('specfile')
    options = parser.parse_args()
    # extra processing of options here
    return options

if __name__ == "__main__":
    main(get_options())
