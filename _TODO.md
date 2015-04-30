TODO
====

* Add order_number to HTML category object.
* Implement sub-category using a new sorting pattern that is more in line
  with Django idioms (e.g. regroup).
  - Design the pattern
* Work out a DRY pattern for category/sub-category display, maybe
  by adding more parameters to the tag currently used for the index page.
* Address `_set_html_object_data()` setting all fields to be internationalizable.
* Contemplate generating more of the HTML via config, specifically
  the keys that should be copied from JSON.
* Get district working for US Senate (with district that references area).
  - include wiki links for House districts
* Add jurisdiction to body and office (at least for national to start out).
  - Maybe a jurisdiction is a name paired with a geographic area?
* Flesh out President and then US Senate (with districts and election method).
* Should CALIFORNIA COURTS OF APPEAL be made an office type?
* Switch Court district and remove geographic label.
* Seat count for school board.
* Clean up & simplify the office HTML and JSON generation.
* Move "row" templates to a rows directory.
* Add jurisdiction to office & body (inherit from district type)?
* Edit notes for body: California Court of Appeal, First District
* Change the i18n fields on body from the translations to the ID.
* Add a way to check that all info is present on each object.
* Add the following to SF Community College:
    name: San Francisco Community College District
    wikipedia: `http://en.wikipedia.org/wiki/City_College_of_San_Francisco`
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
* Show the seat name (that distinguishes among body members)
  - at the top, but below the overall name.
* Add voting method enum (with Wikipedia link).
* Change seats to SF seats, e.g. 2 of 80.
* Have a way to note when translations are missing.
* Document the JSON objects as I go.
* Document Court of Appeals.
* Do Supreme Court.
* Mark partisan.
