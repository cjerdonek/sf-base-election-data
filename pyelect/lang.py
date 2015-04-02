
"""Supports translation and i18n processing.

Terminology
-----------

phrases dict:
  A dict that maps text_id to a translations dict.

translations dict:
  A dict that maps language code to the corresponding translation for a
  specific phrase.

"""

from collections import defaultdict, namedtuple
import csv
import logging
import os
from pprint import pprint
import re
import textwrap

from pyelect import utils


_log = logging.getLogger()

LANG_ENGLISH = 'en'
LANG_SPANISH = 'es'
LANG_FILIPINO = 'fil'
LANG_CHINESE = 'zh'

LANGS_NON_ENGLISH = (
    LANG_CHINESE,
    LANG_SPANISH,
    LANG_FILIPINO
)
LANGS = [LANG_ENGLISH] + list(LANGS_NON_ENGLISH)
# The languages that need to support an Edge format.
LANGS_SHORT = (LANG_ENGLISH, LANG_SPANISH, LANG_FILIPINO)

EDGE_STRING = '_edge'
I18N_SUFFIX = '_i18n'
KEY_ENGLISH_ANNOTATION = '_{0}'.format(LANG_ENGLISH)
KEY_TEXTS = 'texts'

DIR_LANG = 'i18n'
DIR_CONFIG = '_config'
DIR_CSV_FILES = 'csv'
_DIR_PHRASES_CSV = 'phrases_csv'
_DIR_PHRASES_EXTRA = 'phrases_extra'

FILE_NAME_CSV_SKIPS = 'csv_skips.yaml'
FILE_TEXT_IDS_CSV = 'csv_text_ids.yaml'
FILE_NAME_CSV_OVERRIDES = 'csv_overrides.yaml'

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


def get_rel_path_csv_dir():
    """Return the path to the directory containing the source CSV files."""
    lang_dir = get_rel_path_lang_dir()
    return os.path.join(lang_dir, DIR_CSV_FILES)


def get_rel_path_text_ids_csv():
    dir_path = get_rel_path_config_dir()
    return os.path.join(dir_path, FILE_TEXT_IDS_CSV)


def get_rel_path_phrases(dir_name, lang=None):
    """Returns a directory if lang is None."""
    lang_dir = get_rel_path_lang_dir()
    rel_dir = os.path.join(lang_dir, dir_name)
    if lang is None:
        return rel_dir
    file_name = "{0}.yaml".format(lang)
    return os.path.join(rel_dir, file_name)


def get_rel_path_translations_csv(lang=None):
    """Return the path to the file containing the extra phrases."""
    return get_rel_path_phrases(dir_name=_DIR_PHRASES_CSV, lang=lang)


def get_rel_path_translations_extra(lang=None):
    """Return the path to the file containing the extra phrases."""
    return get_rel_path_phrases(dir_name=_DIR_PHRASES_EXTRA, lang=lang)


def get_rel_path_phrases_extra():
    """Return the path to the file containing the extra phrases."""
    return get_rel_path_translations_extra(lang=LANG_ENGLISH)


def _read_csv(rel_path, skip_rows=1):
    repo_dir = utils.get_repo_dir()
    path = os.path.join(repo_dir, rel_path)
    with open(path) as f:
        reader = csv.reader(f)
        for i in range(skip_rows):
            next(reader)
        rows = list(reader)
    return rows


def read_csv_rows_contest():
    rel_dir = get_rel_path_csv_dir()
    rel_path = os.path.join(rel_dir, 'contest_names.csv')
    rows = _read_csv(rel_path)
    # Remove blank lines (separator lines, etc).
    rows = [row for row in rows if row[1]]
    seq = []
    for row in rows:
        data = ContestRow(*(row[CONTEST_INDICES[h]].strip() for h in CONTEST_HEADERS))
        seq.append(data)
    return seq


def get_i18n_field_name(name):
    return "{0}{1}".format(name, I18N_SUFFIX)


