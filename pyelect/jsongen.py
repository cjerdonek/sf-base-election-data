
import glob
import json
import os
from pprint import pprint

from pyelect import utils


COURT_OF_APPEALS_ID = 'ca_court_app'

KEY_DISTRICTS = 'districts'
KEY_ID = '_id'
KEY_OFFICES = 'offices'


def get_language_codes():
    dir_path = utils.get_lang_dir()
    glob_path = os.path.join(dir_path, "*.yaml")
    paths = glob.glob(glob_path)
    langs = []
    for path in paths:
        head, tail = os.path.split(path)
        base, ext = os.path.splitext(tail)
        langs.append(base)
    return langs


def get_translations(lang):
    path = utils.get_language_path(lang)
    return utils.read_yaml(path)


def get_yaml(name):
    path = utils.get_yaml_file_path(name)
    return utils.read_yaml(path)


def add_source(data, source_name):
    source_data = get_yaml(source_name)
    for key, value in source_data.items():
        data[key] = value


def words_from_yaml(lang):
    data = get_translations(lang)
    for text_id, value in data['texts'].items():
        text = value[lang]
        yield (text_id, text)


def make_node_i18n():
    """Return the node containing internationalized data."""
    node = {}
    langs = get_language_codes()
    for lang in langs:
        for text_id, text in words_from_yaml(lang):
            try:
                words = node[text_id]
            except KeyError:
                words = {}
                node[text_id] = words
            words[lang] = text
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


def add_node(data, node_name):
    make_node_function_name = "make_node_{0}".format(node_name)
    make_node = globals()[make_node_function_name]
    node = make_node()
    data[node_name] = node


def make_all_data():
    data ={}

    add_node(data, 'i18n')
    add_source(data, 'offices')
    return data

    add_source(data, 'bodies')
    add_source(data, 'district_types')
    add_source(data, 'office_types')

    # Make districts.
    districts = make_court_of_appeals_districts()
    data['districts'] = districts

    offices = make_court_of_appeals()
    data['court_offices'] = offices

    return data
