
"""Handle noop, command line logging, and command line exit status logging.
"""

import subprocess
import logging

class LoggableCalls(object):
    """Log command line calls to a logger, report exit status if they fail.

    As an added bonus, if 'noop' is set to True, we just log them
    without running them for real.
    """
    def __init__(self, logger, noop=False):
        self.log = logger
        self.noop = noop
        self.internal_log = logging.getLogger(__name__)

    def check_call(self, cmd_args):
        """Log and optionally run
        """
        self.log_cmd(cmd_args)
        self.run_cmd(cmd_args)

    def log_cmd(self, cmd_args):
        """Log the command line at level 'info'.
        """
        self.log.info('Command: %r', cmd_args)

    def run_cmd(self, cmd_args):
        """Run command if noop is not set, and log error if it fails.
        """
        if not self.noop:
            self.really_run_cmd(cmd_args)
        else:
            self.internal_log.debug('noop set, not running command for real')

    def really_run_cmd(self, cmd_args):
        """Run command without checking for noop, and log error if it fails.

        The CalledProcessError is re-raised.
        """
        self.internal_log.debug('running command for real...')
        try:
            subprocess.check_call(cmd_args)
        except subprocess.CalledProcessError, exc:
            self.internal_log.debug('CalledProcessError caught')
            self.log.error(str(exc))
            raise exc
