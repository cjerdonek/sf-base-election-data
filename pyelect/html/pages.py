"""Supports per-page template context."""


def get_page_object(page_base):
    parts = page_base.split('_')
    prefix = "".join(p.title() for p in parts)
    cls_name = "{0}Page".format(prefix)
    page_class = globals()[cls_name]
    page = page_class(page_base)
    return page


class _Page(object):

    def __init__(self, base_name):
        self.base_name = base_name

    def make_href(self):
        return "{0}.html".format(self.base_name)


class BodiesPage(_Page):
    title = "Bodies"


class DistrictTypesPage(_Page):
    title = "District Types"


class IndexPage(_Page):
    title = "Offices"


# TODO: should we use a better name (e.g. area)?
class JurisdictionsPage(_Page):
    title = "Jurisdictions"


class LanguagesPage(_Page):
    title = "Languages"


class PhrasesPage(_Page):
    title = "Translated Phrases"
