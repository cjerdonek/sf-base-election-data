
from collections import defaultdict
from datetime import date
import logging
import os
from pprint import pformat, pprint

from django.template import Context
import yaml

from pyelect.html import common
from pyelect.html.common import NON_ENGLISH_ORDER
from pyelect.html import pages
from pyelect import lang
from pyelect.lang import I18N_SUFFIX, LANG_ENGLISH
from pyelect.common import utils


_log = logging.getLogger()

_JQUERY_LOCAL = 'js/'
_JQUERY_REMOTE = "https://ajax.googleapis.com/ajax/libs/jquery/1.11.2/"
_BOOTSTRAP_REMOTE = "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/"
_BOOTSTRAP_LOCAL = 'bootstrap/'

JSON_OUTPUT_PATH = 'data/sf.json'
LICENSE_PATH = 'data/LICENSE.txt'

# The base names of the pages in the order they should be listed in the
# table of contents on each page.
_TABLE_OF_CONTENTS = """
index
bodies
districts
district_types
phrases
languages
areas
election_methods
""".strip().splitlines()

# The categories in the order they should appear in any page.
CATEGORY_ORDER = """\
category_federal
category_state
category_city_county
category_school
category_transit
category_judicial
category_party
""".splitlines()


OFFICE_BODY_COMMON_FIELDS_YAML = """\
  category_id: {}
  election_method_id: {}
  name:
    type: i18n
  notes: {}
  seed_year: {}
  term_length: {}
  twitter: {}
  url: {}
  wikipedia: {}
"""

TYPE_FIELDS_YAML = """\
body:
  district_type_id:
    required: true
  jurisdiction_area_id:
    required: true
  member_name:
    required: false
  office_name: {}
  office_name_format: {}
  partisan:
    required: true
  seat_count:
    required: true
  seat_name_format: {}
category:
  name:
    type: i18n
district:
  district_code: {}
  district_type_id: {}
  name:
    required: true
  number: {}
  wikipedia: {}
district_type:
  body_id: {}
  category_id: {}
  district_count: {}
  district_name_short_format: {}
  district_name_format:
    # Require this because it is used to generate the name.
    required: true
  geographic: {}
  name:
    required: true
  description_plural:
    required: true
  parent_area_id: {}
  wikipedia: {}
office:
  body_id: {}
  district_id: {}
  # TODO: make this required
  jurisdiction_area_id: {}
  partisan: {}
  seat: {}
  seat_name: {}
"""


class NodeNames(object):

    election_methods = 'election_methods'
    phrases = 'phrases'


def _make_category_ordering():
    ordering = {}
    for i, category_id in enumerate(CATEGORY_ORDER, start=1):
        ordering[category_id] = i
    return ordering


def make_template_context(html_data, page_base):
    page = pages.get_page_object(page_base)
    context = Context(html_data)
    context['current_page'] = page_base
    context['current_title'] = page.title

    objects = page.get_objects(html_data)
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


def make_phrases(json_data):
    """Return the phrases dict for the context."""
    phrases = json_data['phrases']
    for text_id, phrase in phrases.items():
        # TODO: put this validation logic elsewhere.
        if " " in text_id:
            raise Exception("white space: {0}".format(text_id))
        phrase['id'] = text_id
    return phrases


# TODO: remove this function in favor of _set_html_object_fields().
def _set_html_object_data(html_data, json_data, keys):
    for key in keys:
        value = json_data.get(key, None)
        html_data[key] = value
        # Include internationalized values when they are available, for all fields.
        i18n_key = lang.get_i18n_field_name(key)
        html_data[i18n_key] = json_data.get(i18n_key, None)


def _set_html_object_fields(html_data, json_data, fields):
    for field_name in sorted(fields.keys()):
        field = fields[field_name]
        field_type = field.get('type', None)
        value = json_data.get(field_name, None)
        html_data[field_name] = value
        if field_type == 'i18n':
            # Include internationalized values when they are available, for all fields.
            i18n_field_name = lang.get_i18n_field_name(field_name)
            html_data[i18n_field_name] = json_data.get(i18n_field_name, None)


# TODO: remove this function in favor of _make_html_object2().
def _make_html_object(json_data, keys, object_id):
    context = {'id': object_id}
    _set_html_object_data(context, json_data, keys)
    return context


def _make_html_object2(json_data, fields, object_id):
    context = {'id': object_id}
    _set_html_object_fields(context, json_data, fields)
    return context


