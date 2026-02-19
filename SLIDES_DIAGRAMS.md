# TeamAI - Slide Diagrams

## 📊 Slide 1: System Overview (Simple)

```mermaid
graph TB
    A[👤 User] --> B[🎤 Meeting Transcripts]
    A --> C[📧 Email Forwarding]

    B --> D[🤖 TeamAI AI Engine<br/>K2-Think-V2 + K2-V2-Instruct]
    C --> D

    D --> E[💾 Smart Storage<br/>SQLite + Vector DB]
    E --> F[📋 Notion Workspace]
    E --> G[📱 Telegram Reminders]
    E --> H[✉️ Email Auto-Reply]

    F --> A
    G --> A
    H --> A

    style D fill:#667eea,stroke:#333,stroke-width:3px,color:#fff
    style E fill:#22c55e,stroke:#333,stroke-width:2px,color:#fff
    style F fill:#764ba2,stroke:#333,stroke-width:2px,color:#fff
```

**Caption:** "Upload meetings or forward emails → AI extracts tasks → Auto-syncs everywhere"

---

## 🎯 Slide 2: The Magic (3 Steps)

```mermaid
graph LR
    A[1️⃣ Upload<br/>Meeting Transcript] --> B[2️⃣ AI Extracts<br/>Tasks • Decisions • Risks]
    B --> C[3️⃣ Auto-Sync<br/>Notion • Email • Reminders]

    style A fill:#3b82f6,stroke:#333,stroke-width:2px,color:#fff
    style B fill:#667eea,stroke:#333,stroke-width:2px,color:#fff
    style C fill:#22c55e,stroke:#333,stroke-width:2px,color:#fff
```

**Before TeamAI:** 2 hours of manual note-taking → tasks lost in Slack
**After TeamAI:** 20 seconds → tasks auto-created in Notion

---

## 🏢 Slide 3: Multi-Department Intelligence

```mermaid
graph TB
    subgraph "TeamAI"
        A[🌍 Organization]
    end

    A --> B[🚀 Innovation Dept]
    A --> C[⚙️ Engineering Dept]
    A --> D[📣 Marketing Dept]

    B --> B1[Dr. Aisha<br/>Mohammed<br/>Sara]
    B --> B2[Research<br/>Partnerships<br/>Grants]
    B --> B3[📋 Notion DB]

    C --> C1[David<br/>Ahmed<br/>Priya]
    C --> C2[Sprints<br/>Deployments<br/>Bugs]
    C --> C3[📋 Notion DB]

    D --> D1[Nour<br/>Zainab<br/>Tariq]
    D --> D2[Campaigns<br/>Social Media<br/>Events]
    D --> D3[📋 Notion DB]

    style A fill:#667eea,stroke:#333,stroke-width:4px,color:#fff
    style B fill:#22c55e,stroke:#333,stroke-width:2px,color:#fff
    style C fill:#3b82f6,stroke:#333,stroke-width:2px,color:#fff
    style D fill:#f59e0b,stroke:#333,stroke-width:2px,color:#fff
```

**Key Feature:** Avani Gupta can be in both Innovation AND Marketing → No confusion!

---

## 📧 Slide 4: Email Forwarding Flow

```mermaid
sequenceDiagram
    participant 👤 User
    participant 📧 Gmail
    participant 🤖 TeamAI
    participant 📋 Notion

    👤 User->>📧 Gmail: Forward email to<br/>teamaiassistant@gmail.com
    loop Every 30 sec
        🤖 TeamAI->>📧 Gmail: Check for new emails
    end
    📧 Gmail-->>🤖 TeamAI: New email found!
    🤖 TeamAI->>🤖 TeamAI: Extract tasks<br/>with AI
    🤖 TeamAI->>📋 Notion: Create tasks<br/>automatically
    🤖 TeamAI->>📧 Gmail: Send confirmation<br/>+ Notion link
    📧 Gmail-->>👤 User: ✅ Done!<br/>3 tasks created
```

**Impact:** Your email becomes a task creation machine

---

## 🧠 Slide 5: AI Processing Pipeline

```mermaid
graph LR
    A[📝 Raw Transcript] --> B{🤖 K2-Think-V2<br/>Reasoning Model}
    B --> C[📋 Tasks]
    B --> D[✅ Decisions]
    B --> E[⚠️ Risks]

    C --> F[🎯 Smart Assignment<br/>Fuzzy Name Match]
    F --> G[📋 Notion Pages<br/>Created]

    style B fill:#667eea,stroke:#333,stroke-width:3px,color:#fff
    style G fill:#22c55e,stroke:#333,stroke-width:2px,color:#fff
```

