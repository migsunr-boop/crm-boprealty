# WhatsApp Campaign Runbook
## Production-Grade Tata Omni/Smartflo Integration

### Overview
This runbook covers the production WhatsApp template messaging system integrated with Tata Omni/Smartflo for sending campaigns to IVR leads.

### System Architecture

```
CRM Database → Campaign Service → Tata API → WhatsApp → Delivery Webhooks → CRM Updates
```

### Prerequisites

1. **Tata Omnichannel Setup**
   - Templates created and approved in Omnichannel
   - Templates imported to Smartflo with exact same names
   - WhatsApp number (+919355421616) associated with templates
   - "Use for WhatsApp" toggle enabled

2. **Environment Configuration**
   ```env
   TATA_AUTH_TOKEN=your-jwt-token-here
   TATA_BASE_URL=https://wb.omni.tatatelebusiness.com
   WHATSAPP_PHONE_NUMBER=+919355421616
   WHATSAPP_WEBHOOK_VERIFY_TOKEN=your-webhook-secret
   ```

### Campaign Execution Methods

#### Method 1: Web Interface
1. Navigate to `/whatsapp-campaigns/`
2. Configure campaign parameters:
   - **Projects**: Select target projects (or leave empty for all)
   - **Date Range**: IVR lead creation date range (max 90 days)
   - **Template**: Must exist in Tata Omnichannel
   - **Media**: Optional header media (validate URL and size)
   - **Limit**: Max messages per campaign (1-1000)
3. Use "Preview Leads" to download CSV preview
4. Enable "Dry Run" for testing
5. Click "Run Campaign"

#### Method 2: CLI Command
```bash
# Basic campaign
python manage.py whatsapp_campaign \
  --template-name "bop_realty_project_intro" \
  --from-date "2024-01-01" \
  --to-date "2024-01-07" \
  --limit 100 \
  --dry-run

# With project filtering and media
python manage.py whatsapp_campaign \
  --template-name "skyline_phoenix_launch" \
  --from-date "2024-01-01" \
  --to-date "2024-01-07" \
  --projects "Skyline Phoenix" "Eternia Towers" \
  --header-media-url "https://cdn.boprealty.com/brochure.jpg" \
  --header-media-type "image" \
  --limit 500 \
  --export-csv "campaign_results.csv"

# Production run (remove --dry-run)
python manage.py whatsapp_campaign \
  --template-name "bop_realty_project_intro" \
  --from-date "2024-01-01" \
  --to-date "2024-01-07" \
  --limit 100 \
  --force
```

### Template Requirements

#### Template Structure
Templates must be created in Tata Omnichannel with these exact specifications:

1. **Template Name**: No special characters, use underscores
2. **Language**: Must match campaign language parameter
3. **Variables**: Support up to 3 body variables:
   - `{{1}}` = Lead Name
   - `{{2}}` = Project Name  
   - `{{3}}` = Deep Link URL
4. **Buttons**: NO variables allowed in buttons (Omnichannel limitation)
5. **Header Media**: Use public URLs only

#### Example Template
```
Header: [Image from URL]
Body: Hi {{1}}, thank you for your interest in {{2}}. View details: {{3}}
Footer: Bop Realty - Your Dream Home Awaits
Buttons: [Call Now] [Visit Website]
```

### Media Validation

#### Supported Types & Limits
- **Images**: JPG, PNG - Max 5MB
- **Videos**: MP4, 3GP - Max 16MB  
- **Documents**: PDF - Max 100MB

#### Media URL Requirements
- Must be publicly accessible (HTTPS preferred)
- Content-Type header must match file type
- Content-Length header required for size validation
- CDN URLs recommended for performance

### Rate Limiting & Quality

#### Current Limits
- **WABA Tier**: 100,000 messages/24 hours
- **Quality Rating**: Medium
- **System Rate Limit**: 0.8 messages/second (safety buffer)

#### Quality Management
- Monitor quality rating in Tata panel
- Pause campaigns if quality drops to "Low"
- Implement exponential backoff on rate limit errors
- Respect opt-out requests immediately

### Error Handling

#### Common Errors & Solutions

