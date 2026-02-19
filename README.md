# TeamAI — Department Intelligence System

> Built for the **K2 Think × OpenClaw Hackathon**

TeamAI is an AI that attends your meetings, extracts actionable intelligence, and becomes the persistent knowledge interface for every team in your organization. Upload a transcript and within seconds you have structured tasks synced to Notion, risks flagged by severity, decisions logged, and cross-meeting patterns surfaced — all queryable in plain English.

---

## What It Does

| Capability | Description |
|---|---|
| **Meeting Ingestion** | Paste any meeting transcript → AI extracts tasks, decisions, risks |
| **Department Memory** | Every meeting is stored in SQLite + ChromaDB; queryable semantically |
| **Ask AI** | Natural language Q&A over your team's full meeting history |
| **Notion Sync** | All extracted tasks auto-sync to a Notion board, tagged by department |
| **Cross-Meeting Insights** | K2-Think-V2 reasons across multiple meetings to surface patterns |
| **Multi-Department** | Engineering, HR, MarCom, Innovation — isolated memory per team |
| **OpenClaw Orchestration** | Autonomous tool execution via OpenClaw gateway (fallback mode if not running) |

---

## System Design

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           TEAMAI SYSTEM DESIGN                                │
│                                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         USER INTERFACE (Browser)                         │ │
│  │  [Dept Selector] [Upload Meeting] [Ask AI] [Task Board] [Meetings]       │ │
│  └───────────────────────────────┬─────────────────────────────────────────┘ │
│                                  │ HTTP REST                                   │
│  ┌───────────────────────────────▼─────────────────────────────────────────┐ │
│  │                     FastAPI Backend  :8001                               │ │
│  │                                                                           │ │
│  │   /api/meetings/upload   /api/chat   /api/tasks   /api/state   /api/search│ │
│  └──┬──────────────┬──────────────┬──────────────┬───────────────────────┘ │
│     │              │              │              │                            │
│     ▼              ▼              ▼              ▼                            │
│  ┌──────┐    ┌──────────┐  ┌──────────┐  ┌──────────────┐                  │
│  │  K2  │    │  K2 V2   │  │ SQLite   │  │  ChromaDB    │                  │
│  │Think │    │ Instruct │  │          │  │              │                  │
│  │  V2  │    │          │  │meetings  │  │ vector store │                  │
│  │      │    │ Q&A /    │  │tasks     │  │ (MiniLM-L6)  │                  │
│  │Extrac│    │ chat     │  │decisions │  │              │                  │
│  │tion  │    │          │  │risks     │  │ semantic     │                  │
│  │Cross-│    │          │  │          │  │ search       │                  │
│  │mtg   │    │          │  │          │  │              │                  │
│  └──────┘    └──────────┘  └──────────┘  └──────────────┘                  │
│                                  │                                            │
│                    ┌─────────────┼─────────────────┐                         │
│                    ▼             ▼                  ▼                         │
│             ┌─────────────┐ ┌──────────┐  ┌──────────────┐                  │
│             │  OpenClaw   │ │  Notion  │  │   task_board │                  │
│             │  Gateway    │ │   API    │  │   .json      │                  │
│             │  :18789     │ │          │  │              │                  │
│             │ (optional)  │ │ Tasks    │  │ local state  │                  │
│             │             │ │ Tracker  │  │ (fallback)   │                  │
│             │ tool exec + │ │   DB     │  │              │                  │
│             │ agent chat  │ │ dept     │  │              │                  │
│             │             │ │ tagged   │  │              │                  │
│             └─────────────┘ └──────────┘  └──────────────┘                  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Architecture Overview