def _make_text_id(text):
    # Remove non-ascii characters.
    bytes = text.encode('ascii', 'ignore')
    slug = bytes.decode('ascii').lower()
    # TODO: compile these re's.
    slug = re.sub(r'[^a-z0-9]+', '_', slug).strip('_')
    slug = re.sub(r'[_]+', '_', slug)
    return slug


def _get_csv_skips(key):
    rel_dir = get_rel_path_config_dir()
    rel_path = os.path.join(rel_dir, FILE_NAME_CSV_SKIPS)
    skip_phrases = set(utils.read_yaml_rel(rel_path, key=key))

    return skip_phrases


def _get_csv_skip_phrases():
    """Return the CSV phrases to skip as a set."""
    return _get_csv_skips(key='phrases')


def _get_csv_skip_text_ids():
    """Return the CSV phrases to skip as a set."""
    return _get_csv_skips(key='text_ids')


def create_text_ids(path):
    seq = read_csv_rows_contest(path)
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


def _get_csv_overrides():
    """Return the translation overrides as a dict."""
    rel_dir = get_rel_path_config_dir()
    rel_path = os.path.join(rel_dir, FILE_NAME_CSV_OVERRIDES)
    overrides = utils.read_yaml_rel(rel_path, key='overrides')

    return overrides


def _make_english_to_id():
    rel_path = get_rel_path_text_ids_csv()
    id_to_english = utils.read_yaml_rel(rel_path, key='text_ids')

    english_to_id = {}
    for text_id, english in id_to_english.items():
        if english in english_to_id:
            raise Exception("phrase {0!r} occurs twice in: {1}".format(english, rel_path))
        english_to_id[english] = text_id

    return english_to_id


def _process_contest_row(row, phrases, all_overrides, text_id, langs, attr_format):
    translations = phrases.setdefault(text_id, {})
    overrides = all_overrides.get(text_id, {})
    for lang in langs:
        attr_name = attr_format.format(lang)
        translation = overrides.get(lang, getattr(row, attr_name))
        if not translation:
            # Do not store a value if the CSV contained no translation.
            continue
        if lang in translations and translation != translations[lang]:
            err = textwrap.dedent("""\
            differing translation found!

              text_id: {text_id}
                 lang: {lang}
                  old: {0!r}
                  new: {1!r}
            """).format(translations[lang], translation, text_id=text_id, lang=lang)
            raise Exception(err)
        translations[lang] = translation


def read_csv_dir():
    """Read the contents of the CSV directory.

    Returns the contents as a phrases dict.
    """
    skip_phrases = _get_csv_skip_phrases()
    skip_text_ids = _get_csv_skip_text_ids()
    english_to_id = _make_english_to_id()
    overrides = _get_csv_overrides()

    # TODO: process *all* files in the CSV directory.
    seq = read_csv_rows_contest()

    phrases = {}
    for row in seq:
        english = row.en
        if english in skip_phrases:
            continue
        text_id = english_to_id[english]
        _process_contest_row(row, phrases, overrides, text_id=text_id,
                             langs=LANGS, attr_format="{0}")
        english_short = row.en_short
        if not english_short:
            continue
        text_id_short = "{0}_edge".format(text_id)
        if text_id_short in skip_text_ids:
            continue
        _process_contest_row(row, phrases, overrides, text_id=text_id_short,
                             langs=LANGS_SHORT, attr_format="{0}_short")

    return phrases


def _get_text_ids_extra():
    rel_path = get_rel_path_phrases_extra()
    data = utils.read_yaml_rel(rel_path, key=KEY_TEXTS)
    return rel_path, data.keys()


def _get_text_ids_csv():
    rel_path = get_rel_path_text_ids_added()
    phrases_dict = utils.get_yaml_data(rel_path, key='phrases')
    return phrases


