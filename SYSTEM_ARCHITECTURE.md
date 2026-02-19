# TeamAI - System Architecture

## 🏗️ High-Level Architecture

```mermaid
graph TB
    subgraph "User Inputs"
        A[Meeting Transcripts]
        B[Email Forwarding]
        C[Manual Task Entry]
    end

    subgraph "TeamAI Backend - Port 8001"
        D[FastAPI Server]
        E[Email Forwarder Service]
        F[Extraction Agent]
        G[Query Agent]
        H[Notion Client]
        I[Memory Store]
    end

    subgraph "AI Layer"
        J[K2-Think-V2<br/>Reasoning Model]
        K[K2-V2-Instruct<br/>Q&A Model]
    end

    subgraph "Data Storage"
        L[(SQLite<br/>Tasks, Meetings, Teams)]
        M[(ChromaDB<br/>Vector Search)]
        N[(Task Board JSON<br/>OpenClaw)]
    end

    subgraph "External Services"
        O[Notion API<br/>Task Sync]
        P[Gmail IMAP/SMTP<br/>teamaiassistant@gmail.com]
        Q[Telegram Bot<br/>Reminders]
    end

    subgraph "Frontend - Port 8002"
        R[React-like SPA]
        S[Department Selector]
        T[Upload Interface]
        U[Chat Interface]
        V[Dashboard]
    end

    A --> D
    B --> E
    C --> D
    E --> F
    D --> F
    F --> J
    F --> I
    G --> K
    G --> M
    H --> O
    I --> L
    I --> M
    I --> N
    D --> H
    D --> G
    E --> P
    D --> Q
    R --> D
    S --> D
    T --> D
    U --> D
    V --> D

    style J fill:#667eea,stroke:#333,stroke-width:2px,color:#fff
    style K fill:#764ba2,stroke:#333,stroke-width:2px,color:#fff
    style O fill:#22c55e,stroke:#333,stroke-width:2px,color:#fff
    style P fill:#f59e0b,stroke:#333,stroke-width:2px,color:#fff
```

---

## 🔄 Data Flow - Meeting Upload

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant FastAPI
    participant Extraction
    participant K2Think
    participant Memory
    participant Notion
    participant OpenClaw

    User->>Frontend: Upload meeting transcript
    Frontend->>FastAPI: POST /api/meetings/upload
    FastAPI->>Extraction: extract_meeting()
    Extraction->>Memory: get_team_members(dept)
    Memory-->>Extraction: Team context
    Extraction->>K2Think: Chat completion with context
    K2Think-->>Extraction: JSON: tasks, decisions, risks
    Extraction->>Extraction: Parse & validate
    Extraction-->>FastAPI: ExtractionResult
    FastAPI->>Memory: save_meeting()
    Memory->>Memory: SQLite INSERT
    Memory->>Memory: ChromaDB upsert
    FastAPI->>OpenClaw: sync_tasks_to_board()
    OpenClaw-->>FastAPI: Board updated
    FastAPI->>Notion: sync_tasks()
    Notion->>Notion: Match owners to workspace users
    Notion->>Notion: Create pages in database
    Notion-->>FastAPI: Created URLs
    FastAPI->>Memory: update_task_notion_urls()
    FastAPI-->>Frontend: Success + metadata
    Frontend-->>User: Show extracted tasks
```

---

## 📧 Email Forwarding Flow

```mermaid
sequenceDiagram
    participant User
    participant Gmail
    participant EmailForwarder
    participant Extraction
    participant Memory
    participant Notion
    participant SMTP

    User->>Gmail: Forward email to teamaiassistant@gmail.com
    loop Every 30 seconds
        EmailForwarder->>Gmail: IMAP check for UNSEEN
        Gmail-->>EmailForwarder: New email found
    end
    EmailForwarder->>EmailForwarder: Parse subject for [Department] tag
    EmailForwarder->>EmailForwarder: Route by sender email OR tag
    EmailForwarder->>Extraction: process_forwarded_email()
    Extraction->>Memory: Extract tasks/decisions/risks
    Memory-->>Extraction: Saved meeting ID
    Extraction->>Notion: Auto-sync tasks
    Notion-->>Extraction: Notion URLs
    EmailForwarder->>SMTP: send_processing_confirmation()
    SMTP->>Gmail: HTML email with summary + Notion link
    Gmail-->>User: Auto-reply received
