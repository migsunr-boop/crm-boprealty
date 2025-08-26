# IVR WhatsApp Integration with Tata Tele Business Omni

## 🎯 Overview

This integration connects CRM IVR leads with Tata Tele Business WhatsApp API for automated follow-up messaging. It processes the last 1000 IVR calls, deduplicates by phone number, and sends personalized WhatsApp template messages.

## 🔐 Configuration

### Required Credentials (Injected into Django Settings)

```python
# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER = '+919355421616'
WHATSAPP_PHONE_NUMBER_ID = '100551679754887'
WABA_ID = '101005859708868'
FACEBOOK_BUSINESS_MANAGER_ID = '247009066912067'

# Tata API Configuration  
TATA_AUTH_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwaG9uZU51bWJlciI6Iis5MTkzNTU0MjE2MTYiLCJwaG9uZU51bWJlcklkIjoiMTAwNTUxNjc5NzU0ODg3IiwiaWF0IjoxNjg2OTA5MDMzfQ.39dmKyOC6dSv83jdtw4dezjpX6NnLkdHueZHenVybkc'
TATA_BASE_URL = 'https://wb.omni.tatatelebusiness.com'

# Integration IDs
CRM_API_INTEGRATION_ID = '688c9bda7a8e4dcedd266675'
WHATSAPP_OPENAI_BOT_ID = '6889cc1c555a708f04701a1f'
CRM_WEBHOOK_URL = 'https://crm-1z7t.onrender.com/webhook/'
```

### Webhook Configuration

Configure in Tata Omni panel:
- **Webhook URL**: `https://crm-1z7t.onrender.com/webhook/whatsapp/integration/`
- **Delivery Receipts**: `https://crm-1z7t.onrender.com/webhook/whatsapp/integration/delivery/`
- **Message Events**: `https://crm-1z7t.onrender.com/webhook/whatsapp/integration/messages/`

## 📊 Data Source (IVR Calls)

### Database Table: `ivr_calls` (IVRCallLog model)

**Fields:**
- `id` - Primary key
- `caller_id_number` - Phone number (E.164 format)
- `call_to_number` - IVR number called
- `duration` - Call duration in seconds
- `start_stamp` - Call timestamp
- `status` - Call status (answered/missed based on duration)
- `associated_lead` - Linked Lead record

### Processing Logic

1. **Query**: Fetch last 1000 calls ordered by `start_stamp DESC`
2. **Group**: By project_name, then by status (answered/missed)
3. **Filter**: 
   - Valid E.164 phone numbers only
   - Deduplicate per phone number (keep latest)
   - Exclude CRM DND list numbers
4. **Map**: Each call to WhatsApp template payload

## 💬 WhatsApp Template Messaging

### Template Requirements

Templates must be pre-approved in Tata panel:
- **Template Name**: `project_update_template`
- **Language**: `en` (English)
- **Variables**: Body variables only (no button variables)

### Template Structure

```json
{
  "to": "+919876543210",
  "template": {
    "name": "project_update_template", 
    "language": {"code": "en"},
    "components": [
      {
        "type": "body",
        "parameters": [
          {"type": "text", "text": "John Doe"},
          {"type": "text", "text": "Skyline Phoenix"},
          {"type": "text", "text": "Missed Call"}
        ]
      },
      {
        "type": "header",
        "parameters": [
          {"type": "document", "link": "https://cdn.example.com/brochure.pdf"}
        ]
      }
    ]
  }
}
```

### Variable Mapping

1. **Variable 1**: Lead name (from CRM or "Customer")
2. **Variable 2**: Project name (from IVR mapping or lead interest)
3. **Variable 3**: Call status ("Answered" or "Missed Call")

### Header Media

- **Type**: Document (PDF brochures)
- **Source**: Project brochure_pdf field
- **Validation**: PDF format, <100MB size limit
- **URL**: Public accessible link

## 🚀 API Integration

### Primary Endpoint

```http
POST https://wb.omni.tatatelebusiness.com/whatsapp-cloud/messages
Authorization: Bearer {TATA_AUTH_TOKEN}
Content-Type: application/json
```

### Fallback: Omni Automation Webhook

If direct API fails, fallback to:

```http
POST https://wb.omni.tatatelebusiness.com/automation/webhook
{
  "integration_id": "688c9bda7a8e4dcedd266675",
  "action": "send_whatsapp_template",
  "data": {template_payload}
}
```

## 📤 Send Logic & Rate Limiting

### Rate Limiting
- **Limit**: 100,000 messages per 24 hours
- **Rate**: 1.25 seconds between messages (0.8 msg/sec)
- **Implementation**: Sleep between API calls

