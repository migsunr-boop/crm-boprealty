# TATA Webhook Setup Guide

## Webhook Configuration for TATA Panel

### 1. Webhook URL
Configure this URL in your TATA Integration panel:

```
https://crm-1z7t.onrender.com/webhook/
```

### 2. Webhook Settings
- **Method:** POST
- **Content-Type:** application/json
- **Authentication:** None (handled by signature validation)

### 3. Expected Payload Format

#### Incoming WhatsApp Message:
```json
{
  "contacts": [
    {
      "profile": {
        "name": "User Name"
      },
      "wa_id": "919999999999"
    }
  ],
  "messages": {
    "from": "919999999999",
    "id": "wamid.HBgMOTE5MTA2MDg5MzQzFQIAEhggRTQzMEI1QjA5QkU0RkIwREI1MzQyQThENUQ4NkQ4RTMA",
    "timestamp": "1744109205",
    "text": {
      "body": "hi"
    },
    "type": "text"
  },
  "businessPhoneNumber": "+919355421616",
  "id": "268e8b65-59a2-45df-9006-bd4b2aedbfdc"
}
```

#### Message Status Updates:
```json
{
  "statuses": [
    {
      "id": "wamid.HBgMOTE4NDkwMDI5MTA1FQIAERgSRDkwQjFEQURDMEI5MkExNUY3AA==",
      "status": "sent",
      "timestamp": "1729161280",
      "recipient_id": "919999999999"
    }
  ],
  "businessPhoneNumber": "+919355421616"
}
```

### 4. What Happens When Webhook Receives Data:

1. **Message Storage:** All incoming messages are stored in the database
2. **Lead Creation:** If phone number doesn't exist, creates new lead
3. **Lead Notes:** Adds WhatsApp message as a note to the lead
4. **Real-time Updates:** Messages appear instantly in the chat panel

### 5. Testing the Webhook:

Send a test message to your WhatsApp Business number (+919355421616) and check:
- Message appears in https://crm-1z7t.onrender.com/tata-chat/
- New lead is created if phone number is new
- Lead notes are updated with the message

### 6. Chat Panel Features:

- **View Conversations:** All WhatsApp chats organized by phone number
- **Send Replies:** Reply directly from CRM using TATA API
- **Lead Integration:** Messages automatically linked to leads
- **Real-time Updates:** Auto-refresh every 10 seconds

### 7. API Endpoints:

- **Webhook:** `POST /webhook/` - Receives TATA messages
- **Get Conversations:** `GET /ajax/tata-conversations/` - Fetch all chats
- **Send Reply:** `POST /ajax/tata-send-reply/` - Send WhatsApp message
- **Chat Panel:** `GET /tata-chat/` - Main chat interface