```
User (Browser)
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (port 8001)                  │
│                                                                   │
│  POST /api/meetings/upload                                        │
│       │                                                           │
│       ├──► K2-Think-V2 ──► Extract tasks / decisions / risks     │
│       │    (Reasoning)      + Cross-meeting insight analysis      │
│       │                                                           │
│       ├──► SQLite ──────── Persist meeting, tasks, decisions,    │
│       │                    risks (with notion_url per task)       │
│       │                                                           │
│       ├──► ChromaDB ─────── Embed transcript chunks + summary    │
│       │    (MiniLM-L6-v2)   + tasks + decisions for search       │
│       │                                                           │
│       ├──► OpenClaw ──────── Write meeting notes to workspace    │
│       │    (Orchestration)   + Sync task board JSON              │
│       │                                                           │
│       └──► Notion API ────── Create task pages with Department   │
│                              multi_select, owner, deadline        │
│                                                                   │
│  POST /api/chat                                                   │
│       │                                                           │
│       ├──► ChromaDB search ─── Retrieve top-6 relevant chunks    │
│       ├──► SQLite state ─────── Pending tasks, open risks        │
│       ├──► OpenClaw agent ───── (if running) tool-enabled answer │
│       └──► K2-V2-Instruct ──── Direct answer with context       │
└─────────────────────────────────────────────────────────────────┘
                    │                    │
                    ▼                    ▼
             Notion Board          OpenClaw Gateway
          (task tracking)       (localhost:18789, optional)
```

---

## Agents & Models

### K2-Think-V2 — Reasoning Agent
**Endpoint:** `https://build-api.k2think.ai`
**Model:** `LLM360/K2-Think-V2`
**Used for:**
- Meeting transcript extraction — identifies tasks (with owner + deadline), decisions, risks (with severity)
- Department-specific extraction context (e.g. Engineering focuses on sprints/tech debt; HR on hiring/onboarding)
- Cross-meeting insight detection — reasons over the last 5 meetings to flag recurring risks, overloaded owners, unresolved blockers, decision conflicts
- Strips its own `</think_fast>` reasoning tokens before JSON parsing

### K2-V2-Instruct — Q&A Agent
**Endpoint:** `https://instruct-api.k2think.ai`
**Model:** `LLM360/K2-V2-Instruct`
**Used for:**
- Answering questions about team state ("What are our open risks?", "Who owns the deployment task?")
- Receives a built context window: semantic search results + current pending tasks + recent decisions + open risks
- Department-specific system prompts ("You are the Engineering Department AI...")
- Also serves as the LLM behind the OpenClaw agent when it's running

### OpenClaw — Orchestration / Execution Layer
**Gateway:** `http://localhost:18789` (self-hosted, optional)

OpenClaw is a self-hosted agent gateway that connects an AI brain (K2-V2-Instruct) to real execution tools. TeamAI uses it for three specific jobs — each with a direct fallback if OpenClaw is not running.

```
OPENCLAW ORCHESTRATION DETAIL

┌────────────────────────────────────────────────────────────────────┐
│                   OpenClaw Gateway  :18789                          │
│                                                                      │
│  POST /tools/invoke          POST /v1/chat/completions              │
│  ─────────────────           ──────────────────────                 │
│  Executes named tools        OpenAI-compatible endpoint             │
│  with structured args        Routes to "department-ai" agent        │
│                              which uses K2-V2-Instruct as LLM       │
└────────────────────────────────────────────────────────────────────┘

JOB 1: Ask AI (chat)
──────────────────────────────────────────────────────────
  OpenClaw ON  → POST /v1/chat/completions  model=openclaw:department-ai
                 Agent has tool access (shell, files, browser)
                 Can look up files, run queries during answer

  Fallback OFF → POST directly to K2-V2-Instruct API
                 Pure text answer, no tool execution
                 Context built from ChromaDB + SQLite state

JOB 2: Task board sync (after every meeting upload)
──────────────────────────────────────────────────────────
  OpenClaw ON  → POST /tools/invoke  tool=shell
                 Runs Python one-liner via shell to append
                 task JSON to data/task_board.json

  Fallback OFF → Python writes data/task_board.json directly
                 Identical result — no HTTP call to OpenClaw

JOB 3: Meeting notes to workspace
──────────────────────────────────────────────────────────
  Both paths   → Write markdown file to
  (same code)    openclaw/workspace/meetings/YYYYMMDD_{id}.md
                 Contains: summary, tasks checklist, decisions, risks
                 OpenClaw agent can read these files autonomously
                 when answering questions (if running)

NOT handled by OpenClaw (always direct):
  • K2-Think-V2 extraction   → direct API call
  • SQLite writes            → direct Python sqlite3
  • ChromaDB writes          → direct Python chromadb
  • Notion sync              → direct httpx to api.notion.com
```

