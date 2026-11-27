from pathlib import Path
import json
import os
import sqlite3
from datetime import datetime, timezone
from groq import Groq

DB_PATH = Path(__file__).resolve().parent.parent / "wingstack.db"


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_kill_switch_tables() -> None:
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kill_switch_pod_state (
                partnership_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                streak_days INTEGER NOT NULL DEFAULT 0,
                kill_switch_active INTEGER NOT NULL DEFAULT 0,
                last_verdict TEXT NOT NULL DEFAULT 'PENDING',
                last_reason TEXT NOT NULL DEFAULT '',
                last_pod_alert TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kill_switch_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partnership_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                verdict TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                reason TEXT NOT NULL,
                pod_alert TEXT NOT NULL,
                streak_after INTEGER NOT NULL,
                kill_switch_active INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _fallback_judge(daily_task: str, proof_text: str, streak_broken: bool) -> dict:
    cleaned_proof = (proof_text or "").strip()
    lowered = cleaned_proof.lower()
    vague_markers = [
        "done",
        "completed",
        "did it",
        "trust me",
        "finished",
        "na",
        "none",
        "fake",
        "lorem ipsum",
    ]
    has_concrete_signal = any(
        token in lowered
        for token in [
            "http://",
            "https://",
            "github.com",
            "commit",
            "pr ",
            "pull request",
            "endpoint",
            "test",
            "screenshot",
            "deployed",
            "api",
            "db",
            "sql",
            "component",
            "bug",
        ]
    )

    if streak_broken:
        return {
            "is_genuine": False,
            "verdict": "STREAK_BROKEN",
            "confidence_score": 0.99,
            "reason": f"Streak deadline missed for daily task: '{daily_task}'. Kill-switch enforcement engaged.",
            "pod_alert": "KILL-SWITCH ALERT: Streak broken! Pod accountability penalty active—daily streak reset and warning broadcast to pod.",
        }

    if len(cleaned_proof) < 15 or (lowered in vague_markers and not has_concrete_signal):
        return {
            "is_genuine": False,
            "verdict": "FAKE",
            "confidence_score": 0.91,
            "reason": "Submitted proof lacks verifiable technical evidence, concrete deliverables, or clear completion details for the assigned task.",
            "pod_alert": "KILL-SWITCH TRIGGERED: Low-effort/unverified proof flagged by Agent A-5! Streak frozen/reset and pod alert dispatched.",
        }

    return {
        "is_genuine": True,
        "verdict": "GENUINE",
        "confidence_score": 0.92 if has_concrete_signal else 0.82,
        "reason": "Proof provides concrete completion details aligned with the daily sprint task.",
        "pod_alert": "POD UPDATE: Daily proof verified genuine by Agent A-5. Streak incremented.",
    }


def evaluate_proof_with_agent_a5(
    partnership_id: str,
    user_id: str,
    daily_task: str,
    proof_text: str,
    streak_broken: bool = False,
) -> dict:
    init_kill_switch_tables()
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM kill_switch_pod_state WHERE partnership_id = ?",
            (partnership_id,),
        ).fetchone()
        current_streak = int(row["streak_days"]) if row else 0

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    judgment = None

    if api_key and not streak_broken:
        try:
            client = Groq(api_key=api_key)
            prompt = (
                "You are Agent A-5, a strict AI Judge for a War Room accountability sprint.\n"
                "Evaluate whether the user's proof genuinely demonstrates completion of the daily task.\n"
                "Reject vague claims ('done', 'did it', empty/generic filler) or mismatched/fake claims.\n"
                "Respond ONLY with valid JSON matching this schema:\n"
                '{"is_genuine": boolean, "verdict": "GENUINE" | "FAKE", '
                '"confidence_score": number between 0.0 and 1.0, '
                '"reason": "concise strict judge explanation", '
                '"pod_alert": "concise alert message for the accountability pod"}\n\n'
                f"Daily Task: {daily_task}\n"
                f"Submitted Proof: {proof_text}\n"
                f"Current Streak Days: {current_streak}"
            )
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are Agent A-5, an uncompromising technical proof auditor."},
                    {"role": "user", "content": prompt},
                ],
            )
            raw_content = completion.choices[0].message.content or "{}"
            parsed = json.loads(raw_content)
            is_genuine = bool(parsed.get("is_genuine", False))
            verdict = "GENUINE" if is_genuine else "FAKE"
            confidence = float(parsed.get("confidence_score", 0.85))
            confidence = max(0.0, min(1.0, confidence))
            reason = str(parsed.get("reason") or "").strip() or _fallback_judge(daily_task, proof_text, False)["reason"]
            pod_alert = str(parsed.get("pod_alert") or "").strip() or _fallback_judge(daily_task, proof_text, False)["pod_alert"]
            judgment = {
                "is_genuine": is_genuine,
                "verdict": verdict,
                "confidence_score": confidence,
                "reason": reason,
                "pod_alert": pod_alert,
            }
        except Exception:
            judgment = _fallback_judge(daily_task, proof_text, streak_broken)
    else:
        judgment = _fallback_judge(daily_task, proof_text, streak_broken)

    is_genuine = judgment["is_genuine"]
    verdict = judgment["verdict"]

    if is_genuine:
        next_streak = current_streak + 1
        kill_switch_active = 0
        event_type = "PROOF_VERIFIED"
    else:
        next_streak = 0
        kill_switch_active = 1
        event_type = "STREAK_BROKEN_KILL_SWITCH" if streak_broken else "FAKE_PROOF_KILL_SWITCH"

    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO kill_switch_pod_state (
                partnership_id, user_id, streak_days, kill_switch_active,
                last_verdict, last_reason, last_pod_alert, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(partnership_id) DO UPDATE SET
                user_id = excluded.user_id,
                streak_days = excluded.streak_days,
                kill_switch_active = excluded.kill_switch_active,
                last_verdict = excluded.last_verdict,
                last_reason = excluded.last_reason,
                last_pod_alert = excluded.last_pod_alert,
                updated_at = excluded.updated_at
            """,
            (
                partnership_id,
                user_id,
                next_streak,
                kill_switch_active,
                verdict,
                judgment["reason"],
                judgment["pod_alert"],
                now_iso,
            ),
        )
        conn.execute(
            """
            INSERT INTO kill_switch_audit_log (
                partnership_id, user_id, event_type, verdict, confidence_score,
                reason, pod_alert, streak_after, kill_switch_active, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                partnership_id,
                user_id,
                event_type,
                verdict,
                judgment["confidence_score"],
                judgment["reason"],
                judgment["pod_alert"],
                next_streak,
                kill_switch_active,
                now_iso,
            ),
        )
        conn.commit()

    return get_kill_switch_status(partnership_id)


