# ✅ TeamAI Demo Test Checklist

## 🚀 Pre-Demo Setup

### 1. **Start Backend**
```bash
source venv/bin/activate
python -m backend.main
```

**Expected:** Server starts on http://localhost:8000
**Check logs for:** "Application startup complete"

### 2. **Open Frontend**
```bash
# In browser
open http://localhost:8002
```

**Expected:** Landing modal appears after 500ms

---

## 🧪 Test Flow (Step-by-Step)

### **Test 1: Department Registration**

1. **Landing Modal Appears** ✓
   - Two options visible: "Register New Department" | "View Existing Departments"

2. **Click "Register New Department"** ✓

3. **Step 1 - Department Name:**
   - Enter: `Innovation`
   - Or click: `🚀 Innovation` template button

4. **Step 2 - Mission:**
   - Should auto-fill if template clicked
   - Or enter manually

5. **Step 3 - Add Team Member:**
   - Name: `Dr. Aisha Hassan`
   - Role: `Research Lead`
   - Responsibilities: `NLP research, paper writing, grants`
   - Click `+ Add Team Member`

6. **Step 4 - Notion (Optional):**
   - Click "Use Existing Database"
   - Enter Database ID: `30a4529e75ee80b08e33e1d6c582a95c`
   - Or leave empty and skip

7. **Click "✓ Register Department"** ✓

**Expected:**
- ✅ Modal closes
- ✅ Department switches to Innovation
- ✅ Navigates to Team page
- ✅ Shows Dr. Aisha Hassan in team list
- ✅ Success toast appears

**If Error:**
- Check browser console (F12)
- Check backend logs
- Verify database initialized: `ls data/teamai.db`

---

### **Test 2: Upload Meeting**

1. **Click "📨 Upload Meeting/Email" in sidebar** ✓

2. **Verify Page Shows:**
   - Title: "Upload Meeting or Email"
   - Description mentions "forward emails to **teamai@gmail.com**"
   - Department banner shows "Innovation"

3. **Paste Sample Transcript:**
```
We discussed the Q1 research priorities for our healthcare AI project.

Dr. Aisha will lead the ICML paper submission on our NLP model by March 15th.

Mohammed needs to set up the GPU cluster for training by February 28th.

Sara will reach out to 5 hospital partners for pilot programs by end of Q1.

Key decisions:
- Prioritize accuracy over speed for clinical applications
- Focus on Arabic language support as differentiator

Risks:
- GPU cluster delays could push back training timeline
- Hospital approval processes may take 3-6 months
```

4. **Set Title:** `Q1 Research Planning`

5. **Ensure "Auto-sync to Notion" is checked** ✓

6. **Click "Upload & Process"** ✓

**Expected:**
- ✅ Processing spinner appears
- ✅ "Extraction complete" message
- ✅ Shows extracted tasks (3+ tasks)
- ✅ Shows decisions (2)
- ✅ Shows risks (2)
- ✅ Tasks assigned to correct people (Dr. Aisha, Mohammed, Sara)
- ✅ If Notion configured: "3 tasks created in Notion"

**If Error "upload not working":**

Check these:

1. **Backend logs** - Look for extraction errors
2. **Browser console** - Check for fetch errors
3. **Network tab** - Verify `/api/meetings/upload` returns 200
4. **K2 API** - Ensure endpoints are reachable:
   ```bash
   curl http://build-api-2.ifmapp.net:8000/v1/models
   ```

---

### **Test 3: View Tasks**

1. **Navigate to "Task Board"** in sidebar ✓

**Expected:**
- ✅ Opens Notion database in new tab
- ✅ Shows tasks with [🚀 Innovation] tags
- ✅ Assignees matched correctly

---

### **Test 4: Ask AI**

1. **Click "💬 Ask AI" in sidebar** ✓

2. **Ask:** `Who should handle the paper submission?`

**Expected:**
- ✅ AI responds: "Dr. Aisha Hassan"
- ✅ References her responsibilities
- ✅ Shows sources from meeting

3. **Ask:** `What are our open risks?`

