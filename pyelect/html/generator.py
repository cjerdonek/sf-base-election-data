"""Support for making html."""

import json
import logging
import os
from pprint import pprint

from django.template.base import TemplateDoesNotExist
from django.template.loader import get_template

from pyelect.html import context, templateconfig
from pyelect import jsongen
from pyelect import utils


_log = logging.getLogger()

_DIR_NAME_TEMPLATE_PAGE = 'pages'
DIR_NAME_HTML_OUTPUT = 'html'


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


def make_html(output_dir, page_name=None, print_html=False):

    if page_name is None:
        file_names = templateconfig.get_template_page_file_names()
    else:
        file_names = [page_name]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    json_data = jsongen.get_json()
    data = context.make_template_data(json_data)

    templateconfig.init_django()

    for file_name in file_names:
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
