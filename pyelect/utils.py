"""Project-wide helper functions."""

import os


def get_repo_dir():
    repo_dir = os.path.join(os.path.dirname(__file__), os.pardir)
    return os.path.abspath(repo_dir)


def get_template_dir():
    repo_dir = get_repo_dir()
    return os.path.join(repo_dir, 'templates')