**Example:**
- Input: "Avani needs to finish the report"
- AI Matches: "Avani Gupta" in Notion workspace
- Result: Task assigned to correct person ✅

---

## 💡 Slide 6: Key Features (Icon Grid)

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  ⚡ 20-Second Extraction     📧 Email Assistant         │
│     AI processes meetings       Forward emails to get    │
│     in seconds, not hours       instant task creation    │
│                                                          │
│  🎯 Smart Assignment         🔔 Never Forget            │
│     Fuzzy name matching         Telegram reminders for   │
│     to Notion workspace         tasks due soon           │
│                                                          │
│  🏢 Multi-Department         🔍 Cross-Meeting Search    │
│     Same person in multiple     Ask AI about tasks       │
│     teams, zero confusion       across ALL meetings      │
│                                                          │
│  📋 Auto-Sync to Notion      🧠 Context-Aware           │
│     Tasks created without       Each department gets     │
│     manual copying              custom AI context        │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 📈 Slide 7: Impact Metrics

```
┌─────────────────────────────────────────┐
│          BEFORE          →    AFTER     │
├─────────────────────────────────────────┤
│  2 hours manual notes    →  20 seconds  │
│  Tasks lost in Slack     →  100% tracked│
│  Forgotten decisions     →  Searchable  │
│  Manual Notion updates   →  Automated   │
│  Email overload          →  AI assistant│
└─────────────────────────────────────────┘
```

**ROI Example:**
- Team of 10 people
- 3 meetings per week
- Save 2 hours per meeting
- **= 60 hours saved per week = $4,800/week** (at $80/hr)

---

## 🎨 Slide 8: Tech Stack (Simple)

```mermaid
graph TB
    subgraph "AI Layer"
        A[K2-Think-V2<br/>Reasoning]
        B[K2-V2-Instruct<br/>Q&A]
    end

    subgraph "Backend"
        C[FastAPI<br/>Python]
        D[SQLite +<br/>ChromaDB]
    end

    subgraph "Integrations"
        E[Notion API]
        F[Gmail IMAP/SMTP]
        G[Telegram Bot]
    end

    A --> C
    B --> C
    C --> D
    C --> E
    C --> F
    C --> G

    style A fill:#667eea,stroke:#333,stroke-width:2px,color:#fff
    style B fill:#764ba2,stroke:#333,stroke-width:2px,color:#fff
    style E fill:#22c55e,stroke:#333,stroke-width:2px,color:#fff
```

**Built in:** 2 weeks
**Production-ready:** Now

---

## 🚀 Slide 9: Architecture Summary (One Slide)

```mermaid
graph TB
    A[👥 Users] --> B[🌐 Frontend<br/>Port 8002]
    B --> C[⚡ FastAPI Backend<br/>Port 8001]

    C --> D{🤖 AI Agents}
    D --> D1[Extraction Agent]
    D --> D2[Query Agent]
    D --> D3[Email Forwarder]

    D1 --> E[💾 Storage Layer]
    D2 --> E
    D3 --> E

    E --> E1[(SQLite<br/>Structured)]
    E --> E2[(ChromaDB<br/>Vectors)]

    C --> F[🔌 Integrations]
    F --> F1[📋 Notion]
    F --> F2[📧 Gmail]
    F --> F3[📱 Telegram]

    F1 --> A
    F2 --> A
    F3 --> A

    style C fill:#3b82f6,stroke:#333,stroke-width:3px,color:#fff
    style D fill:#667eea,stroke:#333,stroke-width:2px,color:#fff
    style E fill:#22c55e,stroke:#333,stroke-width:2px,color:#fff
    style F fill:#f59e0b,stroke:#333,stroke-width:2px,color:#fff
```

---

## 📊 Slide 10: Department Isolation (Visual)

```
┌─────────────────────────────────────────────────────────┐
│                  🌍 TeamAI Platform                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ 🚀 Innovation│  │ ⚙️ Engineering│  │ 📣 Marketing│  │
│  ├──────────────┤  ├──────────────┤  ├─────────────┤  │
│  │ Team:        │  │ Team:        │  │ Team:       │  │
│  │ • Dr. Aisha  │  │ • David      │  │ • Nour      │  │
│  │ • Mohammed   │  │ • Ahmed      │  │ • Zainab    │  │
│  │ • Sara       │  │ • Priya      │  │ • Avani ✨  │  │
│  │ • Avani ✨   │  │              │  │             │  │
│  ├──────────────┤  ├──────────────┤  ├─────────────┤  │
│  │ Notion DB    │  │ Notion DB    │  │ Notion DB   │  │
│  │ Innovation   │  │ Engineering  │  │ Marketing   │  │
│  ├──────────────┤  ├──────────────┤  ├─────────────┤  │
│  │ Tasks: 12    │  │ Tasks: 8     │  │ Tasks: 15   │  │
│  │ Meetings: 5  │  │ Meetings: 3  │  │ Meetings: 7 │  │
│  └──────────────┘  └──────────────┘  └─────────────┘  │
│                                                         │
│  ✨ Avani Gupta appears in 2 departments               │
│  → Zero confusion, correct routing                     │
└─────────────────────────────────────────────────────────┘
```

