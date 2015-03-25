# The JSON File

This document describes the structure of the JSON file and how to
interpret it in human terms.


## Overview

The overall structure of the JSON is a collection of key-value pairs.

For the purposes of this documentation, we call a collection of key-value
pairs a "dictionary."  Also for this documentation, we use "object" to mean
a dictionary that corresponds to a specific everyday concept or thing
(e.g. a particular office, government body, or district).

For the most part, the top-level key-values in the JSON file are of the
form: "plural object type name" to "dictionary of objects of that type."
For example, the string "offices" might map to a dictionary of "office"
objects (an example of an office is the office of Mayor).  Moreover, each
key-value pair in each dictionary of objects has the form: "string ID"
to "object," where the string ID is the ID of the object.

Each object type has a number of possible key or field names, which we
call attributes.  The attributes describe aspects of each object.
For example, the body object has attributes for the body name and web
site URL, along with several others.  The sections below document the
attributes recognized by each type of object.


## Languages (i18n)

The string "i18n" stands for "[internationalization][i18n]," which is one
of the words commonly used to describe making a web site or application
display correctly in multiple languages.

In the JSON, the value of an internationalized attribute takes the form
of a dictionary whose
keys are string language ID's and whose values are the translations
of the given text into the corresponding language.  For example,
the value of ...

An object attribute whose name ends in `_i18n` is what we call an
internationalized attribute.  The value of such an attribute corresponds
to text that has been translated into possibly several languages.


TODO


## Objects

TODO


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


[i18n]: http://en.wikipedia.org/wiki/Internationalization_and_localization
