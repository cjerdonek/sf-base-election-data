"""Customs custom Django tags.

To define custom tags, Django requires that a module like this exist
in a submodule called "templatetags" of a registered app.

Moreover, the module has to have a "register" attribute of type
django.template.Library().

"""

from functools import wraps
import logging
from pprint import pprint
import sys
import traceback

from django import template

from pyelect.html.common import CATEGORY_ORDER, NON_ENGLISH_ORDER
from pyelect.html import pages
from pyelect import lang


_log = logging.getLogger()

register = template.Library()


# This is a decorator to deal with the fact that by default Django silently
# swallows exceptions when rendering templates.  This default behavior
# can be changed by setting TEMPLATE_DEBUG to True.
def log_errors(func):
    # We need to decorate with functools.wraps() so as not to break tag
    # registration, for example when using @register.inclusion_tag().
    # See also: https://code.djangoproject.com/ticket/24586
    @wraps(func)
    def wrapper(context, *args, **kwargs):
        try:
            return func(context, *args, **kwargs)
        except Exception as err:
            _log.warn("exception: {0}".format(err))
            traceback.print_exc()
            raise
    return wrapper


def _update_context(context, extra):
    # We do not use context.update() since that pushes onto the contest stack.
    for key, value in extra.items():
        context[key] = value
    return context


def pass_context(func):
    """Pass the full context through, in addition to whatever is added."""
    # We need to decorate with functools.wraps() so as not to break tag
    # registration, for example when using @register.inclusion_tag().
    # See also: https://code.djangoproject.com/ticket/24586
    @wraps(func)
    def wrapper(context, *args, **kwargs):
        extra = func(context, *args, **kwargs)
        _update_context(context, extra)
        return context
    return wrapper


def _pprint(text):
    pprint(text, stream=sys.stderr)


# TODO: update the return value to what is documented.
@register.assignment_tag(takes_context=True)
@log_errors
def translations(context, item, attr_name):
    """Returns i18n info for an object attribute.

    Usage:

        {% translations office 'name' as text %}

    Returns (for example):

        {
            "en": "Mayor",
            "non_english": [
                {
                    "lang": "zh",
                    "text": "Alcalde",
                },
                {
                    "lang": "es",
                    "text": "Alcalde",
                }
            ]
        }
    """
    assert 'phrases' in context
    if isinstance(item, str):
        raise Exception("item cannot be str: {0!r}".format(item))
    i18n_field_name = lang.get_i18n_field_name(attr_name)
    phrase_id = item.get(i18n_field_name)
    non_english = []
    if phrase_id:
        phrases = context.get('phrases')
        phrase = phrases[phrase_id]
        non_english = [phrase[lang] for lang in NON_ENGLISH_ORDER if lang in phrase]
    text = {
        "en": "bar",
        "non_english": non_english,
    }
    return text


def get_page_href(page_base):
    page = pages.get_page_object(page_base)
    href = page.make_href()
    return href


def get_page_title(page_base):
    page = pages.get_page_object(page_base)
    title = page.title
    return title


@register.simple_tag(takes_context=True)
def current_object_count(context):
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


def _init_cond_include_context(template_name, should_include):
    return {
        'should_include': should_include,
        'template_name': template_name,
    }


@register.inclusion_tag('cond_include.html', takes_context=True)
@log_errors
def header_with_translation(context, template_name, item, attr_name):
    extra = _init_cond_include_context(template_name, should_include=True)
    header = item.get(attr_name)
    header_id = item['id']
    extra.update({
        'header': header,
        'header_id': header_id,
        'item': item,
        'attr_name': attr_name,
    })
    _update_context(context, extra)
    return context


# TODO: DRY up with _init_cond_include_context().
@register.inclusion_tag('tags/cond_include.html')
def cond_include(should_include, template_name, data):
    """A tag to conditionally include a template."""
    return {
        'should_include': should_include,
        'template_name': template_name,
        'data': data,
    }


# TODO: DRY up with _init_cond_include_context().
def _cond_include_context(template_name, header, value):
    return {
        'header': header,
        'should_include': value is not None,
        'template_name': template_name,
        'value': value,
    }


# TODO: DRY up with _init_cond_include_context().
def _cond_include_context_url(label, href, href_text=None):
    if href_text is None:
        href_text = href
    return {
        'header': label,
        'should_include': href is not None,
        'template_name': 'partials/row_url.html',
        'href': href,
        'href_text': href_text,
    }


@register.inclusion_tag('tags/cond_include.html')
def info_row(header, value):
    return _cond_include_context('partials/row_simple.html', header, value)


@register.inclusion_tag('tags/cond_include.html')
def url_row(header, value):
    return _cond_include_context_url(header, value)


@register.inclusion_tag('tags/cond_include.html', takes_context=True)
@log_errors
def url_row_object(context, label, object_id, type_name):
    """
    Arguments:
      type_name: for example, "languages".
    """
    href = None
    name = None
    if object_id is not None:
        objects = context[type_name]
        obj = objects[object_id]
        name = obj['name']
        page = pages.get_page_object(type_name)
        href = page.make_href(object_id)

    return _cond_include_context_url(label, href, href_text=name)


@register.inclusion_tag('list_objects.html', takes_context=True)
@log_errors
def list_objects(context, objects, title_attr):
    assert 'phrases' in context
    extra = {
        'objects': objects,
        'title_attr': title_attr
    }
    _update_context(context, extra)
    return context


def _group_by_category(objects):
    by_category = {c: {} for c in CATEGORY_ORDER}
    for obj in objects.values():
        category_id = obj['category_id']
        # Raises an exception if the object has an unrecognized category.
        group = by_category[category_id]
        object_id = obj['id']
        group[object_id] = obj
    return by_category


@register.inclusion_tag('list_by_subcategory.html', takes_context=True)
@log_errors
@pass_context
def list_by_subcategory(context, items, sub_group_attr, sub_group_map):
    extra = {
        'items': items,
        'sub_group_attr': sub_group_attr,
        'sub_group_map': sub_group_map,
    }
    return extra


@register.inclusion_tag('list_by_category.html', takes_context=True)
@log_errors
def show_by_category(context, objects):
    return _by_category_context(context, objects)
