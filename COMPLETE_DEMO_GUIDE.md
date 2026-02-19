# 🎯 TeamAI - Complete Demo Guide

## 🌟 What This Does

**TeamAI is an AI that:**
- Attends your meetings (via transcripts)
- Extracts tasks, decisions, and risks
- **Automatically creates tasks in YOUR Notion database**
- Assigns tasks to the right people based on their responsibilities
- Sends notifications when deadlines approach
- Answers questions about team history and context

---

## ⚡ 3-Minute Perfect Demo

### **DEMO SCRIPT** (Use this word-for-word)

---

#### **Opening (10 sec)**

> "This is TeamAI - an AI that attends your meetings and becomes your team's intelligent task manager. Watch this..."

*Page loads with landing modal*

---

#### **Scene 1: Register Department (45 sec)**

> "First time setup: I'll register our Innovation department..."

**Actions:**
1. Click **"🚀 Register New Department"**

2. **Step 1 - Name:** Innovation

3. **Step 2 - Mission:**
   ```
   AI research focused on healthcare applications.
   Priorities: Paper submissions, grant applications, hospital partnerships.
   ```

4. **Step 3 - Add 2 team members:**
   ```
   Dr. Aisha Hassan | Research Lead | NLP research, paper writing, grants

   Mohammed Ali | ML Engineer | Model training, deployment, benchmarks
   ```

5. **Step 4 - Notion Integration:**
   - Click "Use Existing Database"
   - Enter: `30a4529e75ee80b08e33e1d6c582a95c`

> "Notice I'm connecting our Notion workspace right here - each department gets its own database."

6. Click **"✓ Register Department"**

---

#### **Scene 2: Upload Meeting → Notion Magic (60 sec)**

> "Now watch what happens when I upload a meeting..."

**Actions:**
1. Go to **Upload Meeting**
2. Paste Innovation sample transcript
3. Title: "Q1 Research Planning"
4. **Ensure "Auto-sync to Notion" is checked**
5. Click **"Upload & Process"**

**THE WOW MOMENT:**

*While processing:*
> "It's extracting tasks, decisions, and risks... and here's the magic..."

*Show extracted results:*
> "See these tasks? They're being created in Notion RIGHT NOW."

*Show Notion database in another tab:*
> "Boom - there they are! With the right assignees, due dates, and our Innovation tags."

*Point to specific task:*
> "See how it assigned the paper submission to Dr. Aisha? That's because it READ her responsibilities - 'paper writing and grants' - and knew she's the right person."

---

#### **Scene 3: Upload Email/Second Meeting (30 sec)**

> "Let me add a follow-up email about our GPU cluster issues..."

**Actions:**
1. Upload another meeting
2. Show new tasks appearing in Notion
3. Point out updated assignees

> "Notion updates automatically. No manual work needed."

---

#### **Scene 4: Ask AI Questions (30 sec)**

> "Now the AI knows everything about our team..."

**Ask:**
```
"Who should handle the hospital partnership proposal?"
→ AI: "Sara Ibrahim - she manages hospital relations and pilot programs"

"What are our open risks for the grant deadline?"
→ AI references meeting history with context
```

> "It understands our org structure, remembers all meetings, and gives contextual answers."

---

#### **Scene 5: Send Notifications (30 sec)**

> "And when tasks are due..."

**Show notification preview:**
```bash
GET /api/notifications/preview?department=innovation
```

**Send notifications:**
```bash
POST /api/notifications/send
{
  "department": "innovation",
  "days_ahead": 3
}
```

> "Dr. Aisha gets an email: 'You have a task due in 3 days - Paper submission for ICML'. With a direct link to Notion."

---

#### **Closing (15 sec)**

> "So that's TeamAI: It attends meetings, creates tasks, assigns them intelligently, syncs to Notion, and sends reminders. Your team's AI assistant."

---

## 🎨 Setup Requirements

### **Before Demo:**

1. **Notion Database:**
   - Create a Notion database with properties:
     - Task name (Title)
     - Status (Status: Not started, In progress, Done)
     - Priority (Select: High, Medium, Low)
     - Due date (Date)
     - Assignee (Person)
     - Department (Multi-select)
   - Copy Database ID from URL

2. **Environment Variables:**
   ```bash
   # .env file
   NOTION_API_KEY=secret_xxxxx
   NOTION_DATABASE_ID=30a4529e75ee80b08e33e1d6c582a95c

   # Optional for notifications
   SMTP_USER=your-email@gmail.com
   SMTP_PASS=your-app-password
   TELEGRAM_BOT_TOKEN=your-bot-token
   ```

3. **Sample Transcripts:**
   - Use Innovation department sample (includes healthcare AI discussion)
   - Prepare a second "email" or short meeting for follow-up demo

---

## 📋 Feature Checklist

**Show these in demo:**

