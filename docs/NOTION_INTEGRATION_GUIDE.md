# 🔗 TeamAI Notion Integration & Notifications Guide

## ✨ New Features

### 1. **Department-Level Notion Integration**
Each department can connect its own Notion database for task management.

### 2. **Automatic Task Sync**
Meeting tasks are automatically created in Notion with:
- Smart assignee matching based on team member names
- Department tags
- Due dates and priorities
- Direct links back to tasks

### 3. **Task Notifications**
Send reminders to team members via:
- 📧 **Email** - Professional task summaries
- 💬 **Telegram** - Instant notifications

---

## 🚀 Complete Demo Flow (3 minutes)

### **Step 1: Register Department with Notion** (45 sec)

1. **Landing Page**
   - Open http://localhost:8002
   - Landing modal appears automatically
   - Click **"🚀 Register New Department"**

2. **Department Setup**
   - **Name:** Innovation
   - **Mission:** AI research focused on healthcare applications. Priorities: Paper submissions, grant applications, hospital partnerships.

3. **Add Team Members:**
   ```
   Dr. Aisha Hassan | Research Lead | NLP research, paper writing, grants
   Email: aisha@company.com

   Mohammed Ali | ML Engineer | Model training, deployment, benchmarks
   Email: mohammed@company.com

   Sara Ibrahim | Partnership Manager | Hospital relations, pilots, MoUs
   Email: sara@company.com
   ```

4. **Notion Integration (Optional):**
   - Click **"📋 Use Existing Database"**
   - Enter your Notion Database ID: `30a4529e75ee80b08e33e1d6c582a95c`
   - *Or skip and configure later*

5. **Complete Registration**
   - Click **"✓ Register Department"**
   - Auto-navigates to Team page

---

### **Step 2: Upload Meeting & Auto-Sync to Notion** (60 sec)

1. **Navigate to Meetings**
   - Click "Upload Meeting" in sidebar

2. **Paste Transcript**
   - Use Innovation sample transcript (healthcare AI research meeting)
   - Title: "Q1 Research Planning Meeting"

3. **Upload with Auto-Sync**
   - Ensure "Auto-sync to Notion" is checked
   - Click **"Upload & Process"**

4. **Watch the Magic:**
   - AI extracts tasks, decisions, risks
   - **Tasks automatically appear in Notion!**
   - Each task assigned to right person based on responsibilities
   - Links back to TeamAI included

5. **Verify in Notion:**
   - Open your Notion database
   - See tasks with [🚀 Innovation] tags
   - Assignees matched automatically
   - Due dates parsed and set

---

### **Step 3: Upload Email/Second Meeting** (30 sec)

1. **Upload Another Meeting**
   - Title: "Follow-up: GPU Cluster Issues"
   - Paste email content or transcript

2. **New Tasks Created:**
   - Notion database updates with new tasks
   - Existing assignees retained
   - Priority levels set

---

### **Step 4: Chat with AI** (30 sec)

Ask intelligent questions using team context:

```
"Who should handle the paper submission deadline?"
→ AI: "Dr. Aisha Hassan - she handles paper writing and grants"

"What are our open risks in the GPU cluster project?"
→ AI references meeting history with team context

"When is Mohammed's next deadline?"
→ AI checks tasks assigned to Mohammed
```

---

### **Step 5: Send Notifications** (30 sec)

**Via API or Frontend:**

1. **Preview Due Tasks**
   ```bash
   GET http://localhost:8000/api/notifications/preview?department=innovation&days_ahead=3
   ```

2. **Send Notifications**
   ```bash
   POST http://localhost:8000/api/notifications/send
   {
     "department": "innovation",
     "days_ahead": 3
   }
   ```

3. **Team Members Receive:**
   - 📧 Email with task summary
   - 💬 Telegram notification (if configured)
   - Direct Notion links

---

## 🎨 Notion Database Setup

### **Option 1: Use Existing Database**

1. **Find Your Database ID:**
   - Open Notion database in browser
   - URL format: `notion.so/DATABASE_ID?v=...`
   - Copy the DATABASE_ID portion

2. **During Registration:**
   - Select "📋 Use Existing Database"
   - Paste Database ID
   - TeamAI will create tasks in this database

### **Option 2: Create New Database** *(Coming Soon)*

We'll automatically create a database with:
- Task name (title)
- Status (Not started, In progress, Done)
- Priority (High, Medium, Low)
- Due date
- Assignee (person)
- Department (multi-select)

---

## 📧 Email Configuration

### **Setup SMTP (for Email Notifications)**

Add to `.env`:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

### **Gmail App Password:**
1. Google Account → Security
2. Enable 2-Step Verification
3. App Passwords → Generate for "Mail"
4. Use generated password in .env

---

## 💬 Telegram Configuration

### **Setup Bot (for Telegram Notifications)**

1. **Create Bot:**
   - Message @BotFather on Telegram
   - `/newbot` → Follow prompts
   - Copy bot token