| Error Code | Description | Solution |
|------------|-------------|----------|
| `ERR_TEMPLATE_NOT_READY` | Template not found/approved | Verify template exists in Omnichannel and Smartflo |
| `ERR_MEDIA_UNSUPPORTED` | Invalid media type/size | Check MIME type and file size limits |
| `ERR_BUTTON_VARIABLES_UNSUPPORTED` | Variables in buttons | Move dynamic URLs to body variables |
| `ERR_WHATSAPP_RATE_LIMIT` | Rate limit exceeded | Reduce sending rate, implement backoff |
| `ERR_QUALITY_DEGRADED` | Quality rating dropped | Pause campaign, review message content |

#### Webhook Failures
If delivery webhooks fail:
1. Check webhook URL accessibility
2. Verify signature validation
3. Monitor webhook logs: `/webhook/whatsapp/`
4. Manual status polling as fallback

### Monitoring & Analytics

#### Key Metrics
- **Delivery Rate**: Sent vs Delivered
- **Read Rate**: Delivered vs Read  
- **Failure Rate**: Failed vs Total Sent
- **Quality Score**: Monitor in Tata panel

#### Monitoring Endpoints
- Campaign Status: `/whatsapp-campaigns/status/`
- Analytics: `/whatsapp-campaigns/analytics/`
- Webhook Health: Check server logs

### Webhook Configuration

#### Tata Webhook Setup
1. **URL**: `https://yourdomain.com/webhook/whatsapp/`
2. **Verification**: Use `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
3. **Events**: Message status updates, incoming messages

#### Local Development
```bash
# Use ngrok for local testing
ngrok http 8000
# Configure webhook: https://abc123.ngrok.io/webhook/whatsapp/
```

### Security Best Practices

#### Token Management
- Rotate JWT tokens regularly
- Store tokens in environment variables only
- Enable 2FA in Tata Omni panel
- Monitor for token exposure in logs

#### Data Protection
- Mask phone numbers in UI previews
- Log minimal PII in application logs
- Implement proper access controls
- Regular security audits

### Troubleshooting Guide

#### Campaign Not Starting
1. Check template validation: `/api/validate-template/`
2. Verify date range (max 90 days)
3. Confirm leads exist in date range
4. Check DND list exclusions

#### Messages Not Sending
1. Verify JWT token validity
2. Check rate limiting delays
3. Validate phone number format (E.164)
4. Confirm template approval status

#### Delivery Status Not Updating
1. Check webhook endpoint accessibility
2. Verify signature validation
3. Monitor webhook processing logs
4. Confirm message ID matching

#### Media Validation Failing
1. Test URL accessibility with curl/wget
2. Check Content-Type and Content-Length headers
3. Verify file size within limits
4. Ensure HTTPS for security

### Maintenance Tasks

#### Daily
- Monitor campaign success rates
- Check quality rating in Tata panel
- Review failed message logs
- Verify webhook health

#### Weekly  
- Rotate JWT tokens if needed
- Clean up old message records
- Review template performance
- Update DND lists

#### Monthly
- Audit template usage and approval status
- Review media URL performance
- Analyze conversion rates by template
- Update documentation

### Emergency Procedures

#### Quality Rating Drop
1. **Immediate**: Pause all active campaigns
2. **Investigate**: Review recent message content and targeting
3. **Contact**: Tata support for quality review
4. **Resume**: Only after quality rating improves

#### Rate Limit Exceeded
1. **Immediate**: Implement exponential backoff
2. **Reduce**: Campaign batch sizes
3. **Spread**: Messages across longer time periods
4. **Monitor**: Rate limit recovery

#### Webhook Outage
1. **Fallback**: Manual status polling via API
2. **Queue**: Retry webhook deliveries
3. **Alert**: Development team for investigation
4. **Document**: Incident for post-mortem

### Contact Information

#### Tata Support
- **Technical**: Smartflo API documentation
- **Business**: Account manager for quality issues
- **Emergency**: 24/7 support for critical issues

#### Internal Team
- **Development**: For code/integration issues
- **Operations**: For campaign execution
- **Business**: For template content and strategy

---

**Last Updated**: January 2024  
**Version**: 1.0  
**Next Review**: March 2024