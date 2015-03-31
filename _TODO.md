TODO
====

* Rename the `translations_*` directories to phrases*.
* Include the extras in the JSON file.
* Include an "edge" flag in the HTML and JSON?
* Make sure all non-English extras are accounted for (e.g. after updates).
* Add Languages object with notes attribute.
* Make a page to display all translations:
  id
    - en
    - sp
    - ch
    - notes
* Add a source for each translation.
* Settle the language stuff.
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
* Make command to generate a translation file from the English.
  - And start work on manual..
* Clean up en.yaml, and add Spanish and Chinese in the cleaned-up format.
* Prioritize listing the offices as they appear in sf.json.
  - Different groupings and filters can happen later.
  - Come up with a DRY pattern to display each language labeled
    with the language name (try using a macro).
  - Also note when language is missing
  - Document the JSON objects as I go.
* Document Court of Appeals.
* Do Supreme Court.
* Mark partisan.
