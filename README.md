# DEF-4-NEMO

Oude DEF-opstellingen waarvan opmerkingen zijn gemaakt door NEMO om eventueel te gebruiken als inspiratie of direct over te nemen naar het museum.

[Link for webview](https://renshi2.github.io/DEF-4-NEMO/)

## Data model

This repository now treats Git as the source of truth for a small database:

- `/data/projects.csv`
- `/data/comments.csv`
- `/data/photos/<project_id>/*`
- `/data/videos/<project_id>/*`
- `/data/instructables/<project_id>/*`

`comments.project_id` references `projects.id`.

## Build database outputs

Use the sync script to validate the CSV files and generate both:

- `/data/database.sqlite` (local relational database)
- `/docs/database.json` (for online browsing on GitHub Pages)

```bash
python3 scripts/sync_database.py
```

The script accepts both underscore- and space-separated headers and supports the existing typo variants (`catagory`, `catagories`).

## Run locally
### Run website using the designated file
1. Open the terminal in the folder, or navigate to the folder within the terminal using ```cd```.
2. Generate and open the website:

   ```bash
   python3 open_website.py
   ```
### Run website manually
1. Open the terminal in the folder, or navigate to the folder within the terminal using ```cd```.
2. Generate outputs:

   ```bash
   python3 scripts/sync_database.py
   ```

3. Start a local server from the repository root:

   ```bash
   python3 -m http.server 8000
   ```

4. Open [`http://localhost:8000/docs/`](http://localhost:8000/docs/).

## Run online on GitHub

Enable **GitHub Pages** for this repository and set the source to the `/docs` folder on your default branch.

Whenever CSV data changes, re-run:

```bash
python3 scripts/sync_database.py
```

Then commit the updated CSV/JSON files so the hosted site and local clone remain in sync.

The sync step also indexes local media and instructable files by project ID so they can be shown (and instructables downloaded directly) in the website view.

## New entries

To create new projects, first gather the information and fill it into the following Google Form: 

[New Project Form](https://forms.gle/k57tVGZ92YpsKQ9e8)

Or add new comments to an existing project via the following Google Form:

[New Comment Form](https://forms.gle/mFP6x3fdCo2HJxMq8)

These will, using Google Apps Script, create pull requests on GitHub. (If  for some reason it doesn't show up, go to the Google Form and go to the Apps Script (via the 3-dot drop-down menu). Here, go to executions to see any error message for an attempt with the failed status.)

Then, to update the website with the new projects and/or comments, do the following:

- As administrator, open the 'Pull requests'
- Look to see if all the contributions are wanted (to prevent third-party spam additions)
- If everything is ok, accept and merge the pull request
- A few moments later (normally within a minute), a new pull request will appear after reloading, called 'Update generated database'
- Accept and merge this pull request
- The website (the GitHub Pages page) will update. This usually takes between 1 and 5 minutes
