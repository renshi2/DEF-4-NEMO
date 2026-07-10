import tempfile
import unittest
from pathlib import Path

from scripts.sync_database import sync


class SyncDatabaseTests(unittest.TestCase):
    def test_sync_supports_spelling_variants_and_outputs_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            projects_csv = base / "projects.csv"
            comments_csv = base / "comments.csv"
            sqlite_path = base / "database.sqlite"
            json_path = base / "database.json"

            projects_csv.write_text(
                "\n".join(
                    [
                        "id,title,tags,description,year,catagory,rating,curator,project link,created at,updated at,student name,image urls,video urls,catagories",
                        "1,Project A,[],Example,2024,,4,Curator X,https://example.com,,2024-01-01T10:00:00Z,,[],[],[]",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            comments_csv.write_text(
                "\n".join(
                    [
                        "id,project id,comment text,comment type,created at,updated at,author,category,text",
                        "10,1,Nice project,general,2024-01-01T11:00:00Z,2024-01-01T11:00:00Z,3,,",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            sync(projects_csv, comments_csv, sqlite_path, json_path)

            payload = json_path.read_text(encoding="utf-8")
            self.assertIn('"id": "1"', payload)
            self.assertIn('"project_id": "1"', payload)

    def test_sync_rejects_missing_project_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            projects_csv = base / "projects.csv"
            comments_csv = base / "comments.csv"

            projects_csv.write_text(
                "id,title,tags,description,year,category,rating,curator,project_link,created_at,updated_at,student_name,image_urls,video_urls,categories\n"
                "1,Project A,[],Example,2024,,4,Curator X,https://example.com,,2024-01-01T10:00:00Z,,[],[],[]\n",
                encoding="utf-8",
            )

            comments_csv.write_text(
                "id,project_id,comment_text,comment_type,created_at,updated_at,author,category,text\n"
                "10,99,Nice project,general,2024-01-01T11:00:00Z,2024-01-01T11:00:00Z,3,,\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "unknown project_id"):
                sync(projects_csv, comments_csv, base / "database.sqlite", base / "database.json")


if __name__ == "__main__":
    unittest.main()
