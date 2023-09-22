CIF Print Server
------------------
Creation of a new print server for CIF that eliminates bloat and allows greater maintainability.

Set Up
------------------

After pulling the repository, you can get the requirements in one of two ways:

1. **(Preferred)** If you have [devenv](https://devenv.sh) installed, or are
using [Nix](https://nixos.org), start up the dev shell using the `flake.nix`
file. If you also have [direnv](https://direnv.net) set up, this will happen
automatically.

2. Set up a **Python 3.10.13** venv and install dependencies from `requirements.txt`.

Then, create a `config.toml`. See `config.py` for descriptions of available and
required options.

Running in Development
-------------------

In development, run:

```sh
python3 app.py
```

Deploying
-------------------

*TODO: deploy steps*

To-Do
------------------
Homepage
- [x] Fix side text alignment
- [ ] Link intro paragraph to CIF registration
- [ ] Add more content and details about CIF printing
- [ ] Format content within the grid layout

Print Pages
- [x] Fix side text alignment
- [x] Remove select page range and automatically display page range when print all pages is left unchecked
- [ ] Add drop box for file upload
- [ ] Add document display
- [ ] Add pop-ups for invalid form fill
- [ ] Create redirect page to send users to after printing
- [ ] Fix spacing with form fields
- [ ] Ensure page length fits within the document page length

About
- [ ] Find content for about page or remove altogether

General
- [ ] Swap database type to sqlite
- [ ] Add back in login functionality when complete