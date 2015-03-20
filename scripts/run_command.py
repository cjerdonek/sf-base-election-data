"""Entry point for main developer script.

Usage: python scripts/run_command.py -h

"""

import argparse
import json
import logging
import sys

import init_path
from pyelect import htmlgen
from pyelect import jsongen
from pyelect import utils


_FORMATTER_CLASS = argparse.RawDescriptionHelpFormatter


def command_make_json(ns):
    path = ns.output_path

    data = jsongen.make_all_data()
    text = json.dumps(data, indent=4, sort_keys=True)
    with open(path, mode='w') as f:
        f.write(text)
    print(text)


def command_normalize_yaml(ns):
    path = ns.path
    data = utils.read_yaml(path)
    utils.write_yaml(data, path, stdout=True)


def command_sample_html(ns):
    path = ns.output_path
    # Load JSON data.
    json_path = utils.get_default_json_path()
    with open(json_path) as f:
        input_data = json.load(f)
    # Make and output HTML.
    html = htmlgen.make_html(input_data)
    with open(path, "w") as f:
        f.write(html)
    print(html)


def make_subparser(sub, command_name, command_func, help, details=None, **kwargs):
    # Capitalize the first letter for the long description.
    desc = help[0].upper() + help[1:]
    if details is not None:
        desc += "\n\n{0}".format(details)
    parser = sub.add_parser(command_name, formatter_class=_FORMATTER_CLASS,
                            help=help, description=desc, **kwargs)
    parser.set_defaults(run_command=command_func)
    return parser


def create_parser():
    """Return an ArgumentParser object."""
    root_parser = argparse.ArgumentParser(formatter_class=_FORMATTER_CLASS,
            description="command script for repo contributors")
    sub = root_parser.add_subparsers(help='sub-command help')

    default_output = utils.REL_PATH_JSON
    parser = make_subparser(sub, "make_json", command_make_json,
                help="create or update a JSON data file.")
    parser.add_argument('output_path', metavar='PATH', nargs="?", default=default_output,
        help=("the output path. Defaults to the following path relative to the "
              "repo root: {0}.".format(default_output)))

    parser = make_subparser(sub, "norm_yaml", command_normalize_yaml,
                help="normalize a YAML file.")
    parser.add_argument('path', metavar='PATH', help="a path to a YAML file.")

    default_output = "sample.html"
    parser = make_subparser(sub, "sample_html", command_sample_html,
                help="make sample HTML from the JSON data.",
                details="Uses the repo JSON file as input.")
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
        # We need to handle this exception because of the following
        # behavior change:
        #   http://bugs.python.org/issue16308
        parser.print_help()
    else:
        ns.run_command(ns)


if __name__ == '__main__':
    main()
