
from collections import defaultdict, namedtuple
import csv
import logging
import os
import re

from pyelect import utils


_log = logging.getLogger()

DIR_LANG = 'i18n'
DIR_LANG_AUTO = 'auto'
DIR_LANG_CONFIG = '_config'
DIR_LANG_TRANSLATIONS_EXTRA = 'translations_extra'

FILE_EXTRA_TEXT_IDS = 'text_ids_extra.yaml'

LANG_EN = 'en'
LANG_ES = 'es'
LANG_FI = 'fil'
LANG_CH = 'zh'

LANGS = [LANG_EN, LANG_ES, LANG_FI, LANG_CH]
LANGS_SHORT = [LANG_EN, LANG_ES, LANG_FI]

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

ContestRow = namedtuple('ContestRow', CONTEST_HEADERS)


def get_rel_path_lang_dir():
    return os.path.join(utils.DIR_PRE_DATA, DIR_LANG)

def get_rel_path_config_dir():
    lang_dir = get_rel_path_lang_dir()
    return os.path.join(lang_dir, DIR_LANG_CONFIG)

def get_rel_path_extra_translations_dir():
    lang_dir = get_rel_path_lang_dir()
    return os.path.join(lang_dir, DIR_LANG_TRANSLATIONS_EXTRA)

def get_rel_path_extra_text_ids():
    dir_path = get_rel_path_config_dir()
    return os.path.join(dir_path, FILE_EXTRA_TEXT_IDS)


def get_lang_dir():
    dir_path = utils.get_pre_data_dir()
    return os.path.join(dir_path, DIR_LANG)


def get_lang_path(base, ext=None):
    if ext is None:
        ext = '.yaml'
    lang_dir = get_lang_dir()
    return os.path.join(lang_dir, '{0}{1}'.format(base, ext))


def _read_csv(path, skip_rows=1):
    with open(path) as f:
        reader = csv.reader(f)
        for i in range(skip_rows):
            next(reader)
        rows = list(reader)
    return rows


def _get_text_ids():
    lang_dir = get_lang_dir()
    ids_to_en, meta = utils.get_yaml_data(lang_dir, 'text_ids')

    en_to_ids = {}
    for text_id, en in ids_to_en.items():
        if en in en_to_ids:
            raise Exception("key already exists: {0}".format(en))
        en_to_ids[en] = text_id
    return en_to_ids


def _get_yaml_node(base, key):
    path = get_lang_path(base)
    data = utils.read_yaml(path)
    return data[key]


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


def _create_lang_file_data(text_map, lang_code):
    """Create the data object suitable for writing to a language file.

    Arguments:
      text_map: a dict from text_id to dict of: lang_code to
        text translation.
    """
    data = {}
    english_annotation_key = '_{0}'.format(LANG_EN)
    for text_id, translations in text_map.items():
        # TODO: handle the case of the translation being missing.
        translation = translations[lang_code]
        text_entry = {lang_code: translation}
        if lang != LANG_EN:
            # Annotate with the English to make the raw file more readable.
            english = translations[LANG_EN]
            entry[english_annotation_key] = english
        data[text_id] = text_entry
    file_data = {'texts': data}

    return file_data


def update_adds():
    # TODO: load additions.yaml.
    # TODO: check that keys aren't already listed in text_ids.yaml?
    print("**")

def _add_key(dict_, key, value):
    if key in dict_ and value != dict_[key]:
        raise Exception("mismatch for {0!r}:\nold: {1}\nnew: {2}"
                        .format(key, dict_[key], value))
    dict_[key] = value


def _process_row(row, lang_data, skip_text_ids, manual, langs, text_id, attr_format):
    if text_id in skip_text_ids:
        return
    override = manual[text_id] if text_id in manual else []
    for lang_code in langs:
        one_lang = lang_data[lang_code]
        if lang_code in override:
            text = override[lang_code]
        else:
            text = getattr(row, attr_format.format(lang_code))
        _add_key(one_lang, text_id, text)


def lang_contest_csv_to_yaml(input_path):
    seq = read_contest_csv(input_path)

    skip_phrases = _get_yaml_set('_config/skips', 'phrases')
    seq = [row for row in seq if row.en not in skip_phrases]

    english_to_ids = _get_text_ids()
    skip_text_ids = _get_yaml_set('_config/skips', 'text_ids')

    manual = _get_yaml_node('_config/resolve', 'override')
    # Dict from lang_code to dict of: text_id to translation.
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
