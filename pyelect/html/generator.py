"""Support for making html."""

import json
import logging
import os
from pprint import pprint
import shutil

from django.template.base import TemplateDoesNotExist
from django.template.loader import get_template

from pyelect.html import context, templateconfig
from pyelect import jsongen
from pyelect import utils


_log = logging.getLogger()

_DIR_NAME_TEMPLATE_PAGE = 'pages'
STATIC_FILES_DIR = 'static_files'
HTML_OUTPUT_DIRNAME = 'html'

# The subdirectories to create in the HTML output directory.
HTML_OUTPUT_SUB_DIRS = [
    os.path.dirname(context.JSON_OUTPUT_PATH),
    'js'
]


def get_static_dir():
    repo_dir = utils.get_repo_dir()
    dir_path = os.path.join(repo_dir, STATIC_FILES_DIR)
    return dir_path


def get_page_template_name(file_name):
    return os.path.join(_DIR_NAME_TEMPLATE_PAGE, file_name)


def _get_template_page_dir():
    templates_dir = templateconfig.get_templates_dir()
    return os.path.join(templates_dir, _DIR_NAME_TEMPLATE_PAGE)


def get_template_page_file_names():
    dir_path = _get_template_page_dir()
    file_names = os.listdir(dir_path)
    return file_names


def get_template_page_bases():
    file_names = get_template_page_file_names()
    bases = sorted([os.path.splitext(name)[0] for name in file_names])
    return bases


def render_template(file_name, context):
    """Render the sample template as a Unicode string.

    Argument:
      data: a dict of template variables.
    """
    template_name = get_page_template_name(file_name)
    try:
        template = get_template(template_name)
    except TemplateDoesNotExist:
        paths = templateconfig.get_template_page_file_names()
        raise Exception("possible file names:\n  {0}".format("\n  ".join(paths)))
    return template.render(context)


def create_dir(dir_path):
    if not os.path.exists(dir_path):
        _log.info("creating dir: {0}".format(dir_path))
        os.makedirs(dir_path)


def get_copy_info(source_dir, target_dir, root_dir, name):
    source_path = os.path.join(root_dir, name)
    rel_path = os.path.relpath(source_path, start=source_dir)
    target_path = os.path.join(target_dir, rel_path)

    return source_path, target_path

def copy_files(source_dir, target_dir):
    for root_dir, dir_names, file_names in os.walk(source_dir):
        for dir_name in dir_names:
            source_dir, target_dir = get_copy_info(source_dir, target_dir, root_dir, dir_name)
            if not os.path.exists(target_dir):
                os.mkdir(target_dir)
        for file_name in file_names:
            source_path, target_path = get_copy_info(source_dir, target_dir, root_dir, file_name)
            shutil.copyfile(source_path, target_path)


def make_html(output_dir, page_name=None, print_html=False, local_assets=False,
              debug=False):
    """Generate the HTML from the JSON."""
    if page_name is None:
        file_names = get_template_page_file_names()
    else:
        file_names = [page_name]

    # Create the output directory skeleton.
    create_dir(output_dir)
    for dir_name in HTML_OUTPUT_SUB_DIRS:
        dir_path = os.path.join(output_dir, dir_name)
        create_dir(dir_path)

    # Copy all static files.
    static_dir = get_static_dir()
    copy_files(static_dir, output_dir)
    # TODO: use copy_files() also for the data directory.
    json_path_source = jsongen.get_json_path()
    json_path_target = os.path.join(output_dir, context.JSON_OUTPUT_PATH)
    shutil.copyfile(json_path_source, json_path_target)

    json_data = jsongen.get_json()
    data = context.make_html_data(json_data, local_assets=local_assets)

    page_bases = get_template_page_bases()
    templateconfig.init_django(debug=debug)

    for file_name in file_names:
        _log.info('processing: {0}'.format(file_name))
        page_base, ext = os.path.splitext(file_name)
        context_ = context.make_template_context(data, page_base)
        html = render_template(file_name, context=context_)
        if print_html:
            print(html)
        output_path = os.path.join(output_dir, file_name)
        utils.write(output_path, html)
    if len(file_names) == 1:
        start_page = file_names[0]
    else:
        start_page = 'index.html'
    start_path = os.path.join(output_dir, start_page)

    return start_path
