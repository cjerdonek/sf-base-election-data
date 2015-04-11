
from collections import defaultdict
from datetime import date
import logging
import os
from pprint import pprint

from django.template import Context

from pyelect.html.common import CATEGORY_ORDER, NON_ENGLISH_ORDER
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

OFFICE_BODY_COMMON_KEYS = [
    'category_id',
    'election_method_id',
    'jurisdiction_id',
    'name',
    'notes',
    'partisan',
    'seed_year',
    'term_length',
    'twitter',
    'url',
    'wikipedia'
]


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


# TODO: use the pattern that other objects use.
def make_category_map(all_json, phrases):
    keys = [
        'name',
    ]

    categories_json = all_json['categories']

    category_map = {}
    for category_id, category_json in categories_json.items():
        category = _init_html_object_data(category_json, keys, category_id)
        category_map[category_id] = category

    return category_map


def _compute_next_election_year(json_data):
    term_length = json_data.get('term_length')
    # TODO: make this required.
    if not term_length:
        return None
    seed_year = json_data.get('seed_year')
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
        if " " in text_id:
            raise Exception("white space: {0}".format(text_id))
        phrase['id'] = text_id
    return phrases


def _set_html_object_data(html_data, json_data, keys):
    for key in keys:
        value = json_data.get(key, None)
        html_data[key] = value
        # Include internationalized values when they are available, for all fields.
        i18n_key = lang.get_i18n_field_name(key)
        html_data[i18n_key] = json_data.get(i18n_key, None)


def _init_html_object_data(json_data, keys, object_id):
    context = {'id': object_id}
    _set_html_object_data(context, json_data, keys)
    return context


def _set_html_election_data(html_data, json_data):
    html_data['next_election_year'] = _compute_next_election_year(json_data)


def make_one_areas(object_id, json_data, html_data=None):
    keys = ('name', 'notes', 'wikipedia')
    context = _init_html_object_data(json_data, keys, object_id)
    return context


def make_one_bodies(object_id, json_data, phrases, html_data=None):
    keys = [
        'district_type_id',
        'member_name',
        'office_name',
        'office_name_format',
        'seat_count',
        'seat_name_format',
    ]
    keys.extend(OFFICE_BODY_COMMON_KEYS)
    html_data = _init_html_object_data(json_data, keys, object_id)
    _set_html_election_data(html_data, json_data)

    return html_data


def make_one_district_types(object_id, json_data, bodies, html_data=None):
    keys = ('body_id', 'category_id', 'district_count', 'district_name_format', 'geographic',
            'name', 'parent_area_id', 'wikipedia')
    context = _init_html_object_data(json_data, keys, object_id)
    if not context['category_id']:
        body_id = context.get('body_id')
        body = bodies[body_id]
        category_id = body['category_id']
        context['category_id'] = category_id
    if 'name' not in context:
        raise Exception("name and category_id required: {0}".format(context))
    return context


def make_one_election_methods(object_id, json_data, html_data=None):
    keys = [
        'name',
        'notes',
        'wikipedia',
    ]
    context = _init_html_object_data(json_data, keys, object_id)
    return context


def make_one_languages(object_id, json_data, html_data=None):
    keys = ('name', 'code', 'notes')
    context = _init_html_object_data(json_data, keys, object_id)
    return context


# TODO: simplify this and DRY up with make_one_bodies().
def make_one_offices(object_id, json_data, html_data=None):
    keys = [
        'body_id',
        'district_id',
        'seat',
        'seat_name',
    ]
    keys.extend(OFFICE_BODY_COMMON_KEYS)
    html_item = _init_html_object_data(json_data, keys, object_id)
    html_item['district_name'] = html_item['district_id']

    inherited_keys = ('seed_year', 'term_length')
    effective = {k: html_item[k] for k in inherited_keys}

    phrases = html_data[NodeNames.phrases]
    if 'body_id' in json_data:
        body_id = json_data['body_id']
        bodies = html_data['bodies']
        body = utils.get_required(bodies, body_id)
        html_item['category_id'] = body['category_id']
        member_name = body['member_name']
        html_item['member_name'] = member_name

        seat_name_format = body['seat_name_format']
        if seat_name_format is not None:
            seat_name = seat_name_format.format(**html_item)
            html_item['seat_name'] = seat_name

        office_name_format = body['office_name_format']
        if office_name_format is None:
            html_item['name'] = body['office_name']
        else:
            office_name = office_name_format.format(**html_item)
            html_item['name'] = office_name
        for k in inherited_keys:
            if effective[k] is None:
                effective[k] = body[k]

    _set_html_election_data(html_item, effective)

    # TODO: remove this temporary check.
    if not html_item['category_id'] or not html_item['name']:
        return None

    # TODO: use a real seat count.
    html_item['seat_count'] = 1

    assert html_item['name']
    return html_item


def add_english_fields(json_data, phrases):
    """Add a simple field for each internationalized field."""
    for node_name, objects in json_data.items():
        for object_id, obj in objects.items():
            if " " in object_id:
                raise Exception("white space: {0}".format(object_id))
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
        obj = make_object(object_id, json_object, html_data=context, **kwargs)
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

    offices = add_context_node(context, json_data, 'offices')
    office_count = sum([o['seat_count'] for o in offices.values()])
    context['office_count'] = office_count

    add_context_node(context, json_data, 'district_types', bodies=bodies)
    languages = add_context_node(context, json_data, 'languages')

    context['language_map'] = {lang['code']: lang for lang in languages.values()}

    return context
