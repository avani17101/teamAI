# 📧 Setup Your Email for Department Routing

## Quick Setup (1 minute):

**Edit `/Users/avanigupta/teamAI/backend/main.py` around line 100:**

Find this section:
```python
email_to_dept = {
    "avani@example.com": "innovation",
    "avanigupta@gmail.com": "innovation",  # Add your actual email
    # Add more mappings as needed
}
```

**Replace with YOUR actual email:**
```python
email_to_dept = {
    "YOUR_ACTUAL_EMAIL@gmail.com": "innovation",  # Your email here!
    # Add team members' emails:
    # "sarah@company.com": "engineering",
    # "john@company.com": "sales",
}
```

## How It Works:

**When you forward email from YOUR_EMAIL@gmail.com:**
1. ✅ Routes to "innovation" department
2. ✅ Only sees Innovation team members (Avani, Mohammed, Sara)
3. ✅ Uses Innovation's Notion database
4. ✅ Matches "Avani" to Innovation's Avani Gupta (not Engineering's Avani)

**When someone else forwards from unknown@example.com:**
1. ✅ Routes to "engineering" (default fallback)
2. ✅ Uses Engineering team members
3. ✅ No cross-department contamination

## Example:

**You have:**
- Avani Gupta in Innovation dept
- Avani Shah in Engineering dept

**Email forwarded from YOUR_EMAIL → Innovation:**
- AI sees: Dr. Aisha, Mohammed, Sara, Avani Gupta
- "Avani needs to finish report" → Assigns to Avani Gupta ✅

**Email forwarded from someone@else.com → Engineering (default):**
- AI sees: Mike, John, Avani Shah
- "Avani needs to finish report" → Assigns to Avani Shah ✅

**No confusion!** Each email routes to correct department with correct team list.

## Alternative: Parse Subject Line

You can also route by subject:
```
Subject: [Innovation] Weekly team sync
→ Routes to Innovation

Subject: [Sales] Q1 Pipeline review
→ Routes to Sales

Subject: Regular meeting
→ Routes to Engineering (default)
```

Let me know if you want this feature!
