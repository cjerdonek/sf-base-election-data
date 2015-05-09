"""Entry point for main developer script.

Usage: python scripts/run_command.py -h

"""

import argparse
import json
import logging
import os
import subprocess
import sys
import textwrap

import init_path
from pyelect.html import generator as htmlgen
from pyelect import jsongen
from pyelect import lang
from pyelect.lang import PHRASES_BASE_NAME
from pyelect.common import utils
from pyelect.common import yamlutil


_log = logging.getLogger()

DEFAULT_BUILD_DIR_NAME = '_build'
_FORMATTER_CLASS = argparse.RawDescriptionHelpFormatter

DESCRIPTION = """\
Helper script for repository contributors.

The normal workflow is--

1. TODO
2. Run `make_json` to update the JSON from the YAML.
3. Run `sample_html` to generate HTML from the JSON.

"""

def _wrap(text):
    """Format text for help outuput."""
    paras = text.split("\n\n")
    paras = [textwrap.fill(p) for p in paras]
    text = "\n\n".join(paras)

    return text


def get_default_output_dir_rel():
    return os.path.join(DEFAULT_BUILD_DIR_NAME, htmlgen.HTML_OUTPUT_DIRNAME)


def command_lang_csv_ids(ns):
    path = ns.input_path
    data = lang.create_text_ids(path)
    print(utils.yaml_dump(data))

def command_lang_text_csv(ns):
    lang.update_csv_translations()


def command_lang_text_extras(ns):
    lang.update_extras()


def command_make_json(ns):
    path = ns.output_path
    json_data = jsongen.make_json_data()
    text = json.dumps(json_data, indent=4, sort_keys=True)
    utils.write(path, text)


def command_parse_csv(ns):
    path = ns.path
    data = lang.parse_contest_csv(path)
    print(data)


def command_sample_html(ns):
    debug = ns.debug
    local = ns.local
    dir_path = ns.output_dir
    open_browser = ns.open_browser
    page_name = ns.page_name
    print_html = ns.print_html

    if page_name:
        # Only require that the user type a matching prefix.
        names = htmlgen.get_template_page_file_names()
        for name in names:
            if name.startswith(page_name):
                page_name = name
                break
        else:
            raise Exception("no page begins with: {0!r} (choose from: {1})"
                            .format(page_name, ", ".join(names)))

    if dir_path is None:
        repo_dir = utils.get_repo_dir()
        dir_path = os.path.join(repo_dir, get_default_output_dir_rel())

    # Make and output HTML.
    html_path = htmlgen.make_html(dir_path, page_name=page_name,
                                  print_html=print_html, local_assets=local,
                                  debug=debug)
    if open_browser:
        subprocess.call(["open", html_path])


def command_yaml_make_phrases(ns):
    lang.update_yaml_phrases_file()


def _get_all_files(dir_path):
    paths = []
    for root_dir, dir_paths, file_names in os.walk(dir_path):
        for file_name in file_names:
            path = os.path.join(root_dir, file_name)
            paths.append(path)

    return paths


def command_yaml_norm(ns):
    path = ns.path
    if path:
        if not utils.is_yaml_file_normalizable(path):
            raise Exception("not normalizable: {0}".format(path))
        paths = [path]
    else:
        data_dir = utils.get_pre_data_dir()
        paths = _get_all_files(data_dir)
        paths = [p for p in paths if os.path.splitext(p)[1] == '.yaml']
    for path in paths:
        yamlutil.normalize_yaml(path, stdout=False)


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


def make_subparser(sub, command_name, help, command_func=None, details=None, **kwargs):
    if command_func is None:
        command_func_name = "command_{0}".format(command_name)
        command_func = globals()[command_func_name]

    # Capitalize the first letter for the long description.
    desc = help[0].upper() + help[1:]
    if details is not None:
        desc += "\n\n{0}".format(details)
    desc = _wrap(desc)
    parser = sub.add_parser(command_name, formatter_class=_FORMATTER_CLASS,
                            help=help, description=desc, **kwargs)
    parser.set_defaults(run_command=command_func)
    return parser


