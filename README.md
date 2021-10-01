# Undo
Provides a method to perform a "best effort" attempt to undo a previous command.

## Installation
Installing `undo` is fairly simple process. First create a distribution tarball with `make dist`. Unpack the tar with
`tar -xvf undo-<VERSION>.tar.gz`, change to the unpacked directory and install `ch undo-<VERSION> && make install`.

All `Makefiles` have a "help" target documenting the targets and values which can be passed through the command line.

## Overview
With undo you can "undo" the effects of some commands. For example, `mv FILE NEW_NAME` can be undone with `mv NEW_NAME
FILE`. To do this, Undo will pull information from the environment 

First determines where to look for undo files by pulling the `UNDO_INCLUDE_DIRS` environment variable. This value is
much like the `PATH` env var, a colon separated list of directory paths where Undo will for undo  file (default
`/usr/share/undo:/usr/local/share/undo:$HOME/.local/share/undo` if the variable is empty). These directories are not
recursively searched and only top-level undo files will be found. Be careful when setting this environment variable
yourself as you will lose access to the default paths mentioned above, so make sure to check where any existing undo
files are located and be sure to include those paths in the new value.

Next Undo attempts to determine the target shell by looking at the parent process, and extracting the command name. This
means that running Undo outside a shell (ex through an IDE) may produce unexpected behavior because no supported shell
could be determined.

Finally, Undo will pull the target command. There are 2 ways which Undo will identify the command to undo. The easiest
is to let Undo parse the output of your shell's `history` command / built-in to pull the most recently executed command.
It will do this using the shell it found in the previous step. Or the user may explicitly pass Undo the command as an
argument `undo --comand 'mv FILE NEW_NAME'`.

One of the most powerful components of undo are the "undo files" in which you can specify how to undo commands. These
are the declarative configuration files where the user can specify how to undo certain commands. More undo files can be
added at any time, and will be used to resolve undo commands as long as the parent directory is specified in the
`UNDO_INCLUDE_DIRS` environment variable. You can find full documentation of the syntax [here](/undos).