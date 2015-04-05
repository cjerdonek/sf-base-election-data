"""Supports per-page template context."""

from pprint import pprint


def get_page_object(page_base):
    parts = page_base.split('_')
    prefix = "".join(p.title() for p in parts)
    cls_name = "{0}Page".format(prefix)
    page_class = globals()[cls_name]
    page = page_class(page_base)
    return page


class _Page(object):

    object_name = None
    singular = None

    def __init__(self, base_name):
        self.base_name = base_name

    def make_href(self, object_id=None):
        url = "{0}.html".format(self.base_name)
        if object_id is not None:
            url += "#{0}".format(object_id)
        return url

    def get_singular(self):
        if self.singular is not None:
            return self.singular
        # Otherwise, remove the final "s".
        return self.base_name[:-1]

    def get_objects(self, data):
        if self.object_name is None:
            key = self.base_name
        else:
            key = self.object_name
        objects = data[key]
        return objects

    def get_show_template(self):
        """Return the name of the template that shows one instance."""
        singular = self.get_singular()
        return "show_{0}.html".format(singular)


class BodiesPage(_Page):
    singular = 'body'
    title = "Bodies"


class DistrictTypesPage(_Page):
    title = "District Types"


class IndexPage(_Page):
    object_name = 'offices'
    title = "Offices"


# TODO: should we use a better name (e.g. area)?
class JurisdictionsPage(_Page):
    title = "Jurisdictions"


class LanguagesPage(_Page):
    title = "Languages"


class PhrasesPage(_Page):
    title = "Translated Phrases"
