TODO
====

* Choose better names for `office_name` and generic `member_name`:
  - `office_name_format` for office.name
  - `member_name` for generic
* Clean up occurrences of `office_name_format`.
* Fix names for: SF Board of Supervisors and Education:
  - BoS should be, for example:
    1. MEMBER, BOARD OF SUPERVISORS, DISTRICT 2
  - English format strings should always only be used to generate English values.
  - Similarly, an i18n format string should always grab values for the
    corresponding language (if the name of the value ends in i18n).
  - Need to work out i18n format string with i18n values, etc,
    and consider the various combinations.
* Make office names take into account: seat_count, district, etc.
* Make name reflect: "Judge of the Superior Court, Seat No. 20"
* Somehow flag types as required in either the instance or the base
  (e.g. office/body)?
* Internationalize `body_ca_board_of_equalization.office_name`:
  - `text_office_member_state_board_of_eq_d2`
* Make `body.term_length` required.
* Make `body_ca_courts_of_appeal_d1` inherit from `body_ca_courts_of_appeal`.
* Add `name_short_i18n` to district in JSON file?
  - (and the body-specific variations -- search "distrito")
* Get translated phrases working again.
* Skip files beginning with a "." in the `copy_files()` helper function.
* Add court offices.
  - Call to see if they have seat numbers.
* Check Twitter for bodies.
* Check all `body.office_name_i18n` values.
* Add `int` type to fields.yaml.
* Member name for Supreme Court of California: Justice?
* Internationalize district short name.
* Change seats to SF seats, e.g. 2 of 80.
* Flesh out Body more
  - Election method, etc.
  - Try documenting it.
  - Should the `district_type` "object" be a property?
* Compute translations in header tag code?
* Make jurisdiction a name paired with a geographic area?
* Switch Court district and remove geographic label.
* Make a new type for CALIFORNIA COURTS OF APPEAL.
* Clean up & simplify the office HTML generation.
* Move "row" templates to a rows directory.
* Add jurisdiction to office & body (inherit from district type)?
* Edit notes for body: California Court of Appeal, First District
* Change the i18n fields on body from the translations to the ID.
* Add the following to SF Community College:
    name: San Francisco Community College District
    wikipedia: `http://en.wikipedia.org/wiki/City_College_of_San_Francisco`
* Include an "edge" flag in the HTML and JSON?
* Make sure all non-English extras are accounted for (e.g. after updates).
* Hamburger nav
* Add a source for each translation.
  - Allow for translation notes?
* Think about whether internationalized text should be mandatory
  (at least in the config).
  - If so, create a workflow to add new text ID's.
  - This way people will be able to add translations.
  - Also clean things up in this regard (will simplify things going forward).
  - Move extra i18n values into the manual section.
* Add voting method enum (with Wikipedia link).
* Have a way to note when translations are missing.
* Document the JSON objects as I go.
* Document Court of Appeals.
