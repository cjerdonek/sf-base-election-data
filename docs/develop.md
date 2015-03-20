# Development

This document is mainly for project contributors.

## Setup

You should use Python 3.4.  We also recommend setting up a virtual
environment.  Then--

    $ pip install Jinja2 PyYAML


## Excel Language Files

This section discusses the Excel language files from the San Francisco
Department of Elections.

After receiving the Excel files, save each "sheet" (aka tab) of the
spreadsheet as a separate CSV for more predictable parsing.
Save the CSV files to the `misc` directory.

Use the following export options (using [LibreOffice][libre_office],
for example):

* Character set: Unicode (UTF-8)
* Field delimiter: `,` (comma)
* Text delimiter: `"` (double quotes)

See also the screen shot below:

![](images/excel_to_csv.png "Options to Export Excel to CSV")


[libre_office]: http://www.libreoffice.org/
