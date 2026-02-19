# 📧 Email Forwarding Setup - teamaiassistant@gmail.com

## ✅ What You Need to Do

### **Step 1: Get Gmail App Password** (5 minutes)

1. **Go to:** https://myaccount.google.com/security

2. **Enable 2-Step Verification:**
   - Click "2-Step Verification"
   - Follow prompts (use your phone)
   - Complete setup

3. **Generate App Password:**
   - Still on Security page
   - Click "App passwords" (appears after 2-Step enabled)
   - Select:
     - App: **Mail**
     - Device: **Other** → Type "TeamAI"
   - Click **"Generate"**
   - **COPY THE 16-CHARACTER PASSWORD**
     - Format: `xxxx xxxx xxxx xxxx`
     - You won't see it again!

---

### **Step 2: Enable IMAP in Gmail** (1 minute)

1. Go to Gmail → Settings (gear icon) → **"See all settings"**
2. Click **"Forwarding and POP/IMAP"** tab
3. Under "IMAP Access" → Select **"Enable IMAP"**
4. Click **"Save Changes"**

---

### **Step 3: Update .env File** (1 minute)

Open `/Users/avanigupta/teamAI/.env` and replace the placeholder:

**Replace this:**
```bash
SMTP_PASS=PUT_YOUR_16_CHAR_APP_PASSWORD_HERE
TEAMAI_EMAIL_PASSWORD=PUT_YOUR_16_CHAR_APP_PASSWORD_HERE
```

**With your actual app password:**
```bash
SMTP_PASS=abcd efgh ijkl mnop
TEAMAI_EMAIL_PASSWORD=abcd efgh ijkl mnop
```

*Note: Use the SAME password in both places (remove spaces if you want)*

---

### **Step 4: Test Setup** (2 minutes)

Run the test script:

```bash
source venv/bin/activate
python test_email_setup.py
```

**Expected output:**
```
============================
TeamAI Email Setup Verification
============================

📧 Email Address: teamaiassistant@gmail.com
✅ Password configured (length: 16 chars)

🔌 Testing IMAP connection...
✅ IMAP connection successful!
📬 Unread emails: 0

============================
✅ EMAIL FORWARDING READY!
============================
```

**If you see errors:**
- Check app password is correct
- Verify IMAP is enabled
- Make sure 2-Step Verification is on

---

## 🚀 How to Use

### **Start Backend with Email Polling:**

```bash
source venv/bin/activate
python -m backend.main
```

**Look for this in logs:**
```
[EmailForwarder] Started polling teamaiassistant@gmail.com every 30 seconds
```

### **Test Email Forwarding:**

1. **From any email account**, send an email to: **teamaiassistant@gmail.com**

2. **Subject:** Test Task Email

3. **Body:**
```
Hey team,

Quick action items from our call:

1. John needs to finish the Q1 report by Friday
2. Sarah will schedule the client demo for next week
3. Mike should review the PR by tomorrow

Thanks!
```

4. **Watch backend logs** - within 30 seconds you should see:
```
[EmailForwarder] New email: Test Task Email
[EmailForwarder] Processing email: Test Task Email
[EmailForwarder] Saved meeting <meeting-id> with 3 tasks
```

5. **Check in UI:**
   - Go to Meetings page
   - See "Email: Test Task Email"
   - Click to view extracted tasks

---

## 🎯 Demo Flow

### **Act 1: Manual Upload** (Show existing flow)
- Upload meeting transcript
- Show task extraction
- Show Notion sync

### **Act 2: Email Forward** (THE WOW)
- "But wait - I can also forward emails directly..."
- Send email from phone to teamaiassistant@gmail.com
- Wait 30 seconds
- Refresh UI → "See? Email processed automatically!"
- Show tasks extracted from email
- "No copy-paste needed - just forward and forget"

---

## 🎨 UI Enhancement (Optional)

Show the email address in the Upload page:

**Current UI says:**
> "You can also forward emails to **teamai@gmail.com** for processing."

**Perfect - it already shows it!** Just make sure to use **teamaiassistant@gmail.com** instead.

Let me update that:
