import argparse
import logging
import os
import shlex
import subprocess
import typing

from undo import expand
from undo import history
from undo import resolve
from undo import utils


def default_include_dirs():
    return ":".join([
        os.path.join(os.sep, "usr", "share", "undo"),
        os.path.join(os.sep, "usr", "local", "share", "undo"),
        os.path.join(os.sep, os.getenv("HOME"), ".local", "share", "undo"),
    ])


def get_user_selection(commands: list[str]) -> typing.Optional[str]:
    prompt = "Please select the command to run (invalid input will run no commands):"

    for i, command in enumerate(commands):
        prompt += f"\n  {i + 1} ) {command}"

    prompt += "\nselection: "

    selection = input(prompt)

    try:
        return commands[int(selection) - 1]
    except IndexError:
        print(f"input '{int(selection)}' does not match any command")
    except ValueError:
        print(f"input '{selection}' is not a valid number")

    return None


def interact(commands: list[str]) -> typing.Optional[str]:
    if len(commands) == 1:
        response = input(f"run command '{commands[0]}'? [Y/n] ").lower()

        return commands[0] if response == 'y' or response == '' else None

    return get_user_selection(commands)


def parse_args():
    parser = argparse.ArgumentParser(prog="undo",
                                     description="make a 'best effort' attempt to undo the most recently run command")

    parser.add_argument("-v", "--verbose",
                        action="count", default=0,
                        help="increase the level of verbosity, can be stacked (-vvvv) up to 4 times, any more will "
                             "have no additional effect")

    parser.add_argument("-d", "--dry",
                        action="store_true", help="show the resolved command(s) but do not run them, this flag will"
                                                  "disable interactivity if specified")

    parser.add_argument("--allow-imprecise",
                        action="store_true", help="show commands which are not precise and may have unexpected or "
                                                  "unwanted effects")

    parser.add_argument("-c", "--command",
                        type=str, help="undo the command passed as an argument rather than pulling from history",
                        metavar="CMD")

    parser.add_argument("-A", "--all",
                        action="store_true", help="search all undo files rather than stopping after the first file "
                                                  "with a match")

    parser.add_argument("-i", "--interactive",
                        action="store_true", help="require user input before running the found undo command even when "
                                                  "there is only one")

    return parser.parse_args()


def main():
    namespace = parse_args()

    include_dirs = os.getenv("UNDO_INCLUDE_DIRS", default_include_dirs()).split(":")

    logging.basicConfig(format="[%(levelname)s] %(message)s", level=50 - namespace.verbose * 10)

    shell = utils.get_parent_shell()

    command = history.history(shell, 1)[0] if namespace.command is None else namespace.command

    resolved = resolve.resolve(command, include_dirs, namespace.all, namespace.allow_imprecise, shell)

    undos = [expand.expand(undo, env) for (env, undo) in resolved]

    if len(undos) == 0:
        print(f"no command was found to undo '{command}'")
        return
    elif len(undos) == 1 and not namespace.interactive:
        subprocess.run(shlex.split(undos[0]))
    elif namespace.dry:
        print('\n'.join(undos))
    elif namespace.interactive:
        undo_command = interact(undos)

        if undo_command is not None:
            subprocess.run(shlex.split(undo_command))
        else:
            print("no command was selected")
    else:
        print("multiple undo commands found, copy on the the commands below to clipboard to run: ")
        print('\n'.join(f"  {i + 1} ) {command}" for i, command in enumerate(undos)))