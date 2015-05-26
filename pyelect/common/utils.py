"""Project-wide helper functions."""

import functools
import logging
import os
from pprint import pformat, pprint


_log = logging.getLogger()

I18N_SUFFIX = '_i18n'
LANG_ENGLISH = 'en'

DIR_NAME_OBJECTS = 'objects'
DIR_NAME_PRE_DATA = 'pre_data'

JSON_OUTPUT_PATH = 'data/sf.json'
JSON_TYPES_PATH = os.path.join(DIR_NAME_PRE_DATA, 'json_types.yaml')
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
    except AttributeError:
        raise Exception("format_str: {0!r}".format(format_str))
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
    if not id_attr_name.endswith('_id'):
        raise AssertionError("id_attr_name '{0}' does not end in '_id' for object:\n"
                             "-->{1}".format(id_attr_name, object_data))
    object_id = object_data.get(id_attr_name)
    if object_id is None:
        return None
    type_name = id_attr_name[:-3]
    types_name = type_name_to_plural(type_name)
    objects = global_data[types_name]
    ref_object = objects[object_id]

    # TODO: make this return only the object once we make the type name
    #   accessible from the object.
    return type_name, ref_object


def get_field(field_name, fields):
    """Raises KeyError if the field does not exist."""
    if field_name.endswith(I18N_SUFFIX):
        field_name = field_name.rstrip(I18N_SUFFIX)
    field = fields[field_name]

    return field


def set_field_values(obj, object_id, object_data, object_base, type_fields, object_types, global_data):
    # Copy all field data from object_data.  We iterate over type_fields
    # instead of object_data.keys() since the field values stored in
    # object_data do not always correspond directly to the names of fields,
    # for example "copy_from".
    for field_name, field in sorted(type_fields.items()):  # sort for reproducibility.
        value_info = field.resolve_value(object_data, object_types=object_types,
                                         global_data=global_data)
        if value_info is None:
            continue
        resolved_field, value = value_info
        obj[field.normalized_name] = value

    # We copy field values from the base object _after_ setting the concrete
    # values as opposed to before in order to address the issue of
    # possibly invalid field values in the base object.  For example, the
    # base object can generate invalid phrase ID's resulting from a format
    # string in the base.  We do not want to process such ID's in cases
    # where the value is overridden by a concrete setting in the child.
    for field_name, value in sorted(object_base.items()):  # sort for reproducibility.
        field = get_field(field_name, type_fields)
        normalized_field_name = field.normalized_name
        if normalized_field_name in obj:
            continue
        value = easy_format(value, id=object_id, **object_data)
        value = field.normalize_value(field_name, value, global_data)
        obj[normalized_field_name] = value

    # Process format strings last since they rely on other values.
    for field_name, field in sorted(type_fields.items()):  # sort for reproducibility.
        if not field.should_format:
            continue
        field_name = field.normalized_name
        value = obj[field_name]
        # TODO: handle this better and make DRY.
        if isinstance(value, str):
            value = easy_format(value, **obj)
        else:
            # Otherwise, the value is a dict.
            # Copy the value since we are modifying it.
            value = value.copy()
            for key, format_str in sorted(value.items()):
                formatted = easy_format(format_str, **obj)
                value[key] = formatted
            # Since we formatted, the strings no longer match the original.
            try:
                del value['_id']
            except KeyError:
                pass

        obj[field_name] = value


def create_object(object_data, type_name, object_id, object_types, global_data, mixins,
                  object_base=None):
    """Create an object from field configuration data."""
    if object_base is None:
        object_base = {}

    obj = {}

    mixin_id = object_data.get('mixin_id')
    if mixin_id is not None:
        mixin = mixins[mixin_id]
        obj.update(mixin)

    object_type = object_types[type_name]
    type_fields = object_type._fields

    set_field_values(obj, object_id, object_data, object_base, type_fields,
                     object_types=object_types, global_data=global_data)

    return obj


def _on_check_object_error(obj, object_id, type_name, field_name, data_type, details):
    message = "{details} (object_id={object_id!r}, type_name={type_name!r}, field={field_name!r}, data_type={data_type!r}):\n{object}"
    raise Exception(message.format(object=pformat(obj), object_id=object_id,
                                   field_name=field_name, type_name=type_name, details=details,
                                   data_type=data_type))