**Config:** `openclaw/openclaw.json`
- Agent ID: `department-ai`
- LLM: K2-V2-Instruct via `https://instruct-api.k2think.ai/v1`
- Auth token: `teamai-local-token`
- Allowed tools: `shell`, `file_read`, `file_write`, `browser`

---

## Data Flow: Meeting Upload

```
1. User selects department + pastes transcript
2. POST /api/meetings/upload
3. K2-Think-V2 reasons over transcript
   → Returns JSON: { tasks[], decisions[], risks[], summary }
4. IDs assigned to all extracted items
5. save_meeting() → SQLite
   ├── meetings table (id, title, transcript, summary, department, created_at)
   ├── tasks table   (id, description, owner, deadline, status, meeting_id, notion_url)
   ├── decisions     (id, description, meeting_id)
   └── risks         (id, description, severity, meeting_id)
6. _store_in_chroma() → ChromaDB
   ├── Transcript chunked into ~500 char segments
   ├── Each chunk stored with {meeting_id, title, type:"transcript", department}
   ├── Summary stored as single document
   ├── Each task stored as searchable text
   └── Each decision stored as searchable text
7. openclaw.sync_tasks_to_board() → task_board.json
8. openclaw.write_meeting_summary() → workspace/meetings/YYYYMMDD_{id}.md
9. notion_sync_tasks()
   ├── Creates Notion page per task
   ├── Properties: Task name [dept prefix], Status, Priority, Department (select), Due date, Description
   └── Returns url_map: {task_id → notion_url}
10. update_task_notion_urls(url_map) → SQLite tasks.notion_url
11. detect_cross_meeting_insights() if >1 meeting exists
    └── K2-Think-V2 analyzes new meeting vs last 5
12. Response returned to frontend with full extraction + notion links
```

## Data Flow: Ask AI

```
1. User types question in chat
2. POST /api/chat {message, history, department}
3. answer_question()
   ├── search_memory(query, department) → ChromaDB cosine search (top 6)
   ├── get_department_state(department) → SQLite snapshot
   │   ├── pending_tasks (last 20)
   │   ├── recent_decisions (last 10)
   │   └── open_risks (sorted by severity)
   ├── Build context string from search results + state
   ├── Try: openclaw.chat_with_agent(context + question)
   │         → routes to K2-V2-Instruct via OpenClaw agent API
   └── Fallback: K2-V2-Instruct direct API call with context
4. Return (answer, source_meetings[], used_openclaw: bool)
```

---

## File Structure

