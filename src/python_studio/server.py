from __future__ import annotations

import json
import mimetypes
import sqlite3
import webbrowser
import zipfile
from functools import partial
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from .catalog import (
    catalog_payload,
    find_exercise,
    read_exercise_documentation,
)
from .backup import (
    backup_file_path,
    create_learning_backup,
    delete_learning_backup,
    list_learning_backups,
    restore_learning_backup,
)
from .assessment import load_assessment
from .authoring import authored_diagnosis, authored_mentor, tool_registry
from .checker import run_exercise_check
from .companion import (
    CompanionError,
    companion_status,
    generate_and_create_practice,
)
from .config import (
    ai_settings_payload,
    get_deepseek_config,
    test_ai_connection,
    update_ai_settings,
)
from .context_export import (
    build_exercise_context,
    context_to_markdown,
)
from .domain_profiles import load_studio_config, update_studio_config
from .knowledge import knowledge_for_exercise
from .knowledge_graph import refresh_student_skill_state
from .maintenance import (
    cleanup_data,
    maintenance_summary,
    update_generated_exercise,
)
from .materializer import materialize_subject
from .paths import DASHBOARD_DIR
from .progress import load_progress, record_attempt, save_progress, set_last_exercise
from .services.chat_service import (
    chat_payload,
    manage_chat_session,
    new_chat,
    send_chat_message,
    sessions_payload,
)
from .services.assessment_service import submit_assessment
from .services.learning_service import (
    analyze_attempt,
    analyze_failures,
    generate_solution,
    history_payload,
    run_learning_diagnosis,
)
from .store import (
    learning_history_summary,
    latest_analysis,
    get_latest_attempt_for_exercise,
    list_learning_attempts,
    list_mistakes,
    record_learning_attempt,
    skill_summary,
    update_mistake_status,
)
from .subject_compiler import compile_subject, get_subject, list_subjects
from .workspace import (
    get_workspace,
    list_workspaces,
    reset_current_subject,
    set_current_subject,
    workspace_payload,
)
from .workshop import ask_workshop, materialize_node_practice, workshop_payload


