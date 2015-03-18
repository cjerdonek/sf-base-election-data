"""Entry point for main developer script.

Usage: python scripts/run_command.py -h

"""

from argparse import ArgumentParser
import logging
import sys

import init_path
from pyelect import htmlgen


def command_sample_html(ns):
    path = ns.output_path
    html = htmlgen.make_html()
    with open(path, "w") as f:
        f.write(html)
    print(html)


def make_subparser(sub, command_name, command_func, desc=None, **kwargs):
    # Capitalize the first letter for the long description.
    capitalized = desc[0].upper() + desc[1:]
    parser = sub.add_parser(command_name, help=desc, description=capitalized, **kwargs)
    parser.set_defaults(run_command=command_func)
    return parser


def create_parser():
    """Return an ArgumentParser object."""
    root_parser = ArgumentParser(description="command script for repo contributors")
    sub = root_parser.add_subparsers(help='sub-command help')

    default_output = "sample.html"
    parser = make_subparser(sub, "sample_html", command_sample_html,
                desc="make sample HTML from the JSON data.")
    parser.add_argument('output_path', metavar='PATH', nargs="?", default=default_output,
        help=("the output path. Defaults to {0} in the repo root."
              .format(default_output)))

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
        parser.print_help()
    else:
        ns.run_command(ns)


if __name__ == '__main__':
    main()
