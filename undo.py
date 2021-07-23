#!/usr/bin/env python
from pattern import *
from pattern import _UndoArgumentParser


def main():
    pass


if __name__ == "__main__":
    pattern = CommandPattern("test", list(), list())
    parser = _UndoArgumentParser(pattern)
