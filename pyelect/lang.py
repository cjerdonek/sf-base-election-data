
from collections import defaultdict, namedtuple
import csv
import logging
import os
from pprint import pprint
import re

from pyelect import utils


_log = logging.getLogger()

LANG_EN = 'en'
LANG_ES = 'es'
LANG_FI = 'fil'
LANG_CH = 'zh'

LANGS = [LANG_EN, LANG_ES, LANG_FI, LANG_CH]
LANGS_NON_ENGLISH = [c for c in LANGS if c != LANG_EN]
LANGS_SHORT = [LANG_EN, LANG_ES, LANG_FI]

KEY_ENGLISH_ANNOTATION = '_{0}'.format(LANG_EN)
KEY_TEXTS = 'texts'

DIR_LANG = 'i18n'
DIR_CONFIG = '_config'
DIR_TRANSLATIONS_CSV = 'translations_csv'
DIR_TRANSLATIONS_EXTRA = 'translations_extra'

FILE_TEXT_IDS_CSV = 'text_ids_csv.yaml'

# The "short" strings are for Edge review (24 characters max).
CONTEST_INDICES = {
    'en': 1,
    'en_short': 4,
    'es': 6,
    'es_short': 7,
    'fil': 2,
    'fil_short': 3,
    'zh': 5,
}

CONTEST_HEADERS = sorted(CONTEST_INDICES.keys())

COMMENT_TRANSLATIONS_EXTRA_ENGLISH = """\
This file contains a list of phrases to add to the phrases already
covered by the various CSV files.
"""

COMMENT_TRANSLATIONS_EXTRA_NON_ENGLISH = """\
The non-English translations in this file are meant to be updated
by hand.
"""

ContestRow = namedtuple('ContestRow', CONTEST_HEADERS)


def get_rel_path_lang_dir():
    return os.path.join(utils.DIR_PRE_DATA, DIR_LANG)


def get_rel_path_config_dir():
    lang_dir = get_rel_path_lang_dir()
    return os.path.join(lang_dir, DIR_CONFIG)


def get_rel_path_text_ids_csv():
    dir_path = get_rel_path_config_dir()
    return os.path.join(dir_path, FILE_TEXT_IDS_CSV)


def get_rel_path_translations(dir_name, lang=None):
    """Returns a directory if lang is None."""
    lang_dir = get_rel_path_lang_dir()
    rel_dir = os.path.join(lang_dir, dir_name)
    if lang is None:
        return rel_dir
    file_name = "{0}.yaml".format(lang)
    return os.path.join(rel_dir, file_name)


def get_rel_path_translations_csv(lang=None):
    """Return the path to the file containing the extra phrases."""
    return get_rel_path_translations(dir_name=DIR_TRANSLATIONS_CSV, lang=lang)


def get_rel_path_translations_extra(lang=None):
    """Return the path to the file containing the extra phrases."""
    return get_rel_path_translations(dir_name=DIR_TRANSLATIONS_EXTRA, lang=lang)


def get_rel_path_phrases_extra():
    """Return the path to the file containing the extra phrases."""
    return get_rel_path_translations_extra(lang=LANG_EN)


def _read_csv(path, skip_rows=1):
    with open(path) as f:
        reader = csv.reader(f)
        for i in range(skip_rows):
            next(reader)
        rows = list(reader)
    return rows


def _get_yaml_set(base, key):
    """Read a list from the given YAML, and return a set."""
    data = _get_yaml_node(base, key)
    return set(data)


def _make_text_id(text):
    # Remove non-ascii characters.
    bytes = text.encode('ascii', 'ignore')
    slug = bytes.decode('ascii').lower()
    # TODO: compile these re's.
    slug = re.sub(r'[^a-z0-9]+', '_', slug).strip('_')
    slug = re.sub(r'[_]+', '_', slug)
    return slug


