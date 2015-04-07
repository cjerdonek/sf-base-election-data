
from collections import defaultdict
from datetime import date
import logging
import os
from pprint import pprint

from django.template import Context

from pyelect.html.common import NON_ENGLISH_ORDER
from pyelect.html import pages
from pyelect import lang
from pyelect.lang import I18N_SUFFIX, LANG_ENGLISH
from pyelect import utils


_log = logging.getLogger()

_JQUERY_REMOTE = "https://ajax.googleapis.com/ajax/libs/jquery/1.11.2/"
_BOOTSTRAP_REMOTE = "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/"
_BOOTSTRAP_LOCAL = 'bootstrap/'

_TABLE_OF_CONTENTS = """\
index
bodies
district_types
phrases
languages
areas
election_methods
""".strip().splitlines()

CATEGORY_ORDER = """\
category_federal
category_state
category_city_county
category_school
category_transit
category_judicial
category_party
""".strip().splitlines()


class NodeNames(object):

    election_methods = 'election_methods'
    phrases = 'phrases'


def make_template_context(data, page_base):
    page = pages.get_page_object(page_base)
    context = Context(data)
    context['current_page'] = page_base
    context['current_title'] = page.title

    objects = page.get_objects(data)
    if not objects:
        raise Exception("no objects for: {0}".format(page_base))
    context['current_objects'] = objects

    objects_by_category = page.get_objects_by_category(data, categories=CATEGORY_ORDER)
    context['current_objects_by_category'] = objects_by_category

    context['current_show_template'] = page.get_show_template()

    return context


def make_translations(id_, json_data):
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


# TODO: only the phrase ID should be stored on the object.  Also, the
#   template should be responsible for fetching and rendering the i18n.
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


def _set_context(context, json_data, keys):
    for k in keys:
        context[k] = json_data.get(k, None)


def _init_context(json_data, keys, object_id):
    context = {'id': object_id}
    _set_context(context, json_data, keys)
    return context


def _set_context_election_info(context, json_data):
    keys = [
        'election_method_id',
        'partisan',
        'term_length',  # "* year term"
        'vote_method',  # TODO: remove this.
    ]
    _set_context(context, json_data, keys)
    context['next_election_year'] = _compute_next_election_year(json_data)


def make_one_areas(object_id, json_data):
    keys = ('name', 'notes', 'wikipedia')
    context = _init_context(json_data, keys, object_id)
    return context


def make_one_bodies(object_id, json_data, phrases):
    keys = [
        'category_id',
        'district_type_id',
        'notes',
        'seat_count',
        'twitter',
        'url',
        'wikipedia'
    ]
    context = _init_context(json_data, keys, object_id)
    _set_context_election_info(context, json_data)

    # TODO: remove this call.
    add_i18n_field(context, json_data, 'name', phrases=phrases)
    return context


def make_one_district_types(object_id, json_data, bodies):
    keys = ('body_id', 'category_id', 'district_count', 'district_name_format', 'geographic',
            'name', 'parent_area_id', 'wikipedia')
    context = _init_context(json_data, keys, object_id)
    if not context['category_id']:
        body_id = context.get('body_id')
        body = bodies[body_id]
        category_id = body['category_id']
        context['category_id'] = category_id
    if 'name' not in context:
        raise Exception("name and category_id required: {0}".format(context))
    return context


def make_one_election_methods(object_id, json_data):
    keys = ('name', 'notes')
    context = _init_context(json_data, keys, object_id)
    return context


def make_one_languages(object_id, json_data):
    keys = ('name', 'code', 'notes')
    context = _init_context(json_data, keys, object_id)
    return context


def make_one_offices(object_id, json_data, phrases):
    # TODO: remove this logic.
    if 'name_i18n' not in json_data:
        return None

    keys = (
        'category_id',
        'election_method_id',
        'notes',
        'twitter',
        'url',
        'wikipedia'
    )
    context = _init_context(json_data, keys, object_id)
    _set_context_election_info(context, json_data)

    # TODO: use a real seat count.
    context['seat_count'] = 1

    # TODO: remove this.
    add_i18n_field(context, json_data, 'name', phrases=phrases)

    return context


def add_english_fields(json_data, phrases):
    """Add a simple field for each internationalized field."""
    for node_name, objects in json_data.items():
        for object_id, obj in objects.items():
            i18n_attrs = [(field, value) for field, value in obj.items() if
                          field.endswith(I18N_SUFFIX)]
            for field_name, text_id in i18n_attrs:
                simple_name = field_name.rstrip(I18N_SUFFIX)
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
def make_template_data(json_data, local_assets=False):
    """Return the context to use when rendering the template."""
    phrases = make_phrases(json_data)
    add_english_fields(json_data, phrases)

    # TODO: can we use add_context_node() here?
    category_map = make_category_map(json_data, phrases)
    categories = [category_map[id_] for id_ in CATEGORY_ORDER]

    bootstrap_prefix = _BOOTSTRAP_LOCAL if local_assets else _BOOTSTRAP_REMOTE
    jquery_prefix = "" if local_assets else _JQUERY_REMOTE

    context = {
        'categories': categories,
        'jquery_prefix': jquery_prefix,
        'language_codes': [LANG_ENGLISH] + NON_ENGLISH_ORDER,
        'bootstrap_prefix': bootstrap_prefix,
        'page_bases': _TABLE_OF_CONTENTS,
        NodeNames.phrases: phrases,
    }

    for base_name in ('areas', NodeNames.election_methods):
        add_context_node(context, json_data, base_name)

    bodies = add_context_node(context, json_data, 'bodies', phrases=phrases)

    offices = add_context_node(context, json_data, 'offices', phrases=phrases)
    office_count = sum([o['seat_count'] for o in offices.values()])
    context['office_count'] = office_count

    add_context_node(context, json_data, 'district_types', bodies=bodies)
    languages = add_context_node(context, json_data, 'languages')

    context['language_map'] = {lang['code']: lang for lang in languages.values()}

    return context
