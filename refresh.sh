cp ../sf-base-election-data/_build/html/*.html .
cp ../sf-base-election-data/_build/html/css/*.css css/
cp ../sf-base-election-data/_build/html/data/*.json data/
# Copy the LICENSE file.
cp ../sf-base-election-data/_build/html/data/*.txt data/
git add -u
git commit -m "Refresh from master."
git push
