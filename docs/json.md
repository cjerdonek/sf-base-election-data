# The JSON File

This document describes the structure of the JSON file and how to
interpret it in human terms.


### Internationalization (i18n)

TODO

TODO: explain the `_i18n` suffix.


### Categories

The Category objects provide a loose, high-level way to group different
offices.  Currently, the categories correspond to: Federal, State, City
and County, School, and Judicial.

Attributes:

* `name_i18n`: the display name.


### Offices

Attributes:

* name_i18n: the office name, which may or may not be qualified with the
  jurisdiction (e.g. "UNITED STATES REPRESENTATIVE" is and "MAYOR" is not).
* url: the official URL for the office.

Construction:

* name:

