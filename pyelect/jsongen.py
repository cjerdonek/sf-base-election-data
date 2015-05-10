
from collections import defaultdict
from copy import deepcopy
import glob
import json
import logging
import os
from pprint import pformat, pprint
import textwrap

import yaml

from pyelect import lang
from pyelect.common import utils
from pyelect.common.utils import (JSON_OUTPUT_PATH, LANG_ENGLISH, easy_format,
                                  get_i18n_field_name, get_required)
from pyelect.common import yamlutil


COURT_OF_APPEALS_ID = 'ca_court_app'

KEY_DISTRICTS = 'districts'
KEY_ID = '_id'
KEY_OFFICES = 'offices'

_LICENSE = ("The database consisting of this file is made available under "
"the Public Domain Dedication and License v1.0 whose full text can be "
"found at: http://www.opendatacommons.org/licenses/pddl/1.0/ .")

_log = logging.getLogger()


def get_json_path():
    repo_dir = utils.get_repo_dir()
    json_path = os.path.join(repo_dir, JSON_OUTPUT_PATH)
    return json_path


def get_json():
    """Read and return the JSON data."""
    json_path = get_json_path()
    with open(json_path) as f:
        data = json.load(f)

    return data


def get_fields(field_data, node_name):
    type_name = utils.types_name_to_singular(node_name)
    fields = field_data[type_name]

    return fields


def _get_yaml_data(base_name):
    """Return the object data from a YAML file."""
    rel_path = utils.get_yaml_objects_path_rel(base_name)
    data = yamlutil.read_yaml_rel(rel_path)
    meta = yamlutil.get_yaml_meta(data)
    objects = utils.get_required(data, base_name)

    return objects, meta


def yaml_to_json(yaml_data, fields):
    # TODO: construct these fields once per run instead of once per entry.
    fields = list(fields)
    fields += ["{0}_i18n".format(f) for f in fields]
    fields = set(fields)
    json_data = {f: v for f, v in yaml_data.items() if f in fields}
    return json_data


def customize_area(json_object, yaml_data, global_data):
    pass


def customize_district_type(json_object, yaml_data, global_data):
    pass


def customize_district(json_object, object_data, global_data):
    district_type = utils.get_referenced_object(global_data, object_data, 'district_type_id')

    name_format = get_required(district_type, 'district_name_format')
    name = easy_format(name_format, **object_data)
    json_object['name'] = name

    short_name_format = get_required(district_type, 'district_name_short_format')
    short_name = easy_format(short_name_format, **object_data)
    json_object['name_short'] = short_name


def customize_election_method(json_object, yaml_data, global_data):
    pass


def customize_language(json_object, yaml_data, global_data):
    pass


def customize_phrase(json_object, yaml_data, global_data):
    pass


def make_node_languages(objects, meta):

    node = {}
    for lang_id, yaml_lang in objects.items():
        json_lang = make_json_language(yaml_lang)
        node[lang_id] = json_lang

    return node


def make_node_categories(objects, meta):
    name_i18n_format = meta['name_i18n_format']

    node = {}
    for category_id, category in objects.items():
        if 'name' not in category and 'name_i18n' not in category:
            name_i18n = name_i18n_format.format(category_id)
            category['name_i18n'] = name_i18n
        node[category_id] = category

    return node


def make_node_bodies(objects, meta):
    """Return the node containing internationalized data."""
    node = {}
    for body_id, body in objects.items():
        node[body_id] = body

    return node


def make_node_offices(objects, meta, mixins):
    """Return the node containing internationalized data."""
    offices, meta = _get_yaml_data('offices')

    node = {}
    for office_id, office in offices.items():
        try:
            mixin_id = office['mixin_id']
        except KeyError:
            pass
        else:
            # Make the office "extend" from the mixin.
            office_new = deepcopy(mixins[mixin_id])
            office_new.update(office)
            del office_new['mixin_id']
            office = office_new

        node[office_id] = office

    return node


def make_court_of_appeals_division_numbers():
    return range(1, 6)


def make_court_of_appeals_district_id(division):
    return "{0}_d1_div{1}".format(COURT_OF_APPEALS_ID, division)


def make_court_of_appeals_office_type_id(office_type):
    return "{0}_{1}".format(COURT_OF_APPEALS_ID, office_type)


def make_court_of_appeals_office_id(division, office_type):
    return "{0}_d1_div{1}_{2}".format(COURT_OF_APPEALS_ID, division, office_type)


def make_court_of_appeals_district(division):
    _id = make_court_of_appeals_district_id(division)
    district = {
        KEY_ID: _id,
        'district_type_id': 'ca_court_app_d1',
        'district_code': division,
    }
    return district


