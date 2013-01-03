#! /usr/bin/env python

"""Extended builtin list that can accept more than one argument to append()
"""

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
