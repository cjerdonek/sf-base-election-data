
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
from pyelect.common.utils import get_required, Field, ObjectType, LANG_ENGLISH
from pyelect.common import yamlutil


COURT_OF_APPEALS_ID = 'ca_court_app'

KEY_DISTRICTS = 'districts'
KEY_ID = '_id'
KEY_OFFICES = 'offices'

_LICENSE = ("The database consisting of this file is made available under "
"the Public Domain Dedication and License v1.0 whose full text can be "
"found at: http://www.opendatacommons.org/licenses/pddl/1.0/ .")

_log = logging.getLogger()


def get_yaml_data(base_name):
    """Return the object data from a YAML file."""
    rel_path = utils.get_yaml_objects_path_rel(base_name)
    data = yamlutil.read_yaml_rel(rel_path)
    meta = yamlutil.get_yaml_meta(data)
    objects = get_required(data, base_name)

    return objects, meta


def get_fields(field_data, node_name):
    type_name = utils.types_name_to_singular(node_name)
    fields = field_data[type_name]

    return fields


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


def make_json_object(obj, customize_func, object_id, object_base,
                     object_type, object_types, global_data, mixins):
    json_object = utils.create_object(obj, object_id=object_id, object_base=object_base,
                                      object_type=object_type, object_types=object_types,
                                      global_data=global_data, mixins=mixins)
    if customize_func is not None:
        customize_func(json_object, obj, global_data=global_data)

    utils.check_object(json_object, object_id=object_id, object_type=object_type,
                       object_types=object_types, data_type='json')

    return json_object


def add_json_node(json_data, node_name, object_types, mixins, **kwargs):
    """Add the node with key node_name."""
    _log.info("calculating json node: {0}".format(node_name))
    type_name = utils.types_name_to_singular(node_name)
    object_type = object_types[type_name]

    objects, meta = get_yaml_data(node_name)
    object_base = meta.get('base', {})
    # Keep the lines below around for convenience in case we need them.
    # customize_function_name = "customize_{0}".format(type_name)
    # customize_func = globals()[customize_function_name] if object_type.customized else None

    json_node = {}
    # We sort for repeatability when troubleshooting.
    for object_id, object_data in sorted(objects.items()):
        try:
            json_object = make_json_object(object_data, customize_func=None,
                                           object_id=object_id, object_base=object_base,
                                           object_type=object_type, object_types=object_types,
                                           global_data=json_data, mixins=mixins)
        except Exception:
            raise Exception("while processing {0!r} object:\n-->\n{1}"
                            .format(type_name, pformat(object_data)))
        json_node[object_id] = json_object

    json_data[node_name] = json_node


def make_json_data():
    object_types = yamlutil.load_type_definitions(utils.JSON_TYPES_PATH)
    mixins, meta = get_yaml_data('mixins')
    del meta

    node_names = [
        'phrases',
        'areas',
        'categories',
        'district_types',
        'districts',
        'election_methods',
        'languages',
        'bodies',
        'offices',
    ]

    json_data ={}
    for base_name in node_names:
        add_json_node(json_data, base_name, object_types=object_types, mixins=mixins)

    # Remove the i18n form when only English is present to reduce clutter.
    # We can only do this after all nodes have been processed.
    for node_name in node_names:
        json_node = json_data[node_name]
        type_name = utils.types_name_to_singular(node_name)
        object_type = object_types[type_name]
        # We sort for repeatability when troubleshooting.
        for object_id, json_object in sorted(json_node.items()):  # sort for reproducibility.
            for field in object_type.fields():
                if not field.is_i18n or field.normalized_name not in json_object:
                    continue
                phrase = json_object[field.normalized_name]
                if list(phrase.keys()) == [LANG_ENGLISH]:
                    del json_object[field.normalized_name]

    json_data['_meta'] = {
        'license': _LICENSE
    }

    return json_data
