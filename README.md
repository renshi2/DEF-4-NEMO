# DEF-4-NEMO

Oude DEF opstellingen waarvan opmerkingen zijn gemaakt door NEMO om eventueel te gebruiken als inspiratie of direct over te nemen naar het museum.

[Link for webview](https://renshi2.github.io/DEF-4-NEMO/)

## Data model

This repository now treats Git as the source of truth for a small database:

- `/data/projects.csv`
- `/data/comments.csv`

`comments.project_id` references `projects.id`.

## Build database outputs

Use the sync script to validate the CSV files and generate both:

- `/data/database.sqlite` (local relational database)
- `/docs/database.json` (for online browsing on GitHub Pages)

```bash
python3 scripts/sync_database.py
```

The script accepts both underscore and space-separated headers and supports the existing typo variants (`catagory`, `catagories`).

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

3. Start a local server from repository root:

   ```bash
   python3 -m http.server 8000
   ```

4. Open [`http://localhost:8000/docs/`](http://localhost:8000/docs/).

## Run online on GitHub

Enable **GitHub Pages** for this repository and set source to the `/docs` folder on your default branch.

Whenever CSV data changes, re-run:

```bash
python3 scripts/sync_database.py
```

Then commit the updated CSV/JSON files so the hosted site and local clone remain in sync.
