# SF Base Election Data (SFBED)

SFBED is an open data project to provide baseline information about
San Francisco elections in an open, machine-readable, documented, and
structured form.

The end product of the project is a single, static, publicly available
[JSON][json] file (maintained at [`data/sf.json`](data/sf.json)), along
with supporting documentation.  This file is placed in the public domain.
See the [License](#license) section below for details.

The JSON file provides in a structured format information about San
Francisco elections that tends to remain the same from election to election.
This includes things like information about the offices and government
bodies that appear on the ballot, and what precincts and districts they
cover.

Anyone can use this information, for example by [mashing it up][mash_up]
with other election data for your own purposes (e.g. media pieces, research
projects, campaign finance reports, election results, ballot information,
etc.).  The project eliminates the need to manually compile this
information on your own.

See [here][SFBED_gh_page] for a sample web page created from this data.
If you notice any issues with the data or have any other project suggestions,
please file an issue in the [issue tracker][issue_tracker].

SFBED is a project of the [SF Elections Data][sf_elections_data] group
of [Code for San Francisco][code_for_sf].


## Overview

The data is provided as a single JSON file included in this repository:
[`data/sf.json`](data/sf.json).

Examples of the type of information that the project aims to provide include--

* all local, state, and federal offices that appear on San Francisco ballots,
* links to the official web site of each office or office body,
* the lengths of the terms of each office, and
* district information for each office (e.g. list of precincts).

The project focus is on the information that tends to remain the
same from election to election.  Thus, the project does not provide
information about candidates, election results, or current office holders.

To permit a higher guarantee of quality and accuracy, the focus of the
project is on the information that tends to remain the same from election
to election (or that changes infrequently).


## Languages

The project has partial support for [internationalization][i18n] (aka "i18n"),
which means support for multiple languages.  The data provides
translations of some English phrases into the following languages:

* Chinese
* Spanish
* Filipino/Tagalog (limited)

The [San Francisco Department of Elections][SFDOE] currently prints official
ballots in English, Chinese, and Spanish.  In November 2015, the
Department will begin printing official ballots in Filipino (see
[here](http://www.sfmayor.org/index.aspx?recordid=543&page=998) for
information on the San Francisco [Language Access Ordinance][SFLAO], or LAO).

The project would also like to add translations in the following languages--

* Japanese
* Korean
* Vietnamese

In the November 2014 election, in addition to Chinese and Spanish, the
Department of Elections also made translations of election materials
available in the three languages above, as well as Filipino.  Translated
materials included ballots and related instructions, State Voter
Information Guides, and Voter Bill of Rights posters.  Thus, official
San Francisco translations already exist in some form, but just need
to be added to the data.


## Use Cases

Possible uses of the data include "[mashing up][mash_up]" with or otherwise
supplementing presentations of--

* what is on the ballot,
* election results, or
* campaign finance information.


## The Data

For how to interpret the JSON file, see [this page](docs/json.md).


## Sources

See Article XIII: ELECTIONS, SEC. 13.101. TERMS OF ELECTIVE OFFICE. of the
San Francisco Charter for information about terms of offices, etc.

Resources:

* [List of Local Elected Officials](http://www.sfgov2.org/index.aspx?page=832)
* [List of State Elected Officials](http://www.sfgov2.org/index.aspx?page=833)


## Contributors

Contributors should refer to the [contributor documentation](docs/develop.md)
for additional information.


## License

This project (with the exception of the JSON file as described below) is
licensed under the BSD 3-clause license.  See the [`LICENSE`](LICENSE) file
for details.

The database consisting of the JSON file located at
[`data/sf.json`](data/sf.json) in this repository is made available under
the Public Domain Dedication and License v1.0 whose full text can be
found at the file [`data/LICENSE.txt`](data/LICENSE.txt) in this repository,
as well as at the following location:
[http://opendatacommons.org/licenses/pddl/1.0/](http://opendatacommons.org/licenses/pddl/1.0/).


## Author

Chris Jerdonek (<chris.jerdonek@gmail.com>)


[code_for_sf]: http://codeforsanfrancisco.org/
[i18n]: http://en.wikipedia.org/wiki/Internationalization_and_localization
[issue_tracker]: https://github.com/cjerdonek/sf-base-election-data/issues
[json]: http://json.org/
[mash_up]: http://en.wikipedia.org/wiki/Mashup_%28web_application_hybrid%29
[pddl_v1.0]: http://www.opendatacommons.org/licenses/pddl/1.0/
[sf_elections_data]: http://cjerdonek.github.io/sf-elections-data/
[SFBED_gh_page]: http://cjerdonek.github.io/sf-base-election-data
[SFDOE]: http://sfelections.org
[SFLAO]: http://sfgsa.org/index.aspx?page=4450
