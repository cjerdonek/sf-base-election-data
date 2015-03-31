
from collections import defaultdict
from copy import deepcopy
import glob
import json
import os
from pprint import pprint
import textwrap

from pyelect import lang
from pyelect import utils


COURT_OF_APPEALS_ID = 'ca_court_app'

KEY_DISTRICTS = 'districts'
KEY_ID = '_id'
KEY_OFFICES = 'offices'

DIR_NAME_OBJECTS = 'objects'


def get_rel_path_objects_dir():
    return os.path.join(utils.DIR_PRE_DATA, DIR_NAME_OBJECTS)


def get_object_data(base_name):
    rel_path = get_rel_path_objects_dir()
    data = utils.read_yaml_rel(rel_path, file_base=base_name)
    meta = utils.get_yaml_meta(data)
    objects = utils.get_required(data, base_name)

    return objects, meta


def make_node_categories(objects, meta):
    name_i18n_format = meta['name_i18n_format']

    node = {}
    for category_id, category in objects.items():
        name_i18n = name_i18n_format.format(category_id)
        category['name_i18n'] = name_i18n
        node[category_id] = category

    return node


def make_node_i18n():
    """Return the node containing internationalized data."""
    data = lang.get_phrases()
    return data


def make_node_bodies(objects, meta):
    """Return the node containing internationalized data."""
    node = {}
    for body_id, body in objects.items():
        node[body_id] = body

    return node


def make_node_offices(objects, meta, mixins):
    """Return the node containing internationalized data."""
    offices, meta = get_object_data('offices')

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


def make_node_languages(objects, meta):
    fields = ('name', 'code', 'notes')

    node = {}
    for lang_id, lang in objects.items():
        node_obj = {k: v for k, v in lang.items() if k in fields}
        node[lang_id] = node_obj

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


# TODO: remove this function.
def add_source(data, source_name):
    source_data = get_yaml(source_name)
    for key, value in source_data.items():
        data[key] = value


def check_node(node, node_name):
    allowed_types = (bool, int, str)
    for object_id, obj in node.items():
        for attr, value in obj.items():
            if type(value) not in allowed_types:
                err = textwrap.dedent("""\
                json node with key "{node_name}" failed sanity check.
                  object_id: "{object_id}"
                  object attribute name: "{attr_name}"
                  attribute value has type {value_type} (only allowed types are: {allowed_types})
                  object:
                -->{object}
                """.format(node_name=node_name, object_id=object_id, attr_name=attr,
                           value_type=type(value), allowed_types=allowed_types,
                           object=obj))
                raise Exception(err)


def _add_node_base(json_data, node, node_name):
    check_node(node, node_name)
    json_data[node_name] = node


def add_node_object(json_data, node_name, **kwargs):
    make_node_function_name = "make_node_{0}".format(node_name)
    make_node_func = globals()[make_node_function_name]
    objects, meta = get_object_data(node_name)
    node = make_node_func(objects, meta=meta, **kwargs)
    _add_node_base(json_data, node, node_name)


def add_node_i18n(json_data):
    node = make_node_i18n()
    _add_node_base(json_data, node, 'i18n')


def make_all_data():
    mixins, meta = get_object_data('mixins')

    data ={}

    add_node_object(data, 'categories')
    add_node_i18n(data)
    add_node_object(data, 'languages')
    add_node_object(data, 'bodies')
    add_node_object(data, 'offices', mixins=mixins)

    return data

    # TODO
    add_source(data, 'district_types')
    add_source(data, 'office_types')

    # Make districts.
    districts = make_court_of_appeals_districts()
    data['districts'] = districts

    offices = make_court_of_appeals()
    data['court_offices'] = offices

    return data
