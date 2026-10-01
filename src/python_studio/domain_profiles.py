from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paths import DOMAINS_DIR, STUDIO_CONFIG


@dataclass(frozen=True)
class DomainProfile:
    id: str
    name: str
    starter_file: str
    test_file: str
    solution_file: str
    analysis_mode: str
    code_extensions: tuple[str, ...]
    primary_command: tuple[str, ...]
    fallback_command: tuple[str, ...]
    ai_context: str


def load_studio_config() -> dict[str, Any]:
    if not STUDIO_CONFIG.exists():
        return {
            "name": "Learning Studio",
            "tagline": "本地学习训练场",
            "default_domain": "python",
        }
    return json.loads(STUDIO_CONFIG.read_text(encoding="utf-8"))


def update_studio_config(
    *,
    name: str,
    tagline: str,
    default_domain: str,
) -> dict[str, Any]:
    clean_name = name.strip()
    clean_tagline = tagline.strip()
    clean_domain = default_domain.strip()
    if not clean_name:
        raise ValueError("Studio name is required.")
    load_domain_profile(clean_domain)
    payload = {
        "name": clean_name[:80],
        "tagline": clean_tagline[:120],
        "default_domain": clean_domain,
    }
    temporary = STUDIO_CONFIG.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(STUDIO_CONFIG)
    return payload


def load_domain_profile(domain_id: str | None = None) -> DomainProfile:
    studio = load_studio_config()
    resolved_id = domain_id or str(studio.get("default_domain", "python"))
    path = DOMAINS_DIR / f"{resolved_id}.json"
    if not path.exists():
        raise KeyError(f"Unknown domain profile: {resolved_id}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return DomainProfile(
        id=str(payload["id"]),
        name=str(payload["name"]),
        starter_file=str(payload["starter_file"]),
        test_file=str(payload["test_file"]),
        solution_file=str(payload["solution_file"]),
        analysis_mode=str(payload.get("analysis_mode", "generic")),
        code_extensions=tuple(payload.get("code_extensions", [])),
        primary_command=tuple(payload.get("primary_command", [])),
        fallback_command=tuple(payload.get("fallback_command", [])),
        ai_context=str(payload.get("ai_context", "")),
    )


def profile_for_exercise(exercise: dict[str, Any]) -> DomainProfile:
    domain_id = str(exercise.get("domain") or load_studio_config()["default_domain"])
    profile = load_domain_profile(domain_id)
    overrides = dict(profile.__dict__)
    for key in (
        "starter_file",
        "test_file",
        "solution_file",
        "analysis_mode",
    ):
        if exercise.get(key):
            overrides[key] = str(exercise[key])
    if exercise.get("code_extensions"):
        overrides["code_extensions"] = tuple(exercise["code_extensions"])
    if exercise.get("test_command"):
        overrides["primary_command"] = tuple(exercise["test_command"])
        overrides["fallback_command"] = tuple(
            exercise.get("fallback_command") or exercise["test_command"]
        )
    if exercise.get("ai_context"):
        overrides["ai_context"] = str(exercise["ai_context"])
    return DomainProfile(**overrides)


def resolve_command(
    profile: DomainProfile,
    *,
    use_fallback: bool = False,
) -> list[str]:
    command = profile.fallback_command if use_fallback else profile.primary_command
    replacements = {
        "{python}": sys.executable,
        "{test_file}": profile.test_file,
        "{starter_file}": profile.starter_file,
    }
    resolved = []
    for part in command:
        if part in replacements:
            resolved.append(replacements[part])
        else:
            resolved.append(
                part.format(
                    python=sys.executable,
                    test_file=profile.test_file,
                    starter_file=profile.starter_file,
                )
            )
    return resolved
