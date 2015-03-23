"""Support for making html."""

from jinja2 import Environment, FileSystemLoader

from pyelect import utils


def _get_i18n(trans, obj_json, key_base):
    key = '{0}_i18n'.format(key_base)
    text_id = obj_json[key]
    words = trans[text_id]
    english = words['en']
    non_english = [words[lang] for lang in words.keys() if lang != 'en']
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


def make_office(all_json, data):
    categories = all_json['categories']
    trans = all_json['i18n']

    # TODO: there should be an ID attribute separate from name_i18n.
    name_text_id = data.get('name_i18n')
    # TODO: all offices should be fully processed with a name, etc.
    if name_text_id is None:
        return None

    try:
        category_id = data['category_id']
    except KeyError:
        category_name_i18n = None
    else:
        category = categories[category_id]
        category_name_i18n = _get_i18n(trans, category, 'name')

    # TODO: use _get_i18n().
    words = trans[name_text_id]
    name = words['en']
    translations = [words[lang] for lang in words.keys() if lang != 'en']
    translations = filter(None, translations)
    office = {
        'category_name_i18n': category_name_i18n,
        'id': name_text_id,
        'name': name,
        'vote_method': data.get('vote_method'),
        'translations': translations,
        'url': data.get('url')
    }
    return office


def make_offices(all_json):
    offices = [make_office(all_json, v) for v in all_json['offices']]
    return offices


def make_template_data(all_json):
    data = {
#        'districts': make_districts(input_data),
        'offices': make_offices(all_json),
    }

    return data


def render_template(template_name, data):
    """Render the sample template as a Unicode string.

    Argument:
      data: a dict of template variables.
    """
    template_dir = utils.get_template_dir()
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)
    return template.render(data)


def make_html(json_data):
    template_data = make_template_data(json_data)
    html = render_template('sample.html', template_data)
    return html
