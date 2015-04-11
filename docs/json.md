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


## Internationalization (aka "i18n")

The JSON file contains translations of many phrases into a number
of [languages](#languages).  These translations are all in the top
level JSON node with key "i18n," which we call the internationalization
node.

(The string "i18n" stands for "[internationalization][i18n]," which is
the word commonly used to describe making a web site or application render
in multiple languages or countries.)

### Translations node

The internationalization node is a dictionary of translations.  The keys
of the dictionary are text ID's, each of which corresponds to a word or
phrase.  The values ...


### Internationalized attributes

An object attribute whose name ends in `_i18n` is what we call an
internationalized attribute.  The value of such an attribute corresponds
to text that has been translated into possibly several languages.

In the JSON, the value of an internationalized attribute takes the form
of a dictionary whose
keys are language codes and whose values are the translations
of the given text into the corresponding language.  For example,
the value of ...



TODO

## Languages



## Objects

This section describes each type of object and its attributes.  The
object types are listed in alphabetical order.


### Categories

The Category objects provide a loose, high-level way to group different
offices.  Currently, the categories correspond to: Federal, State, City
and County, School, and Judicial.

Attributes:

* `name_i18n`: the display name.


### District Type

District type answers the question: given a district, what type of
district is it (e.g. )
### Offices

Attributes:

* name_i18n: the office name, which may or may not be qualified with the
  jurisdiction (e.g. "UNITED STATES REPRESENTATIVE" is and "MAYOR" is not).
* url: the official URL for the office.

Construction:

* name:


[i18n]: http://en.wikipedia.org/wiki/Internationalization_and_localization
