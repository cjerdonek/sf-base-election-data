"""Support for making html."""

import os

from jinja2 import Environment, FileSystemLoader

from pyelect import lang
from pyelect import utils


NON_ENGLISH_ORDER = [lang.LANG_CH, lang.LANG_ES, lang.LANG_FI]

def _get_template_dir():
    repo_dir = utils.get_repo_dir()
    return os.path.join(repo_dir, 'templates')


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
    non_english = filter(None, non_english)

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


def make_office(all_json, data):
    categories = all_json['categories']
    trans = all_json['i18n']

    # TODO: incorporate a real ID.
    office_id = data.get('name_i18n')
    # TODO: do not skip any offices.
    if office_id is None:
        return None

    name_i18n = _get_i18n(trans, data, 'name')

    try:
        category_id = data['category_id']
    except KeyError:
        category_name_i18n = None
    else:
        category = categories[category_id]
        category_name_i18n = _get_i18n(trans, category, 'name')

    term_length = data.get('term_length')
    if term_length:
        term_length = "{0} year term".format(term_length)

    office = {
        'category_name_i18n': category_name_i18n,
        'id': office_id,
        'name_i18n': name_i18n,
        # TODO: use a real seat count.
        'seat_count': 1,
        'term_length': term_length,
        'vote_method': data.get('vote_method'),
        'url': data.get('url')
    }
    print(office)
    return office


def make_offices(all_json):
    offices = [make_office(all_json, v) for v in all_json['offices']]
    offices = list(filter(None, offices))
    return offices


def make_template_data(all_json):
    """Return the context to use when rendering the template."""
    offices = make_offices(all_json)
    office_count = sum([o['seat_count'] for o in offices])

    data = {
#        'districts': make_districts(input_data),
        'offices': offices,
        'office_count': office_count,
    }

    return data


def render_template(template_name, data):
    """Render the sample template as a Unicode string.

    Argument:
      data: a dict of template variables.
    """
    template_dir = _get_template_dir()
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)
    return template.render(data)


def make_html(json_data):
    template_data = make_template_data(json_data)
    html = render_template('sample.html', template_data)
    return html
