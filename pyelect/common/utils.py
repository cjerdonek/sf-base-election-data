"""Project-wide helper functions."""

import logging
import os
from pprint import pformat, pprint


_log = logging.getLogger()

I18N_SUFFIX = '_i18n'
LANG_ENGLISH = 'en'

DIR_NAME_OBJECTS = 'objects'
DIR_NAME_PRE_DATA = 'pre_data'

JSON_FIELDS_PATH = os.path.join(DIR_NAME_PRE_DATA, 'json_fields.yaml')
JSON_OUTPUT_PATH = 'data/sf.json'
LICENSE_PATH = 'data/LICENSE.txt'

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


def append_i18n_suffix(base_name):
    return "{0}{1}".format(base_name, I18N_SUFFIX)


def filter_dict_by_keys(data, keys):
    return {k: v for k, v in data.items() if k in keys}


class KeyMissingError(Exception):
    pass


def get_required(mapping, key):
    try:
        value = mapping[key]
    except KeyError:
        raise KeyMissingError("key missing: '{key}'\n{0}".format(pformat(mapping), key=key))
    return value


def get_yaml_file_name(base_name):
    return "{0}.yaml".format(base_name)


def get_repo_dir():
    repo_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    return os.path.abspath(repo_dir)


def get_pre_data_dir():
    repo_dir = get_repo_dir()
    dir_path = os.path.join(repo_dir, DIR_NAME_PRE_DATA)
    return dir_path


def get_yaml_objects_dir_rel():
    return os.path.join(DIR_NAME_PRE_DATA, DIR_NAME_OBJECTS)


def get_yaml_objects_path_rel(base_name):
    dir_path = get_yaml_objects_dir_rel()
    file_name = get_yaml_file_name(base_name)

    return os.path.join(dir_path, file_name)


def write(path, text):
    _log.info("writing to: {0}".format(path))
    with open(path, mode='w') as f:
        f.write(text)


def get_referenced_object(object_data, id_attr_name, global_data):
    """Retrieve an object referenced by ID from the global data.

    Arguments:
      id_attr_name: name of the attribute whose value is an ID.
    """
    assert id_attr_name.endswith('_id')
    object_id = object_data.get(id_attr_name)
    if object_id is None:
        return None
    type_name = id_attr_name[:-3]
    types_name = type_name_to_plural(type_name)
    objects = global_data[types_name]
    ref_object = objects[object_id]

    return ref_object

def get_field(field_name, fields):
    if field_name.endswith(I18N_SUFFIX):
        field_name = field_name.rstrip(I18N_SUFFIX)
    field = fields[field_name]

    return field


def normalize_field_name(field_name, fields):
    field = get_field(field_name, fields)
    if field.get('i18n_okay') and not field_name.endswith(I18N_SUFFIX):
        field_name = append_i18n_suffix(field_name)

    return field_name


# TODO: DRY up with normalize_field_name().
def normalize_field_info(field_name, value, fields, global_data):
    """Return a normalized 2-tuple of: field_name, value.

    For i18n fields, the field_name return value should end in "_i18n" and
    the value should be the dict of translations (supplemented with
    the phrase ID stored with key "_id").
    """
    if field_name.endswith(I18N_SUFFIX):
        phrase_id = value
        simple_field_name = field_name.rstrip(I18N_SUFFIX)
        field = fields[simple_field_name]
        assert field.get('i18n_okay')
        phrases = get_required(global_data, 'phrases')
        value = phrases[phrase_id].copy()
        value['_id'] = phrase_id
    else:
        field = fields[field_name]
        if field.get('i18n_okay'):
            field_name = append_i18n_suffix(field_name)
            value = {LANG_ENGLISH: value}

    return field_name, value


def get_field_value(obj, field_name, field):
    """Look up a field value from an object.

    Arguments:
      field_name: the non-i18n name of the field.
    """
    if field.get('i18n_okay'):
        i18n_field_name = append_i18n_suffix(field_name)
        if i18n_field_name in obj:
            # Sanity check: make sure the non-i18n version isn't also defined.
            assert field_name not in obj
            field_name = i18n_field_name
    if field_name not in obj:
        return None
    value = obj[field_name]

    return field_name, value


def get_object_data_field_info(object_data, field_name, field, global_data):
    # TODO: examine copy_from?
    field_info = get_field_value(object_data, field_name, field)

    # TODO: uncomment the below if it turns out we need to support "inherit".
    # if field_info is not None:
    #     return field_info
    #
    # # Otherwise, fetch the inherited value if there is one.
    # inherit_field_name = field.get('inherit')
    # if inherit_field_name is None:
    #     return None
    # parent = get_referenced_object(object_data, inherit_field_name, global_data=global_data)
    # if parent is None:
    #     return None
    # # TODO: use the parent type's field object rather than the child's.
    # field_info = get_field_value(parent, field_name, field)

    return field_info


def create_object(object_data, fields, object_id, global_data, object_base=None):
    """Create an object from field configuration data."""
    if object_base is None:
        object_base = {}

    obj = {}
    # Copy all field data from object_data.  We iterate over fields.keys()
    # rather than object_data.keys() since the field values stored in
    # object_data do not always correspond directly to the names of fields,
    # for example "copy_from".
    for field_name, field in sorted(fields.items()):  # We sort for reproducibility.
        info = get_object_data_field_info(object_data, field_name, field=field,
                                          global_data=global_data)
        if info is None:
            continue
        field_name, value = info
        field_name, value = normalize_field_info(field_name, value, fields,
                                    global_data=global_data)
        obj[field_name] = value

    # We copy field values from the base object _after_ setting the concrete
    # values as opposed to before in order to address the issue of
    # possibly invalid field values in the base object.  For example, the
    # base object can generate invalid phrase ID's resulting from a format
    # string in the base.  We do not want to process such ID's in cases
    # where the value is overridden by a concrete setting in the child.
    for field_name, value in sorted(object_base.items()):  # We sort for reproducibility.
        normalized_field_name = normalize_field_name(field_name, fields)
        if normalized_field_name in obj:
            continue
        value = easy_format(value, id=object_id, **object_data)
        try:
            field_name, value = normalize_field_info(field_name, value, fields,
                                        global_data=global_data)
        except:
            raise Exception("while processing object (field={0!r}):\n{1}"
                             .format(field_name, pformat(obj)))
        obj[field_name] = value

    return obj


def _on_check_object_error(html_obj, type_name, field_name, data_type, details):
    message = "{details} (data_type={data_type!r}, type_name={type_name!r}, field={field_name!r}):\n{object}"
    raise Exception(message.format(object=pformat(html_obj), field_name=field_name,
                                   type_name=type_name, details=details,
                                   data_type=data_type))


# TODO: decide re: not existing versus existing as None.
#   Answer: start out by requiring that values not be None.
#   If needed, we can always add a "none_okay" attribute.
def check_object(obj, fields, type_name, data_type):
    # We sort when iterating for repeatability when troubleshooting.
    for field_name in sorted(fields.keys()):
        field = fields[field_name]
        if not field.get('required'):
            continue
        if field_name not in obj:
            _on_check_object_error(obj, type_name, field_name, data_type,
                                   details="required field missing")
        if obj[field_name] is None:
            _on_check_object_error(obj, type_name, field_name, data_type,
                                   details="required field is None")
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
