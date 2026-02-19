"""Test email forwarding setup"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_email_config():
    """Check if email is configured correctly"""
    print("=" * 60)
    print("TeamAI Email Setup Verification")
    print("=" * 60)

    email = os.getenv("TEAMAI_EMAIL", "")
    password = os.getenv("TEAMAI_EMAIL_PASSWORD", "")

    print(f"\n📧 Email Address: {email}")

    if not email:
        print("❌ TEAMAI_EMAIL not set in .env")
        return False

    if not password or password == "PUT_YOUR_16_CHAR_APP_PASSWORD_HERE":
        print("❌ TEAMAI_EMAIL_PASSWORD not set properly in .env")
        print("\nTo fix:")
        print("1. Go to https://myaccount.google.com/security")
        print("2. Enable 2-Step Verification")
        print("3. Generate App Password for 'Mail'")
        print("4. Add to .env: TEAMAI_EMAIL_PASSWORD=your-16-char-password")
        return False

    print(f"✅ Password configured (length: {len(password)} chars)")

    # Test IMAP connection
    print("\n🔌 Testing IMAP connection...")
    try:
        import imaplib
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email, password)
        mail.select("inbox")
        print("✅ IMAP connection successful!")

        # Check for unread emails
        status, messages = mail.search(None, "UNSEEN")
        if status == "OK":
            unread_count = len(messages[0].split())
            print(f"📬 Unread emails: {unread_count}")

        mail.close()
        mail.logout()
        return True

    except imaplib.IMAP4.error as e:
        print(f"❌ IMAP connection failed: {e}")
        print("\nPossible issues:")
        print("- App password is incorrect")
        print("- IMAP not enabled in Gmail (Settings → Forwarding and POP/IMAP)")
        print("- Wrong email address")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_email_config()

    print("\n" + "=" * 60)
    if success:
        print("✅ EMAIL FORWARDING READY!")
        print("\nNext steps:")
        print("1. Start backend: python -m backend.main")
        print("2. Forward an email to: teamaiassistant@gmail.com")
        print("3. Watch backend logs for processing")
    else:
        print("❌ EMAIL SETUP INCOMPLETE")
        print("\nPlease fix the issues above and run this test again")
    print("=" * 60)
