"""Customs custom Django tags.

To define custom tags, Django requires that a module like this exist
in a submodule called "templatetags" of a registered app.

Moreover, the module has to have a "register" attribute of type
django.template.Library().

"""

from django import template

register = template.Library()

@register.inclusion_tag('tags/cond_include.html')
def cond_include(should_include, template_name, data):
    """A tag to conditionally include a template."""
    return {
        'should_include': should_include,
        'template_name': template_name,
        'data': data,
    }


@register.inclusion_tag('tags/page_nav.html')
def page_nav(current_file_name, file_name, display_name):
    """A tag to use in site navigation."""
    return {
        'current_file_name': current_file_name,
        'file_name': file_name,
        'display_name': display_name,
    }
