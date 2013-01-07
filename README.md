Backup Scripts
==============

# Aims

## Complete
* Produce a backup script that can snapshot LVMs, making it suitable for backing up root filesystems while Linux is running.

## Future
* Refactor so that the common code for backing up my machines is all in one library or tool.

# Limitations of Scope

I currently don't plan to support backing up (via snapshots) non-Linux operating systems (unless any other operating systems support the same LVM commands).

The generic file backup stuff should work on any unix-like OS that has 'dar' and 'python' installed however, when that option is complete.

# Notes
## Tools

* lvm
* python
* dar

# Running
## Produce a configuration file

There's an example configuration file in the examples directory.  Take a
copy and edit to suit your backup scheme.

## Prepare the target directories

Make sure that the paths in ```[backup]target``` and, if applicable,
the ```[rsync]target_dir``` actually exist and are readable, writable and
executable (i.e. enterable) by the user that backup will be run as.

For backing up complete systems, that user will have to be ```root```, but
if just backing up your own home directory somewhere your own login _may_
suffice

## Do an 'ideal' test run

Run the following:

```
sudo ./backup /path/to/your/backup_config.ini -lINFO --noop
```

That will let you see what would, all things being set up correctly,
be run.

Once you're happy that you know what will happen, and understand what
the commands are that will be run and their implications, you can test for
real:

```
sudo ./backup /path/to/your/backup_config.ini -lINFO
```

You may want to leave the ```-lINFO``` off (or set it at ```-lDEBUG``` and redirect stdout
and stdin to a file) when you schedule a cron job,
but I suggest you leave it on when doing manual runs.

I plan to add a feature to allow logging to a log file at DEBUG level and only output
normal output and WARNING or worse to the usual stderr and stdout streams,
to make it nice and convenient to run in cron yet still have full real-world debugging
information in a file in case it goes wrong.

## Finally set up cron or a shortcut to run it

How you do this is up to you - I tend to write a small wrapper script that
calls the complete command line, so it's more readable in my crontab or daily manual run script.

# Program Structure
Here's a brief description of what each program and module does:

## backup

`backup` is the launcher script itself, and the only file that does anything useful when actually called as a script.  The remaining .py files are modules imported directly or indirectly by the script 'backup'.

## arglist.py
contains a slight extension to the built-in list() type that makes building argument lists that bit more readable.

## backup\_conf.py
reads and interprets the backup profile, which is in ConfigParser format (similar to Win-DOS .ini format).

## backup\_script.py
oversees preparation and teardown for the backup operation.  I wrote it with a top-down structured programming approach.

## backup\_operation.py
oversees the backup operation (the putting of files into .dar archives in the correct directories) itself.  It looks a little strange because it is an almost direct Python port of the my old Ruby-based backup script, except that the incremental and full backup types have been refactored into their own Strategy classes and some info is picked up from the config file.

## program\_runners.py
encapsulates the code for running external programs, logging the command lines and exit codes, and optionally skipping running them for real with a 'noop' option to the constructor.
