"""
Gmail SMTP Authentication Fix Guide
This script provides solutions for the authentication error when sending bulk emails.
"""

def gmail_app_password_setup():
    """
    Step-by-step guide to set up Gmail App Password
    """
    steps = [
        "1. Enable 2-Factor Authentication on your Google Account",
        "2. Go to Google Account settings (myaccount.google.com)",
        "3. Navigate to Security > 2-Step Verification",
        "4. Scroll down to 'App passwords'",
        "5. Select 'Mail' as the app and 'Other' as device",
        "6. Enter a custom name like 'Django Bulk Email'",
        "7. Copy the 16-character password (no spaces)",
        "8. Use this App Password instead of your regular password"
    ]
    
    print("=== Gmail App Password Setup ===")
    for step in steps:
        print(step)
    
    print("\n=== Alternative Email Providers ===")
    providers = {
        "Gmail": {"smtp": "smtp.gmail.com", "port": 587, "note": "Requires App Password"},
        "Outlook/Hotmail": {"smtp": "smtp.office365.com", "port": 587, "note": "Use regular password"},
        "Yahoo": {"smtp": "smtp.mail.yahoo.com", "port": 587, "note": "Requires App Password"},
        "SendGrid": {"smtp": "smtp.sendgrid.net", "port": 587, "note": "Use API key as password"}
    }
    
    for provider, config in providers.items():
        print(f"{provider}: {config['smtp']}:{config['port']} - {config['note']}")

def test_smtp_connection():
    """
    Test SMTP connection with different configurations
    """
    import smtplib
    
    # Test configurations
    configs = [
        {"server": "smtp.gmail.com", "port": 587, "name": "Gmail TLS"},
        {"server": "smtp.gmail.com", "port": 465, "name": "Gmail SSL"},
        {"server": "smtp.office365.com", "port": 587, "name": "Outlook"},
    ]
    
    print("=== SMTP Server Test ===")
    for config in configs:
        try:
            server = smtplib.SMTP(config["server"], config["port"])
            if config["port"] == 587:
                server.starttls()
            print(f"✅ {config['name']}: Connection successful")
            server.quit()
        except Exception as e:
            print(f"❌ {config['name']}: {str(e)}")

# Run the functions
gmail_app_password_setup()
print("\n" + "="*50 + "\n")
test_smtp_connection()