def read_translations_file(rel_dir, lang):
    """Return the dict of: text_id to dict of info."""
    rel_path = os.path.join(rel_dir, "{0}.yaml".format(lang))
    phrases = utils.read_yaml_rel(rel_path, key=KEY_TEXTS)
    for text_id, translations in phrases.items():
        translations.pop(KEY_ENGLISH_ANNOTATION, None)
    return phrases


def read_phrases_dir(rel_dir):
    """Read a YAML phrases directory, and return its contents as a phrases dict.

    If the translation for a phrase is None for a particular language,
    the translations dict in the return value will not include that
    language as a key for that phrase.
    """
    # Use the English file to establish the text ID's.
    phrases = read_translations_file(rel_dir, lang=LANG_ENGLISH)
    for lang in LANGS_NON_ENGLISH:
        non_english = read_translations_file(rel_dir, lang=lang)
        for text_id, translations in non_english.items():
            try:
                text_info = phrases[text_id]
            except KeyError:
                # Then the text ID is present in the non-English but not English.
                raise Exception("text_id: {0}".format(text_id))
            if translations[lang] is None:
                del translations[lang]
            text_info.update(translations)

    return phrases


def get_phrases():
    phrases_seq = []
    for dir_name in (_DIR_PHRASES_CSV, _DIR_PHRASES_EXTRA):
        rel_dir = get_rel_path_phrases(dir_name=dir_name)
        phrases = read_phrases_dir(rel_dir)
        phrases_seq.append(phrases)
    phrases1, phrases2 = phrases_seq
    text_ids1, text_ids2 = (set(p) for p in phrases_seq)
    common_ids = set(text_ids1).intersection(set(text_ids2))
    if common_ids:
        raise Exception("should be empty: {0}".format(common_ids))
    phrases1.update(phrases2)
    return phrases1


def get_lang_phrase(translations, lang):
    # This requires that the key be present for English.
    return translations[lang] if lang == LANG_ENGLISH else translations.get(lang, None)


def _make_translations_texts(phrases, lang):
    """Create the texts node suitable for writing to a translations file."""
    data = {}
    for text_id, translations in phrases.items():
        # TODO: use a less-brittle approach.
        if EDGE_STRING in text_id and lang not in LANGS_SHORT:
            # Do not include text ID's for edge phrases in language files
            # that do not need to, because it would create the wrong
            # perception that such phrases need to be translated.
            continue
        phrase = get_lang_phrase(translations, lang)
        entry = {lang: phrase}
        if lang != LANG_ENGLISH:
            # Annotate with the English to make the raw file more readable.
            english = get_lang_phrase(translations, LANG_ENGLISH)
            entry[KEY_ENGLISH_ANNOTATION] = english
        data[text_id] = entry

    return data


def write_translations_file(phrases, dir_name, file_type, lang, comments=None):
    rel_path = get_rel_path_phrases(dir_name, lang=lang)
    data = _make_translations_texts(phrases, lang)
    data = {'texts': data}
    utils.write_yaml_with_header(data, rel_path=rel_path, file_type=file_type,
                                 comments=comments)


def write_translations_dir_csv(phrases):
    """Write the phrases to the extra translations directory."""
    dir_name = _DIR_PHRASES_CSV
    file_type = utils.FILE_AUTO_GENERATED
    for lang in LANGS:
        write_translations_file(phrases, dir_name=dir_name, file_type=file_type, lang=lang)


def write_translations_extra(phrases):
    """Write the phrases to the extra translations directory."""
    dir_name = _DIR_PHRASES_EXTRA
    file_type = utils.FILE_AUTO_UPDATED
    write_translations_file(phrases, dir_name=dir_name, file_type=file_type, lang=LANG_ENGLISH,
                            comments=COMMENT_TRANSLATIONS_EXTRA_ENGLISH)
    for lang in LANGS_NON_ENGLISH:
        write_translations_file(phrases, dir_name=dir_name, file_type=file_type, lang=lang,
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
    phrases = read_phrases_dir(rel_dir)

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


def update_csv_translations():
    phrases = read_csv_dir()
    write_translations_dir_csv(phrases)