# TODO: decide re: not existing versus existing as None.
#   Answer: start out by requiring that values not be None.
#   If needed, we can always add a "none_okay" attribute.
def check_object(obj, object_id, type_name, data_type, object_types):
    object_type = object_types[type_name]
    type_fields = object_type._fields

    for field_name, value in sorted(obj.items()):  # sort for reproducibility.
        try:
            # Ensure that every field value is supposed to be there.
            field = get_field(field_name, type_fields)
        except KeyError:
            raise Exception("field '{0}' is not defined for type '{1}':\n{2}"
                            .format(field_name, type_name, pformat(obj)))
        if (field.is_i18n and not field_name.endswith(I18N_SUFFIX) and
            not isinstance(value, str)):
            raise Exception("field {0!r} should be a string:\n{1}"
                            .format(field_name, pformat(value)))

    # We sort when iterating for repeatability when troubleshooting.
    for field_name, field in sorted(type_fields.items()):  # sort for reproducibility.
        if not field.is_required:
            continue
        if field_name not in obj:
            _on_check_object_error(obj, object_id, type_name, field_name, data_type,
                                   details="required field missing")
        if obj[field_name] is None:
            _on_check_object_error(obj, object_id, type_name, field_name, data_type,
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


def make_phrase_value(phrase_id, global_data):
    phrases = get_required(global_data, 'phrases')
    value = phrases[phrase_id].copy()
    value['_id'] = phrase_id

    return value


class Field(object):

    def __init__(self, name, data):
        self.data = data
        self.name = name

    def __repr__(self):
        return ("<Field at {1} (name={0!r}, data={2!r})>"
                .format(self.name, hex(id(self)), self.data))

    @property
    def is_i18n(self):
        return self.data.get('i18n_okay')

    @property
    def is_required(self):
        return self.data.get('required')

    @property
    def should_format(self):
        return self.data.get('format')

    @property
    def i18n_field_name(self):
        return append_i18n_suffix(self.name)

    @property
    def normalized_name(self):
        return self.i18n_field_name if self.is_i18n else self.name

    @property
    def inherit_name(self):
        return self.data.get('inherit')

    def normalize_value(self, name, value, global_data):
        if not self.is_i18n:
            return value
        if name.endswith(I18N_SUFFIX):
            # Then the value is a phrase ID.
            value = make_phrase_value(value, global_data)
        else:
            # Then the value is the English form, and there is no phrase ID.
            value = {LANG_ENGLISH: value}
        return value

    # TODO: distinguish between None and not found in the return value.
    def get_value(self, obj, global_data):
        """Look up a field value on an object, and return the value.

        This returns the normalized form of the value in the case of i18n
        fields.

        Arguments:
          obj: an object dict on which to look up the field value.
        """
        if self.is_i18n and self.i18n_field_name in obj:
            # TODO: add validation somewhere that i18n and non-i18n are not
            #   both defined in the raw data.
            field_name = self.i18n_field_name
        else:
            field_name = self.name
        value = obj.get(field_name)
        if value is None:
            return None
        value = self.normalize_value(field_name, value, global_data)

        return value

    def resolve_value(self, obj, object_types, global_data):
        """Look up and resolve a field value on an object.

        Returns (field, field_value).

        Arguments:
          obj: an object dict on which to look up the field value.
          field_name: the non-i18n name of the field.
          field: the dict describing the field.
        """
        # TODO: examine copy_from?
        value = self.get_value(obj, global_data)

        if value is not None:
            return self, value

        # Otherwise, fetch the inherited value if there is one.
        inherit_name = self.inherit_name
        if inherit_name is None:
            return None
        try:
            id_field_name, child_field_name = inherit_name.split('.')
        except ValueError:
            # Then use the same field name.
            id_field_name, child_field_name = inherit_name, self.name
        ref_info = get_referenced_object(obj, id_field_name, global_data=global_data)
        if ref_info is None:
            return None
        ref_type_name, ref_obj = ref_info
        ref_type = object_types[ref_type_name]
        ref_fields = ref_type._fields
        ref_field = ref_fields[child_field_name]
        value = ref_obj.get(ref_field.normalized_name)

        return ref_field, value


class ObjectType(object):

    def __init__(self, name, fields, data):
        """
        Arguments:
          fields: a dict mapping field_name to Field object.
        """
        self._data = data
        self._fields = fields
        self._name = name

    @property
    def customized(self):
        # Default to True because that will alert us to errors.
        return self._data.get('customized', True)

    def fields(self):
        # We sort for reproducibility.
        for field_name, field in sorted(self._fields.items()):
            yield field
