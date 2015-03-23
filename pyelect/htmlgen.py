"""Support for making html."""

from collections import defaultdict
from datetime import date
import os

from jinja2 import Environment, FileSystemLoader

from pyelect import lang
from pyelect import utils


CATEGORY_ORDER = ["federal", "state", "city_county", "school", "judicial"]
DIR_NAME_HTML_OUTPUT = 'html'
NON_ENGLISH_ORDER = [lang.LANG_CH, lang.LANG_ES, lang.LANG_FI]
TEMPLATE_PAGE_NAMES = """\
index.html
bodies.html
offices.html
""".strip().split()


def _get_templates_dir():
    repo_dir = utils.get_repo_dir()
    return os.path.join(repo_dir, 'templates')


def _get_page_templates_dir():
    templates_dir = _get_templates_dir()
    return os.path.join(templates_dir, 'pages')


def _get_translations(trans, text_id):
    try:
        dict_ = trans[text_id]
    except KeyError:
        raise Exception("json translations node does not have text_id: {0!r}".format(text_id))
    return dict_

def _get_i18n(trans, obj_json, key_base):
    key = '{0}_i18n'.format(key_base)
    text_id = obj_json[key]
    words = _get_translations(trans, text_id)
    english = words[lang.LANG_EN]
    non_english = [words[lang] for lang in NON_ENGLISH_ORDER]
    # Remove empty strings.
    non_english = filter(None, non_english)

    i18n = {
        'english': english,
        'non_english': non_english
    }

    return i18n


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
    try:
        seed_year = office_json['seed_year']
    except KeyError:
        raise Exception("office: {0!r}".format(office_json))
    year = date.today().year
    # Find a year before the current year.
    while seed_year >= year:
        seed_year -= term_length
    # Advance until the current or later.
    while seed_year < year:
        seed_year += term_length
    return seed_year


def make_office(all_json, data):
    trans = all_json['i18n']

    # TODO: incorporate a real ID.
    office_id = data.get('name_i18n')
    # TODO: do not skip any offices.
    if office_id is None:
        return None

    name_i18n = _get_i18n(trans, data, 'name')

    term_length = data.get('term_length')
    if term_length:
        term_length = "{0} year term".format(term_length)

    next_election_year = _compute_next_election_year(data)

    office = {
        'category_id': data.get('category_id'),
        'id': office_id,
        'name_i18n': name_i18n,
        'next_election_text': "{0} next".format(next_election_year),
        # TODO: use a real seat count.
        'seat_count': 1,
        'term_length': term_length,
        'twitter': data.get('twitter'),
        'vote_method': data.get('vote_method'),
        'url': data.get('url')
    }
    print(office)
    return office


def make_offices(all_json):
    offices = [make_office(all_json, v) for v in all_json['offices']]
    offices = list(filter(None, offices))
    return offices


def make_template_data(all_json):
    """Return the context to use when rendering the template."""
    trans = all_json['i18n']
    categories = make_categories(all_json, trans)

    offices = make_offices(all_json)
    office_count = sum([o['seat_count'] for o in offices])

    offices_by_category = defaultdict(list)
    for office in offices:
        category_id = office['category_id']
        seq = offices_by_category[category_id]
        seq.append(office)

    data = {
        'categories': categories,
        'category_ids': CATEGORY_ORDER,
        'offices_by_category': offices_by_category,
#        'districts': make_districts(input_data),
        'offices': offices,
        'office_count': office_count,
    }

    return data


def _make_template_env():
    templates_dir = _get_templates_dir()
    page_templates_dir = _get_page_templates_dir()
    env = Environment(loader=FileSystemLoader([templates_dir, page_templates_dir]))
    return env


def render_template(env, template_name, data):
    """Render the sample template as a Unicode string.

    Argument:
      data: a dict of template variables.
    """
    template = env.get_template(template_name)
    return template.render(data)


def make_html(json_data, output_dir):
    data = make_template_data(json_data)
    env = _make_template_env()
    page_templates_dir = _get_page_templates_dir()

    for file_name in TEMPLATE_PAGE_NAMES:
        html = render_template(env, file_name, data=data)
        output_path = os.path.join(output_dir, file_name)
        utils.write(output_path, html)
    index_path = os.path.join(output_dir, TEMPLATE_PAGE_NAMES[0])

    return index_path
