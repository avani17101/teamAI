"""
Memory Store - SQLite for structured data + Chroma for semantic vector search.
"""
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import chromadb
from chromadb.utils import embedding_functions

from ..config import DB_PATH, CHROMA_PATH
from ..models.schemas import Meeting, Task, Decision, Risk, ExtractionResult


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _get_chroma():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    # Use default embedding (sentence-transformers/all-MiniLM-L6-v2)
    ef = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name="department_memory",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def init_db():
    """Initialize SQLite tables."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)

    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            transcript TEXT NOT NULL,
            summary TEXT,
            department TEXT DEFAULT 'engineering',
            created_at TEXT NOT NULL
        );
        -- Add department column to existing DBs (safe to run multiple times)
        PRAGMA journal_mode=WAL;

        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            owner TEXT NOT NULL,
            deadline TEXT,
            status TEXT DEFAULT 'pending',
            meeting_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        );

        CREATE TABLE IF NOT EXISTS decisions (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            meeting_id TEXT NOT NULL,
            FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        );

        CREATE TABLE IF NOT EXISTS risks (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            severity TEXT NOT NULL,
            meeting_id TEXT NOT NULL,
            resolved INTEGER DEFAULT 0,
            FOREIGN KEY (meeting_id) REFERENCES meetings(id)
        );
    """)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS team_members (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT DEFAULT '',
            role_details TEXT DEFAULT '',
            responsibilities TEXT DEFAULT '',
            department TEXT DEFAULT '',
            email TEXT DEFAULT '',
            telegram_handle TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS org_context (
            department TEXT PRIMARY KEY,
            mission TEXT DEFAULT '',
            notion_database_id TEXT DEFAULT '',
            notion_page_id TEXT DEFAULT '',
            updated_at TEXT NOT NULL
        );
    """)
    # Migrate existing DB: add new columns safely
    for migration in [
        "ALTER TABLE meetings ADD COLUMN department TEXT DEFAULT 'engineering'",
        "ALTER TABLE tasks ADD COLUMN notion_url TEXT",
        "ALTER TABLE tasks ADD COLUMN notion_page_id TEXT",
        "ALTER TABLE org_context ADD COLUMN notion_database_id TEXT DEFAULT ''",
        "ALTER TABLE org_context ADD COLUMN notion_page_id TEXT DEFAULT ''",
    ]:
        try:
            conn.execute(migration)
            conn.commit()
        except Exception:
            pass  # Column already exists
    conn.commit()
    conn.close()


def save_meeting(
    title: str,
    transcript: str,
    summary: str,
    extraction: ExtractionResult,
    department: str = "engineering",
) -> str:
    """Save meeting and all extracted data. Returns meeting_id."""
    meeting_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    conn = _get_db()

    # Save meeting
    conn.execute(
        "INSERT INTO meetings (id, title, transcript, summary, department, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (meeting_id, title, transcript, summary, department, now),
    )

    # Save tasks - use existing ID if set, otherwise generate new one
    for task in extraction.tasks:
        task_id = task.id if task.id else str(uuid.uuid4())
        conn.execute(
            "INSERT INTO tasks (id, description, owner, deadline, status, meeting_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (task_id, task.description, task.owner, task.deadline, task.status, meeting_id, now),
        )

    # Save decisions
    for decision in extraction.decisions:
        conn.execute(
            "INSERT INTO decisions (id, description, meeting_id) VALUES (?, ?, ?)",
            (str(uuid.uuid4()), decision.description, meeting_id),
        )

    # Save risks
    for risk in extraction.risks:
        conn.execute(
            "INSERT INTO risks (id, description, severity, meeting_id) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), risk.description, risk.severity, meeting_id),
        )

    conn.commit()
    conn.close()

    # Store in Chroma for semantic search
    _store_in_chroma(meeting_id, title, transcript, summary, extraction, department)

    return meeting_id


def _store_in_chroma(
    meeting_id: str,
    title: str,
    transcript: str,
    summary: str,
    extraction: ExtractionResult,
    department: str = "engineering",
):
    """Store meeting content in vector DB for semantic search."""
    collection = _get_chroma()

    # Store the full transcript (chunked if needed)
    chunks = _chunk_text(transcript, chunk_size=500)
    for i, chunk in enumerate(chunks):
        collection.upsert(
            documents=[chunk],
            metadatas=[{
                "meeting_id": meeting_id,
                "title": title,
                "type": "transcript",
                "department": department,
                "chunk_index": i,
            }],
            ids=[f"{meeting_id}_transcript_{i}"],
        )

    # Store summary
    if summary:
        collection.upsert(
            documents=[f"Meeting: {title}\nSummary: {summary}"],
            metadatas=[{"meeting_id": meeting_id, "title": title, "type": "summary", "department": department}],
            ids=[f"{meeting_id}_summary"],
        )

    # Store tasks as searchable text
    for i, task in enumerate(extraction.tasks):
        doc = f"Task: {task.description} | Owner: {task.owner} | Deadline: {task.deadline}"
        collection.upsert(
            documents=[doc],
            metadatas=[{"meeting_id": meeting_id, "title": title, "type": "task", "department": department}],
            ids=[f"{meeting_id}_task_{i}"],
        )

    # Store decisions
    for i, decision in enumerate(extraction.decisions):
        collection.upsert(
            documents=[f"Decision made: {decision.description}"],
            metadatas=[{"meeting_id": meeting_id, "title": title, "type": "decision", "department": department}],
            ids=[f"{meeting_id}_decision_{i}"],
        )


def _chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    """Split text into chunks of ~chunk_size characters at sentence boundaries."""
    sentences = text.replace("\n", " ").split(". ")
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) > chunk_size and current:
            chunks.append(current.strip())
            current = sentence + ". "
        else:
            current += sentence + ". "
    if current:
        chunks.append(current.strip())
    return chunks or [text]


def search_memory(query: str, n_results: int = 5, department: Optional[str] = None) -> list[dict]:
    """Semantic search over stored meeting content, optionally filtered by department."""
    collection = _get_chroma()
    try:
        count = collection.count()
        if count == 0:
            return []
        query_kwargs = {
            "query_texts": [query],
            "n_results": min(n_results, count),
        }
        if department:
            query_kwargs["where"] = {"department": department}
        results = collection.query(**query_kwargs)
        if not results["documents"][0]:
            return []
        return [
            {
                "text": doc,
                "metadata": meta,
                "distance": dist,
            }
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]
    except Exception:
        return []


def get_all_tasks(status: Optional[str] = None, department: Optional[str] = None) -> list[dict]:
    conn = _get_db()
    conditions, params = [], []
    if status:
        conditions.append("t.status = ?")
        params.append(status)
    if department:
        conditions.append("m.department = ?")
        params.append(department)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = conn.execute(
        f"SELECT t.*, m.title as meeting_title, m.department FROM tasks t JOIN meetings m ON t.meeting_id = m.id {where} ORDER BY t.created_at DESC",
        params,
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_meetings(department: Optional[str] = None) -> list[dict]:
    conn = _get_db()
    if department:
        rows = conn.execute(
            "SELECT * FROM meetings WHERE department = ? ORDER BY created_at DESC",
            (department,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM meetings ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_meeting_by_id(meeting_id: str) -> Optional[dict]:
    conn = _get_db()
    row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
    if not row:
        conn.close()
        return None
    meeting = dict(row)
    meeting["tasks"] = [
        dict(r) for r in conn.execute("SELECT * FROM tasks WHERE meeting_id = ?", (meeting_id,)).fetchall()
    ]
    meeting["decisions"] = [
        dict(r) for r in conn.execute("SELECT * FROM decisions WHERE meeting_id = ?", (meeting_id,)).fetchall()
    ]
    meeting["risks"] = [
        dict(r) for r in conn.execute("SELECT * FROM risks WHERE meeting_id = ?", (meeting_id,)).fetchall()
    ]
    conn.close()
    return meeting


def update_task_status(task_id: str, status: str) -> bool:
    conn = _get_db()
    result = conn.execute(
        "UPDATE tasks SET status = ? WHERE id = ?", (status, task_id)
    )
    conn.commit()
    conn.close()
    return result.rowcount > 0


def update_task_notion_urls(url_map: dict, page_id_map: dict = None) -> None:
    """Persist notion_url and notion_page_id for each task.
    url_map = {task_id: notion_url}
    page_id_map = {task_id: notion_page_id}
    """
    if not url_map and not page_id_map:
        return
    conn = _get_db()
    for task_id, notion_url in (url_map or {}).items():
        conn.execute(
            "UPDATE tasks SET notion_url = ? WHERE id = ?", (notion_url, task_id)
        )
    for task_id, page_id in (page_id_map or {}).items():
        conn.execute(
            "UPDATE tasks SET notion_page_id = ? WHERE id = ?", (page_id, task_id)
        )
    conn.commit()
    conn.close()


def get_task_by_id(task_id: str) -> Optional[dict]:
    """Get a single task by ID."""
    conn = _get_db()
    row = conn.execute(
        "SELECT t.*, m.title as meeting_title, m.department FROM tasks t "
        "JOIN meetings m ON t.meeting_id = m.id WHERE t.id = ?",
        (task_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_task(task_id: str, updates: dict) -> bool:
    """Update task fields. Returns True if updated."""
    if not updates:
        return False

    allowed_fields = {"description", "owner", "deadline", "status", "notion_url", "notion_page_id"}
    filtered = {k: v for k, v in updates.items() if k in allowed_fields}
    if not filtered:
        return False

    set_clause = ", ".join(f"{k} = ?" for k in filtered.keys())
    values = list(filtered.values()) + [task_id]

    conn = _get_db()
    result = conn.execute(
        f"UPDATE tasks SET {set_clause} WHERE id = ?", values
    )
    conn.commit()
    conn.close()
    return result.rowcount > 0


def find_matching_task(description: str, department: str = None, threshold: float = 0.7) -> Optional[dict]:
    """
    Find an existing task that matches the given description.
    Uses simple word overlap similarity. Returns the best match if above threshold.
    """
    tasks = get_all_tasks(department=department)
    if not tasks:
        return None

    def word_overlap_score(text1: str, text2: str) -> float:
        """Calculate Jaccard similarity based on word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    best_match = None
    best_score = 0.0

    for task in tasks:
        # Skip completed tasks - they shouldn't be updated
        if task.get("status") == "done":
            continue

        score = word_overlap_score(description, task.get("description", ""))
        if score > best_score and score >= threshold:
            best_score = score
            best_match = task

    if best_match:
        best_match["_match_score"] = best_score

    return best_match


def get_department_state(department: Optional[str] = None) -> dict:
    """Get a full snapshot of current department state, optionally filtered by department."""
    conn = _get_db()
    dept_filter = "AND m.department = ?" if department else ""
    dept_params = [department] if department else []

    pending_tasks = [
        dict(r) for r in conn.execute(
            f"SELECT t.*, m.title as meeting_title, m.department FROM tasks t JOIN meetings m ON t.meeting_id = m.id WHERE t.status = 'pending' {dept_filter} ORDER BY t.created_at DESC LIMIT 20",
            dept_params,
        ).fetchall()
    ]
    recent_decisions = [
        dict(r) for r in conn.execute(
            f"SELECT d.*, m.title as meeting_title FROM decisions d JOIN meetings m ON d.meeting_id = m.id WHERE 1=1 {dept_filter} ORDER BY m.created_at DESC LIMIT 10",
            dept_params,
        ).fetchall()
    ]
    open_risks = [
        dict(r) for r in conn.execute(
            f"SELECT r.*, m.title as meeting_title FROM risks r JOIN meetings m ON r.meeting_id = m.id WHERE r.resolved = 0 {dept_filter} ORDER BY CASE r.severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END LIMIT 10",
            dept_params,
        ).fetchall()
    ]
    count_filter = "WHERE department = ?" if department else ""
    total_meetings = conn.execute(
        f"SELECT COUNT(*) FROM meetings {count_filter}",
        dept_params,
    ).fetchone()[0]
    conn.close()

    return {
        "pending_tasks": pending_tasks,
        "recent_decisions": recent_decisions,
        "open_risks": open_risks,
        "total_meetings": total_meetings,
        "department": department,
    }


# ── Team Members ──────────────────────────────────────────────────────────────

def save_team_member(
    name: str,
    role: str = "",
    role_details: str = "",
    responsibilities: str = "",
    department: str = "",
    email: str = "",
    telegram_handle: str = "",
) -> str:
    """Insert a new team member. Returns the generated id."""
    member_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    conn = _get_db()

    # Try to insert with new columns, fall back to ALTER TABLE if they don't exist
    try:
        conn.execute(
            "INSERT INTO team_members (id, name, role, role_details, responsibilities, department, email, telegram_handle, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (member_id, name, role, role_details, responsibilities, department, email, telegram_handle.lstrip("@"), now),
        )
    except Exception:
        # Migrate the table by adding missing columns
        try:
            conn.execute("ALTER TABLE team_members ADD COLUMN role_details TEXT DEFAULT ''")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE team_members ADD COLUMN responsibilities TEXT DEFAULT ''")
        except Exception:
            pass
        # Retry insert
        conn.execute(
            "INSERT INTO team_members (id, name, role, role_details, responsibilities, department, email, telegram_handle, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (member_id, name, role, role_details, responsibilities, department, email, telegram_handle.lstrip("@"), now),
        )

    conn.commit()
    conn.close()
    return member_id


def get_team_members(department: Optional[str] = None) -> list[dict]:
    conn = _get_db()
    if department:
        rows = conn.execute(
            "SELECT * FROM team_members WHERE department = ? OR department = '' ORDER BY name ASC",
            (department,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM team_members ORDER BY name ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_team_member(member_id: str) -> bool:
    conn = _get_db()
    result = conn.execute("DELETE FROM team_members WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()
    return result.rowcount > 0


# ── Org Context ───────────────────────────────────────────────────────────────

def get_org_context(department: str) -> dict:
    conn = _get_db()
    row = conn.execute(
        "SELECT * FROM org_context WHERE department = ?", (department,)
    ).fetchone()
    conn.close()
    return dict(row) if row else {
        "department": department,
        "mission": "",
        "notion_database_id": "",
        "notion_page_id": ""
    }


def save_org_context(
    department: str,
    mission: str,
    notion_database_id: str = "",
    notion_page_id: str = ""
) -> None:
    now = datetime.utcnow().isoformat()
    conn = _get_db()
    conn.execute(
        "INSERT INTO org_context (department, mission, notion_database_id, notion_page_id, updated_at) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(department) DO UPDATE SET mission = excluded.mission, notion_database_id = excluded.notion_database_id, "
        "notion_page_id = excluded.notion_page_id, updated_at = excluded.updated_at",
        (department, mission, notion_database_id, notion_page_id, now),
    )
    conn.commit()
    conn.close()