2. **Get Chat ID:**
   - Message your bot
   - Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Find `"chat":{"id": YOUR_CHAT_ID}`

3. **Add to .env:**
   ```bash
   TELEGRAM_BOT_TOKEN=your-bot-token
   TELEGRAM_CHAT_ID=your-chat-id
   ```

---

## 🔄 API Endpoints

### **Notion Integration**

```bash
# Get department context (includes Notion DB ID)
GET /api/org/context?department=innovation

# Update department context with Notion
PUT /api/org/context
{
  "department": "innovation",
  "mission": "AI research...",
  "notion_database_id": "30a4529e75ee80b08e33e1d6c582a95c",
  "notion_page_id": ""
}
```

### **Notifications**

```bash
# Preview tasks that would trigger notifications
GET /api/notifications/preview?department=innovation&days_ahead=3

# Send notifications to team members
POST /api/notifications/send
{
  "department": "innovation",
  "days_ahead": 3
}
```

### **Meetings with Notion Sync**

```bash
POST /api/meetings/upload
{
  "title": "Q1 Planning Meeting",
  "transcript": "...",
  "department": "innovation",
  "auto_sync_notion": true  # Auto-create in Notion
}
```

---

## 🎯 Perfect Hackathon Demo Script

### **Opening (15 sec)**
> "This is TeamAI - it attends your meetings, understands your team, and becomes your intelligent task manager. Let me show you the complete workflow..."

### **Act 1: Setup (45 sec)**
> "First, we register the Innovation department..."
- Show landing modal
- Quick department setup
- **Highlight:** "Notice how I'm adding Notion integration right here - one database per department"

### **Act 2: Meeting Processing (60 sec)**
> "Now I upload a meeting transcript..."
- Paste transcript
- Click upload
- **The WOW moment:** "Watch - it's extracting tasks AND creating them in Notion automatically!"
- Show Notion database updating in real-time
- **Highlight:** "See how it assigned the paper submission to Dr. Aisha? It read her responsibilities."

### **Act 3: Intelligence (30 sec)**
> "The AI understands everything..."
- Ask contextual questions
- Show smart responses based on team structure
- **Highlight:** "It knows who does what, what's at risk, and what's coming up"

### **Act 4: Notifications (30 sec)**
> "And when deadlines approach..."
- Send notification
- **Highlight:** "Team members get emails and Telegram messages with direct Notion links"
- "No manual work needed - the AI handles everything"

---

## 💡 Key Selling Points

### 1. **Zero Friction**
- One modal, four steps, fully configured
- Department gets its own Notion workspace
- Tasks flow automatically

### 2. **Smart Assignment**
- AI reads responsibilities
- Matches tasks to right people
- No manual assignment needed

### 3. **Multi-Department**
- Each department independent
- Own Notion database
- Own team context

### 4. **Complete Workflow**
```
Meeting → AI Extraction → Notion Tasks → Team Notifications
```

### 5. **Context-Aware**
- Remembers all meetings
- Understands team structure
- Answers based on full history

---

## 🐛 Troubleshooting

### **Notion Sync Failing?**

**Check:**
1. Notion API key in `.env`
2. Database ID is correct (32 chars, no hyphens)
3. Database has required properties:
   - Task name (title)
   - Status (status)
   - Priority (select)
   - Due date (date)
   - Assignee (person)
   - Department (multi-select)

**Fix:**
```bash
# Test Notion connection
curl -H "Authorization: Bearer YOUR_NOTION_KEY" \
  https://api.notion.com/v1/databases/YOUR_DB_ID
```

### **Notifications Not Sending?**

**Email:**
1. Check SMTP credentials in `.env`
2. For Gmail, use App Password (not account password)
3. Check team member email addresses

**Telegram:**
1. Verify bot token
2. Ensure chat_id is correct
3. Bot must be able to message the user

### **Tasks Not Assigning Correctly?**

1. Team member names must match extraction output
2. Check responsibilities are descriptive enough
3. Verify department is set for all team members

---

## ⚡ Quick Reference

| Feature | Endpoint/Action |
|---------|----------------|
| **Register with Notion** | Landing → Register → Step 4: Notion Integration |
| **Auto-sync meeting** | Upload Meeting → Check "Auto-sync to Notion" |
| **Manual Notion sync** | POST `/api/meetings/sync-notion` |
| **Send notifications** | POST `/api/notifications/send` |
| **Preview due tasks** | GET `/api/notifications/preview` |
| **Update Notion DB** | PUT `/api/org/context` with `notion_database_id` |

---

## 🏆 You're Ready!

**The Complete Flow:**
1. ✅ Register department with Notion
2. ✅ Add team members with emails
3. ✅ Upload meeting → Tasks auto-create in Notion
4. ✅ AI assigns tasks intelligently
5. ✅ Send notifications to team
6. ✅ Chat for insights

**Demo this in 3 minutes and win the hackathon!** 🎉
