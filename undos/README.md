This is the parent directory for all undo files. In this README you will find documentation for the undo file syntax and
a list of general best practices and guidelines to follow when writing your own undo files.

# Format
All undo files are written in [TOML](https://toml.io/en/) files, due to it's easy to read and write format. If you are
unfamiliar with TOML files, take some time to review its documentation, this project only leverages some of the most
basic parts of the format, so it will not take you long before you are able to write and read the TOML syntax you will
see in Undo files. There are several supported keys which you must use to properly declare an undo file:

| name              | meaning                                                                                          |
| ----------------- | ------------------------------------------------------------------------------------------------ |
| supported-shells  | a list of shells that every undo command will be valid in or `"all"` (default) if all shells are supported |
| entry             | a simple object containing a command pattern and an undo expression                              |
| entry.cmd         | the command pattern                                                                              |
| entry.undo        | the undo expression                                                                              |
| entry.precise     | specifies whether the current entry is [precise](#precision}                                     |

Besides, TOML there are two types of syntax you will need to learn in order write your own undo files:
[command patterns](#command-patterns) and [undo expressions](#undo-patterns-and-expressions). It is important to note
that in both argument and undo patterns, whitespace is largely ignored, but they are case-sensitive.

## Precision
One key concept of Undo is the idea of "precision." An Undo file entry can be considered precise if the state before the
original command is executed is the same, or functionally the same, as when the undo command is executed. For example,
if the original command is `cp ORIGINAL COPY`, the typical way to undo this would be to remove the `COPY` file, and at a
surface level this works fine; however, there is no way to know if the `mv` replaced a pre-existing file called `COPY`.

On the other hand `cp --no-clobber ORIGINAL COPY` could be considered precise since so file would be overridden. Of
course this is still no guarantee, if the file `COPY` existed, then the `cp` command would fail and not overwrite the
file, but the command would still match the appropriate [command pattern](#command-patterns) and execute the
corresponding [undo expression](#undo-patterns-and-expressions). Because of this limitation, the responsibility is on
the user to pay attention to avoid unintentionally removing files.

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
In some cases you might need to ensure that at least one argument in a list of required arguments is present for things
like ensuring a command is precise. There is no dynamic way to do thing without grouping them together in some way.
Argument group patterns provide this functionality without too much more additional syntax.

An argument group pattern is essentially just a list of the same argument patterns you already know wrapped up in
`(...)`. To make the group required you must add a `!` after the opening parenthesis. For example the pattern
`([-n --no-clobber] [--remove-destination])` is optional and `(![-n --no-clobber] [--remove-destination])` is required.
Generally speaking an optional argument group does not add much value, and will not likely be used in most situations. A
required group will keep a  command pattern from matching a command unless at least one of the arguments in the group is
present. These groups are not mutually exclusive and two required arguments can be matched.

### Putting it All Together
Now lets walk through an example. Take the following usage text

```
USAGE: foo [-v] <--do-nothing|--do-something|--do-something-else> BAR...

Options:
  -v --verbose          run verbosely

Instruction arguments (at least one must be specified):
  --do-nothing          do nothing
  --do-something        do something
  --do-something-else   do something else
```

The first thing to look for is the main command, in this case `foo`. Then look for any arguments that can be safely
ignored for our purposes. Here we can only ignore `--verbose` since it does not change what the command does, only what
is printed to the console. Now we search for anything that is required for a command to have for it to matching, which
there are a few here. First we have a required group including the arguments `--do-nothing`, `--do-something`, and
`--do-something-else`. Lastly, we have a positional `BAR` which expects at least one value to be supplied. All together
we end up with a command pattern like this:

```
foo
    [-v --verbose]
    
    (! [--do-nothing] [--do-something] [--do-someting-else])
    
    <BAR...>
```

The different pieces we extracted are separated on different lines for clarity and readability rather than necessity,
but it is encouraged you do so too.

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
In this section you will find some

## Grouping files
As much as possible try to group related commands into their own directory, such as how all the GNU Coreutils commands
are stored under the [`coreutils`](/undos/coreutils) directory. This may also apply to a single command with large sub commands like `git`,
where each sub-command should be separated into its own file. For example, the command `git add` should be stored in a
file called `git/git-add.toml`.

## Testing