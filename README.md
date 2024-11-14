CIF Print Server
------------------
Creation of a new print server for CIF that eliminates bloat and allows greater maintainability (again). Updated 2024.

# Quick Start
- install Python >= 3.8
- **(Recommended)** Create a virtual environment with `python3 -m venv .venv` and activate it with `source .venv/bin/activate`
- run `python3 -m pip install -r requirements.txt`
- copy `config.example.cfg` to `config.cfg` and adjust the configuration
- run `python3 main.py`

# Command Line Arguments
```
usage: app.py [-h] [--config CONFIG]

Print server for remotely printing to CIF lab printer

options:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to print server config file.
```

# Operation
Print data is retrieved from print.cif.rochester.edu hosted by the server.  After ensuring files are nonnull and all pdfs,
a copy of each file uploaded is saved to the path specified by ``file_storage_path`` in the config, prefixed by the time and date of
attempted print.  An entry to the log, located at ``log_path`` is also created containing the date, time, user, file, and relevant page info.
Note a print need not be successful to have a log entry.  While most syntax errors such as "No file attached" and "Maximum page limit exceeded"
will not log the attempts, errors from the lpr command are thrown before logging and thus are logged and the files saved.
All such failed print attempts are denoted with "PRINT FAILED" in the log.  Also note that file storage is only updated
when a print is attempted and not at regular intervals.  This means that the files in storage represent all attempted print
files within a certain time of the latest attempted print, not necessarily the current date.

After any attempted print without exception, file storage is updated and all files older than a certain threshold are deleted.
This threshold is specified by the ``file_storage_time`` parameter in the config.