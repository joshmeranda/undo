This is the parent directory for all undo files. In this README you will find documentation for the undo file syntax and
a list of general best practices and guidelines to follow when writing your own undo files.

# Syntax
The two groups of syntax you will need to learn in order write your own undo files are
[command patterns](#command-patterns) and [undo expressions](#undo-patterns-and-expressions).

## Command Patterns
Command patterns are used to describe a specific command with or without sub-commands or arguments. For a command
pattern to "match" with a command, the pattern must specify the same command, sub-commands, and arguments as the target
command. All of the command pattern's [argument patterns](#argument-pattern) must agree with the arguments that are
present or not present in the given command as well as the amount of values that are given. For example, if an argument
pattern specifies that an argument is required and takes exactly 2 values, the given command will not match if the
required argument either is not present or does not have exactly 2 values.

In an effort to keep the command patterns as readable and easy to write as possible, the syntax is kept fairly close to
the conventions when writing command's usage or help text. For example, for a command `cmd` whose usage looks like this:
`USAGE: cmd [--verbose] NUMBER` where `--verbose` is an optional flag and `NUMBER` is some required positional, you
would have a command pattern like this: `cmd [--verbose] <NUMBER>`.

### Commands
The simplest part of a command pattern is the main command and sub-commands. They can be simply listed as they would be
when pass through the command line. For example, a command pattern "cmd sub-command" would match a command only if the
main command was `cmd` and the sub-command was `sub-command`. It doesn't matter how levels of sub-commands there are,
you will simply list them one after another in the order that they would be called.

Obviously rare is the command which takes only sub-commands and no arguments. This is where argument patterns fit in.

### Argument Pattern
Argument patterns are the basic building blocks of any command pattern. Almost all except the most simple command
patterns will need at least a few argument patterns in order to completely describe the functionality the command
provides. Any argument pattern can be broken down into a few parts:
 - Argument names (ex -v, --verbose)
 - [Variable Name](#variable-name)
 - [Quantifier](#quantifiers)
 - An optional delimiter if the argument takes a [list value](#list-values)

The argument names will in most cases be the first part of the argument pattern, except in the case of positional
arguments (see below). You can specify as many as you want as long as they are separated by at least one space. For
example, the pattern `[-z --gzip --gunzip --ungzip]` would match any argument with the name `-z`, `--gzip`, `--gunzip`,
or `--ungzip`. You can intermingle long and short argument names; however, it is more clear to list the short names
before the long names.

All arguments can also be either required or optional, and or positional or not positional. All positional arguments
must also be required (but can be made optional by giving a [quantifier](#quantifiers) of '*'). You can specify whether
an argument is required or not by wrapping them in either `[...]` (optional) or `<...>` (required). For example, the
pattern `[--verbose]` is optional but `<--fields=>` is required.

Positional arguments might be slightly more difficult to spot. They will always be wrapped in `<...>` and will never
have any leading argument names. They will simply stand alone. For example, "<SRC>" or even "<>" (this situation is
covered in detail in the [variable name](#variable-name) section.)

### Argument Group Patten


#### Variable Name
The name associated with an argument

#### Quantifiers

#### List Values

### Argument Group

### Put it All Together

## Undo Patterns and Expressions

### Value Expressions

#### Accessor Expressions

#### Ternary Expressions

#### String Literal Expressions

#### String Expansion Expressions

### Conditional Expressions

#### Existence Expressions

### Command Expressions

#### Value Command Expressions

#### Conditional Command Expressions

# Best Practices and Guidelines

## Grouping files
As much as possible try to group related commands into their own directory, such as how all the GNU Coreutils commands
are stored under the `coreutils` directory. This may also apply to a single command with large sub commands like `git`,
where each sub-command should be separated into its own file. For example, the command `git add` should be stored in a
file called `git-add.toml`.

## Precise Arguments
Any argument that can ensure that no files are overwritten, or that when "undone" would result in essentially the same
condition as before can be considered precise. For example, a `--no-clobber` argument to `mv` is precise as it ensures
that no files will be overwritten; however, `--interactive` is imprecise as it is still possible for the user to have
elected to remove the original file.

## Testing