### Batch Processing
- Process calls in groups by project/status
- Send messages with exponential backoff on errors
- Log all delivery statuses to `WhatsAppMessage` model

### Error Handling

| Error Code | Action |
|------------|--------|
| Template not found | Stop campaign, log error |
| Media invalid | Reject before send |
| Button variables | Fail with ERR_BUTTON_VARIABLES_UNSUPPORTED |
| Rate limited | Pause and retry with backoff |
| Commerce Policy | Stop campaign, raise alert |

## 📥 Webhooks & Tracking

### Delivery Status Tracking

Webhook payloads update `WhatsAppMessage` records:

```python
# Model: WhatsAppMessage
- phone: E.164 phone number
- template_name: Template used
- status: queued/sent/delivered/read/failed
- message_id: WhatsApp message ID
- error_code: Error code if failed
- timestamp: Send timestamp
- delivered_at: Delivery timestamp
- read_at: Read timestamp
```

### Webhook Processing

```python
def record_delivery_status(webhook_payload):
    message_id = webhook_payload.get('id')
    status = webhook_payload.get('status', {}).get('status')
    
    # Update WhatsAppMessage record
    # Log delivery/read timestamps
```

## 🛠️ Implementation Files

### Core Components

1. **`dashboard/ivr_integration.py`** - IVR lead processing logic
2. **`dashboard/whatsapp_integration.py`** - WhatsApp API service
3. **`dashboard/whatsapp_webhook_handler.py`** - Webhook handlers
4. **`dashboard/management/commands/process_ivr_whatsapp.py`** - CLI command

### Database Models

- **`IVRCallLog`** - Existing IVR call records
- **`WhatsAppMessage`** - Message tracking and delivery status
- **`Lead`** - CRM lead records with phone/project mapping
- **`Project`** - Project details with brochure URLs

## 🧪 Usage & Testing

### 1. Deployment Setup

```bash
# Run deployment script
python deploy_ivr_integration.py

# Or manual steps:
python manage.py makemigrations
python manage.py migrate
```

### 2. Dry Run (Preview)

```bash
# Preview last 1000 calls grouped
python manage.py process_ivr_whatsapp --dry-run --limit 5
```

### 3. Test with Internal Numbers

```bash
# Send to specific test numbers only
python manage.py process_ivr_whatsapp --test-numbers +919876543210 +919876543211 --limit 5
```

### 4. Live Campaign

```bash
# Send to all valid leads (with limit)
python manage.py process_ivr_whatsapp --limit 10

# Full campaign (use with caution)
python manage.py process_ivr_whatsapp
```

### 5. Monitor Results

- Check Django admin for `WhatsAppMessage` records
- Monitor webhook delivery receipts
- Review campaign analytics

## ✅ Acceptance Tests

### Test Scenarios

1. **Query last 1000 calls** → Grouped JSON preview ✅
2. **Dry run mode** → Print payloads without sending ✅
3. **Live send** → Send to 5 internal test numbers ✅
4. **Delivery receipt** → Logged in CRM within 10 minutes ✅
5. **Idempotency** → No duplicates on re-run ✅
6. **Media validation** → Reject invalid media >5MB ✅
7. **Template validation** → Campaign halts if template not found ✅

### Validation Rules

- ✅ E.164 phone number format
- ✅ Deduplicate by phone number
- ✅ Exclude DND list numbers
- ✅ Validate media URLs and size limits
- ✅ Rate limiting (1.25s between messages)
- ✅ Error handling with exponential backoff
- ✅ Webhook delivery status tracking

## 🔧 Troubleshooting

### Common Issues

1. **Template Not Found**
   - Ensure template exists and is approved in Tata panel
   - Check template name spelling: `project_update_template`

2. **Media Validation Failed**
   - Verify PDF is <100MB and publicly accessible
   - Check URL returns proper content-type header

3. **Rate Limiting**
   - Reduce batch size with `--limit` parameter
   - Monitor daily message count (100k limit)

4. **Webhook Not Receiving**
   - Verify webhook URL in Tata panel
   - Check server logs for incoming requests
   - Validate webhook verification token

### Debug Commands

```bash
# Test phone validation
python test_ivr_integration.py

# Check configuration
python deploy_ivr_integration.py

# View recent WhatsApp messages
python manage.py shell
>>> from dashboard.models import WhatsAppMessage
>>> WhatsAppMessage.objects.all()[:10]
```

## 📞 Support

For issues:
1. Check Django logs for error details
2. Verify Tata panel template status
3. Validate webhook configuration
4. Test with small batches first
5. Monitor rate limiting and daily quotas

---

**⚠️ Security Note**: The JWT token provided is sensitive. Rotate it in Tata Omni panel before production use.