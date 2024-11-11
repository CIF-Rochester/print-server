CIF Print Server
------------------
Creation of a new print server for CIF that eliminates bloat and allows greater maintainability (again). Updated 2024.

# Operation
Print data is retrieved from print.cif.rochester.edu? hosted by the server.  After ensuring files are nonnull and all pdfs,
a copy of each file uploaded is saved to the path labeled ``UPLOAD_FOLDER`` in app.py, prefixed by the time and date of
attempted print.  An entry to print.log is also created containing the date, time, user, file, and relevant page info.
Note a print need not be successful to have a log entry.  Any error thrown will result in a new log entry and the file
uploaded to storage.  The two exceptions are the "No file attached" and "Attached file is not pdf" errors.  Also note that
file storage is only updated when a print is attempted and not at regular intervals.  This means that the files in storage
represent all attempted print files within a certain type of the latest attempted print, not necessarily the current date.

After any attempted print without exception, file storage is updated and all files older than a certain threshold are deleted.
This threshold is specified by the ``FILE_SAVE_TIME`` parameter in app.py

# Variables
As mentioned above, app.py contains 4 adjustable variables: ``UPLOAD_FOLDER``, ``PRINTER_NAME``, ``MAX_PAGES``, and ``FILE_SAVE_TIME``.
``UPLOAD_FOLDER`` specifies the path and name of the file storage folder.  ``PRINTER_NAME`` stores the name of the printer
and should not be altered unless the printer is replaced or renamed.  A list of printer names can be found by running ``lpstat -p``
in terminal.  As of November 2024, the printer is correctly named "Brother_HL_L3280CDW_series_USB".  ``MAX_PAGES`` controls
many pages are allowed at a single time before a print fails.  Finally, ``FILE_SAVE_TIME`` stores how long in seconds files
should be saved to file storage

# Website
I have no prior experience with frontend or web dev.  As such all HTML and CSS present is self-taught and by no means final.
Should the website or layout of the HTML files disgust some future tech director, feel free to rework it to your liking.
If so, do be aware that each file contains a form with a hidden username input with a default value that stores the username
for log purposes.  Should this be changed, be aware that the python code will need to be altered accordingly.