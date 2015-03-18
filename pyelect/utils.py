"""Project-wide helper functions."""

import os


REL_PATH_JSON = "offices.json"

def get_repo_dir():
    repo_dir = os.path.join(os.path.dirname(__file__), os.pardir)
    return os.path.abspath(repo_dir)


def get_data_path(name):
    repo_dir = get_repo_dir()
    path = os.path.join(repo_dir, 'data', '{0}.yaml'.format(name))
    return path


def get_default_json_path():
    repo_dir = get_repo_dir()
    return os.path.join(repo_dir, REL_PATH_JSON)


def get_template_dir():
    repo_dir = get_repo_dir()
    return os.path.join(repo_dir, 'templates')
