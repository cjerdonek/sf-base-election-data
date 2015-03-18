
import json
import os

import yaml

from pyelect import utils


COURT_OF_APPEALS_ID = 'ca_court_app'

KEY_DISTRICTS = 'districts'
KEY_ID = '_id'
KEY_OFFICES = 'offices'


def read_source(name):
    path = utils.get_data_path(name)
    with open(path) as f:
        data = yaml.load(f)
    return data


def add_source(data, source_name):
    source_data = read_source(source_name)
    for key, value in source_data.items():
        data[key] = value


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


def make_all_data():
    data ={}
    add_source(data, 'bodies')
    add_source(data, 'district_types')
    add_source(data, 'office_types')

    # Make districts.
    districts = make_court_of_appeals_districts()
    data['districts'] = districts

    offices = make_court_of_appeals()
    data['offices'] = offices

    return data
