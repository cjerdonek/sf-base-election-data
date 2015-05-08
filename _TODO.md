TODO
====

* DRY up `description_plural` in district_types.yaml
* Make command to generate phrases.yaml.
* Get i18n node working in JSON as first node.
* Include i18n name fields in district_types JSON.
* Add `name_short_i18n` to district in JSON file?
  - (and the body-specific variations -- search "distrito")
* Get translated phrases working again.
* Add `name` and `name_i18n` to Office in JSON file.
  - Also document this for Office object.
* Add court offices.
  - Call to see if they have seat numbers.
* Somehow flag types as required in either the instance or the base (e.g. office/body)?
* Check Twitter for bodies.
* Internationalize district short name.
* Change seats to SF seats, e.g. 2 of 80.
* Flesh out Body more
  - Election method, etc.
  - Try documenting it.
  - Should the `district_type` "object" be a property?
* Make partisan required in Office only if no Body (and must be different).
* Compute translations in header tag code?
* Make jurisdiction a name paired with a geographic area?
* Switch Court district and remove geographic label.
* Make a new type for CALIFORNIA COURTS OF APPEAL.
* Clean up & simplify the office HTML and JSON generation.
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
* Add a `seat_name` attribute to Office that distinguishes members from
  one another (and `office_name` is the more generic name).
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