def make_court_of_appeals_districts():
    districts = [make_court_of_appeals_district(c) for c in
                 make_court_of_appeals_division_numbers()]
    return districts


def make_court_of_appeals_office(division, office_type, seat_count=None):
    office = {
        KEY_ID: make_court_of_appeals_office_id(division, office_type),
        'office_type_id': make_court_of_appeals_office_type_id(office_type),
    }
    if seat_count is not None:
        office['seat_count'] = seat_count

    return office


def make_court_of_appeals():
    keys = (KEY_DISTRICTS, KEY_OFFICES)
    # TODO: make the following two lines into a helper function.
    data = {k: [] for k in keys}
    districts, offices = [data[k] for k in keys]

    division_numbers = make_court_of_appeals_division_numbers()
    for division in division_numbers:
        office = make_court_of_appeals_office(division, 'pj')
        offices.append(office)
        office = make_court_of_appeals_office(division, 'aj', seat_count=3)
        offices.append(office)

    return offices


# TODO: remove this function?
def _add_json_node_base(json_data, node, node_name, field_data):
    json_data[node_name] = node


# TODO: remove this function?
def add_json_node_legacy(json_data, base_name, field_data, **kwargs):
    """Add the node with key base_name."""
    make_node_function_name = "make_node_{0}".format(base_name)
    make_node_func = globals()[make_node_function_name]
    objects, meta = _get_yaml_data(base_name)
    node = make_node_func(objects, meta=meta, **kwargs)
    _add_json_node_base(json_data, node, base_name, field_data)


def make_json_object(object_data, fields, customize_func, object_base,
                     global_data, type_name):
    json_object = utils.create_object(object_data, fields, global_data=global_data,
                                      object_base=object_base)
    customize_func(json_object, object_data, global_data=global_data)

    # TODO: review the code below in light of the new way we are treating i18n.
    #
    # Prep the i18n data by setting the non-i18n version to simplify
    # English-only processing of the JSON file.
    for field_name in sorted(fields.keys()):
        field = fields[field_name]
        if not field.get('i18n_okay'):
            continue
        i18n_field_name = get_i18n_field_name(field_name)
        try:
            phrase = json_object[i18n_field_name]
        except KeyError:
            # Then the internationalized field is not present.
            continue
        english = phrase[LANG_ENGLISH]
        json_object[field_name] = english
        english = phrase[LANG_ENGLISH]
        json_object[field_name] = english

    utils.check_object(json_object, fields, type_name=type_name, data_type='JSON')

    return json_object


def add_json_node(json_data, node_name, field_data, **kwargs):
    """Add the node with key node_name."""
    _log.info("calculating json node: {0}".format(node_name))
    type_name = utils.types_name_to_singular(node_name)
    fields = field_data[type_name]

    objects, meta = _get_yaml_data(node_name)
    object_base = meta.get('base', {})
    customize_function_name = "customize_{0}".format(type_name)
    customize_func = globals()[customize_function_name]

    json_node = {}
    # We sort the objects for repeatability when troubleshooting.
    for object_id in sorted(objects.keys()):
        object_data = objects[object_id]
        try:
            json_object = make_json_object(object_data, fields, customize_func,
                                           object_base=object_base,
                                           global_data=json_data, type_name=type_name)
        except:
            raise Exception("while processing {0!r} object:\n-->{1}"
                            .format(type_name, object_data))


        json_node[object_id] = json_object

    _add_json_node_base(json_data, json_node, node_name, field_data)


def load_json_fields():
    data = yamlutil.read_yaml_rel(utils.JSON_FIELDS_PATH)
    fields = get_required(data, 'fields')
    return fields


# TODO
#
# # Make districts.
# districts = make_court_of_appeals_districts()
# data['districts'] = districts
#
# offices = make_court_of_appeals()
# data['court_offices'] = offices
def make_json_data():
    field_data = load_json_fields()
    mixins, meta = _get_yaml_data('mixins')

    node_names = [
        'phrases',
        'areas',
        'district_types',
        'districts',
        'election_methods',
        'languages'
    ]

    json_data ={}
    for base_name in node_names:
        add_json_node(json_data, base_name, field_data)

    # TODO: DRY up the remaining object types.
    add_json_node_legacy(json_data, 'categories', field_data)
    add_json_node_legacy(json_data, 'bodies', field_data)
    add_json_node_legacy(json_data, 'offices', field_data, mixins=mixins)

    json_data['_meta'] = {
        'license': _LICENSE
    }

    return json_data
