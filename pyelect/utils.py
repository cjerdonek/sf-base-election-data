"""Project-wide helper functions."""

import logging
import os

import yaml


_log = logging.getLogger()

REL_PATH_JSON = "offices.json"

def get_repo_dir():
    repo_dir = os.path.join(os.path.dirname(__file__), os.pardir)
    return os.path.abspath(repo_dir)


def get_data_dir():
    repo_dir = get_repo_dir()
    dir_path = os.path.join(repo_dir, 'pre_data')
    return dir_path


def get_yaml_path(name):
    data_dir = get_data_dir()
    path = os.path.join(data_dir, name)
    return path


def get_lang_dir():
    return get_yaml_path('languages')


def get_language_path(lang):
    lang_dir = get_lang_dir()
    return os.path.join(lang_dir, '{0}.yaml'.format(lang))


def get_yaml_file_path(name):
    return get_yaml_path('{0}.yaml'.format(name))


def get_default_json_path():
    repo_dir = get_repo_dir()
    return os.path.join(repo_dir, REL_PATH_JSON)


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
    return yaml.dump(*args, default_flow_style=False)


def write_yaml(data, path, stdout=False):
    with open(path, "w") as f:
        yaml_dump(data, f)
    if stdout:
        print(yaml_dump(data))