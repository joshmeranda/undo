This is the parent directory for all undo files. In this README you will find documentation for the undo file syntax and
a list of general best practices and guidelines to follow when writing your own undo files.

# Syntax
The two groups of syntax you will need to learn in order write your own undo files are
[command patterns](#command-patterns) and [undo expressions](#undo-patterns-and-expressions). It is important to note
that in both argument and undo patterns, whitespace is largely ignored, but they are case-sensitive.

## Command Patterns
Command patterns are used to describe a specific command with or without sub-commands or arguments. For a command
pattern to "match" with a command, the pattern must specify the same command, sub-commands, and arguments as the target
command. Each of the command pattern's [argument patterns](#argument-pattern) must agree with the arguments that are
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
 - [Identifier](#identifier)
 - [Quantifier](#quantifier)
 - [Delimiter](#delimiter)

The argument names will in most cases be the first part of the argument pattern, except in the case of positional
arguments (see below). You can specify as many as you want as long as they are separated by at least one space. For
example, the pattern `[-z --gzip --gunzip --ungzip]` would match any argument with the name `-z`, `--gzip`, `--gunzip`,
or `--ungzip`. You can intermingle long and short argument names; however, it is more clear to list the short names
before the long names.

All arguments can also be either required or optional, and or positional or not positional. All positional arguments
must also be required (but can be made optional by giving a [quantifier](#quantifier) of '*'). You can specify whether
an argument is required or not by wrapping them in either `[...]` (optional) or `<...>` (required). For example, the
pattern `[--verbose]` is optional but `<--verbose>` is required (although a required flag is probably not of much use).

Positional arguments might be slightly more difficult to spot. They will always be wrapped in `<...>` and will never
have any leading argument names. They will simply stand alone. For example, `<SRC>` or even `<>` (this situation is
covered in detail in the [identifier](#identifier) section.)

#### Identifier
The names associated with an argument are themselves not very useful, but when used in combination with an
[undo expression](#undo-patterns-and-expressions), they can be fairly powerful as they are used to access the values
pass on the command line. The name associated with an argument can be either implicit or explicit. Implicit names are
the simplest. If the argument pattern is non-positional (it has argument names) and no identifier is explicitly
given, Undo will take the longest identifier and cast it to upper camel case. For example, the pattern
`[-c --no-clobber]` would have the identifier `NO_CLOBBER`. The implicit name of positional arguments is dependent on
their position, in that the first positionals name is `1` the second's is `2`, and so on and so forth.

Explicit names can be more tricky, but the most simple in positional arguments. Many positional arguments are going to
consist of the identifier and nothing else. For example, the argument pattern `<SRC>` describes a positional argument
whose identifier is `SRC`. Non-positional arguments are slightly more complex. If the argument is a flag and does not
expect to receive any arguments, right after the argument names wrap the identifier in `[...]` (ex.
`[--verbose [VERBOSE]]`). Most often flags will be used with implicit identifiers. Arguments expecting a value are
very similar but the name is only wrapped in `[...]` if the argument is able to take 0 values as well, but will always
have an `=` before the actual name. For example, an argument which can either take 1 or 0 values with an explicit name
would look like this `[--arg[=ARGUMENT]]`, but if required exactly 1 argument it would look like this `[--arg=ARGUMENT]`.
The next section will cover how to specify the amount of values an argument pattern expects.

There is some crossover between implicit and explicit identifiers. For example the pattern `<--src[=]>` generates the
identifier even though the `[...]` pattern is present, and so it is an implicit name using explicit syntax.

```
# simple implicit flag: NO_CLOBBBER
[-c --no-clobber]

# argument with explicit quantifier but implcit name: SRC
[--src=...]

# positionals with implicit identifiers mixed with explicit identifiers: 1, SRC, 2
<> <SRC> <>

# simple explicit flag VERBOSE
[-v --verbose [VERBOSE]]

# argument taking value: NUMBER
[-n=NUMBER]

# argument taking optional values: OPTIONAL
[--optional[=OPTIONAL]]

# identical to the above pattern
[--optional[=]]
```

#### Quantifier
Quantifiers are how we specify how many values an argument expects to receive, the table below describes each of the
possible quantifiers:

| name          | example                         | meaning                                                            |
| ------------- | ------------------------------- | ------------------------------------------------------------------ |
| Flag          | `[-f --flag]`                   | no explicit quantifier or explicitly zero value quantifier (ie `{0}`) represents a simple boolean flag |
| Optional      | `[-o --optional[=VALUE]]`       | when the argument name and `=` is wrapped in `[...]`, the argument may take either 0 or 1 values |
| At least one  | `[-a --at-least-one=VALUE...]`  | the argument must have at least 1 value, with no limit             |
| Any           | `[-A --any=VALUE*]`             | the argument can take any amount of values (including 0), useful for specifying optional positionals |
| N             | `[-n --number=NUMBER{3}]`       | the argument expects exactly N values                              |

Combining the optional and at least one  quantifier can be ued to create. For example, the pattern `[-A --any[=ANY...]]`
specifies that the argument expects an optional value but also expects at least one values. The argument expects either
no values or any number of values, so the quantifier produced is the any quantifier. Neither way is preferred, just be
consistent with the method you use. This means you can specify a positional argument expecting any number of arguments
as either `<*>` or `<[...]>`.

You do not need to specify an identifier to specify a quantifier, you can simply put the quantifier where you would
expect the identifier (ex `[-n --numbers=...]`)

#### Delimiter
Some arguments may take a list of values rather the several distinct values, and when accessing those values later in an
[undo expression](#undo-patterns-and-expressions) it might be tremendously helpful to be able to split up those values
to be able to operate on them individually. To allow this, you may specify a delimiter in your argument pattern.

The delimiter is started with a `:` and should follow the identifier and quantifier if they exist. Anything between the
`:` and the closing brace or bracket will be considered the delimiter, no matter how long or what the content is. For
example, the pattern `<-f --fields=:,>` has a delimiter of `,` and `<--colons=::>` has a delimiter of `:`. When the list
value is pulled from the target command, its value is split into a list. For example, if "1,2,4,5" is passed as the
value for `<-f --fields=:,>`, its accessible value in the undo expression would be `["1", "2", "4", "5"]`.

Not all arguments may have a delimiter, since it does not make sense for them to. To use a delimiter, the argument can
only expect to take 1 value and can be optional.

### Argument Group Pattern

### Putting it All Together

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