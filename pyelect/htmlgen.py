"""Support for making html."""

from jinja2 import Environment, FileSystemLoader

from pyelect import utils


def make_district(value):
    data = {
        'name': value['district_code']
    }
    return data

def make_districts(data):
    districts = [make_district(v) for v in data['districts']]
    return districts


def make_office(trans, office_json):
    # TODO: there should be an ID attribute separate from name_i18n.
    name_text_id = office_json.get('name_i18n')
    # TODO: all offices should be fully processed with a name, etc.
    if name_text_id is None:
        return None

    words = trans[name_text_id]
    name = words['en']
    translations = [words[lang] for lang in words.keys() if lang != 'en']
    translations = filter(None, translations)
    office = {
        'id': name_text_id,
        'name': name,
        'vote_method': office_json.get('vote_method'),
        'translations': translations,
        'url': office_json.get('url')
    }
    return office


def make_offices(data):
    trans = data['i18n']
    offices = [make_office(trans, v) for v in data['offices']]
    return offices


def make_template_data(input_data):
    data = {
#        'districts': make_districts(input_data),
        'offices': make_offices(input_data),
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


def make_html(input_data):
    template_data = make_template_data(input_data)
    html = render_template('sample.html', template_data)
    return html
