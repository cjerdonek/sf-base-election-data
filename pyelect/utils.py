"""Project-wide helper functions."""

import logging
import os

import yaml


_log = logging.getLogger()

DIR_PRE_DATA = 'pre_data'
KEY_META = '_meta'

def get_repo_dir():
    repo_dir = os.path.join(os.path.dirname(__file__), os.pardir)
    return os.path.abspath(repo_dir)


def get_pre_data_dir():
    repo_dir = get_repo_dir()
    dir_path = os.path.join(repo_dir, DIR_PRE_DATA)
    return dir_path


def get_template_dir():
    repo_dir = get_repo_dir()
    return os.path.join(repo_dir, 'templates')


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
    return data[KEY_META]


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


def _is_yaml_normalizable(data):
    try:
        meta = _get_yaml_meta(data)
        normalizable = meta['normalizable']
    except KeyError:
        normalizable = False
    return normalizable


def normalize_yaml(path, stdout=None):
    data = read_yaml(path)
    if not _is_yaml_normalizable(data):
        raise Exception("file not marked normalizable: {0}".format(path))
    meta = _get_yaml_meta(data)
    meta['_auto'] = "WARNING: comments will be deleted during normalization"
    write_yaml(data, path, stdout=stdout)
