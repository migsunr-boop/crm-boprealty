#!/usr/bin/env python
import os
import sys
import django
import requests
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realty_dashboard.settings')
django.setup()

# Test webhook with sample data
webhook_url = "https://crm-1z7t.onrender.com/webhook/"

# Sample WhatsApp message payload
sample_payload = {
    "entry": [{
        "id": "PHONE_NUMBER_ID",
        "changes": [{
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {
                    "display_phone_number": "919355421616",
                    "phone_number_id": "PHONE_NUMBER_ID"
                },
                "contacts": [{
                    "profile": {
                        "name": "John Doe"
                    },
                    "wa_id": "919876543210"
                }],
                "messages": [{
                    "from": "919876543210",
                    "id": "wamid.test123",
                    "timestamp": "1640995200",
                    "text": {
                        "body": "Hi, I'm interested in your properties. Can you share more details about 2BHK apartments?"
                    },
                    "type": "text"
                }]
            },
            "field": "messages"
        }]
    }]
}

try:
    response = requests.post(webhook_url, json=sample_payload, timeout=10)
    print(f"Webhook test response: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error testing webhook: {e}")