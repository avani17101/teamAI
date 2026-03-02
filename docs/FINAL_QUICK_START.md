# 🚀 TeamAI - Quick Start Guide

## ✨ What You'll See

### 🎯 Landing Modal (First Load)
Two clear options:
- **🚀 Register New Department** - Set up a new department
- **👥 View Existing Departments** - Browse current departments

### 📋 Department Registration Flow
**3 Simple Steps:**
1. **Select Department** - Choose from 6 departments
2. **Department Mission** - Define goals and priorities
3. **Team Members** - Add people with their responsibilities

---

## 🚀 How to Access (3 Ways)

### Method 1: Click Button ⭐ **EASIEST**
Top-right corner → **"🚀 Quick Setup"**

### Method 2: URL Parameter
`http://localhost:8002?setup=true`

### Method 3: Keyboard
Press **D** key

---

## 📋 Perfect Demo Flow (2 minutes)

### Step 1: Landing (5 sec)
- Page loads → Landing modal appears
- **Click "Register New Department"**

### Step 2: Setup (45 sec)
**Select Department:**
- Choose **Innovation** from dropdown

**Add Mission:**
```
AI research focused on healthcare applications.
Priorities: Paper submissions, grant applications, hospital partnerships.
```

**Add Team Members:**
1. Dr. Aisha Hassan | Research Lead | NLP research, paper writing, grants
2. Mohammed Ali | ML Engineer | Model training, deployment, benchmarks
3. Sara Ibrahim | Partnership Manager | Hospital relations, pilots, MoUs

**Click "Register Department"**

### Step 3: Auto-Navigation (5 sec)
- Switches to Innovation department automatically
- Shows team page with all members
- Success toast appears

### Step 4: Test Intelligence (60 sec)
**Upload Meeting:**
- Use Innovation sample transcript
- Watch AI extract tasks
- **See smart assignment** based on responsibilities

**Ask Questions:**
- "Who should handle the paper submission?"
- "What are our open risks?"
- **AI uses department context** in responses

---

## 🎨 All 6 Departments

| Department | Icon | Key Focus |
|-----------|------|-----------|
| **Engineering** | ⚙️ | Software dev, infrastructure, sprints |
| **HR** | 👥 | Hiring, performance, team welfare |
| **Marketing & Comms** | 📣 | Campaigns, content, events |
| **Innovation** | 🚀 | Research, partnerships, grants |
| **Sales** | 💼 | Deals, pipeline, client relations |
| **Product** | 🎨 | Strategy, roadmap, design, research |

Each department has:
- Custom AI extraction context
- Specialized Q&A prompts
- Sample meeting transcripts

---

## 🔄 Reset for Fresh Demo

**Per Department:**
- Click "🚀 Quick Setup"
- Click "🔄 Clear Department Data"
- Only clears current department (others untouched)

**Complete Reset:**
```javascript
localStorage.clear();
location.reload();
```

---

## 💡 Key Features to Highlight

### 1. Department-Specific Intelligence
- Each department has its own AI context
- Specialized task extraction
- Custom Q&A responses

### 2. Smart Task Assignment
- AI reads team member responsibilities
- Assigns tasks to the right person
- No manual work needed

### 3. Click-to-Edit
- Click any team member → Edit modal
- Update responsibilities anytime
- Changes reflect immediately in AI

### 4. Multi-Department Ready
- 6 departments out of the box
- Each with unique context
- Independent data and teams

---

## 🎯 Hackathon Talking Points

### The Problem:
> "Teams waste hours in meetings, then waste more hours figuring out who should do what. Critical tasks slip through the cracks."

### The Solution:
> "TeamAI attends your meetings, extracts everything important, and assigns tasks to the right people based on their actual responsibilities."

### The Tech:
- **K2-Think-V2** for reasoning and extraction
- **K2-V2-Instruct** for Q&A
- **ChromaDB** for semantic memory
- **Department-specific contexts** for specialized intelligence

### The Wow:
1. **Beautiful onboarding** - No learning curve
2. **Department selection** - Multi-tenant from day 1
3. **Smart assignment** - AI reads responsibilities
4. **Contextual answers** - Knows your org structure
5. **Click to edit** - Change anything instantly

---

## 🎬 Demo Script (Word-for-Word)

### Opening (10 sec)
> "This is TeamAI - an AI that actually understands your team structure. Let me show you..."

### Setup (30 sec)
> "When you first open it, you get this choice: register a new department or view existing ones. I'll register Innovation..."
>
> *Select Innovation, add mission, add 2-3 team members*
>
> "Notice how I'm adding their responsibilities? That's the key - watch what happens..."

### The Magic (60 sec)
> "Now I upload a meeting transcript... and boom - it extracts tasks, decisions, and risks."
>
> "But here's the magic: see how it assigned the paper submission to Dr. Aisha? That's because it read her responsibilities and knew she handles research papers."
>
> "And when I ask it questions..."
>
> *Ask: "Who should handle the GPU cluster issue?"*
>
> "It suggests Mohammed because his responsibilities include infrastructure and benchmarks. The AI actually understands who does what."

### The Closer (20 sec)
> "Every department gets its own specialized AI. HR gets HR context, Sales gets sales context - all customized."
>
> "And if anything changes? Just click and edit. The AI updates instantly."

---

## ⚡ Quick Reference

| Action | Method |
|--------|--------|
| **Open Setup** | Click "🚀 Quick Setup" or press D |
| **Register Department** | Landing → Register New Department |
| **View Departments** | Landing → View Existing Departments |
| **Edit Member** | Click on team member card |
| **Clear Data** | Setup modal → Clear Department Data |
| **Close Modal** | Press Escape |
| **Complete Reset** | `localStorage.clear()` in console |

---

## 🐛 Troubleshooting

**Landing modal not showing?**
- Click "🚀 Quick Setup" button (top-right)
- Or visit `?setup=true`

**Want fresh start?**
- Setup modal → "Clear Department Data"
- Or: `localStorage.clear()` + refresh

**Can't edit members?**
- Click the team member card (not Remove button)

---

## 🏆 You're Ready!

1. Open http://localhost:8002
2. Landing modal appears automatically
3. Click "Register New Department"
4. Set up Innovation (or any department)
5. Upload a meeting
6. Watch the AI assign tasks intelligently
7. Win the hackathon! 🎉

**Remember:** The key differentiator is **smart assignment based on responsibilities** - make sure you emphasize that!

Good luck! 🚀
