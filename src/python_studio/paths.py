from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOMAINS_DIR = PROJECT_ROOT / "domains"
STUDIO_CONFIG = PROJECT_ROOT / "studio.json"
SUBJECTS_DIR = PROJECT_ROOT / "subjects"
SUBJECT_REGISTRY = SUBJECTS_DIR / "registry.json"
CURRICULUM_DIR = PROJECT_ROOT / "curriculum"
EXERCISES_DIR = PROJECT_ROOT / "exercises"
PROJECTS_DIR = PROJECT_ROOT / "projects"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
PROGRESS_FILE = PROJECT_ROOT / "progress.json"
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_FILE = DATA_DIR / "study.db"
