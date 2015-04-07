TODO
====

* Flesh out President and then US Senate (with districts and election method).
* Edit notes for body: California Court of Appeal, First District
* Add jurisdiction to body (inherit from district type)?
* Change the i18n fields on body from the translations to the ID.
* Add the following to SF Community College:
    name: San Francisco Community College District
    wikipedia: http://en.wikipedia.org/wiki/City_College_of_San_Francisco
* Include an "edge" flag in the HTML and JSON?
* Make sure all non-English extras are accounted for (e.g. after updates).
* Hamburger nav
* Add a source for each translation.
  - Allow for translation notes?
* Review `office_bart_director` id.
* Add a `seat_name` attribute to Office that distinguishes members from
  one another (and `office_name` is the more generic name).
* Think about whether internationalized text should be mandatory
  (at least in the config).
  - If so, create a workflow to add new text ID's.
  - This way people will be able to add translations.
  - Also clean things up in this regard (will simplify things going forward).
  - Move extra i18n values into the manual section.
* Show the body name when there is a body (or else None).
  - Work on BOS first.
* Link to the body in each office section.
* Show the seat name (that distinguishes among body members)
  - at the top, but below the overall name.
* Add voting method enum (with Wikipedia link).
* Change seats to SF seats, e.g. 2 of 80.

* Add vote method object (to spell it out)
* Prioritize listing the offices as they appear in sf.json.
  - Different groupings and filters can happen later.
  - Also note when language is missing
  - Document the JSON objects as I go.
* Document Court of Appeals.
* Do Supreme Court.
* Mark partisan.