class StudioHandler(BaseHTTPRequestHandler):
    server_version = "PythonStudio/0.1"

    def __init__(self, *args: Any, root: Path, **kwargs: Any) -> None:
        self.root = root
        super().__init__(*args, **kwargs)

    def parse_request(self) -> bool:
        success = super().parse_request()
        self._subject_token = None
        mode = str(self.headers.get("X-Studio-Mode") or "").strip().lower()
        self._studio_origin = "workshop" if mode == "workshop" else "course"
        if success:
            subject_id = self.headers.get("X-Subject-Id")
            if subject_id:
                try:
                    self._subject_token = set_current_subject(subject_id)
                except KeyError:
                    self.send_error(HTTPStatus.NOT_FOUND, "Unknown subject.")
                    return False
        return success

    def _origin(self) -> str:
        return getattr(self, "_studio_origin", "course")

    def finish(self) -> None:
        try:
            super().finish()
        finally:
            if getattr(self, "_subject_token", None) is not None:
                reset_current_subject(self._subject_token)
                self._subject_token = None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/api/health":
            self._send_json({"ok": True})
            return
        if parsed.path == "/api/tools":
            self._send_json({"tools": tool_registry()})
            return
        if parsed.path == "/api/catalog":
            self._send_json(
                catalog_payload(
                    load_progress(self._progress_path()),
                    origin=self._origin(),
                )
            )
            return
        if parsed.path == "/api/exercise":
            self._handle_exercise(query)
            return
        if parsed.path == "/api/hint":
            self._handle_hint(query)
            return
        if parsed.path == "/api/learning/history":
            self._handle_history()
            return
        if parsed.path == "/api/companion":
            self._handle_companion()
            return
        if parsed.path == "/api/maintenance":
            self._send_json(maintenance_summary())
            return
        if parsed.path == "/api/context/export":
            self._handle_context_export(query)
            return
        if parsed.path == "/api/chat":
            self._handle_chat_history(query)
            return
        if parsed.path == "/api/chat/sessions":
            self._handle_chat_sessions()
            return
        if parsed.path == "/api/maintenance/backups/download":
            self._handle_backup_download(query)
            return
        if parsed.path == "/api/settings/ai":
            self._send_json(ai_settings_payload())
            return
        if parsed.path == "/api/studio":
            self._send_json(load_studio_config())
            return
        if parsed.path == "/api/subjects":
            self._send_json({"subjects": list_subjects()})
            return
        if parsed.path == "/api/workspaces":
            self._send_json(
                {
                    "workspaces": [
                        workspace_payload(workspace)
                        for workspace in list_workspaces()
                    ]
                }
            )
            return
        if parsed.path == "/api/workshop":
            session_id = self._query_value(query, "session_id")
            try:
                self._send_json(
                    workshop_payload(int(session_id) if session_id else None)
                )
            except (KeyError, ValueError):
                self._send_json(
                    {"error": "Workshop session not found."},
                    HTTPStatus.NOT_FOUND,
                )
            return
        if parsed.path == "/api/subject":
            self._handle_subject(query)
            return
        if parsed.path.startswith("/api/"):
            self._send_json({"error": "Unknown API route."}, HTTPStatus.NOT_FOUND)
            return

        self._serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/api/check":
            self._handle_check(query)
            return
        if parsed.path == "/api/select":
            self._handle_select(query)
            return
        if parsed.path == "/api/companion/analyze":
            self._handle_companion_analysis()
            return
        if parsed.path == "/api/mistake/status":
            self._handle_mistake_status(query)
            return
        if parsed.path == "/api/practice/generate":
            self._handle_practice_generation(query)
            return
        if parsed.path == "/api/learning/analyze-attempt":
            self._handle_attempt_analysis(query)
            return
        if parsed.path == "/api/learning/analyze-failures":
            self._handle_failure_analyses()
            return
        if parsed.path == "/api/learning/generate-solution":
            self._handle_solution_generation(query)
            return
        if parsed.path == "/api/maintenance/cleanup":
            self._handle_cleanup(query)
            return
        if parsed.path == "/api/maintenance/generated":
            self._handle_generated_exercise(query)
            return
        if parsed.path == "/api/chat/message":
            self._handle_chat_message()
            return
        if parsed.path == "/api/chat/new":
            self._handle_new_chat()
            return
        if parsed.path == "/api/chat/session":
            self._handle_chat_session_action()
            return
        if parsed.path == "/api/maintenance/backup":
            self._handle_backup_create()
            return
        if parsed.path == "/api/maintenance/restore":
            self._handle_backup_restore()
            return
        if parsed.path == "/api/maintenance/backup/delete":
            self._handle_backup_delete()
            return
        if parsed.path == "/api/settings/ai":
            self._handle_ai_settings_update()
            return
        if parsed.path == "/api/settings/ai/test":
            self._handle_ai_settings_test()
            return
        if parsed.path == "/api/studio":
            self._handle_studio_update()
            return
        if parsed.path == "/api/subjects/compile":
            self._handle_subject_compile()
            return
        if parsed.path == "/api/subjects/materialize":
            self._handle_subject_materialize()
            return
        if parsed.path == "/api/assessment/check":
            self._handle_assessment_check()
            return
        if parsed.path == "/api/workshop/ask":
            self._handle_workshop_ask()
            return
        if parsed.path == "/api/workshop/practice":
            self._handle_workshop_practice()
            return
        self._send_json({"error": "Unknown API route."}, HTTPStatus.NOT_FOUND)

    def _handle_exercise(self, query: dict[str, list[str]]) -> None:
        exercise_id = self._query_value(query, "id")
        if not exercise_id:
            self._send_json({"error": "Missing exercise id."}, HTTPStatus.BAD_REQUEST)
            return
        try:
            exercise = find_exercise(exercise_id)
        except KeyError as error:
            self._send_json({"error": str(error)}, HTTPStatus.NOT_FOUND)
            return

        progress = load_progress(self._progress_path())
        set_last_exercise(progress, exercise_id)
        save_progress(self._progress_path(), progress)
        payload = dict(exercise)
        payload["readme"] = read_exercise_documentation(exercise)
        payload["knowledge"] = knowledge_for_exercise(exercise)
        payload["assessment"] = load_assessment(exercise)
        payload["mentor"] = authored_mentor(exercise)
        payload["progress"] = progress["attempts"].get(exercise_id, {})
        self._send_json(payload)

    def _handle_hint(self, query: dict[str, list[str]]) -> None:
        exercise_id = self._query_value(query, "id")
        level = int(self._query_value(query, "level") or "1")
        try:
            exercise = find_exercise(exercise_id)
        except KeyError as error:
            self._send_json({"error": str(error)}, HTTPStatus.NOT_FOUND)
            return

        hints = exercise.get("hints", [])
        if not hints:
            self._send_json({"hint": "这道题暂时没有额外提示。"})
            return
        index = min(max(level, 1), len(hints)) - 1
        self._send_json(
            {
                "hint": hints[index],
                "level": index + 1,
                "total": len(hints),
            }
        )

    def _handle_check(self, query: dict[str, list[str]]) -> None:
        exercise_id = self._query_value(query, "id")
        if not exercise_id:
            self._send_json({"error": "Missing exercise id."}, HTTPStatus.BAD_REQUEST)
            return
        try:
            result = run_exercise_check(exercise_id)
        except KeyError as error:
            self._send_json({"error": str(error)}, HTTPStatus.NOT_FOUND)
            return

        progress = load_progress(self._progress_path())
        progress = record_attempt(progress, exercise_id, result)
        save_progress(self._progress_path(), progress)
        exercise = find_exercise(exercise_id)
        record_learning_attempt(result, exercise)
        refresh_student_skill_state()
        result["stats"] = catalog_payload(progress, origin=self._origin())["stats"]
        self._send_json(result)

    def _handle_history(self) -> None:
        self._send_json(history_payload(origin=self._origin()))

    def _handle_companion(self) -> None:
        origin = self._origin()
        self._send_json(
            {
                "status": companion_status(),
                "origin": origin,
                "history": learning_history_summary(origin=origin),
                "skills": skill_summary(origin=origin),
                "analysis": latest_analysis(origin=origin),
                "mistakes": list_mistakes(origin=origin),
                "authored_diagnosis": authored_diagnosis(),
            }
        )

    def _handle_companion_analysis(self) -> None:
        self._send_json(run_learning_diagnosis(origin=self._origin()))

    def _handle_attempt_analysis(self, query: dict[str, list[str]]) -> None:
        raw_id = self._query_value(query, "id")
        try:
            attempt_id = int(raw_id)
        except ValueError:
            self._send_json({"error": "Invalid attempt id."}, HTTPStatus.BAD_REQUEST)
            return
        try:
            result = analyze_attempt(attempt_id)
        except KeyError as error:
            self._send_json({"error": "Attempt not found."}, HTTPStatus.NOT_FOUND)
            return
        except (CompanionError, ValueError, RuntimeError, OSError) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json(result)

    def _handle_failure_analyses(self) -> None:
        self._send_json({"analyzed": analyze_failures(limit=5)})

    def _handle_solution_generation(self, query: dict[str, list[str]]) -> None:
        raw_id = self._query_value(query, "id")
        try:
            attempt_id = int(raw_id)
        except ValueError:
            self._send_json({"error": "Invalid attempt id."}, HTTPStatus.BAD_REQUEST)
            return
        try:
            result = generate_solution(attempt_id)
        except KeyError as error:
            self._send_json({"error": "Attempt not found."}, HTTPStatus.NOT_FOUND)
            return
        except (ValueError, CompanionError) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json({"attempt_id": attempt_id, **result})

    def _handle_mistake_status(self, query: dict[str, list[str]]) -> None:
        raw_id = self._query_value(query, "id")
        status = self._query_value(query, "status")
        try:
            mistake_id = int(raw_id)
            updated = update_mistake_status(mistake_id, status)
        except ValueError as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        if not updated:
            self._send_json({"error": "Mistake not found."}, HTTPStatus.NOT_FOUND)
            return
        self._send_json({"ok": True, "id": mistake_id, "status": status})

    def _handle_practice_generation(self, query: dict[str, list[str]]) -> None:
        knowledge_point = self._query_value(query, "knowledge_point")
        if not knowledge_point:
            self._send_json(
                {"error": "Missing knowledge_point."},
                HTTPStatus.BAD_REQUEST,
            )
            return
        source_exercise_id = self._query_value(query, "source_exercise_id") or None
        source_task = self._query_value(query, "source_task") or None
        config = get_deepseek_config()
        attempts = list_learning_attempts(limit=config.history_limit)
        try:
            created = generate_and_create_practice(
                attempts,
                knowledge_point=knowledge_point,
                source_exercise_id=source_exercise_id,
                source_task=source_task,
                config=config,
                origin=self._origin(),
                stage="workshop" if self._origin() == "workshop" else None,
                scope=(
                    "workshop"
                    if self._origin() == "workshop"
                    else "tutoring"
                ),
            )
        except (ValueError, OSError) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json(created, HTTPStatus.CREATED)

    def _handle_cleanup(self, query: dict[str, list[str]]) -> None:
        scope = self._query_value(query, "scope")
        try:
            result = cleanup_data(scope)
        except ValueError as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json(result)

    def _handle_generated_exercise(self, query: dict[str, list[str]]) -> None:
        exercise_id = self._query_value(query, "id")
        action = self._query_value(query, "action")
        try:
            result = update_generated_exercise(exercise_id, action)
        except KeyError as error:
            self._send_json({"error": str(error)}, HTTPStatus.NOT_FOUND)
            return
        except ValueError as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json(result)

    def _handle_backup_create(self) -> None:
        try:
            backup = create_learning_backup("manual")
        except (OSError, sqlite3.Error) as error:
            self._send_json({"error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self._send_json({"backup": backup}, HTTPStatus.CREATED)

    def _handle_backup_restore(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        name = str(body.get("name", "")).strip()
        try:
            result = restore_learning_backup(name)
        except KeyError as error:
            self._send_json({"error": str(error)}, HTTPStatus.NOT_FOUND)
            return
        except (ValueError, OSError, zipfile.BadZipFile) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json(result)

    def _handle_backup_delete(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        name = str(body.get("name", "")).strip()
        try:
            delete_learning_backup(name)
        except KeyError as error:
            self._send_json({"error": str(error)}, HTTPStatus.NOT_FOUND)
            return
        except ValueError as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json({"deleted": name})

    def _handle_ai_settings_update(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        try:
            payload = update_ai_settings(
                api_key=body.get("api_key"),
                base_url=str(body.get("base_url", "")),
                model=str(body.get("model", "")),
                timeout_seconds=int(body.get("timeout_seconds", 60)),
                history_limit=int(body.get("history_limit", 40)),
                clear_api_key=bool(body.get("clear_api_key", False)),
            )
        except (TypeError, ValueError) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json({"ok": True, "settings": payload})

    def _handle_ai_settings_test(self) -> None:
        try:
            result = test_ai_connection()
        except ValueError as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json(result)

    def _handle_studio_update(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        try:
            payload = update_studio_config(
                name=str(body.get("name", "")),
                tagline=str(body.get("tagline", "")),
                default_domain=str(body.get("default_domain", "")),
            )
        except (KeyError, ValueError) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json({"ok": True, "studio": payload})

    def _handle_subject(self, query: dict[str, list[str]]) -> None:
        subject_id = self._query_value(query, "id")
        if not subject_id:
            self._send_json({"error": "Invalid subject id."}, HTTPStatus.BAD_REQUEST)
            return
        subject = get_subject(subject_id)
        if subject is None:
            self._send_json({"error": "Subject not found."}, HTTPStatus.NOT_FOUND)
            return
        self._send_json(subject)

    def _handle_subject_compile(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        try:
            result = compile_subject(
                subject=str(body.get("subject", "")),
                material=str(body.get("material", "")),
                requested_mode=str(body.get("mode", "auto")),
            )
            if bool(body.get("materialize", True)):
                result["materialization"] = materialize_subject(str(result["id"]))
        except (TypeError, ValueError, RuntimeError) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json(result, HTTPStatus.CREATED)

    def _handle_subject_materialize(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        subject_id = str(body.get("id", "")).strip()
        if not subject_id:
            self._send_json({"error": "Subject id is required."}, HTTPStatus.BAD_REQUEST)
            return
        try:
            result = materialize_subject(subject_id)
        except KeyError as error:
            self._send_json({"error": str(error)}, HTTPStatus.NOT_FOUND)
            return
        except (ValueError, OSError, RuntimeError) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json(result)

    def _handle_assessment_check(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        exercise_id = str(body.get("exercise_id", ""))
        answers = body.get("answers")
        if not exercise_id or not isinstance(answers, dict):
            self._send_json(
                {"error": "exercise_id and answers are required."},
                HTTPStatus.BAD_REQUEST,
            )
            return
        try:
            result = submit_assessment(
                exercise_id,
                answers,
                origin=self._origin(),
            )
        except KeyError as error:
            self._send_json({"error": str(error)}, HTTPStatus.NOT_FOUND)
            return
        except (ValueError, OSError) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json(result)

    def _handle_workshop_ask(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        try:
            result = ask_workshop(
                question=str(body.get("question", "")),
                session_id=(
                    int(body["session_id"])
                    if body.get("session_id") is not None
                    else None
                ),
                selected_node_id=(
                    str(body["selected_node_id"])
                    if body.get("selected_node_id")
                    else None
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json(result)

    def _handle_workshop_practice(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        node_id = str(body.get("node_id", "")).strip()
        if not node_id:
            self._send_json({"error": "node_id is required."}, HTTPStatus.BAD_REQUEST)
            return
        try:
            result = materialize_node_practice(node_id)
        except KeyError as error:
            self._send_json({"error": str(error)}, HTTPStatus.NOT_FOUND)
            return
        except (ValueError, OSError, RuntimeError) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json(result, HTTPStatus.CREATED)

    def _handle_backup_download(self, query: dict[str, list[str]]) -> None:
        name = self._query_value(query, "name")
        if not name:
            self._send_json({"error": "Missing backup name."}, HTTPStatus.BAD_REQUEST)
            return
        available = {item["name"]: item for item in list_learning_backups()}
        if name not in available:
            self._send_json({"error": "Backup not found."}, HTTPStatus.NOT_FOUND)
            return
        try:
            path = backup_file_path(name)
        except (KeyError, ValueError):
            self._send_json({"error": "Backup not found."}, HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/zip")
        self.send_header(
            "Content-Disposition",
            f'attachment; filename="{name}"',
        )
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_context_export(self, query: dict[str, list[str]]) -> None:
        exercise_id = self._query_value(query, "exercise_id")
        raw_attempt_id = self._query_value(query, "attempt_id")
        attempt = None
        if raw_attempt_id:
            try:
                attempt = get_learning_attempt(int(raw_attempt_id))
            except ValueError:
                attempt = None
            if attempt:
                exercise_id = str(attempt["exercise_id"])
        if not exercise_id:
            self._send_json(
                {"error": "Missing exercise_id or attempt_id."},
                HTTPStatus.BAD_REQUEST,
            )
            return
        try:
            exercise = find_exercise(exercise_id, include_inactive=True)
        except KeyError:
            self._send_json({"error": "Exercise not found."}, HTTPStatus.NOT_FOUND)
            return
        if attempt is None:
            attempt = get_latest_attempt_for_exercise(exercise_id)
        context = build_exercise_context(exercise, attempt)
        self._send_json(
            {
                "context": context,
                "markdown": context_to_markdown(context),
            }
        )

    def _handle_chat_history(self, query: dict[str, list[str]]) -> None:
        raw_session_id = self._query_value(query, "session_id")
        try:
            session_id = int(raw_session_id) if raw_session_id else None
        except ValueError:
            session_id = None
        self._send_json(chat_payload(session_id))

    def _handle_chat_sessions(self) -> None:
        self._send_json(sessions_payload())

    def _handle_new_chat(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        title = str(body.get("title") or "新的伴学对话")
        context = body.get("context")
        if not isinstance(context, dict):
            context = None
        self._send_json(new_chat(title, context), HTTPStatus.CREATED)

    def _handle_chat_message(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        message = str(body.get("message", "")).strip()
        if not message:
            self._send_json({"error": "Message is required."}, HTTPStatus.BAD_REQUEST)
            return
        raw_session_id = body.get("session_id")
        try:
            session_id = int(raw_session_id)
        except (TypeError, ValueError):
            session_id = None
        context = body.get("context")
        try:
            result = send_chat_message(
                session_id,
                message,
                context,
                origin=self._origin(),
            )
        except CompanionError as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_GATEWAY)
            return
        self._send_json(result)

    def _handle_chat_session_action(self) -> None:
        body = self._read_json_body()
        if body is None:
            return
        action = str(body.get("action", ""))
        try:
            session_id = int(body.get("session_id"))
        except (TypeError, ValueError):
            self._send_json({"error": "Invalid session_id."}, HTTPStatus.BAD_REQUEST)
            return
        try:
            updated = manage_chat_session(
                session_id,
                action,
                title=str(body.get("title", "")).strip() or None,
                context=body.get("context"),
                marker=str(body.get("marker", "")).strip() or None,
            )
        except ValueError as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        if not updated:
            self._send_json({"error": "Chat session not found."}, HTTPStatus.NOT_FOUND)
            return
        self._send_json({"ok": True, "action": action, "session_id": session_id})

    def _read_json_body(self) -> dict[str, Any] | None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        if content_length > 1_000_000:
            self._send_json({"error": "Request body is too large."}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return None
        raw_body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            body = json.loads(raw_body.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json({"error": "Invalid JSON body."}, HTTPStatus.BAD_REQUEST)
            return None
        if not isinstance(body, dict):
            self._send_json({"error": "JSON body must be an object."}, HTTPStatus.BAD_REQUEST)
            return None
        return body

    def _handle_select(self, query: dict[str, list[str]]) -> None:
        exercise_id = self._query_value(query, "id")
        if not exercise_id:
            self._send_json({"error": "Missing exercise id."}, HTTPStatus.BAD_REQUEST)
            return
        try:
            find_exercise(exercise_id)
        except KeyError as error:
            self._send_json({"error": str(error)}, HTTPStatus.NOT_FOUND)
            return
        progress = load_progress(self._progress_path())
        set_last_exercise(progress, exercise_id)
        save_progress(self._progress_path(), progress)
        self._send_json({"ok": True, "selected": exercise_id})

    def _serve_static(self, request_path: str) -> None:
        relative = unquote(request_path).lstrip("/") or "index.html"
        candidate = (DASHBOARD_DIR / relative).resolve()
        dashboard_root = DASHBOARD_DIR.resolve()

        if not candidate.is_relative_to(dashboard_root):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if candidate.is_dir():
            candidate = candidate / "index.html"
        if not candidate.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        body = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    @staticmethod
    def _progress_path() -> Path:
        return get_workspace().progress_file

    @staticmethod
    def _query_value(query: dict[str, list[str]], key: str) -> str:
        values = query.get(key, [])
        return values[0] if values else ""

    def log_message(self, message_format: str, *args: Any) -> None:
        print(f"[studio] {message_format % args}")


def serve(root: Path, port: int, open_browser: bool = False) -> None:
    handler = partial(StudioHandler, root=root)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}"
    print(f"Python Studio: {url}")
    print("Press Ctrl+C to stop.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Python Studio.")
    finally:
        server.server_close()
