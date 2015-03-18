"""Support for making html."""

from jinja2 import Environment, FileSystemLoader

from pyelect import utils

def make_html():
    template_dir = utils.get_template_dir()
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('sample.html')
    return template.render(title="Foo")
