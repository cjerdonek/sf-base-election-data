"""Support for making html."""

from collections import defaultdict
from datetime import date
import os
from pprint import pprint

from django.template import Context
from django.template.loader import get_template

from pyelect import lang
from pyelect import templateconfig
from pyelect import utils


CATEGORY_ORDER = ["federal", "state", "city_county", "school", "bart", "judicial", "party"]
DIR_NAME_HTML_OUTPUT = 'html'
NON_ENGLISH_ORDER = [lang.LANG_CH, lang.LANG_ES, lang.LANG_FI]


def _get_translations(trans, text_id):
    try:
        dict_ = trans[text_id]
    except KeyError:
        raise Exception("json translations node does not have text_id: {0!r}".format(text_id))
    return dict_


# TODO: remove this function.
def _get_i18n(trans, obj_json, key_base):
    key = '{0}_i18n'.format(key_base)
    text_id = utils.get_required(obj_json, key, message="translation")
    # TODO: remove this hack and insist that everything appear in the i18n dict.
    if text_id not in trans:
        english = utils.get_required(obj_json, 'name')
        words = {lang.LANG_EN: english}
        non_english = []
    else:
        words = utils.get_required(trans, text_id)
        english = words[lang.LANG_EN]
        non_english = [words[lang] for lang in NON_ENGLISH_ORDER]
    # Remove empty strings.
    non_english = list(filter(None, non_english))

    i18n = {
        'english': english,
        'non_english': non_english
    }

    return i18n


def make_languages_one(lang_id, data):
    data['id'] = lang_id
    return data


def make_district(value):
    data = {
        'name': value['district_code']
    }
    return data


def make_districts(data):
    districts = [make_district(v) for v in data['districts']]
    return districts


def make_categories(all_json, trans):
    categories_json = all_json['categories']

    categories = {}
    for category_id, category_json in categories_json.items():
        name_i18n = _get_i18n(trans, category_json, 'name')
        categories[category_id] = name_i18n

    return categories


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


def _make_election_info(data):

    vote_method = data.get('vote_method')

    next_election_year = _compute_next_election_year(data)
    if next_election_year is not None:
        next_election_text = "{0} next".format(next_election_year)
    else:
        next_election_text = None

    term_length = data.get('term_length')
    if term_length:
        term_length = "{0} year term".format(term_length)

    partisan = data.get('partisan')
    if partisan is not None:
        partisan_text = "{0}partisan".format("" if partisan else "non-")
    else:
        partisan_text = None

    return list(filter(None, [term_length, next_election_text, vote_method, partisan_text]))


def get_i18n_field_name(name):
    return "{0}_i18n".format(name)

def add_i18n_field(object_data, json_data, field_name):
    i18n_field = get_i18n_field_name(field_name)
    try:
        json_data[i18n_field]
    except KeyError:
        key_name = field_name
    else:
        key_name = i18n_field
    object_data[key_name] = json_data[key_name]


def make_bodies_one(body_id, data, **kwargs):

    category_id = utils.get_required(data, 'category_id')

    body = {
        'category_id': category_id,
        'district_count': data.get('district_count'),
        'election_info': _make_election_info(data),
        'notes': data.get('notes'),
        'seat_count': data.get('seat_count'),
        'twitter': data.get('twitter'),
        'url': data.get('url'),
        'wikipedia': data.get('wikipedia')
    }

    add_i18n_field(body, data, 'name')

    return body


def make_offices_one(office_id, data, trans):
    # TODO: remove this logic.
    if 'name_i18n' not in data:
        return None

    name_i18n = _get_i18n(trans, data, 'name')

    office = {
        'category_id': data.get('category_id'),
        'election_info': _make_election_info(data),
        'id': office_id,
        'name_i18n': name_i18n,
        # TODO: use a real seat count.
        'seat_count': 1,
        'twitter': data.get('twitter'),
        'url': data.get('url')
    }

    return office


def add_objects(template_data, json_data, node_name, **kwargs):
    make_object_func_name = "make_{0}_one".format(node_name)
    make_object = globals()[make_object_func_name]

    json_node = json_data[node_name]

    objects = []
    object_ids = sorted(json_node.keys())
    for object_id in object_ids:
        data = json_node[object_id]
        obj = make_object(object_id, data, **kwargs)
        # TODO: remove this hack (used to skip offices).
        if not obj:
            continue
        obj['id'] = object_id
        objects.append(obj)

    template_data[node_name] = objects

    # Return it in case the caller wants to do something more with it.
    return objects


def _group_by(objects, key):
    grouped = defaultdict(list)
    for obj in objects:
        try:
            value = obj[key]
        except KeyError:
            raise Exception(repr(obj))
        seq = grouped[value]
        seq.append(obj)
    return grouped


def make_template_data(json_data):
    """Return the context to use when rendering the template."""
    data = {}
    bodies = add_objects(data, json_data, 'bodies')

    trans = json_data['i18n']
    categories = make_categories(json_data, trans)


    offices = add_objects(data, json_data, 'offices', trans=trans)
    office_count = sum([o['seat_count'] for o in offices])

    bodies_by_category = _group_by(bodies, 'category_id')
    offices_by_category = _group_by(offices, 'category_id')

    all_categories = set()
    for d in (bodies_by_category, offices_by_category):
        all_categories.update(d.keys())
    if all_categories > set(CATEGORY_ORDER):
        extra = all_categories - set(CATEGORY_ORDER)
        raise Exception("unrecognized categories: {0}".format(extra))

    data = {
        'bodies_count': len(bodies),
        'bodies_by_category': bodies_by_category,
        'categories': categories,
        'category_ids': CATEGORY_ORDER,
        'offices_by_category': offices_by_category,
#        'districts': make_districts(input_data),
        'office_count': office_count,
        # TODO
        'translations': "TODO",
        'translation_count': 0,
    }

    add_objects(data, json_data, 'languages')

    return data


def render_template(file_name, data):
    """Render the sample template as a Unicode string.

    Argument:
      data: a dict of template variables.
    """
    template_name = templateconfig.get_page_template_name(file_name)
    template = get_template(template_name)
    context = Context(data)
    context['current_page'] = os.path.basename(template_name)
    return template.render(context)


def make_html(json_data, output_dir, page_name=None):
    if page_name is None:
        file_names = templateconfig.get_template_page_file_names()
    else:
        file_names = [page_name]

    templateconfig.init_django()
    data = make_template_data(json_data)

    for file_name in file_names:
        html = render_template(file_name, data=data)
        print(html)
        output_path = os.path.join(output_dir, file_name)
        utils.write(output_path, html)
    if len(file_names) == 1:
        start_page = file_names[0]
    else:
        start_page = 'index.html'
    start_path = os.path.join(output_dir, start_page)

    return start_path
