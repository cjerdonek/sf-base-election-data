"""Entry point for main developer script.

Usage: python scripts/run_command.py -h

"""

import argparse
import json
import logging
import os
import subprocess
import sys

import init_path
from pyelect import htmlgen
from pyelect import jsongen
from pyelect import lang
from pyelect import utils


_log = logging.getLogger()

_DEFAULT_OUTPUT_DIR_NAME = '_build'
_FORMATTER_CLASS = argparse.RawDescriptionHelpFormatter
_REL_PATH_JSON_DATA = "data/sf.json"


def get_default_json_path():
    repo_dir = utils.get_repo_dir()
    return os.path.join(repo_dir, _REL_PATH_JSON_DATA)


def get_sample_html_default_rel_dir():
    return os.path.join(utils.DIR_NAME_OUTPUT, htmlgen.DIR_NAME_HTML_OUTPUT)


def command_lang_convert_csv(ns):
    path = ns.input_path
    lang.lang_contest_csv_to_yaml(path)


def command_lang_make_ids(ns):
    path = ns.input_path
    data = lang.create_text_ids(path)
    print(utils.yaml_dump(data))


def command_lang_update_adds(ns):
    lang.update_adds()


def command_make_json(ns):
    path = ns.output_path
    data = jsongen.make_all_data()
    text = json.dumps(data, indent=4, sort_keys=True)
    utils.write(path, text)


def command_parse_csv(ns):
    path = ns.path
    data = lang.parse_contest_csv(path)
    print(data)


def command_sample_html(ns):
    page_name = ns.page_name

    dir_path = ns.output_dir
    open_browser = ns.open_browser

    if dir_path is None:
        dir_path = os.path.join(utils.get_repo_dir(), get_sample_html_default_rel_dir())
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    # Load JSON data.
    json_path = get_default_json_path()
    with open(json_path) as f:
        json_data = json.load(f)
    # Make and output HTML.
    start_path = htmlgen.make_html(json_data, dir_path, page_name=page_name)
    if open_browser:
        subprocess.call(["open", start_path])


def _get_all_files(dir_path):
    paths = []
    for root_dir, dir_paths, file_names in os.walk(dir_path):
        for file_name in file_names:
            path = os.path.join(root_dir, file_name)
            paths.append(path)

    return paths


def command_yaml_norm(ns):
    if ns.all:
        data_dir = utils.get_pre_data_dir()
        paths = _get_all_files(data_dir)
        paths = [p for p in paths if os.path.splitext(p)[1] == '.yaml']
    else:
        paths = [ns.path]
    for path in paths:
        utils.normalize_yaml(path, stdout=True)


def command_yaml_temp(ns):
    path = ns.path
    data = utils.read_yaml(path)
    offices = data['offices']
    node = {}
    for office in offices:
        if 'id' in office:
            id_ = office['id']
        elif 'name_i18n' in office:
            id_ = office['name_i18n']
        elif 'name' in office:
            name = office['name']
            id_ = "office_{0}".format(name.lower())
        elif 'body_id' in office:
            name = office['body_id']
            district = office['district']
            id_ = "office_{0}_{1}".format(name.lower(), district)
        else:
            raise Exception(office)
        print(id_)
        if id_ in node:
            raise Exception(id_)
        if 'id' in office:
            del office['id']
        node[id_] = office
        print(office)

    data['offices'] = node
    utils.write_yaml(data, path)


def command_yaml_update_lang(ns):
    path = ns.path
    data = utils.read_yaml(path)
    utils.write_yaml(data, path, stdout=True)


def make_subparser(sub, command_name, help, command_func=None, details=None, **kwargs):
    if command_func is None:
        command_func_name = "command_{0}".format(command_name)
        command_func = globals()[command_func_name]

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

    parser = make_subparser(sub, "lang_convert_csv",
                help="generate the automated translations from a CSV file.")
    parser.add_argument('input_path', metavar='CSV_PATH',
        help="a path to a CSV file.")

    parser = make_subparser(sub, "lang_make_ids",
                help="create text ID's from a CSV file.")
    parser.add_argument('input_path', metavar='CSV_PATH',
        help="a path to a CSV file.")

    parser = make_subparser(sub, "lang_update_adds",
                help="update the manual language files from additions.yaml.")

    default_output = _REL_PATH_JSON_DATA
    parser = make_subparser(sub, "make_json",
                help="create or update a JSON data file.")
    parser.add_argument('output_path', metavar='PATH', nargs="?", default=default_output,
        help=("the output path. Defaults to the following path relative to the "
              "repo root: {0}.".format(default_output)))

    parser = make_subparser(sub, "parse_csv",
                help="parse a CSV language file from the Department.")
    parser.add_argument('path', metavar='PATH', help="a path to a CSV file.")

    parser = make_subparser(sub, "sample_html",
                help="make sample HTML from the JSON data.",
                details="Uses the repo JSON file as input.")
    parser.add_argument('--page', dest='page_name',
        help='the page to generate (e.g. "bodies.html").  Defaults to all pages.')
    parser.add_argument('--output_dir', metavar='OUTPUT_DIR',
        help=("the output directory.  Defaults to the following directory relative "
              "to the repo: {0}".format(get_sample_html_default_rel_dir())))
    parser.add_argument('--no-browser', dest='open_browser', action='store_false',
        help='suppress opening the browser.')

    parser = make_subparser(sub, "yaml_norm",
                help="normalize YAML files.")
    parser.add_argument('--all', dest='all', action='store_true',
        help='normalize all YAML files.')
    parser.add_argument('path', metavar='PATH', nargs='?',
        help="a path to a YAML file.")

    parser = make_subparser(sub, "yaml_temp",
                help="temporary scratch command.")
    parser.add_argument('path', metavar='PATH', nargs='?',
        help="the target path of a non-English YAML file.")

    parser = make_subparser(sub, "yaml_update_lang",
                help="update a YAML translation file from the English.")
    parser.add_argument('path', metavar='PATH',
        help="the target path of a non-English YAML file.")

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
