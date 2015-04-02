"""Support for making html."""

from collections import defaultdict
from datetime import date
import json
import logging
import os
from pprint import pprint

from django.template import Context
from django.template.loader import get_template

from pyelect import jsongen
from pyelect import lang
from pyelect.lang import LANG_ENGLISH
from pyelect import templateconfig
from pyelect import utils


CATEGORY_ORDER = """\
category_federal
category_state
category_city_county
category_school
category_bart
category_judicial
category_party
""".strip().splitlines()

DIR_NAME_HTML_OUTPUT = 'html'
NON_ENGLISH_ORDER = [lang.LANG_CHINESE, lang.LANG_SPANISH, lang.LANG_FILIPINO]

_log = logging.getLogger()

# TODO: remove this function.
def _get_i18n(trans, obj_json, key_base):
    if key_base in obj_json:
        english = utils.get_required(obj_json, 'name')
        words = {LANG_ENGLISH: english}
        non_english = []
    else:
        field_name = lang.get_i18n_field_name(key_base)
        text_id = utils.get_required(obj_json, field_name, message="translation")
        words = utils.get_required(trans, text_id)
        non_english = [words[lang] for lang in words.keys() if lang in NON_ENGLISH_ORDER]
    english = words[LANG_ENGLISH]
    # Remove empty strings.
    non_english = list(filter(None, non_english))

    i18n = {
        'english': english,
        'non_english': non_english
    }

    return i18n


def make_languages_one(lang_id, data):
    keys = ('name', 'code', 'notes')
    # TODO: make this into a helper function.
    lang = {k: data.setdefault(k, None) for k in keys}
    lang['id'] = lang_id
    return lang


def make_translations_one(id_, json_data):
    if not json_data[LANG_ENGLISH]:
        return None
    json_data['id'] = id_
    return json_data


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
    seed_year = office_json.get('seed_year')
    if seed_year is None:
        return None

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
    if next_election_year is not None:
        next_election_text = "{0} next".format(next_election_year)
    else:
        next_election_text = None

    term_length = data.get('term_length')
    if term_length:
        term_length = "{0} year term".format(term_length)

    partisan = data.get('partisan')
    if partisan is not None:
        partisan_text = "{0}partisan".format("" if partisan else "non-")
    else:
        partisan_text = None

    return list(filter(None, [term_length, next_election_text, vote_method, partisan_text]))


def add_i18n_field(obj, json_data, field_name, phrases):
    # We require that the simple field be present in the JSON.
    english = json_data[field_name]
    obj[field_name] = english

    i18n_field_name = lang.get_i18n_field_name(field_name)
    try:
        text_id = json_data[i18n_field_name]
    except KeyError:
        return
    translations = phrases[text_id]
    obj[i18n_field_name] = translations


def make_bodies_one(body_id, data, phrases, **kwargs):

    category_id = utils.get_required(data, 'category_id')

    body = {
        'category_id': category_id,
        'district_count': data.get('district_count'),
        'election_info': _make_election_info(data),
        'notes': data.get('notes'),
        'seat_count': data.get('seat_count'),
        'twitter': data.get('twitter'),
        'url': data.get('url'),
        'wikipedia': data.get('wikipedia')
    }

    add_i18n_field(body, data, 'name', phrases=phrases)

    return body


def make_offices_one(office_id, data, trans):
    # TODO: remove this logic.
    if 'name_i18n' not in data:
        return None

    name_i18n = _get_i18n(trans, data, 'name')

    office = {
        'category_id': data.get('category_id'),
        'election_info': _make_election_info(data),
        'id': office_id,
        'name_i18n': name_i18n,
        # TODO: use a real seat count.
        'seat_count': 1,
        'twitter': data.get('twitter'),
        'url': data.get('url')
    }

    return office


def add_objects(template_data, json_data, node_name, json_key=None, **kwargs):
    if json_key is None:
        json_key = node_name
    make_object_func_name = "make_{0}_one".format(node_name)
    make_object = globals()[make_object_func_name]

    json_node = json_data[json_key]

    objects = []
    object_ids = sorted(json_node.keys())
    for object_id in object_ids:
        data = json_node[object_id]
        obj = make_object(object_id, data, **kwargs)
        # TODO: remove this hack (used to skip offices).
        if not obj:
            continue
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
        seq = grouped[value]
        seq.append(obj)
    return grouped


def make_translations(json_data):
    translations = json_data['i18n']
    new_translations = {}
    for text_id, text in translations.items():
        if not text[LANG_ENGLISH]:
            continue
        text['id'] = text_id
    return translations


def add_english_fields(json_data, phrases):
    """Add a simple field for each internationalized field."""
    for node_name, objects in json_data.items():
        for object_id, obj in objects.items():
            i18n_attrs = [(field, value) for field, value in obj.items() if
                          field.endswith(lang.I18N_SUFFIX)]
            for field_name, text_id in i18n_attrs:
                simple_name = field_name.rstrip(lang.I18N_SUFFIX)
                # TODO: make a general helper function out of this?
                try:
                    translations = phrases[text_id]
                except KeyError:
                    raise Exception("object (node={node_name!r}, id={object_id!r}): {0}"
                                    .format(obj, node_name=node_name, object_id=object_id))
                english = translations[LANG_ENGLISH]
                _log.debug("Setting field: {0}.{1}={2}".format(object_id, simple_name, english))
                obj[simple_name] = english


def make_template_data():
    """Return the context to use when rendering the template."""
    json_data = jsongen.get_json()

    phrases = json_data['i18n']
    add_english_fields(json_data, phrases)

    phrases = make_translations(json_data)

    data = {}
    bodies = add_objects(data, json_data, 'bodies', phrases=phrases)

    categories = make_categories(json_data, phrases)


    offices = add_objects(data, json_data, 'offices', trans=phrases)
    office_count = sum([o['seat_count'] for o in offices])

    bodies_by_category = _group_by(bodies, 'category_id')
    offices_by_category = _group_by(offices, 'category_id')

    all_categories = set()
    for d in (bodies_by_category, offices_by_category):
        all_categories.update(d.keys())
    if not all_categories <= set(CATEGORY_ORDER):
        extra = all_categories - set(CATEGORY_ORDER)
        raise Exception("unrecognized categories: {0}".format(extra))

    data = {
        'bodies_count': len(bodies),
        'bodies_by_category': bodies_by_category,
        'categories': categories,
        'category_ids': CATEGORY_ORDER,
        'offices_by_category': offices_by_category,
#        'districts': make_districts(input_data),
        'office_count': office_count,
        'non_english_codes': lang.LANGS_NON_ENGLISH,
        'translations': phrases,
    }

    language_list = add_objects(data, json_data, 'languages')
    data['language_map'] = {lang['code']: lang for lang in language_list}

    return data


def render_template(file_name, data):
    """Render the sample template as a Unicode string.

    Argument:
      data: a dict of template variables.
    """
    template_name = templateconfig.get_page_template_name(file_name)
    template = get_template(template_name)
    context = Context(data)
    context['current_page'] = os.path.basename(template_name)
    return template.render(context)


def make_html(output_dir, page_name=None, print_html=False):

    if page_name is None:
        file_names = templateconfig.get_template_page_file_names()
    else:
        file_names = [page_name]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    data = make_template_data()

    templateconfig.init_django()

    for file_name in file_names:
        html = render_template(file_name, data=data)
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