def _set_html_election_data(html_data, json_data):
    html_data['next_election_year'] = _compute_next_election_year(json_data)


def make_one_areas(object_id, json_data, html_data=None):
    keys = [
        'name',
        'notes',
        'wikipedia'
    ]
    context = _make_html_object(json_data, keys, object_id)
    return context


def make_one_body2(html_obj, html_data, json_obj):
    # TODO: DRY this up with make_one_offices2().
    _set_html_election_data(html_obj, html_obj)
    _set_category_order(html_data, html_obj)

    return html_obj


def make_one_category2(html_obj, html_data, json_obj, ordering):
    category_id = html_obj['id']
    order = ordering[category_id]
    html_obj['order'] = order

    return html_obj


def make_one_district_type2(html_obj, html_data, json_obj):
    name_format = html_obj['district_name_format']
    if name_format is None:
        name = html_obj['name']
        name_format = "{name} {{number}}".format(name=name)
        html_obj['district_name_format'] = name_format

    if not html_obj['category_id']:
        body = utils.get_referenced_object(html_data, json_obj, 'body_id')
        category_id = body.get('category_id')
        html_obj['category_id'] = category_id

    _set_category_order(html_data, html_obj)
    # TODO: revisit message re: category_id.
    if 'name' not in html_obj:
        raise Exception("name and category_id required: {0}".format(context))

    return html_obj


# TODO: inherit properties from district type (like office from body).
def make_one_district2(html_obj, html_data, json_obj):
    district_type = utils.get_referenced_object(html_data, json_obj, 'district_type_id')
    category_id = district_type['category_id']

    # TODO: remove this.
    name_short_format = district_type['district_name_short_format']
    if name_short_format is not None:
        name_short = format(name_short_format, **html_obj)
        html_obj['name_short'] = name_short

    html_obj['category_id'] = category_id
    _set_category_order(html_data, html_obj)

    return html_obj


def make_one_election_methods(object_id, json_data, html_data=None):
    keys = [
        'name',
        'notes',
        'wikipedia',
    ]
    context = _make_html_object(json_data, keys, object_id)
    return context


def make_one_languages(object_id, json_data, html_data=None):
    keys = ('name', 'code', 'notes')
    context = _make_html_object(json_data, keys, object_id)
    return context


def _set_category_order(html_data, html_obj):
    category_id = utils.get_required(html_obj, 'category_id')
    if category_id is None:
        category_order = 0
    else:
        categories = html_data['categories']
        category = categories[category_id]
        category_order = category['order']
    html_obj['category_order'] = category_order


# TODO: simplify this and DRY up with make_one_bodies().
def make_one_office2(html_obj, html_data, json_obj):
    # TODO: come up with a pattern for inheriting properties between
    # objects for which a relationship exists.
    inherited_keys = ('partisan', 'seed_year', 'term_length')
    effective = {k: html_obj[k] for k in inherited_keys}

    phrases = html_data[NodeNames.phrases]
    if 'body_id' in json_obj:
        district = get_from_html_data(html_data, json_obj, 'district_id')
        if district is None:
            short_name = None
        else:
            short_name = district.get('name_short') or district['name']
        html_obj['district_name_short'] = short_name

        body = get_from_html_data(html_data, json_obj, 'body_id')
        html_obj['category_id'] = body['category_id']
        member_name = body['member_name']
        html_obj['member_name'] = member_name

        seat_name_format = body['seat_name_format']
        if seat_name_format is not None:
            seat_name = seat_name_format.format(**html_obj)
            html_obj['seat_name'] = seat_name

        office_name_format = body['office_name_format']
        if office_name_format is None:
            html_obj['name'] = body['office_name']
        else:
            office_name = office_name_format.format(**html_obj)
            html_obj['name'] = office_name
        for k in inherited_keys:
            if effective[k] is None:
                effective[k] = body[k]

    _set_html_election_data(html_obj, effective)
    _set_category_order(html_data, html_obj)

    # TODO: remove this temporary check.
    if not html_obj['category_id'] or not html_obj['name']:
        return None

    # TODO: use a real seat count.
    html_obj['seat_count'] = 1

    return html_obj


