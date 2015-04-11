
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
_REL_PATH_JSON_DATA = "data/sf.json"

_LICENSE = ("The database consisting of this file is made available under "
"the Public Domain Dedication and License v1.0 whose full text can be "
"found at: http://www.opendatacommons.org/licenses/pddl/1.0/ .")


def get_rel_path_json_data():
    return _REL_PATH_JSON_DATA


def _get_rel_path_objects_dir():
    return os.path.join(utils.DIR_PRE_DATA, DIR_NAME_OBJECTS)


def get_json_path():
    repo_dir = utils.get_repo_dir()
    rel_path = get_rel_path_json_data()
    json_path = os.path.join(repo_dir, rel_path)
    return json_path


def get_json():
    """Read and return the JSON data."""
    json_path = get_json_path()
    with open(json_path) as f:
        data = json.load(f)

    return data


def _get_yaml_data(base_name):
    """Return the object data from a YAML file."""
    rel_path = _get_rel_path_objects_dir()
    data = utils.read_yaml_rel(rel_path, file_base=base_name)
    meta = utils.get_yaml_meta(data)
    objects = utils.get_required(data, base_name)

    return objects, meta


def yaml_to_json(yaml_data, fields):
    # TODO: construct these fields once per run instead of once per entry.
    fields = list(fields)
    fields += ["{0}_i18n".format(f) for f in fields]
    fields = set(fields)
    json_data = {f: v for f, v in yaml_data.items() if f in fields}
    return json_data


def make_object_areas(yaml_data):
    return yaml_data


def make_object_district_types(yaml_data):
    return yaml_data


def make_object_election_methods(yaml_data):
    return yaml_data


def make_object_languages(yaml_data):
    return yaml_data


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


# TODO: remove this function.
def add_source(data, source_name):
    source_data = get_yaml(source_name)
    for key, value in source_data.items():
        data[key] = value


def add_json_node_i18n(json_data):
    node = make_node_i18n()
    _add_json_node_base(json_data, node, 'phrases')


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


def _add_json_node_base(json_data, node, node_name):
    check_node(node, node_name)
    json_data[node_name] = node


# TODO: remove this function?
def add_json_node(json_data, base_name, **kwargs):
    """Add the node with key base_name."""
    make_node_function_name = "make_node_{0}".format(base_name)
    make_node_func = globals()[make_node_function_name]
    objects, meta = _get_yaml_data(base_name)
    node = make_node_func(objects, meta=meta, **kwargs)
    _add_json_node_base(json_data, node, base_name)


def add_json_node_simple(json_data, base_name, **kwargs):
    """Add the node with key base_name."""
    objects, meta = _get_yaml_data(base_name)
    make_object_function_name = "make_object_{0}".format(base_name)
    make_object = globals()[make_object_function_name]

    json_node = {}
    for object_id, yaml_data in objects.items():
        json_object = make_object(yaml_data)
        json_node[object_id] = json_object

    _add_json_node_base(json_data, json_node, base_name)


# TODO
# add_source(data, 'office_types')
#
# # Make districts.
# districts = make_court_of_appeals_districts()
# data['districts'] = districts
#
# offices = make_court_of_appeals()
# data['court_offices'] = offices
def make_json_data():
    mixins, meta = _get_yaml_data('mixins')

    json_data ={
        '_meta': {
            'license': _LICENSE
        }
    }

    for base_name in ('areas', 'district_types', 'election_methods', 'languages'):
        add_json_node_simple(json_data, base_name)

    # TODO: DRY up the remaining object types.
    add_json_node(json_data, 'categories')
    add_json_node(json_data, 'bodies')
    add_json_node(json_data, 'offices', mixins=mixins)
    add_json_node_i18n(json_data)

    return json_data
