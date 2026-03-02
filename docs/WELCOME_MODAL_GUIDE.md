# 🎉 Welcome Modal - Quick Guide

## How to Trigger the Welcome Modal

### Option 1: Clear localStorage (Recommended for Testing)

1. Open your browser DevTools (F12 or Right-click → Inspect)
2. Go to the **Console** tab
3. Run this command:
   ```javascript
   localStorage.clear()
   ```
4. Refresh the page (F5 or Cmd+R)
5. The welcome modal will appear! 🎊

### Option 2: Manual Trigger (Quick Demo)

Open browser console and run:
```javascript
showWelcomeModal()
```

This will show the modal immediately without clearing anything.

### Option 3: Remove the Setup Flag Only

```javascript
localStorage.removeItem('teamai_setup_complete')
```
Then refresh the page.

---

## What the Welcome Modal Does

### Step 1: Team Context
- Users enter their team's mission and priorities
- Example: "Build innovative AI products that empower teams. Focus on user experience, scalability, and rapid iteration."
- This context is used by K2-Think-V2 during meeting extraction

### Step 2: Team Members
- Add team members with:
  - **Name** (required)
  - **Role** (e.g., "Engineering Lead")
  - **Responsibilities** (e.g., "Backend architecture, API design, code reviews")
- The responsibilities field helps AI assign tasks to the right people

### Features
- ✅ Checks automatically on first load
- ✅ Can skip and complete later
- ✅ Saves to database via API
- ✅ Beautiful animations and modern UI
- ✅ Stores completion state in localStorage

---

## Testing Flow

1. **Clear localStorage** → Refresh page
2. **Welcome modal appears**
3. **Enter team mission**: "Innovation team focused on AI research and product development"
4. **Add team members**:
   - Name: "Avani Gupta"
   - Role: "Engineering Lead"
   - Responsibilities: "Backend architecture, API design, team mentorship"
5. **Click "Complete Setup"**
6. **See success toast** → Modal closes
7. **Navigate to Team Setup page** to verify members were saved

---

## For Hackathon Demo

### Best Practices:
1. **Start fresh** before each demo:
   ```javascript
   localStorage.clear()
   ```

2. **Pre-fill sample data** for quick demos:
   - Keep sample mission text ready to paste
   - Prepare 2-3 team member examples

3. **Show the flow**:
   - "When users first open TeamAI..."
   - "They're guided through setup..."
   - "This helps AI understand their team..."
   - "Now watch how smart task assignment works!"

4. **Highlight the value**:
   - "Notice how AI knows everyone's responsibilities"
   - "It automatically assigns tasks to the right person"
   - "No manual work needed!"

---

## Troubleshooting

**Modal not appearing?**
- Check: `localStorage.getItem('teamai_setup_complete')`
- If it returns `"true"`, clear it: `localStorage.removeItem('teamai_setup_complete')`

**Modal stuck?**
- Force close: `hideWelcomeModal()`
- Force open: `showWelcomeModal()`

**Setup not saving?**
- Check browser console for errors
- Verify backend is running on port 8002
- Test API manually: `curl http://localhost:8002/api/team`

---

## API Endpoints Used

The welcome modal calls:
- `PUT /api/org/context` - Saves team mission
- `POST /api/team` - Adds each team member
- `GET /api/org/context?department=X` - Checks if setup needed
- `GET /api/team?department=X` - Checks if members exist

---

## Pro Tips for Demos

🎯 **Create a reset script** for quick demos:
```javascript
function resetDemo() {
  localStorage.clear();
  location.reload();
}
```

🎯 **Pre-populate data** in modal for faster demos (modify the modal HTML with default values)

🎯 **Record a video** showing the full flow - judges love visual demos!

🎯 **Emphasize the AI intelligence**: "The system learns your team structure and uses it for smart task assignment"