def get_kill_switch_status(partnership_id: str) -> dict:
    init_kill_switch_tables()
    with get_db_connection() as conn:
        state_row = conn.execute(
            "SELECT * FROM kill_switch_pod_state WHERE partnership_id = ?",
            (partnership_id,),
        ).fetchone()
        logs = conn.execute(
            """
            SELECT id, partnership_id, user_id, event_type, verdict, confidence_score,
                   reason, pod_alert, streak_after, kill_switch_active, created_at
            FROM kill_switch_audit_log
            WHERE partnership_id = ?
            ORDER BY id DESC
            LIMIT 15
            """,
            (partnership_id,),
        ).fetchall()

    if not state_row:
        return {
            "partnership_id": partnership_id,
            "user_id": "member-1",
            "streak_days": 0,
            "kill_switch_active": False,
            "last_verdict": "PENDING",
            "last_reason": "No proof evaluated yet by Agent A-5.",
            "last_pod_alert": "Pod standing by for daily proof submission.",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "audit_logs": [],
        }

    return {
        "partnership_id": state_row["partnership_id"],
        "user_id": state_row["user_id"],
        "streak_days": int(state_row["streak_days"]),
        "kill_switch_active": bool(state_row["kill_switch_active"]),
        "last_verdict": state_row["last_verdict"],
        "last_reason": state_row["last_reason"],
        "last_pod_alert": state_row["last_pod_alert"],
        "updated_at": state_row["updated_at"],
        "audit_logs": [dict(r) for r in logs],
    }