**Expected:**
- ✅ Lists GPU cluster delays and hospital approval timelines
- ✅ Shows meeting as source

---

### **Test 5: Notifications (If Configured)**

**Setup `.env` first:**
```bash
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

**Test:**
```bash
curl -X POST http://localhost:8000/api/notifications/preview \
  -H "Content-Type: application/json" \
  -d '{"department": "innovation", "days_ahead": 30}'
```

**Expected:**
- ✅ Returns list of tasks due in next 30 days
- ✅ Shows task count

---

## 🐛 Common Issues & Fixes

### **Issue: "Team creation error"**

**Possible Causes:**
1. JavaScript error in browser console
2. Backend not running
3. Database not initialized

**Fix:**
```bash
# Reinitialize database
python -c "from backend.agents.memory_store import init_db; init_db()"

# Check browser console for exact error
# Open DevTools (F12) → Console tab
```

---

### **Issue: "Upload meeting not working"**

**Possible Causes:**
1. K2 API unreachable
2. Transcript too short (<50 chars)
3. Department not set

**Fix:**
```bash
# Test K2 API
curl http://build-api-2.ifmapp.net:8000/v1/models

# Check backend logs for extraction errors
tail -f backend.log

# Verify department is selected in sidebar
```

---

### **Issue: "Notion sync failing"**

**Possible Causes:**
1. Notion API key not set
2. Database ID incorrect
3. Database missing required properties

**Fix:**
```bash
# Check .env has Notion credentials
cat .env | grep NOTION

# Test Notion API
curl -H "Authorization: Bearer YOUR_NOTION_KEY" \
  https://api.notion.com/v1/databases/YOUR_DB_ID

# Verify database has these properties:
# - Task name (title)
# - Status (status)
# - Priority (select)
# - Due date (date)
# - Assignee (person)
# - Department (multi-select)
```

---

## ✅ Final Checklist Before Demo

- [ ] Backend starts without errors
- [ ] Frontend loads at http://localhost:8002
- [ ] Landing modal appears
- [ ] Can register department successfully
- [ ] Can add team members
- [ ] Can upload meeting transcript
- [ ] Tasks extract correctly
- [ ] Tasks assign to right people
- [ ] Notion sync works (if configured)
- [ ] Ask AI responds correctly
- [ ] Sample transcripts ready for each department

---

## 🎯 Quick Reset Between Tests

```bash
# Option 1: Clear current department data
# UI: Click "🚀 Quick Setup" → "🔄 Clear Department Data"

# Option 2: Complete reset
python -c "
from backend.agents.memory_store import _get_db
conn = _get_db()
conn.execute('DELETE FROM team_members')
conn.execute('DELETE FROM org_context')
conn.execute('DELETE FROM meetings')
conn.execute('DELETE FROM tasks')
conn.execute('DELETE FROM decisions')
conn.execute('DELETE FROM risks')
conn.commit()
print('Database cleared!')
"

# Then refresh browser
```

---

## 📞 Emergency Debug

If everything is broken:

```bash
# 1. Check Python version (must be 3.9+)
python --version

# 2. Reinstall dependencies
pip install -r requirements.txt

# 3. Reset database
rm data/teamai.db data/teamai.db-shm data/teamai.db-wal
python -c "from backend.agents.memory_store import init_db; init_db()"

# 4. Check all env variables
cat .env

# 5. Test backend endpoints
curl http://localhost:8000/api/departments
curl http://localhost:8000/api/team
curl http://localhost:8000/api/state?department=engineering
```

---

## 🎬 Demo Day Checklist

**1 Hour Before:**
- [ ] Fresh database (`rm data/teamai.db*; init_db()`)
- [ ] Backend running smoothly
- [ ] Browser cache cleared
- [ ] Sample transcripts in clipboard
- [ ] Notion database empty and ready
- [ ] Demo script printed/memorized

**5 Minutes Before:**
- [ ] Close all unneeded tabs
- [ ] Open Notion in separate tab
- [ ] Test one quick registration
- [ ] Verify network connection
- [ ] Take deep breath! 😊

**Good luck! 🚀**
