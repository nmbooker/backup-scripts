
"""Handle noop, command line logging, and command line exit status logging.
"""

import subprocess

class LoggableCalls(object):
    """Log command line calls to a logger, report exit status if they fail.

    As an added bonus, if 'noop' is set to True, we just log them
    without running them for real.
    """
    def __init__(self, logger, noop=False):
        self.log = logger
        self.noop = noop

    def check_call(self, cmd_args):
        """Log and optionally run
        """
        log_cmd(cmd_args)
        run_cmd(cmd_args)

    def log_cmd(self, cmd_args):
        """Log the command line at level 'info'.
        """
        self.log.info('Command: %r', cmd_args)

    def run_cmd(self, cmd_args):
        """Run command if noop is not set, and log error if it fails.
        """
        if not self.noop:
            self.really_run_cmd(cmd_args)

    def really_run_cmd(self, cmd_args):
        """Run command without checking for noop, and log error if it fails.

        The CalledProcessError is re-raised.
        """
        try:
            subprocess.check_call(cmd_args)
        except subprocess.CalledProcessError, exc:
            self.log.error(str(exc))
            raise exc
