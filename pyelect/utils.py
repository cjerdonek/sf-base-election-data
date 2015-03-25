"""Project-wide helper functions."""

import logging
import os

import yaml


_log = logging.getLogger()

FILE_MANUAL = 'manual'
FILE_NORMALIZABLE = 'normalizable'
FILE_AUTO = 'auto_generated'

FILE_TYPES = (FILE_MANUAL, FILE_NORMALIZABLE, FILE_AUTO)

DIR_NAME_OUTPUT = '_build'
DIR_PRE_DATA = 'pre_data'
KEY_META = '_meta'
KEY_FILE_TYPE = 'type'


def get_from(dict_, key, message=None):
    try:
        value = dict_[key]
    except:
        raise Exception("error getting key {0!r} from: {1!r} message={2}"
                        .format(key, dict_, message))
    return value


def get_repo_dir():
    repo_dir = os.path.join(os.path.dirname(__file__), os.pardir)
    return os.path.abspath(repo_dir)


def get_pre_data_dir():
    repo_dir = get_repo_dir()
    dir_path = os.path.join(repo_dir, DIR_PRE_DATA)
    return dir_path


def write(path, text):
    _log.info("writing to: {0}".format(path))
    with open(path, mode='w') as f:
        f.write(text)


def read_yaml(path):
    with open(path) as f:
        data = yaml.load(f)
    return data


def yaml_dump(*args):
    return yaml.dump(*args, default_flow_style=False, allow_unicode=True)


def write_yaml(data, path, stdout=False):
    with open(path, "w") as f:
        yaml_dump(data, f)
    if stdout:
        print(yaml_dump(data))


def _get_yaml_meta(data):
    return get_from(data, KEY_META)


def _fix_header(data, file_type=None):
    try:
        meta = data[KEY_META]
    except KeyError:
        meta = {}
        data[KEY_META] = meta
    meta['_auto_comment'] = ("WARNING: normalization will remove YAML comments.")
    if file_type is not None:
        meta[KEY_FILE_TYPE] = file_type


def get_yaml_data(dir_path, base_name):
    """Return the data in a YAML file as a pair of dicts.

    Arguments:
      name: base name of the objects file (e.g. "offices" for "offices.yaml").
    """
    file_name = "{0}.yaml".format(base_name)
    path = os.path.join(dir_path, file_name)
    all_yaml = read_yaml(path)
    data = all_yaml[base_name]
    try:
        meta = _get_yaml_meta(all_yaml)
    except KeyError:
        raise Exception("from file at: {0}".format(path))

    return data, meta


def _get_yaml_file_type(data):
    meta = _get_yaml_meta(data)
    file_type = get_from(meta, 'type')
    if file_type not in FILE_TYPES:
        raise Exception('bad file type: {0}'.format(file_type))
    return file_type


def _is_yaml_normalizable(data):
    file_type = _get_yaml_file_type(data)
    # Use a white list instead of a black list to be safe.
    return file_type in (FILE_NORMALIZABLE, FILE_AUTO)


def normalize_yaml(path, stdout=None):
    data = read_yaml(path)
    try:
        normalizable = _is_yaml_normalizable(data)
    except:
        raise Exception("for file: {0}".format(path))
    if not normalizable:
        _log.info("skipping normalization: {0}".format(path))
        return

    _fix_header(data, file_type=None)

    write_yaml(data, path, stdout=stdout)
