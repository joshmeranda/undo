This is the parent directory for all undo files. In this README you will find documentation for the undo file syntax and
a list of general best practices and guidelines to follow when writing your own undo files.

# Syntax

## Command Patterns
In an effort to keep the command patterns as readable and easy to write as possible, the syntax is kept fairly close to
the conventions when writing command's usage or help text.

### Argument Pattern

#### Variable Name

#### Quantifiers

#### List Values

### Argument Group

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