---

## 🎬 Slide 11: Demo Flow (Visual Roadmap)

```
Step 1: UPLOAD                Step 2: EXTRACT              Step 3: SYNC
┌──────────────┐             ┌──────────────┐            ┌──────────────┐
│  📝 Paste    │             │  🤖 AI finds: │            │  ✅ Created: │
│  Meeting     │   ──────>   │  • 7 Tasks    │  ──────>   │  • Notion    │
│  Transcript  │             │  • 2 Decisions│            │  • Email     │
│              │             │  • 1 Risk     │            │  • Board     │
└──────────────┘             └──────────────┘            └──────────────┘
   20 seconds                   AI Processing                Automatic

Step 4: SEARCH               Step 5: REMIND               Step 6: INTELLIGENCE
┌──────────────┐             ┌──────────────┐            ┌──────────────┐
│  🔍 Ask AI:  │             │  📱 Telegram │            │  📊 Cross-   │
│  "Tasks for  │             │  3 days      │            │  Meeting     │
│  Avani?"     │             │  before due  │            │  Insights    │
└──────────────┘             └──────────────┘            └──────────────┘
   Instant answers              Never miss                  Patterns
```

---

## 💰 Slide 12: Value Proposition

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│          THE PROBLEM                                  │
│   ═══════════════════════════════════════            │
│   • Meetings create tasks → lost in notes            │
│   • Manual Notion updates → time waste               │
│   • Decisions forgotten → repeated discussions       │
│   • Email overload → missed action items             │
│                                                       │
├───────────────────────────────────────────────────────┤
│                                                       │
│          THE SOLUTION: TeamAI                         │
│   ═══════════════════════════════════════            │
│   ✅ AI attends every meeting                        │
│   ✅ Extracts tasks automatically                    │
│   ✅ Syncs to Notion in real-time                    │
│   ✅ Sends reminders before deadlines                │
│   ✅ Answers questions about past meetings           │
│                                                       │
├───────────────────────────────────────────────────────┤
│                                                       │
│          THE RESULT                                   │
│   ═══════════════════════════════════════            │
│   📈 60 hours saved per week (10-person team)        │
│   🎯 100% task capture rate                          │
│   🧠 Searchable meeting memory                       │
│   💰 $4,800/week value (@ $80/hr)                    │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## 🎯 Slide 13: Live Demo Checklist

```
✅ Pre-Demo (2 min before)
   □ Backend running on port 8001
   □ Frontend open: localhost:8002
   □ Notion tab open in background
   □ Sample transcript ready
   □ Email forwarder active

📋 Demo Steps (3 minutes)
   1. Upload Innovation Lab meeting
   2. Watch AI extract 7 tasks
   3. Show Notion auto-sync
   4. Switch to Marketing dept
   5. Show Avani in both depts
   6. Forward test email
   7. Show auto-reply
   8. Ask AI a question
   9. Show dashboard stats

🎬 Closing
   "Meeting intelligence, not just notes."
```

---

## 🔑 Slide 14: Key Differentiators

```
┌────────────────────────────────────────────────────┐
│                                                    │
│  TeamAI vs. Competitors                            │
│  ════════════════════════════                      │
│                                                    │
│  ❌ Fireflies.ai                                   │
│     • Generic transcription only                  │
│     • No department context                       │
│     • Manual Notion sync                          │
│                                                    │
│  ❌ Otter.ai                                       │
│     • Transcription focus                         │
│     • No task extraction                          │
│     • No team awareness                           │
│                                                    │
│  ❌ Notion AI                                      │
│     • Lives inside Notion only                    │
│     • No email integration                        │
│     • No autonomous processing                    │
│                                                    │
│  ✅ TeamAI                                         │
│     • Department-aware intelligence               │
│     • Auto-extracts tasks/decisions/risks         │
│     • Email forwarding assistant                  │
│     • Cross-meeting search                        │
│     • Auto-sync everywhere                        │
│     • Fuzzy name matching                         │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

**All diagrams are Mermaid-compatible and can be:**
- Rendered in Markdown viewers
- Exported to PNG/SVG for slides
- Used in Notion pages
- Embedded in presentations

**To convert to images for PowerPoint/Keynote:**
1. Use https://mermaid.live
2. Paste diagram code
3. Export as PNG/SVG
4. Insert into slides
