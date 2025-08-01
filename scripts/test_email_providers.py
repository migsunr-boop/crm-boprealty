"""
Automated Email Provider Testing and Setup
This script tests multiple email providers and finds the best working option
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

def test_email_providers():
    """Test different email providers and return the best working option"""
    
    # Test configurations for different providers
    providers = [
        {
            "name": "SendGrid",
            "smtp_server": "smtp.sendgrid.net",
            "port": 587,
            "username": "apikey",
            "password": "YOUR_SENDGRID_API_KEY",  # Replace with actual API key
            "test_email": "noreply@yourdomain.com",
            "notes": "Most reliable for bulk emails, no authentication issues"
        },
        {
            "name": "Gmail",
            "smtp_server": "smtp.gmail.com", 
            "port": 587,
            "username": "your-email@gmail.com",  # Replace with actual Gmail
            "password": "YOUR_APP_PASSWORD",  # Replace with 16-char app password
            "test_email": "your-email@gmail.com",
            "notes": "Requires App Password, good for small volumes"
        },
        {
            "name": "Outlook",
            "smtp_server": "smtp.office365.com",
            "port": 587, 
            "username": "your-email@outlook.com",  # Replace with actual Outlook
            "password": "YOUR_APP_PASSWORD",  # Replace with app password
            "test_email": "your-email@outlook.com",
            "notes": "Requires App Password, Microsoft restrictions apply"
        }
    ]
    
    print("🔍 Testing Email Providers...")
    print("=" * 50)
    
    working_providers = []
    
    for provider in providers:
        print(f"\n📧 Testing {provider['name']}...")
        
        try:
            # Test SMTP connection
            server = smtplib.SMTP(provider['smtp_server'], provider['port'])
            server.starttls()
            
            # Skip actual login test if credentials are placeholders
            if "YOUR_" in provider['password'] or "your-email" in provider['username']:
                print(f"⚠️  {provider['name']}: Skipped (needs real credentials)")
                print(f"   📝 Setup: {provider['notes']}")
                continue
                
            # Test authentication
            server.login(provider['username'], provider['password'])
            server.quit()
            
            print(f"✅ {provider['name']}: Connection successful!")
            working_providers.append(provider)
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ {provider['name']}: Authentication failed - {str(e)}")
        except smtplib.SMTPConnectError as e:
            print(f"❌ {provider['name']}: Connection failed - {str(e)}")
        except Exception as e:
            print(f"❌ {provider['name']}: Error - {str(e)}")
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    
    if working_providers:
        print(f"✅ Found {len(working_providers)} working provider(s)")
        for provider in working_providers:
            print(f"   • {provider['name']}: {provider['smtp_server']}")
    else:
        print("❌ No working providers found with current credentials")
        print("\n🔧 RECOMMENDED SETUP:")
        print("1. SendGrid (Easiest):")
        print("   • Sign up at sendgrid.com (free tier: 100 emails/day)")
        print("   • Get API key from Settings > API Keys")
        print("   • Username: 'apikey', Password: your API key")
        print("\n2. Gmail (Alternative):")
        print("   • Enable 2FA at myaccount.google.com/security")
        print("   • Create App Password for Mail")
        print("   • Use 16-character app password")
    
    return working_providers

def create_sample_email_data():
    """Create sample email data for testing"""
    sample_data = [
        {"name": "John Doe", "email": "john@example.com"},
        {"name": "Jane Smith", "email": "jane@example.com"},
        {"name": "Bob Johnson", "email": "bob@example.com"}
    ]
    
    print("\n📝 Sample Email Data Created:")
    for person in sample_data:
        print(f"   • {person['name']} - {person['email']}")
    
    return sample_data

def simulate_bulk_email_send(provider, recipients, subject, template):
    """Simulate sending bulk emails"""
    print(f"\n📤 Simulating bulk email send via {provider['name']}...")
    
    sent_count = 0
    failed_count = 0
    
    for recipient in recipients:
        try:
            # Simulate email creation
            personalized_content = template.replace("{name}", recipient['name'])
            
            # Simulate sending (we won't actually send to avoid spam)
            print(f"   ✅ Would send to {recipient['email']}")
            sent_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed to send to {recipient['email']}: {str(e)}")
            failed_count += 1
    
    print(f"\n📊 Simulation Results:")
    print(f"   ✅ Successful: {sent_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📈 Success Rate: {(sent_count/(sent_count+failed_count))*100:.1f}%")
    
    return sent_count, failed_count

# Run the tests
print("🚀 Starting Automated Email System Test...")
working_providers = test_email_providers()

# Create sample data
sample_recipients = create_sample_email_data()

# Test email template
email_template = """
Hello {name}!

Thank you for your interest in our properties. 

This is a test email from our automated bulk email system.

Best regards,
Real Estate Team
"""

# If we have working providers, simulate sending
if working_providers:
    best_provider = working_providers[0]
    print(f"\n🎯 Using best provider: {best_provider['name']}")
    simulate_bulk_email_send(best_provider, sample_recipients, "Test Email", email_template)
else:
    print("\n⚙️  No providers configured yet. Please set up credentials first.")

print("\n🎉 Test Complete!")
