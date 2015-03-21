"""Project-wide helper functions."""

import logging
import os

import yaml


_log = logging.getLogger()

REL_PATH_JSON = "offices.json"

def get_repo_dir():
    repo_dir = os.path.join(os.path.dirname(__file__), os.pardir)
    return os.path.abspath(repo_dir)


def get_pre_data_dir():
    repo_dir = get_repo_dir()
    dir_path = os.path.join(repo_dir, 'pre_data')
    return dir_path


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
    return yaml.dump(*args, default_flow_style=False, allow_unicode=True)


def write_yaml(data, path, stdout=False):
    with open(path, "w") as f:
        yaml_dump(data, f)
    if stdout:
        print(yaml_dump(data))
