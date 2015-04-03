"""Customs custom Django tags.

To define custom tags, Django requires that a module like this exist
in a submodule called "templatetags" of a registered app.

Moreover, the module has to have a "register" attribute of type
django.template.Library().

"""

from django import template

from pyelect import lang
from pyelect.htmlgen import NON_ENGLISH_ORDER

register = template.Library()

@register.inclusion_tag('tags/page_nav.html')
def page_nav(current_file_name, file_name, display_name):
    """A tag to use in site navigation."""
    return {
        'current_file_name': current_file_name,
        'file_name': file_name,
        'display_name': display_name,
    }


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


@register.inclusion_tag('list_objects.html')
def list_objects(objects, title_attr, template_name):
    return {
        'objects': objects,
        'title_attr': title_attr,
        'template_name': template_name
    }
