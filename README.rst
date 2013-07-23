Introduction
============
The occams.lab product is an add-on to the avrc.aeh clinical product that acts
as an inventory of banked specimen, associating these specimen with patients,
study cycles and visit dates. The product controls how specimen are aliquoted,
and allows aliquot to be stored in a freezer/rack/box location, as well as tracking
aliquot check in and check out. Occams.lab uses event listeners to automatically
queue specimen for draw when a patient visit is added to the system (see
avrc.aeh for more information regarding patients, visits, studies and cycles.)

This product may contain traces of nuts.

Installation and Setup
======================
There are a few installation gotchas for the occams.lab product. After installing
the product through the "Add-on" section of plone, make sure you do the following:

1) Set up the behaviors
for some reason, the product's behaviors are not installed correctly. You must
manually set them up. Here is how:

After installing, navigate to the dexterity types section of site setup.
- Clinical Lab: Add both the Specimen Label Sheet and Aliquot Label Sheet behaviors.
- Research Lab: Add both the Specimen Label Sheet and Aliquot Label Sheet behaviors.
- Site: Add the Lab Location behavior.
- Study: Add the Available Specimen behavior.
- Cycle: Add Required Specimen behavior.
- Visit: Add Requested Specimen behavior.

2) Set up the Lab Locations.
There is currently a beta view through which to edit lab locations. Alternatively
you can edit them directly in the location table. To edit ttw, add a new institute
to your site, and then navigate to the "./lablocations" view.

3) Assign a default location to your Sites.
Each Site needs to have a default lab location. This controls where automatically
created specimen show up for draw. To do so, just select the Edit tab for your site
and use the lab location dropdown.

4) Add the Plone Lab objects to your Sites. There are two sorts of Labs. Clinical
Labs can draw specimen from a patient, as well as process those specimen into aliquot.
Research Labs only process specimen into aliquot. When configuring a Lab, there
are a few pieces to set up.

- Clinical Lab:
-- Set up the Lab's location. This should be the same location as its corresponding Site.
-- Set up the Lab's processing location. This can either be the same as its location (
meaning that specimen will be processed at the same location), or a different location,
if specimen will be shipped to another location before being aliquotted.
-- Set up the Lab's Specimen Sheet. Use the dimensions for the sort of Specimen labels
the lab will be using.
-- Set up the Lab's Aliquot sheet. Use the dimensions for the sort of Aliquot labels
the lab will be using.

- Research Lab:
-- Set up the Lab's location. This will be the same as the processing location from
the Research Lab's corresponding clinical lab.
-- Set up the Lab's storage location. This is the location where aliquot will be
placed upon completion. It is often the same as the Lab's location, but sometimes
the aliquot will be shipped to a final destination after being aliquotted.
-- Set up the Lab's Aliquot sheet. Use the dimensions for the sort of Aliquot labels
the lab will be using.

5) Set up the Specimen/Aliquot in the database. There is currently no ttw option
for configuring this aspect of the system. To set up this aspect of the occams.lab
system, use your preferred method of editing the database to add the specimen
to the specimentype table, and how that specimentype aliquots in the aliquottype
table.

Usage
=====

Study Configuration
-------------------
On a study's edit tab, there will be a sub-tab for specimen. There, type the
name of the specimen that you want associated with that study, and select it from
the drop-down list.

Cycle Configuration
-------------------
On a cycle's edit tab, there will be a sub-tab for specimen. There, type the
name of the specimen you want to be automatically queued when a visit with that
cycle is added.


Specimen Lifecycle
==================
When a visit is added to a patient, specimen for the visit's associated cycles
are created. (This behavior can be overridden by unchecking the "create specimen"
checkbox on the specimen sub-tab of the add a visit screen.)

These created specimen appear on the view screen (Specimen to be processed) of
the Clinical Lab if the visit date is on or before today in a pending state. Lab workers fill out
the appropriate information for the specimen, print labels using the label queue,
and then "Complete Selected". If the processing lab location is the same location
as this clinical lab, the specimen are moved to the "Batched" tab, awaiting processing.
If the processing lab location is at a different lab, the specimen will show up
in that lab's batched tab, if its a clinical lab, or its primary view if it is
a processing lab.

The Batched/Processing lab view lists all specimen that were successfully drawn.
The lab worker can then select some or all of the specimen and move them to the
"Ready to Aliquot" tab.

Under the "Ready to Aliquot" tab, each specimen will be displayed as a collection
of aliquot templates that directly reflects how those specimen aliquot. For instance,
if blood aliquot into plasma and pbmc, two templates will show at the top of the
screen for that blood aliquot. Using the template, the lab worker can create
a number of identical aliquot from a specimen, which show in the second table
on the same page. These pending aliquot can have labels printed, then either
checked in, checked out, or deleted (in case more aliquot were created in the
system than were actually aliquotted.)

If the aliquot were checked in, they are now available to view through the "View
Stored Aliquot" links at the top of the screen.

If the aliquot were checked out, they will show up on the Checkout Queue. This
queue allows you to set a new location as well as other sent information to the
aliquot.
Once checked out, if they were checked out to a location that has a Lab, the
aliquot will show up in the Check in tab of that Lab.


==================
Self-Certification
==================

    [ ] Internationalized

    [ ] Unit tests

    [ ] End-user documentation

    [ ] Internal documentation (documentation, interfaces, etc.)

    [ ] Existed and maintained for at least 6 months

    [ ] Installs and uninstalls cleanly

    [ ] Code structure follows best practice
