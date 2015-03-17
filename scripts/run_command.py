"""Entry point for main developer script.

Usage: python scripts/run_command.py -h

"""

from argparse import ArgumentParser
import logging
import sys

import pyelect


def command_sample_html(ns):
    print(ns)


def make_subparser(sub, command_name, desc=None, **kwargs):
    # Capitalize the first letter for the long description.
    capitalized = desc[0].upper() + desc[1:]
    parser = sub.add_parser(command_name, help=desc, description=capitalized, **kwargs)
    return parser


def create_parser():
    """Return an ArgumentParser object."""
    root_parser = ArgumentParser(description="command script for repo contributors")
    sub = root_parser.add_subparsers(help='sub-command help')

    parser = make_subparser(sub, "sample_html",
                desc="make sample HTML from the JSON data.")
    parser.set_defaults(run_command=command_sample_html)

    return root_parser


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    logging.basicConfig(level='INFO')
    parser = create_parser()
    ns = parser.parse_args(argv)
    try:
        ns.run_command
    except AttributeError:
        parser.error("you must enter a command")
    ns.run_command(ns)


if __name__ == '__main__':
    main()
