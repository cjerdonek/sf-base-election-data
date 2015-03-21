
from collections import defaultdict, namedtuple
import csv
import logging
import os
import re

from pyelect import utils


_log = logging.getLogger()

DIR_LANG = 'i18n'
DIR_LANG_AUTO = 'auto'

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


def get_lang_dir():
    dir_path = utils.get_pre_data_dir()
    return os.path.join(dir_path, DIR_LANG)


def get_lang_path(base, ext=None):
    if ext is None:
        ext = '.yaml'
    lang_dir = get_lang_dir()
    return os.path.join(lang_dir, '{0}{1}'.format(base, ext))


def add_key(dict_, key, value):
    if key in dict_ and value != dict_[key]:
        raise Exception("mismatch for {0!r}:\nold: {1}\nnew: {2}"
                        .format(key, dict_[key], value))
    dict_[key] = value


def _read_csv(path, skip_rows=1):
    with open(path) as f:
        reader = csv.reader(f)
        for i in range(skip_rows):
            next(reader)
        rows = list(reader)
    return rows


def _get_text_ids():
    path = utils.get_lang_path('text_ids/text_ids')
    ids_to_en = utils.read_yaml(path)
    en_to_ids = {}
    for text_id, en in ids_to_en.items():
        if en in en_to_ids:
            raise Exception("key already exists: {0}".format(en))
        en_to_ids[en] = text_id
    return en_to_ids


def _get_skip_words(base):
    path = utils.get_lang_path(base)
    data = utils.read_yaml(path)
    words = set(data['texts'])
    return words


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


def foo():
    # text_id = _make_text_id(data[0])
    # data = tuple([text_id] + data)

    skip_words = _get_skip_words()
    row_data = []
    text_map = {}
    for data in row_data:
        text_id = data[0]
        en_text = data[1]
        if en_text in skip_words:
            continue
        if text_id in text_map:
            # Then confirm that the text info is the same.
            if data != text_map[text_id]:
                raise Exception("different strings for key {0!r}:\n1: {1}\n2: {2}"
                                .format(text_id, data, text_map[text_id]))
        else:
            text_map[text_id] = data

    return text_map


def create_text_ids(path):
    seq = read_contest_csv(path)
    text_map = {}  # maps text ID to English phrase.
    skip = _get_skip_words('text_ids/_skip')
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


def create_auto_translations(path):
    en_to_ids = _get_text_ids()
    skip = _get_skip_words('manual/_skip')
    seq = read_contest_csv(path)
    # Mapp from language code to dict of: text_id to translation.
    all_langs = defaultdict(dict)
    for row in seq:
        english = row.en
        if english in skip:
            continue
        try:
            text_id = en_to_ids[english]
        except KeyError:
            # Do not process English words not in the dict of ID's.
            continue
        for code in LANGS:
            translations = all_langs[code]
            translated = getattr(row, code)
            add_key(translations, text_id, translated)
        for lang in LANGS_SHORT:
            translations = all_langs[lang]
            translated = getattr(row, "{0}_short".format(lang))
            add_key(translations, "{0}_edge".format(text_id), translated)

    en_translations = all_langs[LANG_EN]
    for lang in LANGS:
        yaml_texts = {}
        for text_id, text in all_langs[lang].items():
            entry = {lang: text}
            if lang != LANG_EN:
                # Add English to non-English files for readability.
                entry['_{0}'.format(LANG_EN)] = en_translations[text_id]
            yaml_texts[text_id] = entry
        data = {'texts': yaml_texts}
        path = utils.get_lang_path('auto/{0}'.format(lang))
        utils.write_yaml(data, path, stdout=True)
