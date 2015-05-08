"""Project-wide helper functions."""

import logging
import os
from pprint import pformat

_log = logging.getLogger()

DIR_PRE_DATA = 'pre_data'

_SINGULAR_TO_PLURAL = {
    'body': 'bodies',
    'category': 'categories',
}

_PLURAL_TO_SINGULAR = {p: s for s, p in _SINGULAR_TO_PLURAL.items()}


def easy_format(format_str, *args, **kwargs):
    """Call format() with more informative errors."""
    try:
        formatted = format_str.format(*args, **kwargs)
    except KeyError:
        raise Exception("with: format_str={0!r}, args={1!r}, kwargs={2!r}"
                        .format(format_str, args, kwargs))
    return formatted


def type_name_to_plural(singular):
    """Return the node name given an object type name.

    For example, "body" yields "bodies".
    """
    try:
        plural = _SINGULAR_TO_PLURAL[singular]
    except KeyError:
        plural = "{0}s".format(singular)
    return plural


def types_name_to_singular(plural):
    try:
        singular = _PLURAL_TO_SINGULAR[plural]
    except KeyError:
        singular = plural[:-1]
    return singular


def filter_dict_by_keys(data, keys):
    return {k: v for k, v in data.items() if k in keys}


class KeyMissingError(Exception):
    pass


def get_required(mapping, key):
    try:
        value = mapping[key]
    except:
        raise KeyMissingError("key missing: '{key}'\n{0}".format(pformat(mapping), key=key))
    return value


def get_repo_dir():
    repo_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    return os.path.abspath(repo_dir)


def get_pre_data_dir():
    repo_dir = get_repo_dir()
    dir_path = os.path.join(repo_dir, DIR_PRE_DATA)
    return dir_path


def write(path, text):
    _log.info("writing to: {0}".format(path))
    with open(path, mode='w') as f:
        f.write(text)


def get_referenced_object(global_data, object_data, id_attr_name):
    """Retrieve an object referenced by ID from the global data."""
    assert id_attr_name.endswith('_id')
    object_id = get_required(object_data, id_attr_name)
    type_name = id_attr_name[:-3]
    types_name = type_name_to_plural(type_name)
    objects = global_data[types_name]
    ref_object = objects[object_id]

    return ref_object


def _on_check_object_error(html_obj, type_name, field_name, data_type, details):
    message = "{details} (data_type={data_type!r}, type_name={type_name!r}, field={field_name!r}):\n{object}"
    raise Exception(message.format(object=pformat(html_obj), field_name=field_name,
                                   type_name=type_name, details=details, data_type=data_type))


# TODO: decide re: not existing versus existing as None.
def check_object(obj, fields, type_name, data_type):
    # We sort when iterating for repeatability when troubleshooting.
    for field_name in sorted(fields.keys()):
        field = fields[field_name]
        if not field.get('required'):
            continue
        if field_name not in obj:
            _on_check_object_error(obj, type_name, field_name, data_type,
                                   details="field missing")
        if obj[field_name] is None:
            _on_check_object_error(obj, type_name, field_name, data_type,
                                   details="field should not be None")
        # allowed_types = (bool, int, str)
        # for attr, value in json_obj.items():
        #     if type(value) not in allowed_types:
        #         err = textwrap.dedent("""\
        #         json node with key "{node_name}" failed sanity check.
        #           object_id: "{object_id}"
        #           object attribute name: "{attr_name}"
        #           attribute value has type {value_type} (only allowed types are: {allowed_types})
        #           object:
        #         -->{object}
        #         """.format(node_name=node_name, object_id=object_id, attr_name=attr,
        #                    value_type=type(value), allowed_types=allowed_types,
        #                    object=json_obj))
        #         raise Exception(err)
