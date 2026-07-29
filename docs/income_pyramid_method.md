# Household gross-income benchmark — method and data

## One input

The calculator accepts one figure: total annual gross income for the whole
household. It does not ask for separate earners or optional household net
income. An automatic gross-to-net conversion would create false precision
because taxes, social insurance, age, other income and transfers differ.

## What the ladder means

The reference is the average gross household income in Destatis EU-SILC 2025,
selected by official household type. The six available categories are a single
adult, two adults without children, another household with at least three
adults and no child, a single parent, two adults with children, and another
household with at least three adults and children. “Three or more adults” is
therefore not a relationship label. It may describe, for example, an adult
shared flat, parents with an economically independent adult child, or a
multigenerational household. This replaces the earlier EVS size-only
approximation, which could not justify labels such as “couple with one child”.

In this EU-SILC household typology, a child is a person under 18 or an
economically dependent person aged 18 to 24. Consequently, a 20-year-old with
an independent livelihood counts as an adult for these groups, while an
economically dependent 20-year-old counts as a child.

The interface calls the two-adult/no-child category “DINKs*” because the term
is familiar. The asterisk is essential: the source does not establish whether
both adults work or receive an income, so it is not a measured dual-income
category. EU-SILC does not split these averages by the exact number of children
or earners. Those types must not be inferred.

The selector shows a persistent explanation for the currently selected type.
The same explanation is attached to the selector and its options as a native
tooltip so that abbreviated or clipped labels remain understandable.

Current official data do not publish reliable top-10 or bottom-10 thresholds
for each exact household type used by the interface. The display therefore uses
transparent distance bands around the official average: below 50%, 50–75%,
75–90%, 90–110%, 110–150%, 150–200%, and at least 200%. These are RealityCheck
benchmark groups, not measured percentiles or social classes.

Housing cost, regional prices, tax, debt and wealth are not deducted. The
result is statistical orientation, not tax, social-security or financial
advice.

## Tests

- `node tests/income_pyramid.test.js`
- `php -d zend.assertions=1 -d assert.exception=1 tests/income_pyramid_data_test.php`
- a direct HTTP request for the protected data include must return 404