def create_parser():
    """Return an ArgumentParser object."""
    root_parser = argparse.ArgumentParser(formatter_class=_FORMATTER_CLASS,
            description=DESCRIPTION)
    sub = root_parser.add_subparsers(help='sub-command help')

    parser = make_subparser(sub, "lang_csv_ids",
                help="create text ID's from a CSV file.")
    parser.add_argument('input_path', metavar='CSV_PATH',
        help="a path to a CSV file.")

    csv_dir = lang.get_rel_path_csv_dir()
    csv_trans_dir = lang.get_rel_path_translations_csv()
    details = textwrap.dedent("""\
    Update the translation files in the directory {0} with the information
    in the CSV files in the directory: {1}.
    """.format(csv_trans_dir, csv_dir))
    parser = make_subparser(sub, "lang_text_csv",
                help="update the i18n files for the CSV phrases.",
                details=details)

    extra_phrases_path = lang.get_rel_path_phrases_extra()
    extra_trans_dir = lang.get_rel_path_translations_extra()
    details = textwrap.dedent("""\
    Add to the translation files in the directory {0} any new phrases in
    the file: {1}.
    """.format(extra_trans_dir, extra_phrases_path))
    parser = make_subparser(sub, "lang_text_extras",
                help='update the i18n files for the "extra" phrases.',
                details=details)

    rel_path_default = jsongen.get_rel_path_json_data()
    parser = make_subparser(sub, "make_json",
                help="create or update a JSON data file.")
    parser.add_argument('output_path', metavar='PATH', nargs="?", default=rel_path_default,
        help=("the output path. Defaults to the following path relative to the "
              "repo root: {0}.".format(rel_path_default)))

    parser = make_subparser(sub, "parse_csv",
                help="parse a CSV language file from the Department.")
    parser.add_argument('path', metavar='PATH', help="a path to a CSV file.")

    page_bases = htmlgen.get_template_page_bases()
    parser = make_subparser(sub, "sample_html",
                help="make sample HTML from the JSON data.",
                details="Uses the repo JSON file as input.")
    parser.add_argument('--page', dest='page_name',
        help=('the page to generate (from: {0}).  Defaults to all pages.'
              .format(", ".join(page_bases))))
    parser.add_argument('--output_dir', metavar='OUTPUT_DIR',
        help=("the output directory.  Defaults to the following directory relative "
              "to the repo: {0}".format(get_default_output_dir_rel())))
    parser.add_argument('--local', action='store_true',
        help=('link to assets locally rather than via a CDN.  This is useful '
              'for developing locally without internet access.'))
    parser.add_argument('--no-browser', dest='open_browser', action='store_false',
        help='suppress opening the browser.')
    parser.add_argument('--print-html', dest='print_html', action='store_true',
        help='write the HTML to stdout.')
    parser.add_argument('--debug', action='store_true',
        help="set Django's TEMPLATE_DEBUG to True.")

    phrases_file_name = utils.get_yaml_file_name(PHRASES_BASE_NAME)
    phrases_rel_path = utils.get_yaml_objects_path_rel(PHRASES_BASE_NAME)
    parser = make_subparser(sub, "yaml_make_phrases",
                help="create or update the i18n object file {0}.".format(phrases_file_name),
                details="Updates the file at: {0}.".format(phrases_rel_path))

    parser = make_subparser(sub, "yaml_norm",
                help="normalize one or more YAML files.")
    parser.add_argument('--all', dest='all', action='store_true',
        help='normalize all YAML files.')
    parser.add_argument('path', metavar='PATH', nargs='?',
        help="a path to a YAML file.")

    parser = make_subparser(sub, "yaml_temp",
                help="temporary scratch command.")
    parser.add_argument('path', metavar='PATH', nargs='?',
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