```

---

## 🧠 Department-Aware Architecture

```mermaid
graph LR
    subgraph "Multi-Department System"
        A[Global Department Registry]

        subgraph "Innovation Department"
            B1[Team Members:<br/>Dr. Aisha, Mohammed, Sara]
            C1[Mission Context]
            D1[Notion DB: Innovation]
            E1[Meetings & Tasks]
        end

        subgraph "Engineering Department"
            B2[Team Members:<br/>David, Ahmed, Priya]
            C2[Mission Context]
            D2[Notion DB: Engineering]
            E2[Meetings & Tasks]
        end

        subgraph "MarCom Department"
            B3[Team Members:<br/>Nour, Zainab, Tariq]
            C3[Mission Context]
            D3[Notion DB: MarCom]
            E3[Meetings & Tasks]
        end
    end

    A --> B1
    A --> B2
    A --> B3
    B1 --> E1
    B2 --> E2
    B3 --> E3
    C1 --> E1
    C2 --> E2
    C3 --> E3
    D1 --> E1
    D2 --> E2
    D3 --> E3

    style A fill:#667eea,stroke:#333,stroke-width:3px,color:#fff
```

**Key Isolation:**
- Each department has separate team members
- Separate mission context for AI extraction
- Separate Notion databases
- Same person can exist in multiple departments (e.g., Avani in Innovation + MarCom)
- No cross-department task contamination

---

## 🗄️ Database Schema

```mermaid
erDiagram
    MEETINGS ||--o{ TASKS : contains
    MEETINGS ||--o{ DECISIONS : contains
    MEETINGS ||--o{ RISKS : contains
    DEPARTMENTS ||--o{ MEETINGS : has
    DEPARTMENTS ||--o{ TEAM_MEMBERS : has
    DEPARTMENTS ||--|| ORG_CONTEXT : configures

    MEETINGS {
        string id PK
        string title
        text transcript
        text summary
        timestamp created_at
        string department FK
    }

    TASKS {
        string id PK
        text description
        string owner
        string deadline
        string status
        string meeting_id FK
        timestamp created_at
        string notion_url
        string department
    }

    DECISIONS {
        string id PK
        text description
        string meeting_id FK
        string department
    }

    RISKS {
        string id PK
        text description
        string severity
        string meeting_id FK
        string department
    }

    TEAM_MEMBERS {
        string id PK
        string name
        string role
        string responsibilities
        string department FK
        string email
        string telegram_handle
    }

    ORG_CONTEXT {
        string department PK
        text mission
        string notion_database_id
        string notion_page_id
        timestamp updated_at
    }

    DEPARTMENTS {
        string id PK
        string name
        string icon
        string color
        text description
    }
```

---

## 🔌 API Endpoints

### **Meetings**
- `POST /api/meetings/upload` - Upload & extract meeting
- `GET /api/meetings` - List all meetings (filterable by department)
- `GET /api/meetings/{id}` - Get meeting details

### **Tasks**
- `GET /api/tasks` - List tasks (filter by status, department)
- `PUT /api/tasks/{id}/status` - Update task status
- `POST /api/tasks/sync-notion` - Manual Notion sync

### **Chat / Q&A**
- `POST /api/chat` - Ask department AI a question

### **Departments**
- `GET /api/departments` - List all departments
- `GET /api/state?department={dept}` - Get department dashboard state

### **Team Management**
- `GET /api/team?department={dept}` - List team members
- `POST /api/team` - Add team member
- `PUT /api/team/{id}` - Update team member
- `DELETE /api/team/{id}` - Remove team member

### **Org Context**
- `GET /api/org/context?department={dept}` - Get department mission
- `POST /api/org/context` - Save department mission

### **Notifications**
- `POST /api/notifications/due-reminders` - Send due task reminders

### **OpenClaw**
- `GET /api/openclaw/status` - Check OpenClaw gateway status
- `GET /api/board` - Get task board JSON

---

## 🧩 Component Breakdown

### **1. FastAPI Backend (`backend/main.py`)**
- Central API server
- Routes requests to agents
- Handles CORS, static file serving
- Manages startup/shutdown hooks

### **2. Extraction Agent (`backend/agents/extraction_agent.py`)**
- Uses K2-Think-V2 for reasoning
- Department-aware extraction
- Returns structured JSON: tasks, decisions, risks
- Cross-meeting insights detection

### **3. Memory Store (`backend/agents/memory_store.py`)**
- SQLite for structured data
- ChromaDB for semantic search
- Department filtering
- Task board JSON management

### **4. Notion Client (`backend/agents/notion_client.py`)**
- Workspace user matching (fuzzy name matching)
- Task page creation
- Multi-select property support (Status, Priority)
- Department-specific database routing

### **5. Email Forwarder (`backend/agents/email_forwarder.py`)**
- IMAP polling every 30 seconds
- Subject parsing for department tags
- Sender-to-department mapping
- Auto-reply with HTML email + Notion link

### **6. Query Agent (`backend/agents/query_agent.py`)**
- Uses K2-V2-Instruct for Q&A
- Searches ChromaDB + SQLite
- Department context injection
- Returns sources with answers

### **7. OpenClaw Client (`backend/agents/openclaw_client.py`)**
- Optional agentic workflow gateway
- Task board JSON management
- Meeting note markdown generation

### **8. Telegram Client (`backend/agents/telegram_client.py`)**
- Due task reminders
- Task assignment notifications
- Department-aware messaging

---

## 🎨 Frontend Architecture

```
Frontend (Single Page App)
│
├── Department Selector (Global State)
│   └── Updates all components on change
│
├── Navigation (Sidebar)
│   ├── Dashboard
│   ├── Upload Meeting/Email
│   ├── Ask AI
│   ├── Tasks
│   ├── Meetings History
│   ├── Team Setup
│   └── OpenClaw
│
├── Dashboard View
│   ├── Stats Cards (Meetings, Tasks, Decisions, Risks)
│   ├── Recent Tasks List
│   └── Open Risks List
│
├── Upload View
│   ├── Meeting/Email Toggle
│   ├── Department Selector
│   ├── Title Input
│   ├── Transcript Textarea
│   ├── Load Sample Button
│   ├── Auto-sync Notion Toggle
│   └── Results Display (Tasks, Decisions, Risks)
│
├── Chat View
│   ├── Department Context Header
│   ├── Suggested Questions Chips
│   ├── Chat History
│   ├── Input Field
│   └── Sources Display
│
├── Tasks View
│   ├── Department Board Grid
│   └── Notion Links
│
├── Meetings View
│   ├── Meeting Cards
│   └── Task/Decision/Risk Counts
│
└── Team Setup View
    ├── Team Members Table
    ├── Add Member Form
    ├── Edit Member Modal
    └── Org Context Form
```

---

## 🔐 Security & Configuration

### **Environment Variables (.env)**
```bash
# AI Models
K2_API_KEY=sk-xxx
OPENCLAW_BASE_URL=http://localhost:18789
OPENCLAW_TOKEN=teamai-local-token

# Notion
NOTION_API_KEY=ntn_xxx
NOTION_DATABASE_ID=30a4529e-75ee-80b0-8e33-e1d6c582a95c

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=teamaiassistant@gmail.com
SMTP_PASS=app_password_16_chars

TEAMAI_EMAIL=teamaiassistant@gmail.com
TEAMAI_EMAIL_PASSWORD=app_password_16_chars
IMAP_SERVER=imap.gmail.com
EMAIL_POLLING_INTERVAL=30

# Telegram (Optional)
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
```

### **Data Storage Locations**
```
/Users/avanigupta/teamAI/data/
├── teamai.db           # SQLite database
├── task_board.json     # OpenClaw task board
└── chroma/             # ChromaDB vector store
    ├── chroma.sqlite3
    └── [UUID]/         # Collection data
```

---

## 🚀 Deployment Options

### **Local Development**
```bash
# Backend
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload

# Frontend (served by backend)
# Access at http://localhost:8001
```

### **Production Options**

**1. Single Server (Recommended for Demo)**
```bash
# Backend on 8001, frontend served statically
uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

**2. ngrok (Temporary Public Access)**
```bash
ngrok http 8001
# Share the https://xxx.ngrok.io URL
```

**3. Cloud Deployment**
- **Railway**: One-click deploy, persistent storage
- **Render**: Free tier available, auto-deploy from git
- **Fly.io**: Edge deployment, global CDN

---

## 📊 Data Flow Summary

```
1. User Input
   ↓
2. FastAPI Endpoint
   ↓
3. Department Context Loading
   ↓
4. AI Processing (K2 Models)
   ↓
5. Data Persistence (SQLite + ChromaDB)
   ↓
6. External Sync (Notion + Email)
   ↓
7. Response to User
```

**Key Features:**
- ✅ Real-time extraction (20-30 seconds)
- ✅ Department isolation (no cross-contamination)
- ✅ Automatic Notion sync
- ✅ Email forwarding with auto-reply
- ✅ Cross-meeting search
- ✅ Task reminders (Telegram)
- ✅ Fuzzy name matching
- ✅ Multi-department user support

---

## 🎯 System Highlights

### **Innovation Points**
1. **Department-Aware AI**: Each department gets custom context for extraction
2. **Fuzzy Name Matching**: "Avani" correctly matches "Avani Gupta" in Notion
3. **Email Routing**: Subject tags `[Innovation]` or sender email mapping
4. **Cross-Meeting Intelligence**: K2-Think-V2 finds patterns across meetings
5. **Zero Manual Sync**: Tasks auto-create in Notion with correct assignees
6. **24/7 Email Assistant**: Forward emails, get instant task extraction

### **Tech Stack**
- **Backend**: FastAPI (Python 3.9+)
- **AI**: K2-Think-V2 (reasoning), K2-V2-Instruct (Q&A)
- **Database**: SQLite (structured), ChromaDB (vectors)
- **Integrations**: Notion API, Gmail IMAP/SMTP, Telegram Bot
- **Frontend**: Vanilla JS + CSS (no framework)
- **Deployment**: Uvicorn ASGI server

---

**Built for demo on:** 2026-02-19
**Architecture Version:** 1.0
