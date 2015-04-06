
import os

import django
from django.conf import settings
import django.template.defaulttags as defaulttags

from pyelect import utils


_TEMPLATE_DIR_NAMES = ('base', 'objects', 'partials')


def get_templates_dir():
    repo_dir = utils.get_repo_dir()
    return os.path.join(repo_dir, 'templates')


def _get_template_search_dirs():
    base_dir = get_templates_dir()
    sub_dirs = [os.path.join(base_dir, name) for name in _TEMPLATE_DIR_NAMES]
    dirs = [base_dir] + sub_dirs
    return dirs


@defaulttags.register.filter
def get_item(dict_, key):
    return dict_.get(key)


def init_django():
    """Initialize Django."""
    search_dirs = _get_template_search_dirs()
    settings.configure(
        INSTALLED_APPS=('pyelect', ),
        # TEMPLATE_DEBUG=True,
        TEMPLATE_DIRS=search_dirs,
        TEMPLATE_STRING_IF_INVALID="**%s**",
        # The default setting contains this:
        #   'django.template.loaders.app_directories.Loader'
        # See this issue for more information:
        #   https://code.djangoproject.com/ticket/24527
        TEMPLATE_LOADERS=('django.template.loaders.filesystem.Loader', ),
    )
    django.setup()
