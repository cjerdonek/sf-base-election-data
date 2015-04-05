
from collections import defaultdict
from datetime import date
import logging
import os

from django.template import Context

from pyelect.html.common import NON_ENGLISH_ORDER
from pyelect.html import pages
from pyelect import lang
from pyelect.lang import LANG_ENGLISH
from pyelect import utils


_log = logging.getLogger()

_PAGE_BASES = """\
index
bodies
district_types
jurisdictions
phrases
languages
""".strip().splitlines()

CATEGORY_ORDER = """\
category_federal
category_state
category_city_county
category_school
category_bart
category_judicial
category_party
""".strip().splitlines()


def make_template_context(data, page_base):
    page = pages.get_page_object(page_base)
    context = Context(data)
    context['current_page'] = page_base
    context['current_title'] = page.title
    objects = page.get_objects(data)
    if not objects:
        raise Exception("no objects for: {0}".format(page_base))
    context['current_objects'] = objects
    context['current_show_template'] = page.get_show_template()

    return context


def make_phrases(id_, json_data):
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


def make_category_map(all_json, phrases):
    categories_json = all_json['categories']

    category_map = {}
    for category_id, category_json in categories_json.items():
        category = {
            'id': category_id,
        }
        add_i18n_field(category, category_json, 'name', phrases=phrases)
        category_map[category_id] = category

    return category_map


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


def make_one_bodies(body_id, data, phrases):

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


def make_one_offices(office_id, data, phrases):
    # TODO: remove this logic.
    if 'name_i18n' not in data:
        return None
    office = {
        'category_id': data.get('category_id'),
        'election_info': _make_election_info(data),
        'id': office_id,
        # TODO: use a real seat count.
        'seat_count': 1,
        'twitter': data.get('twitter'),
        'url': data.get('url')
    }

    add_i18n_field(office, data, 'name', phrases=phrases)

    return office


def _group_by(objects, key):
    grouped = defaultdict(list)
    for obj in objects.values():
        try:
            value = obj[key]
        except KeyError:
            raise Exception(repr(obj))
        seq = grouped[value]
        seq.append(obj)
    return grouped


def make_phrases(json_data):
    """Return the phrases dict for the context."""
    phrases = json_data['phrases']
    for text_id, phrase in phrases.items():
        phrase['id'] = text_id
    return phrases


def _json_to_context(json_data, keys, object_id):
    context = {k: json_data.setdefault(k, None) for k in keys}
    context['id'] = object_id
    return context


def make_one_district_types(object_id, json_data, bodies):
    keys = ('district_count', 'geographic', 'name', 'parent_area_name')
    context = _json_to_context(json_data, keys, object_id)
    body_id = json_data['body_id']
    body = bodies[body_id]
    context['body'] = body
    if not context['name']:
        raise Exception("name is required: {0}".format(context))
    return context


def make_one_languages(object_id, json_data):
    keys = ('name', 'code', 'notes')
    context = _json_to_context(json_data, keys, object_id)
    return context


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


def add_context_node(context, json_data, node_name, json_key=None, **kwargs):
    if json_key is None:
        json_key = node_name
    make_object_func_name = "make_one_{0}".format(node_name, **kwargs)
    make_object = globals()[make_object_func_name]

    json_node = json_data[json_key]

    objects = {}
    for object_id, json_object in json_node.items():
        obj = make_object(object_id, json_object, **kwargs)
        # TODO: remove this hack (used to skip offices).
        if not obj:
            continue
        obj['id'] = object_id
        objects[object_id] = obj

    context[node_name] = objects

    # Return it in case the caller wants to do something more with it.
    return objects


# TODO: switch this to use add_context_node() everywhere possible.
def make_template_data(json_data):
    """Return the context to use when rendering the template."""
    phrases = make_phrases(json_data)
    add_english_fields(json_data, phrases)

    context = {}

    bodies = add_context_node(context, json_data, 'bodies', phrases=phrases)

    add_context_node(context, json_data, 'district_types', bodies=bodies)
    languages = add_context_node(context, json_data, 'languages')

    context['language_map'] = {lang['code']: lang for lang in languages.values()}

    return context

    category_map = make_category_map(json_data, phrases)
    categories = [category_map[id_] for id_ in CATEGORY_ORDER]

    data = {}

    offices = add_context_node(data, json_data, 'offices', phrases=phrases)
    office_count = sum([o['seat_count'] for o in offices.values()])

    bodies_by_category = _group_by(bodies, 'category_id')
    offices_by_category = _group_by(offices, 'category_id')

    all_categories = set()
    for d in (bodies_by_category, offices_by_category):
        all_categories.update(d.keys())
    if not all_categories <= set(CATEGORY_ORDER):
        extra = all_categories - set(CATEGORY_ORDER)
        raise Exception("unrecognized categories: {0}".format(extra))

    context = {
        'category_map': category_map,
        'categories': categories,
        'offices': offices_by_category,
        'jurisdictions': [],
        'office_count': office_count,
        'language_codes': [LANG_ENGLISH] + NON_ENGLISH_ORDER,
        'page_bases': _PAGE_BASES,
        'phrases': phrases,
    }

