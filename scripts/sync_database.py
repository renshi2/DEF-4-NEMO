#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import plistlib
import re
import shutil
import sqlite3
from pathlib import Path

PROJECT_COLUMN_ALIASES = {
    "id": ("id",),
    "title": ("title",),
    "tags": ("tags",),
    "description": ("description",),
    "year": ("year",),
    "category": ("category", "catagory"),
    "rating": ("rating",),
    "curator": ("curator",),
    "project_link": ("project_link", "project link"),
    "created_at": ("created_at", "created at"),
    "updated_at": ("updated_at", "updated at"),
    "student_name": ("student_name", "student name"),
    "image_urls": ("image_urls", "image urls"),
    "video_urls": ("video_urls", "video urls"),
    "categories": ("categories", "catagories"),
}

COMMENT_COLUMN_ALIASES = {
    "id": ("id",),
    "project_id": ("project_id", "project id"),
    "comment_text": ("comment_text", "comment text"),
    "comment_type": ("comment_type", "comment type"),
    "created_at": ("created_at", "created at"),
    "updated_at": ("updated_at", "updated at"),
    "author": ("author",),
    "category": ("category",),
    "text": ("text",),
}


def _is_ignored_file(path: Path) -> bool:
    return path.name.startswith(".") or path.name.startswith("~$")


def _extract_external_url(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        content = path.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"https?://\S+", content)
        return match.group(0).strip() if match else ""

    if suffix == ".webloc":
        try:
            payload = plistlib.loads(path.read_bytes())
        except Exception:
            return ""
        url = payload.get("URL")
        return str(url).strip() if isinstance(url, str) else ""

    return ""


def _collect_project_files(folder: Path, json_path: Path, include_external_links: bool) -> dict[str, list[dict[str, str]]]:
    if not folder.exists():
        return {}

    files_by_project: dict[str, list[dict[str, str]]] = {}
    json_parent = json_path.parent

    for project_folder in sorted(path for path in folder.iterdir() if path.is_dir()):
        items: list[dict[str, str]] = []
        for file_path in sorted(path for path in project_folder.iterdir() if path.is_file() and not _is_ignored_file(path)):
            relative_path = os.path.relpath(file_path, start=json_parent).replace(os.sep, "/")
            item = {
                "name": file_path.name,
                "path": relative_path,
            }
            if include_external_links:
                external_url = _extract_external_url(file_path)
                if external_url:
                    item["external_url"] = external_url
            items.append(item)

        if items:
            files_by_project[project_folder.name] = items

    return files_by_project


def _publish_docs_media(
    files_by_project: dict[str, list[dict[str, str]]],
    json_parent: Path,
    media_subfolder: str,
) -> dict[str, list[dict[str, str]]]:
    published_root = json_parent / "media" / media_subfolder
    if published_root.exists():
        shutil.rmtree(published_root)

    published: dict[str, list[dict[str, str]]] = {}
    for project_id, files in files_by_project.items():
        project_items: list[dict[str, str]] = []
        for file in files:
            source_path = (json_parent / file["path"]).resolve()
            if not source_path.exists():
                continue

            relative_target = Path("media") / media_subfolder / project_id / file["name"]
            target_path = json_parent / relative_target
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)

            project_items.append(
                {
                    **file,
                    "path": f"./{relative_target.as_posix()}",
                }
            )

        if project_items:
            published[project_id] = project_items

    return published


def _resolve_aliases(rows: list[dict[str, str]], aliases: dict[str, tuple[str, ...]]) -> list[dict[str, str]]:
    if not rows:
        return []

    keys = set(rows[0].keys())
    mapping: dict[str, str] = {}
    for canonical_name, options in aliases.items():
        match = next((candidate for candidate in options if candidate in keys), None)
        if match is None:
            raise ValueError(f"Missing required column: {canonical_name} (expected one of {options})")
        mapping[canonical_name] = match

    return [{canonical_name: row.get(source, "") for canonical_name, source in mapping.items()} for row in rows]


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        return [dict(row) for row in reader]


