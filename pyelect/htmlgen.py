"""Support for making html."""

from collections import defaultdict
from datetime import date
import os
from pprint import pprint

import django
from django.conf import settings
import django.template
from django.template import Context
import django.template.defaulttags as defaulttags
from django.template.loader import get_template

from pyelect import lang
from pyelect import utils
from pyelect.templatetags import custom_tags


CATEGORY_ORDER = ["federal", "state", "city_county", "school", "judicial"]
DIR_NAME_HTML_OUTPUT = 'html'
DIR_NAME_TEMPLATE_PAGE = 'pages'
NON_ENGLISH_ORDER = [lang.LANG_CH, lang.LANG_ES, lang.LANG_FI]


@defaulttags.register.filter
def get_item(dict_, key):
    return dict_.get(key)


def init_django():
    """Initialize Django."""
    search_dirs = _get_template_search_dirs()
    settings.configure(
        INSTALLED_APPS=('pyelect', ),
        TEMPLATE_DIRS=search_dirs,
        TEMPLATE_STRING_IF_INVALID="NOT_FOUND: '%s'",
        # The default setting contains this:
        #   'django.template.loaders.app_directories.Loader'
        # See this issue for more information:
        #   https://code.djangoproject.com/ticket/24527
        TEMPLATE_LOADERS=('django.template.loaders.filesystem.Loader', ),
    )
    django.setup()


def _get_templates_dir():
    repo_dir = utils.get_repo_dir()
    return os.path.join(repo_dir, 'templates')


def _get_template_page_dir():
    templates_dir = _get_templates_dir()
    return os.path.join(templates_dir, DIR_NAME_TEMPLATE_PAGE)


def _get_template_search_dirs():
    return [_get_templates_dir()]


def get_template_page_file_names():
    dir_path = _get_template_page_dir()
    file_names = os.listdir(dir_path)
    return file_names


def _get_translations(trans, text_id):
    try:
        dict_ = trans[text_id]
    except KeyError:
        raise Exception("json translations node does not have text_id: {0!r}".format(text_id))
    return dict_

def _get_i18n(trans, obj_json, key_base):
    key = '{0}_i18n'.format(key_base)
    text_id = obj_json[key]
    words = _get_translations(trans, text_id)
    english = words[lang.LANG_EN]
    non_english = [words[lang] for lang in NON_ENGLISH_ORDER]
    # Remove empty strings.
    non_english = list(filter(None, non_english))

    i18n = {
        'english': english,
        'non_english': non_english
    }

    return i18n


def make_district(value):
    data = {
        'name': value['district_code']
    }
    return data


def make_districts(data):
    districts = [make_district(v) for v in data['districts']]
    return districts


def make_categories(all_json, trans):
    categories_json = all_json['categories']

    categories = {}
    for category_id, category_json in categories_json.items():
        name_i18n = _get_i18n(trans, category_json, 'name')
        categories[category_id] = name_i18n

    return categories


def _compute_next_election_year(office_json):
    term_length = office_json.get('term_length')
    # TODO: make this required.
    if not term_length:
        return None
    try:
        seed_year = office_json['seed_year']
    except KeyError:
        raise Exception("office: {0!r}".format(office_json))
    year = date.today().year
    # Find a year before the current year.
    while seed_year >= year:
        seed_year -= term_length
    # Advance until the current or later.
    while seed_year < year:
        seed_year += term_length
    return seed_year


def _make_election_info(data):

    vote_method = data.get('vote_method')

    next_election_year = _compute_next_election_year(data)
    next_election_text = "{0} next".format(next_election_year)

    term_length = data.get('term_length')
    if term_length:
        term_length = "{0} year term".format(term_length)

    return list(filter(None, [term_length, next_election_text, vote_method]))


def make_office(all_json, data):
    trans = all_json['i18n']

    # TODO: incorporate a real ID.
    office_id = data.get('name_i18n')
    # TODO: do not skip any offices.
    if office_id is None:
        return None

    name_i18n = _get_i18n(trans, data, 'name')

    election_info = _make_election_info(data)

    office = {
        'category_id': data.get('category_id'),
        'election_info': election_info,
        'id': office_id,
        'name_i18n': name_i18n,
        # TODO: use a real seat count.
        'seat_count': 1,
        'twitter': data.get('twitter'),
        'url': data.get('url')
    }

    return office


def make_offices(all_json):
    offices = [make_office(all_json, v) for v in all_json['offices']]
    # TODO: remove the filter.
    offices = list(filter(None, offices))
    return offices


def make_bodies_one(body_id, data, **kwargs):

    print(data)
    body = {
        'name': data['name'],
    }

    return body

    # trans = all_json['i18n']
    #
    # # TODO: incorporate a real ID.
    # office_id = data.get('name_i18n')
    # # TODO: do not skip any offices.
    # if office_id is None:
    #     return None
    #
    # name_i18n = _get_i18n(trans, data, 'name')
    #
    # election_info = _make_election_info(data)
    #
    # office = {
    #     'category_id': data.get('category_id'),
    #     'election_info': election_info,
    #     'id': office_id,
    #     'name_i18n': name_i18n,
    #     # TODO: use a real seat count.
    #     'seat_count': 1,
    #     'twitter': data.get('twitter'),
    #     'url': data.get('url')
    # }
    #
    # return office


def add_objects(template_data, json_data, node_name, **kwargs):
    make_object_func_name = "make_{0}_one".format(node_name)
    make_object = globals()[make_object_func_name]

    objects = []
    for object_id, data in json_data[node_name].items():
        obj = make_object(object_id, data, **kwargs)
        obj['id'] = object_id
        objects.append(obj)

    template_data[node_name] = objects

    # Return it in case the caller wants to do something more with it.
    return objects


def _group_by(objects, key):
    grouped = defaultdict(list)
    for obj in objects:
        try:
            value = obj[key]
        except KeyError:
            raise Exception(repr(obj))
        seq = offices_by_category[value]
        seq.append(obj)
    return grouped


def make_template_data(json_data):
    """Return the context to use when rendering the template."""
    data = {}
    bodies = add_objects(data, json_data, 'bodies')

    bodies_by_category = _group_by(bodies, 'category_id')

    pprint(data)
    exit()

    trans = json_data['i18n']
    categories = make_categories(json_data, trans)

    offices = make_offices(json_data)
    office_count = sum([o['seat_count'] for o in offices])

    offices_by_category = _group_by(offices, 'category_id')

    data = {
        'categories': categories,
        'category_ids': CATEGORY_ORDER,
        'offices_by_category': offices_by_category,
#        'districts': make_districts(input_data),
        'offices': offices,
        'office_count': office_count,
    }

    return data


def render_template(file_name, data):
    """Render the sample template as a Unicode string.

    Argument:
      data: a dict of template variables.
    """
    template_name = os.path.join(DIR_NAME_TEMPLATE_PAGE, file_name)
    template = get_template(template_name)
    context = Context(data)
    context['current_page'] = os.path.basename(template_name)
    return template.render(context)


def make_html(json_data, output_dir, page_name=None):
    if page_name is None:
        file_names = get_template_page_file_names()
    else:
        file_names = [page_name]

    init_django()
    data = make_template_data(json_data)

    for file_name in file_names:
        html = render_template(file_name, data=data)
        print(html)
        output_path = os.path.join(output_dir, file_name)
        utils.write(output_path, html)
    if len(file_names) == 1:
        start_page = file_names[0]
    else:
        start_page = 'index.html'
    start_path = os.path.join(output_dir, start_page)

    return start_path
