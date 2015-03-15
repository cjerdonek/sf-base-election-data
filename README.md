# San Francisco Elected Offices

This is an open data project to provide information about the offices on
the ballot in San Francisco elections.


## Overview

The data is provided as [YAML](http://www.yaml.org/) files checked into
the repository.

The data can be
"[mashed up](http://en.wikipedia.org/wiki/Mashup_%28web_application_hybrid%29)"
with or otherwise used to supplement information about--

* what is on the ballot,
* election results, or
* campaign finance information.

Examples of the type of information that the project aims to provide include--

* all local, state, and federal offices that appear on San Francisco ballots,
* links to the official web site of each office or office body,
* the lengths of the terms of each office, and
* district information for each office (e.g. list of precincts).

The focus of this project is on the information that tends to remain the
same from election to election.  Thus, the project does not provide
information about candidates, election results, or current office holders.

Other project features include--

* the data is in an open, machine-readable, structured format
  ([YAML](http://www.yaml.org/));
* textual information occurs in multiple languages (e.g. English,
  Chinese, Spanish, and Filipino);
* the data includes the precincts covered by each office;


## Rules

* A mixin cannot be used if a body_id is present.


## Background

See Article XIII: ELECTIONS, SEC. 13.101. TERMS OF ELECTIVE OFFICE. of the
San Francisco Charter for information about terms of offices, etc.

Resources:

* [List of Local Elected Officials](http://www.sfgov2.org/index.aspx?page=832)
* [List of State Elected Officials](http://www.sfgov2.org/index.aspx?page=833)