def read_contest_csv(path):
    rows = _read_csv(path)
    # Remove blank lines (separator lines, etc).
    rows = [row for row in rows if row[1]]
    seq = []
    for row in rows:
        data = ContestRow(*(row[CONTEST_INDICES[h]].strip() for h in CONTEST_HEADERS))
        seq.append(data)
    return seq


def create_text_ids(path):
    seq = read_contest_csv(path)
    text_map = {}  # maps text ID to English phrase.
    skip = _get_skip_phrases('text_ids/_skip')
    for row in seq:
        english = row.en
        if english in skip:
            continue
        text_id = _make_text_id(english)
        if text_id in text_map and english != text_map[text_id]:
            raise Exception("mismatch for {0!r}:\n {1!r}\n {2!r}"
                            .format(text_id, english, text_map[text_id]))
        text_map[text_id] = english
    return text_map


def _get_text_ids_extra():
    rel_path = get_rel_path_phrases_extra()
    data = utils.read_yaml_rel(rel_path, key=KEY_TEXTS)
    return rel_path, data.keys()


def _get_text_ids_csv():
    rel_path = get_rel_path_text_ids_added()
    phrases_dict = utils.get_yaml_data(rel_path, key='phrases')
    return phrases


# TODO: remove this or convert it into a function that validates a
#   text_id dict.
def _get_text_ids():
    lang_dir = get_lang_dir()
    ids_to_en, meta = utils.get_yaml_data(lang_dir, 'text_ids')

    en_to_ids = {}
    for text_id, en in ids_to_en.items():
        if en in en_to_ids:
            raise Exception("key already exists: {0}".format(en))
        en_to_ids[en] = text_id
    return en_to_ids


def read_translations_file(rel_dir, lang):
    """Return the dict of: text_id to dict of info."""
    rel_path = os.path.join(rel_dir, "{0}.yaml".format(lang))
    phrases = utils.read_yaml_rel(rel_path, key=KEY_TEXTS)
    for text_id, translations in phrases.items():
        translations.pop(KEY_ENGLISH_ANNOTATION, None)
    return phrases


def read_translations_dir(rel_dir):
    """Read and return the i18n data from a translations directory.

    Returns the data as a combined dict mapping text_id to dict
    of translations.  Each dict of translations maps language code
    to translation.
    """
    # Use the English file to establish the text ID's.
    phrases = read_translations_file(rel_dir, lang=LANG_EN)
    for lang in LANGS_NON_ENGLISH:
        non_english = read_translations_file(rel_dir, lang=lang)
        for text_id, translations in non_english.items():
            try:
                text_info = phrases[text_id]
            except KeyError:
                # Then the text ID is present in the non-English but not English.
                continue
            text_info.update(translations)

    return phrases


def get_translations():
    rel_dir = get_rel_path_translations_csv()
    return read_translations_dir(rel_dir)


def get_lang_phrase(translations, lang):
    # This requires that the key be present for English.
    return translations[lang] if lang == LANG_EN else translations.get(lang, '')


def _make_translations_texts(phrases, lang):
    """Create the texts node suitable for writing to a translations file.

    Arguments:
      phrases: a dict from text_id to dict of: lang to
        text translation.
    """
    data = {}
    for text_id, translations in phrases.items():
        if not text_id.startswith('text_'):
            text_id = "text_{0}".format(text_id)
        phrase = get_lang_phrase(translations, lang)
        entry = {lang: phrase}
        if lang != LANG_EN:
            # Annotate with the English to make the raw file more readable.
            english = get_lang_phrase(translations, LANG_EN)
            entry[KEY_ENGLISH_ANNOTATION] = english
        data[text_id] = entry

    return data


def write_translations_file(phrases, dir_name, file_type, lang, comments=None):
    rel_path = get_rel_path_translations(dir_name, lang=lang)
    data = _make_translations_texts(phrases, lang)
    data = {'texts': data}
    utils.write_yaml_with_header(data, rel_path=rel_path, file_type=file_type,
                                 comments=comments)


