"""Customs custom Django tags.

To define custom tags, Django requires that a module like this exist
in a submodule called "templatetags" of a registered app.

Moreover, the module has to have a "register" attribute of type
django.template.Library().

"""

from django import template

from pyelect.html.common import NON_ENGLISH_ORDER
from pyelect import htmlgen
from pyelect import lang


_PAGE_TITLES = {
    'bodies': 'Bodies',
    'index': 'Offices',
    'languages': 'Languages',
    'phrases': 'Translated Phrases',
}


register = template.Library()


def get_page_href(page_base):
    return "{0}.html".format(page_base)


def get_page_title(page_base):
    return _PAGE_TITLES[page_base]


@register.simple_tag(takes_context=True)
def current_title(context):
    current_page_base = context['current_page']
    page_title = get_page_title(current_page_base)
    return page_title


@register.inclusion_tag('tags/page_nav.html', takes_context=True)
def page_nav(context, page_base):
    """A tag to use in site navigation."""
    current_page_base = context['current_page']
    data = {
        'page_href': get_page_href(page_base),
        'page_title': get_page_title(page_base),
        'same_page': page_base == current_page_base
    }

    return data


@register.inclusion_tag('anchor.html')
def anchor(id_):
    return {
        'id': id_
    }


def _header_context(item_data, field_name, item_id):
    name = item_data[field_name]
    i18n_field_name = lang.get_i18n_field_name(field_name)
    translations = item_data.get(i18n_field_name, {})
    non_english = [translations[lang] for lang in NON_ENGLISH_ORDER if lang in translations]
    return {
        'header': name,
        'header_non_english': non_english,
        'header_id': item_id,
    }


@register.inclusion_tag('header_section.html')
def header_section(item_data, field_name, item_id):
    return _header_context(item_data, field_name, item_id)


@register.inclusion_tag('header_item.html')
def header_item(item_data, field_name, item_id):
    return _header_context(item_data, field_name, item_id)


@register.inclusion_tag('tags/cond_include.html')
def cond_include(should_include, template_name, data):
    """A tag to conditionally include a template."""
    return {
        'should_include': should_include,
        'template_name': template_name,
        'data': data,
    }


def _cond_include_context(template_name, header, value):
    return {
        'header': header,
        'should_include': value is not None,
        'template_name': template_name,
        'value': value,
    }


@register.inclusion_tag('tags/cond_include.html')
def info_row(header, value):
    return _cond_include_context('partials/row_simple.html', header, value)


@register.inclusion_tag('tags/cond_include.html')
def url_row(header, value):
    return _cond_include_context('partials/row_url.html', header, value)


@register.inclusion_tag('list_objects.html', takes_context=True)
def list_objects(context, objects, title_attr, template_name):
    return {
        'context': context,
        'objects': objects,
        'title_attr': title_attr,
        'template_name': template_name
    }