def ensure_numeric_constraints(projects: list[dict[str, str]], comments: list[dict[str, str]]) -> None:
    project_ids: set[int] = set()

    for project in projects:
        try:
            project_id = int(project["id"])
        except ValueError as error:
            raise ValueError(f"Project id must be an integer: {project['id']}") from error

        if project_id in project_ids:
            raise ValueError(f"Duplicate project id: {project_id}")

        rating = int(project["rating"])
        if rating < 0 or rating > 5:
            raise ValueError(f"Project rating must be between 0 and 5 for project id {project_id}")

        project_ids.add(project_id)

    comment_ids: set[int] = set()
    for comment in comments:
        try:
            comment_id = int(comment["id"])
            project_id = int(comment["project_id"])
        except ValueError as error:
            raise ValueError(f"Comment id and project_id must be integers: {comment}") from error

        if comment_id in comment_ids:
            raise ValueError(f"Duplicate comment id: {comment_id}")
        comment_ids.add(comment_id)

        if project_id not in project_ids:
            raise ValueError(f"Comment {comment_id} references unknown project_id {project_id}")

        author = comment["author"].strip()
        if not author:
            raise ValueError(f"Comment author must not be empty for comment id {comment_id}")


def write_sqlite(sqlite_path: Path, projects: list[dict[str, str]], comments: list[dict[str, str]]) -> None:
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_path.exists():
        sqlite_path.unlink()

    connection = sqlite3.connect(sqlite_path)
    try:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                tags TEXT NOT NULL,
                description TEXT NOT NULL,
                year TEXT NOT NULL,
                category TEXT NOT NULL,
                rating INTEGER NOT NULL,
                curator TEXT NOT NULL,
                project_link TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                student_name TEXT NOT NULL,
                image_urls TEXT NOT NULL,
                video_urls TEXT NOT NULL,
                categories TEXT NOT NULL
            );

            CREATE TABLE comments (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL,
                comment_text TEXT NOT NULL,
                comment_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                author TEXT NOT NULL,
                category TEXT NOT NULL,
                text TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );
            """
        )

        connection.executemany(
            """
            INSERT INTO projects (
                id, title, tags, description, year, category, rating, curator,
                project_link, created_at, updated_at, student_name, image_urls,
                video_urls, categories
            ) VALUES (
                :id, :title, :tags, :description, :year, :category, :rating, :curator,
                :project_link, :created_at, :updated_at, :student_name, :image_urls,
                :video_urls, :categories
            )
            """,
            projects,
        )

        connection.executemany(
            """
            INSERT INTO comments (
                id, project_id, comment_text, comment_type, created_at, updated_at,
                author, category, text
            ) VALUES (
                :id, :project_id, :comment_text, :comment_type, :created_at, :updated_at,
                :author, :category, :text
            )
            """,
            comments,
        )

        connection.commit()
    finally:
        connection.close()


def write_json(json_path: Path, projects: list[dict[str, str]], comments: list[dict[str, str]], data_root: Path) -> None:
    comments_by_project: dict[str, list[dict[str, str]]] = {}
    for comment in comments:
        comments_by_project.setdefault(comment["project_id"], []).append(comment)

    photos_by_project = _collect_project_files(data_root / "photos", json_path, include_external_links=False)
    photos_by_project = _publish_docs_media(photos_by_project, json_path.parent, "photos")
    videos_by_project = _collect_project_files(data_root / "videos", json_path, include_external_links=True)
    instructables_by_project = _collect_project_files(data_root / "instructables", json_path, include_external_links=False)

    payload = {
        "projects": [
            {
                **project,
                "comments": comments_by_project.get(project["id"], []),
                "photo_files": photos_by_project.get(project["id"], []),
                "video_files": videos_by_project.get(project["id"], []),
                "instructable_files": instructables_by_project.get(project["id"], []),
            }
            for project in projects
        ]
    }

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sync(projects_path: Path, comments_path: Path, sqlite_path: Path, json_path: Path) -> None:
    raw_projects = load_csv(projects_path)
    raw_comments = load_csv(comments_path)

    projects = _resolve_aliases(raw_projects, PROJECT_COLUMN_ALIASES)
    comments = _resolve_aliases(raw_comments, COMMENT_COLUMN_ALIASES)

    ensure_numeric_constraints(projects, comments)
    write_sqlite(sqlite_path, projects, comments)
    write_json(json_path, projects, comments, data_root=projects_path.parent)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync project/comment CSV files into SQLite and JSON outputs")
    parser.add_argument("--projects", type=Path, default=Path("data/projects.csv"), help="Path to projects CSV")
    parser.add_argument("--comments", type=Path, default=Path("data/comments.csv"), help="Path to comments CSV")
    parser.add_argument("--sqlite", type=Path, default=Path("data/database.sqlite"), help="SQLite output path")
    parser.add_argument("--json", type=Path, default=Path("docs/database.json"), help="JSON output path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sync(args.projects, args.comments, args.sqlite, args.json)


if __name__ == "__main__":
    main()