def write_translations_extra(phrases):
    """Write the phrases to the extra translations directory."""
    rel_path, file_type = DIR_TRANSLATIONS_EXTRA, utils.FILE_AUTO_UPDATED
    write_translations_file(phrases, rel_path, file_type=file_type, lang=LANG_EN,
                            comments=COMMENT_TRANSLATIONS_EXTRA_ENGLISH)
    for lang in LANGS_NON_ENGLISH:
        write_translations_file(phrases, rel_path, file_type=file_type, lang=lang,
                                comments=COMMENT_TRANSLATIONS_EXTRA_NON_ENGLISH)


def update_extras():
    rel_path, text_ids = _get_text_ids_extra()
    text_ids = set(text_ids)

    # Check that none of the extra text ID's is already taken by a CSV word.
    csv_rel_path = get_rel_path_text_ids_csv()
    csv_text_ids = set(utils.read_yaml_rel(csv_rel_path, key='text_ids'))
    intersection = text_ids.intersection(csv_text_ids)
    if intersection:
        raise Exception("some text ID's in: {0}\n"
                        "are already in: {1}\n-->{2}"
                        .format(rel_path, csv_rel_path, intersection))

    # TODO: check for text ID's that don't belong.
    rel_dir = get_rel_path_translations_extra()
    phrases = read_translations_dir(rel_dir)

    write_translations_extra(phrases)

    exit()

    # TODO: check that keys aren't already listed in text_ids.yaml?
    print(new_text_ids)
    for lang in LANGS:
        # TODO: write a function to load all of the language data in
        # a given directory
        # TODO: load existing language file, check the keys, add new ones,
        #   and write the file back.
        print(lang)


def _add_key(dict_, key, value):
    if key in dict_ and value != dict_[key]:
        raise Exception("mismatch for {0!r}:\nold: {1}\nnew: {2}"
                        .format(key, dict_[key], value))
    dict_[key] = value


def _process_row(row, lang_data, skip_text_ids, manual, langs, text_id, attr_format):
    if text_id in skip_text_ids:
        return
    override = manual[text_id] if text_id in manual else []
    for lang in langs:
        one_lang = lang_data[lang]
        if lang in override:
            text = override[lang]
        else:
            text = getattr(row, attr_format.format(lang))
        _add_key(one_lang, text_id, text)


def lang_contest_csv_to_yaml(input_path):
    seq = read_contest_csv(input_path)

    skip_phrases = _get_yaml_set('_config/skips', 'phrases')
    seq = [row for row in seq if row.en not in skip_phrases]

    english_to_ids = _get_text_ids()
    skip_text_ids = _get_yaml_set('_config/skips', 'text_ids')

    manual = _get_yaml_node('_config/resolve', 'override')
    # Dict from lang to dict of: text_id to translation.
    lang_data = defaultdict(dict)
    for row in seq:
        english = row.en
        text_id = english_to_ids[english]
        _process_row(row, lang_data, skip_text_ids, manual=manual, langs=LANGS,
                     text_id=text_id, attr_format="{0}")
        short_text_id = "{0}_edge".format(text_id)
        _process_row(row, lang_data, skip_text_ids, manual=manual, langs=LANGS_SHORT,
                     text_id=short_text_id, attr_format="{0}_short")

    en_translations = lang_data[LANG_EN]
    for lang in LANGS:
        yaml_texts = {}
        for text_id, text in lang_data[lang].items():
            entry = {lang: text}
            if lang != LANG_EN:
                # Add English to non-English files for readability.
                entry['_{0}'.format(LANG_EN)] = en_translations[text_id]
            yaml_texts[text_id] = entry
        data = {'texts': yaml_texts}
        path = get_lang_path('auto/{0}'.format(lang))
        write_yaml_with_header(data, path, file_type=utils.FILE_AUTO)
