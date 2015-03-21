
import csv

from pyelect import utils


# The short strings are for Edge review (24 characters max).
CONTEST_HEADER_INDICES = {
    'en': 1,
    'en_short': 4,
    'es': 6,
    'es_short': 7,
    'fi': 2,
    'fi_short': 3,
    'zh': 5,
}

def _get_skip_words():
    path = utils.get_lang_path('manual/_skip')
    data = utils.read_yaml(path)
    words = set(data['texts'])
    return words

def parse_contest_csv(path):
    skip_words = _get_skip_words()
    with open(path) as f:
        reader = csv.reader(f)
        rows = [row for row in reader if row[1]]
    headers = sorted(CONTEST_HEADER_INDICES.keys())
    row_data = []
    for row in rows:
        data = tuple((row[CONTEST_HEADER_INDICES[h]].strip() for h in headers))
        row_data.append(data)
    text_map = {}
    for data in row_data:
        en_text = data[0]
        # if en_text in skip_words:
        #     continue
        if en_text in text_map:
            # Then confirm that the text info is the same.
            if data != text_map[en_text]:
                raise Exception("different translations for same English:\n1: {0}\n2: {1}"
                                .format(data, text_map[en_text]))
        else:
            text_map[en_text] = data

    return None