```
teamAI/
├── setup.sh                      # One-command setup + start
├── requirements.txt              # Python dependencies
├── .env                          # API keys (K2, Notion, OpenClaw)
│
├── backend/
│   ├── main.py                   # FastAPI app, all API endpoints
│   ├── config.py                 # Centralized config / env vars
│   ├── models/
│   │   └── schemas.py            # Pydantic models (Task, Meeting, ChatRequest…)
│   └── agents/
│       ├── extraction_agent.py   # K2-Think-V2: transcript → structured data
│       ├── query_agent.py        # K2-V2-Instruct: Q&A with memory context
│       ├── memory_store.py       # SQLite + ChromaDB read/write layer
│       ├── openclaw_client.py    # OpenClaw HTTP client + fallback mode
│       ├── notion_client.py      # Notion API: task creation + department tagging
│       └── departments.py        # Department definitions, prompts, sample transcripts
│
├── frontend/
│   └── index.html                # Full SPA dashboard (vanilla JS, dark theme)
│
├── data/                         # Runtime data (auto-created)
│   ├── teamai.db                 # SQLite database
│   ├── task_board.json           # OpenClaw task board state
│   └── chroma/                   # ChromaDB vector store
│
└── openclaw/
    ├── openclaw.json             # OpenClaw gateway config
    └── workspace/
        ├── AGENTS.md             # Agent documentation
        └── meetings/             # Auto-generated meeting notes (markdown)
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/meetings/upload` | Upload transcript → extract + sync |
| `GET` | `/api/meetings` | List meetings (`?department=engineering`) |
| `GET` | `/api/meetings/{id}` | Full meeting detail with tasks/decisions/risks |
| `GET` | `/api/departments` | All departments + sample transcripts |
| `GET` | `/api/state` | Department snapshot (`?department=hr`) |
| `GET` | `/api/tasks` | All tasks (`?status=pending&department=hr`) |
| `PATCH` | `/api/tasks/{id}` | Update task status |
| `POST` | `/api/chat` | Ask department AI a question |
| `GET` | `/api/search` | Semantic search (`?q=deployment&department=engineering`) |
| `GET` | `/api/openclaw/status` | OpenClaw gateway health |
| `POST` | `/api/openclaw/execute` | Execute tool via OpenClaw |

---

## Departments

| ID | Name | Focus Areas |
|---|---|---|
| `engineering` | ⚙️ Engineering | Sprints, tech debt, deployments, code reviews, infrastructure |
| `hr` | 👥 HR | Hiring pipeline, onboarding, performance reviews, policy, retention |
| `marcom` | 📣 Marketing & Comms | Campaigns, content calendar, events, brand, PR, analytics |
| `innovation` | 🚀 Industry Innovation | Research, grants, partnerships, datasets, IP, pilots |

Each department has:
- Isolated memory (same DB, filtered by `department` column)
- Specialized extraction prompt for K2-Think-V2
- Specialized Q&A system prompt for K2-V2-Instruct
- Sample transcript for demo

---

## Notion Integration

Tasks are synced to Notion after every meeting upload:

- **Database:** Tasks Tracker (`30a4529e-75ee-80b0-8e33-e1d6c582a95c`)
- **Properties written:** Task name (with dept emoji prefix), Status, Priority, Department (select), Due date, Description
- **Department values:** `Engineering` / `HR` / `MarCom` / `Innovation` — filter or group by this in Notion to see team-specific boards
- **Notion URLs** are stored back in SQLite (`tasks.notion_url`) and surfaced as 📋 links on every task card in the dashboard

---

## Setup

```bash
# 1. Clone and set up
git clone <repo>
cd teamAI
cp .env.example .env      # fill in K2_API_KEY, NOTION_API_KEY, NOTION_DATABASE_ID

# 2. Start (auto-installs deps, starts server)
bash setup.sh

# 3. Open browser
open http://localhost:8001

# Optional: OpenClaw (enables tool execution)
npm install -g openclaw
openclaw onboard --install-daemon
cp openclaw/openclaw.json ~/.openclaw/openclaw.json
openclaw dashboard        # starts on port 18789
```

**Required environment variables:**
```
K2_API_KEY=<your-k2-api-key>
NOTION_API_KEY=<your-notion-integration-token>
NOTION_DATABASE_ID=<your-notion-database-id>

# Optional (system works without these)
OPENCLAW_BASE_URL=http://localhost:18789
OPENCLAW_TOKEN=teamai-local-token
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn (Python 3.9+) |
| Reasoning | K2-Think-V2 (`LLM360/K2-Think-V2`) |
| Q&A | K2-V2-Instruct (`LLM360/K2-V2-Instruct`) |
| Vector Search | ChromaDB + sentence-transformers/all-MiniLM-L6-v2 |
| Structured Data | SQLite (WAL mode) |
| Orchestration | OpenClaw gateway (optional) |
| Task Tracking | Notion API v2022-06-28 |
| Frontend | Vanilla JS SPA, dark-theme CSS |
