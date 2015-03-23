
from collections import defaultdict
from copy import deepcopy
import glob
import json
import os
from pprint import pprint

from pyelect import lang
from pyelect import utils



COURT_OF_APPEALS_ID = 'ca_court_app'

KEY_DISTRICTS = 'districts'
KEY_ID = '_id'
KEY_OFFICES = 'offices'

DIR_NAME_OBJECTS = 'objects'


def dd_dict():
    """A factory function that returns a defaultdict(dict)."""
    return defaultdict(dict)


def get_data_dir(dir_name):
    return os.path.join(utils.get_pre_data_dir(), dir_name)


def get_yaml_path(dir_name, file_base):
    file_name = "{0}.yaml".format(file_base)
    return os.path.join(get_data_dir(dir_name), file_name)


def get_object_path(name):
    return get_yaml_path(DIR_NAME_OBJECTS, name)


def make_node_categories(node_name):
    categories, meta = get_object_data(node_name)

    name_i18n_format = meta['name_i18n_format']

    node = {}
    for category_id, data in categories.items():
        name_i18n = name_i18n_format.format(category_id)
        category = {
            'name_i18n': name_i18n,
        }
        node[category_id] = category

    return node


def path_to_langcode(path):
    """Extract the language code from a path and return it."""
    head, tail = os.path.split(path)
    base, ext = os.path.splitext(tail)
    return base


def yaml_to_words(data, lang):
    """Return a dict from: text_id to word in the given language."""
    text_node = data['texts']
    # Each trans_map is a dict from: language code to translation.
    words = {text_id: trans_map[lang] for text_id, trans_map in text_node.items()}
    return words


def read_phrases(path):
    """Read a file, and return a dict of: text_id to translation."""
    lang_code = path_to_langcode(path)
    yaml_data = utils.read_yaml(path)
    words = yaml_to_words(yaml_data, lang_code)
    return lang_code, words


def make_node_i18n(node_name):
    """Return the node containing internationalized data."""
    lang_dir = lang.get_lang_dir()
    auto_dir = os.path.join(lang_dir, lang.DIR_LANG_AUTO)
    glob_path = os.path.join(auto_dir, "*.yaml")
    paths = glob.glob(glob_path)

    data = defaultdict(dd_dict)
    for path in paths:
        lang_code, phrases = read_phrases(path)
        for text_id, phrase in phrases.items():
            data[text_id][lang_code] = phrase

    return data


def make_node_offices(node_name, mixins):
    """Return the node containing internationalized data."""
    offices, meta = get_object_data('offices')

    # TODO: convert this to a dict with office_id's.
    node = []
    for office in offices:
        try:
            mixin_id = office['mixin_id']
        except KeyError:
            pass
        else:
            # Make the office "extend" from the mixin.
            office_new = deepcopy(mixins[mixin_id])
            office_new.update(office)
            office = office_new

        node.append(office)

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


def add_node(json_data, node_name, **kwargs):
    make_node_function_name = "make_node_{0}".format(node_name)
    make_node_func = globals()[make_node_function_name]
    node = make_node_func(node_name, **kwargs)
    json_data[node_name] = node


def make_all_data():
    mixins, meta = get_object_data('mixins')

    json_data ={}

    add_node(json_data, 'categories')
    add_node(json_data, 'i18n')
    add_node(json_data, 'offices', mixins=mixins)

    return json_data

    # TODO
    add_source(data, 'bodies')
    add_source(data, 'district_types')
    add_source(data, 'office_types')

    # Make districts.
    districts = make_court_of_appeals_districts()
    data['districts'] = districts

    offices = make_court_of_appeals()
    data['court_offices'] = offices

    return data
