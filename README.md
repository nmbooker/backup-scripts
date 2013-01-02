Backup Scripts
==============

# Aims

* Produce a backup script that can snapshot LVMs, making it suitable for backing up root filesystems while Linux is running.

* Refactor so that the common code for backing up my machines is all in one library or tool.

# Limitations of Scope

I currently don't plan to support backing up (via snapshots) non-Linux operating systems (unless any other operating systems have LVM).

The generic file backup stuff should work on any unix-like OS that has 'dar' and 'python' installed however.

# Notes
## Tools

* lvm
* python
* dar