def _add_english_fields_object(phrases, object_id, obj):
    # TODO: put this validation logic elsewhere.
    if " " in object_id:
        raise Exception("white space: {0}".format(object_id))
    i18n_attrs = [(field, value) for field, value in obj.items() if
                  field.endswith(I18N_SUFFIX)]
    for field_name, text_id in i18n_attrs:
        simple_name = field_name.rstrip("_" + I18N_SUFFIX)
        # TODO: make a general helper function out of this?
        try:
            translations = phrases[text_id]
        except KeyError:
            raise Exception("object (node={node_name!r}, id={object_id!r}): {0}"
                            .format(obj, node_name=node_name, object_id=object_id))
        english = translations[LANG_ENGLISH]
        _log.debug("Setting field: {0}.{1}={2}".format(object_id, simple_name, english))
        obj[simple_name] = english


def add_english_fields(json_data, phrases):
    """Add a simple field for each internationalized field."""
    for node_name, objects in json_data.items():
        if node_name.startswith("_"):
            # Skip metadata.
            continue
        for object_id, obj in objects.items():
            try:
                _add_english_fields_object(phrases, object_id, obj)
            except:
                raise Exception("object (id={0}): {1}".format(object_id, obj))


# TODO: remove this in favor of add_html_node().
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


def add_html_node(base_name, html_data, json_data, field_data, json_key=None, **kwargs):
    type_name = utils.types_name_to_singular(base_name)

    # TODO: document json_key vs. base_name.
    if json_key is None:
        json_key = base_name
    make_object_func_name = "make_one_{0}2".format(type_name, **kwargs)
    set_object_fields = globals()[make_object_func_name]

    fields = field_data[type_name]
    json_node = json_data[json_key]

    objects = {}

    # Sort the items to get repeatability.  This helps when troubleshooting
    # issues, so that the same item will error out when running a second time.
    for object_id in sorted(json_node.keys()):
        json_obj = json_node[object_id]
        html_obj = _make_html_object2(json_obj, fields, object_id)
        set_object_fields(html_obj, html_data, json_obj, **kwargs)
        # TODO: remove this hack (used to skip offices).
        if html_obj['name'] is None:
            continue
        utils.check_object(html_obj, fields, type_name=type_name, data_type='HTML')
        objects[object_id] = html_obj

    html_data[base_name] = objects

    # Return it in case the caller wants to do something more with it.
    return objects


def load_field_data():
    field_data = yaml.load(TYPE_FIELDS_YAML)
    for name in ('body', 'office'):
        fields = field_data[name]
        extra_fields = yaml.load(OFFICE_BODY_COMMON_FIELDS_YAML)
        fields.update(extra_fields)

    return field_data


# TODO: switch this to use add_context_node() everywhere possible.
def make_html_data(json_data, local_assets=False):
    """Return the template data that will be used to create the context."""
    category_ordering = _make_category_ordering()

    phrases = make_phrases(json_data)
    add_english_fields(json_data, phrases)

    bootstrap_prefix = _BOOTSTRAP_LOCAL if local_assets else _BOOTSTRAP_REMOTE
    jquery_prefix = _JQUERY_LOCAL if local_assets else _JQUERY_REMOTE

    html_data = {
        'jquery_prefix': jquery_prefix,
        'json_path': JSON_OUTPUT_PATH,
        'language_codes': [LANG_ENGLISH] + NON_ENGLISH_ORDER,
        'license_path': LICENSE_PATH,
        'bootstrap_prefix': bootstrap_prefix,
        'page_bases': _TABLE_OF_CONTENTS,
        NodeNames.phrases: phrases,
    }

    base_names = [
        'areas',
        NodeNames.election_methods,
    ]
    for base_name in base_names:
        add_context_node(html_data, json_data, base_name)

    field_data = load_field_data()

    def _add_node(base_name, **kwargs):
        add_html_node(base_name, html_data, json_data, field_data, **kwargs)

    _add_node('categories', ordering=category_ordering)

    base_names = [
        'bodies',
        'district_types',
        'districts',
        'offices',
    ]
    for base_name in base_names:
        _add_node(base_name)

    offices = html_data['offices']
    office_count = 0
    for office in offices.values():
        office_count += office['seat_count']
    html_data['office_count'] = office_count

    # Compute: district_count_sf
    district_types = html_data['district_types']
    for district in html_data['districts'].values():
        district_type_id = district['district_type_id']
        district_type = district_types[district_type_id]
        try:
            district_type['district_count_sf'] += 1
        except KeyError:
            district_type['district_count_sf'] = 1

    languages = add_context_node(html_data, json_data, 'languages')

    html_data['language_map'] = {lang['code']: lang for lang in languages.values()}

    return html_data
