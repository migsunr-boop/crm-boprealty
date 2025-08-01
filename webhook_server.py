from flask import Flask, request, jsonify, render_template_string
from chat_panel import TataChatPanel
import hashlib
import hmac

app = Flask(__name__)
chat_panel = TataChatPanel("YOUR_AUTH_TOKEN_HERE")

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive WhatsApp/RCS webhooks"""
    payload = request.json
    
    # Validate webhook signature (optional but recommended)
    signature = request.headers.get('x-hub-signature-256')
    if signature:
        # Validate signature here if needed
        pass
    
    # Process incoming message
    chat_panel.webhook_handler(payload)
    return jsonify({"status": "ok"})

@app.route('/api/conversations')
def get_conversations():
    """API to get all conversations"""
    return jsonify(chat_panel.get_conversations())

@app.route('/api/send-reply', methods=['POST'])
def send_reply():
    """API to send reply"""
    data = request.json
    phone = data.get('phone')
    message = data.get('message')
    
    success = chat_panel.send_reply(phone, message)
    return jsonify({"success": success})

@app.route('/')
def index():
    """Serve the chat UI"""
    with open('chat_ui.html', 'r') as f:
        return f.read()

if __name__ == '__main__':
    app.run(debug=True, port=5000)