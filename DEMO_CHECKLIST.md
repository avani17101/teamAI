# TeamAI - 3-Minute Demo Checklist

## ✅ Pre-Demo Setup (2 minutes)

### 1. Start Backend
```bash
cd /Users/avanigupta/teamAI
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

### 2. Start Frontend
```bash
# In another terminal
uvicorn backend.main:app --host 0.0.0.0 --port 8002 --reload
```

### 3. Open Browser
Navigate to: `http://localhost:8002`

### 4. Verify Services
- ✅ Backend running on port 8001
- ✅ Frontend running on port 8002
- ✅ Email forwarder polling (check backend logs)
- ✅ Notion credentials configured (.env)

---

## 🎬 Demo Flow (3 Minutes)

### **Minute 1: Upload & Extract (0:00-1:00)**

**Script:**
*"Every meeting, your team makes decisions and assigns tasks. But they get lost in notes and email threads. Watch this."*

**Actions:**
1. Click **"Upload Meeting/Email"** in sidebar
2. Select **Innovation** department from dropdown
3. Click **"Load Sample"** (uses realistic Innovation Lab transcript)
4. Click **"Upload & Process"**
5. Watch extraction happen (takes ~20-30 seconds)
6. Point out:
   - ✅ 7 tasks extracted with owners
   - ✅ Dr. Aisha → Complete ACL paper
   - ✅ Khalid → Publish Arabic Voice Dataset
   - ✅ 2 decisions, 1 risk identified

**Talking point:** *"In 20 seconds, AI extracted every task, every decision, every risk. No manual work."*

---

### **Minute 2: Intelligence Layer (1:00-2:00)**

**Script:**
*"But here's where it gets powerful - department-aware intelligence."*

**Actions:**
1. Switch to **Product** department (click dept dropdown)
2. Show dashboard updates:
   - Different team members
   - Different tasks
   - Different metrics
3. Go to **Team Setup** tab
4. Show: Avani Gupta exists in **both** Innovation AND MarCom
5. Switch back to Innovation → show correct Avani

**Talking point:** *"Same person, different departments. No cross-contamination. The AI knows context."*

**Demo Email Forwarding:**
1. Forward pre-written email to `teamaiassistant@gmail.com`
2. Check your inbox for auto-reply (within 30 secs)
3. Show auto-reply email with:
   - ✅ Task summary
   - ✅ Assignees and deadlines
   - ✅ Notion database link button

**Talking point:** *"Your team's AI assistant running 24/7. Forward any email, get instant task extraction."*

---

### **Minute 3: Memory & Search (2:00-3:00)**

**Script:**
*"Unlike Slack or email, TeamAI REMEMBERS everything."*

**Actions:**
1. Go to **Ask AI** tab
2. Ask: *"What tasks are assigned to Avani?"*
3. Watch AI search across ALL meetings
4. Show results with sources
5. Ask: *"What risks do we have in Innovation?"*
6. Show: GPU cluster bottleneck identified

**Talking point:** *"Cross-meeting intelligence. Search your team's entire knowledge base instantly."*

**Demo Close:**
1. Go to **Dashboard**
2. Show live stats: X meetings, Y tasks, Z decisions
3. Click Notion link → open task board

**Closing line:**
*"Meeting intelligence, not just meeting notes. Every meeting becomes searchable memory. Every task tracked. Every decision documented. That's TeamAI."*

---

## 🎯 Key Features to Highlight

### Core Value Props:
1. **Instant Extraction** - 20 seconds vs hours of manual note-taking
2. **Auto-Sync** - Tasks appear in Notion automatically
3. **Department Intelligence** - Context-aware across teams
4. **24/7 Email Processing** - Forward emails, get instant replies
5. **Cross-Meeting Search** - Find anything across all meetings

### Skip These (Boring for Demo):
- ❌ Team member registration flow
- ❌ Org context configuration
- ❌ Manual task status updates
- ❌ OpenClaw integration details

---

## 📧 Email Forwarding Test

### Sample Email to Forward:
```
To: teamaiassistant@gmail.com
Subject: [Innovation] Quick Team Sync

Action items from today:
1. Avani - finish the white paper by Friday
2. Mohammed - schedule client demo for next week
3. Risk: Dataset release blocked by security review
```

**Expected Auto-Reply:**
- Subject: RE: [Innovation] Quick Team Sync
- Body: Beautiful HTML with task summary + Notion link
- Delivery: Within 30 seconds

---

## 🚀 Going Live Options

### Option 1: Local Demo (Recommended)
- Run on localhost:8002
- Screen share during presentation
- No deployment needed
- ✅ Safest, fastest

### Option 2: ngrok (Temporary Public Link)
```bash
ngrok http 8002
# Share the https://xxx.ngrok.io link
```
- ✅ Others can access remotely
- ⚠️ Link expires when stopped
- ⚠️ Free tier has rate limits

### Option 3: Deploy (Permanent Link)
```bash
# Railway, Render, or Fly.io
# ~5 minutes setup
# Permanent URL
```
- ✅ Always accessible
- ⚠️ Requires deployment config
- ⚠️ May incur hosting costs

---

## 🐛 Troubleshooting

### Backend won't start?
```bash
# Kill old processes
lsof -i :8001 | grep LISTEN | awk '{print $2}' | xargs kill -9
# Restart
uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

### Email forwarding not working?
```bash
# Check .env has correct credentials
cat .env | grep TEAMAI_EMAIL
# Check backend logs for email polling
# Should see: "[EmailForwarder] Starting inbox polling..."
```

### Extraction fails?
```bash
# Check K2 API key in .env
cat .env | grep K2_API_KEY
# Check backend logs for detailed error
```

### Frontend not loading?
```bash
# Verify API endpoint
# frontend/index.html line 708: const API = 'http://localhost:8001';
```

---

## 📝 Demo Notes

**Timing:**
- Upload: 30 seconds
- Department switch: 10 seconds
- Email demo: 45 seconds
- AskAI queries: 30 seconds each
- Buffer: 15 seconds

**Total:** ~3 minutes

**Backup Plan:**
If live demo fails, have screen recording ready!

---

## ✨ Wow Moments to Emphasize

1. **Speed**: "20 seconds vs 20 minutes of manual work"
2. **Accuracy**: "AI correctly assigned tasks to Dr. Aisha, not just 'Aisha'"
3. **Integration**: "Notion sync is automatic, not manual"
4. **Intelligence**: "Department-aware, not generic"
5. **Memory**: "Searches across ALL meetings, not just one"

---

**Good luck with your demo!** 🚀
