# Opportunities Tracker - User Guide

## What It Does

TeamAI automatically detects and extracts information from opportunity emails including:
- Call for Interest (CFI)
- Expression of Interest (EOI)
- Call for Proposals (CFP)
- Request for Proposals (RFP)
- Grant Opportunities
- Funding Calls
- Partnership/Collaboration Requests

When you forward these emails to TeamAI, it:
1. Extracts key fields (deadline, organization, requirements, etc.)
2. Saves to the opportunities database
3. Exports to an Excel tracker
4. Sends you a confirmation email with a download link

---

## How to Use

### Step 1: Forward an Opportunity Email

Forward any opportunity email to: **teamaiassistant@gmail.com**

Example email types that work:
- "Call for Interest: AI Research Collaboration"
- "CFP: International Conference on Machine Learning"
- "Expression of Interest - Industry Partnership"
- "Grant Opportunity: Innovation Fund 2025"

### Step 2: Wait for Processing

TeamAI checks for new emails every 30 seconds. You'll receive a confirmation email within 1-2 minutes containing:

- Summary of the extracted opportunity
- Key details (deadline, organization, requirements)
- Excel file attached with all opportunities
- Download link for the latest Excel

### Step 3: Access Your Opportunities

**Option A: Email Link**
Click the "Download Updated Excel" button in your confirmation email to get the latest tracker.

**Option B: Direct Download**
Visit: `https://your-server/api/opportunities/download`

**Option C: API**
```bash
# List all opportunities
curl https://your-server/api/opportunities

# Download Excel
curl -O https://your-server/api/opportunities/download
```

---

## What Gets Extracted

| Field | Description |
|-------|-------------|
| Title | Official title of the opportunity |
| Type | CFI, CFP, EOI, Grant, etc. |
| Deadline | Submission deadline |
| Organization | Issuing organization |
| Contact Email | Contact for inquiries |
| Contact Name | Contact person |
| Budget | Funding amount (if mentioned) |
| Eligibility | Who can apply |
| Requirements | List of requirements |
| Submission Link | URL for submission portal |
| Summary | Brief summary |

---

## Excel Tracker Features

The exported Excel file includes:
- Color-coded status column (New, Reviewing, Applied, Rejected, Won)
- Auto-filter on all columns
- Frozen header row
- Formatted for easy reading

### Status Workflow

Update opportunity status via API:
```bash
curl -X PATCH "https://your-server/api/opportunities/{id}?status=reviewing"
```

Valid statuses: `new`, `reviewing`, `applied`, `rejected`, `won`

---

## Tips for Best Results

1. **Forward the full email** - Include all content for better extraction

2. **Use subject tags** for department routing:
   - `[Innovation]` - Routes to Innovation department
   - `[MarCom]` - Routes to Marketing
   - `[Engineering]` - Routes to Engineering

3. **Check deadlines** - The system extracts dates but verify important ones manually

4. **Download fresh Excel** - Use the download link to always get the latest data (includes all opportunities, not just the one you forwarded)

---

## Troubleshooting

**Email not processed?**
- Check it was sent to the correct address
- Ensure the email contains opportunity keywords (CFI, EOI, CFP, deadline, etc.)
- Wait 1-2 minutes for processing

**Missing fields in extraction?**
- Some fields may not be present in the original email
- AI extraction works best with structured emails

**Excel not attached?**
- Check if `openpyxl` is installed on the server
- The download link will still work

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/opportunities` | GET | List all opportunities |
| `/api/opportunities/{id}` | PATCH | Update status |
| `/api/opportunities/download` | GET | Download Excel file |
| `/api/opportunities/export` | GET | Export and get file path |
| `/api/opportunities/extract` | POST | Manually submit email for extraction |

### Example: Manual Extraction

```bash
curl -X POST https://your-server/api/opportunities/extract \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Call for Interest: AI Partnership",
    "body": "We are seeking partners for...",
    "sender_email": "partner@org.com",
    "department": "innovation"
  }'
```
