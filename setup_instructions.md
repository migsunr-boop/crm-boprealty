# Tata Chat Panel Setup

## Quick Setup:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your auth token:**
   - Edit `webhook_server.py`
   - Replace `"YOUR_AUTH_TOKEN_HERE"` with your actual Tata API token

3. **Run the server:**
   ```bash
   python webhook_server.py
   ```

4. **Access the panel:**
   - Open browser: `http://localhost:5000`

## Webhook Configuration:

Configure these webhook URLs in your Tata dashboard:
- **WhatsApp Messages:** `http://your-domain.com/webhook`
- **RCS Messages:** `http://your-domain.com/webhook`

## Features:

- ✅ View all previous conversations
- ✅ Real-time message updates
- ✅ Send replies directly from CRM
- ✅ Support for both WhatsApp and RCS
- ✅ Auto-refresh every 5 seconds

## API Endpoints:

- `GET /api/conversations` - Get all conversations
- `POST /api/send-reply` - Send reply to customer
- `POST /webhook` - Receive incoming messages