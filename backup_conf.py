#! /usr/bin/env python

"""Help to read and interpret the config file.
"""

import sys
import argparse
import ConfigParser
import shlex

class BackupConf(object):
    """Backup configuration.
    """
    def __init__(self, options):
        self.options = options
        self.conf = ConfigParser.ConfigParser()
        self._read_config()

    def _read_config(self):
        self.conf.read([self.options.specfile])

    def backup_source_type(self):
        """Currently supported: lvm"""
        return self.conf.get('backup', 'source_type')

    def source_is_lvm(self):
        return self.backup_source_type() == 'lvm'

    def should_snapshot_source(self):
        return self.source_is_lvm()

    def lvm_snapshot_size(self):
        return self.conf.get('lvm', 'snapshot_size')

    def lvm_snapshot_lv_name(self):
        return self.conf.get('lvm', 'snapshot_lv_name')

    def lvm_vg(self):
        return self.conf.get('lvm', 'volume_group')

    def lvm_lv(self):
        return self.conf.get('lvm', 'logical_volume')

    def backup_target(self):
        return self.conf.get('backup', 'target')

    def bindmounts_equals(self):
        if not (self.conf.has_option('bindmounts', 'equals')):
            return []
        return shlex.split(self.conf.get('bindmounts', 'equals'))


def main(options):
    """Main program."""
    return

def get_options():
    """Get options for the script."""
    parser = argparse.ArgumentParser(
               description="test config file reader",
             )
    # parser.add_argument() calls here
    options = parser.parse_args()
    # extra processing of options here
    return options

if __name__ == "__main__":
    main(get_options())