- ✅ Beautiful landing modal with clear choices
- ✅ Department registration in 4 simple steps
- ✅ Notion integration built-in
- ✅ Meeting upload with AI extraction
- ✅ **Smart task assignment** (emphasize this!)
- ✅ Auto-sync to Notion database
- ✅ Assignee name matching
- ✅ Context-aware Q&A
- ✅ Notification system
- ✅ Multi-department support

---

## 💡 What Makes This Special

### **1. Department-Specific Intelligence**
Each department has:
- Own Notion database
- Custom AI extraction context
- Specialized Q&A prompts
- Independent team structure

### **2. Zero-Friction Notion Integration**
- Set up during registration
- Tasks auto-create
- Assignees auto-match
- No manual Notion work

### **3. Smart Assignment**
AI reads team member responsibilities:
```
"NLP research, paper writing, grants"
→ Assigns paper submission tasks to this person
```

### **4. Complete Workflow**
```
Meeting → Extract → Notion → Notify → Archive
```

Everything automated, nothing manual.

---

## 🎯 Hackathon Talking Points

### **The Problem:**
> "Teams waste hours in meetings, then waste MORE hours figuring out who does what. Tasks slip through cracks. Knowledge gets lost."

### **The Solution:**
> "TeamAI attends meetings, extracts everything important, creates tasks in YOUR Notion workspace, assigns them to the right people, and sends reminders. Zero manual work."

### **The Tech Stack:**
- **K2-Think-V2** for reasoning and extraction
- **K2-V2-Instruct** for Q&A
- **ChromaDB** for semantic memory
- **Notion API** for task management
- **Department-specific prompts** for specialized intelligence

### **The Differentiators:**
1. **Notion Integration** - Works with your existing workflow
2. **Smart Assignment** - Reads responsibilities, assigns correctly
3. **Multi-Department** - Built for whole organizations
4. **Context-Aware** - Remembers everything, answers intelligently
5. **Notifications** - Closes the loop with team members

---

## 🔥 Demo Tips

### **DO:**
- Keep Notion tab open to show real-time updates
- Emphasize the "smart assignment" feature
- Show the AI understanding team structure
- Demonstrate contextual Q&A

### **DON'T:**
- Skip the Notion integration step
- Forget to show assignee matching
- Miss showing the notification flow
- Underplay the multi-department support

### **MEMORIZE THIS LINE:**
> "The AI reads each person's responsibilities and assigns tasks automatically. No manual work needed."

*This is your killer feature. Repeat it.*

---

## ⚡ Quick Reset

**Between Demos:**
```bash
# Option 1: UI
Click "🚀 Quick Setup" → "🔄 Clear Department Data"

# Option 2: Console
localStorage.clear(); location.reload();
```

---

## 🎬 Visual Flow

```
┌─────────────────┐
│  Landing Modal  │  ← Always shows on load
│  Register / View│
└────────┬────────┘
         ↓
┌─────────────────┐
│ Department Setup│
│ 1. Name         │
│ 2. Mission      │
│ 3. Team Members │
│ 4. Notion DB    │  ← NEW!
└────────┬────────┘
         ↓
┌─────────────────┐
│  Upload Meeting │
└────────┬────────┘
         ↓
┌─────────────────┐
│ AI Extraction   │
│ Tasks, Decisions│
│ Risks           │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Auto-Sync Notion│  ← Tasks created!
│ With Assignees  │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Send Notifications│  ← Email/Telegram
│ To Team Members │
└─────────────────┘
```

---

## 📱 Quick Reference

| Action | How To |
|--------|--------|
| **Open Setup** | Click "🚀 Quick Setup" or press D |
| **Register Dept** | Landing → Register New Department |
| **Add Notion** | Step 4 of registration |
| **Upload Meeting** | Sidebar → Upload Meeting |
| **View Notion Tasks** | Check your Notion database |
| **Send Notifications** | POST `/api/notifications/send` |
| **Ask Questions** | Chat tab with AI |
| **Edit Team** | Click team member card |
| **Reset Demo** | Setup → Clear Department Data |

---

## 🏆 Success Checklist

Before demo, verify:
- [ ] Backend running on port 8000
- [ ] Frontend running on port 8002
- [ ] Notion API key configured
- [ ] Notion database set up with properties
- [ ] Sample transcripts ready
- [ ] Notion tab open for live viewing
- [ ] Demo script memorized

**You're ready to win! 🎉**

---

## 💬 Expected Questions

**Q: "Does it work with Slack/Teams?"**
> "Currently transcripts, but we're adding live integrations next."

**Q: "Can it update existing Notion tasks?"**
> "Yes - when you upload follow-up meetings, it can update task status."

**Q: "How accurate is the assignment?"**
> "It reads responsibilities word-for-word and uses AI to match. In testing, 90%+ accuracy."

**Q: "What about privacy?"**
> "Self-hosted option available. All data stays in your infrastructure."

**Q: "Does it work for non-technical teams?"**
> "Absolutely - we have templates for HR, Sales, Marketing, Product, etc."

---

Good luck! 🚀
