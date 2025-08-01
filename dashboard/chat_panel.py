import requests
import json
from datetime import datetime

class TataChatPanel:
    def __init__(self, auth_token):
        self.auth_token = auth_token
        self.base_url = "https://wb.omni.tatatelebusiness.com"
        self.headers = {"Authorization": f"Bearer {auth_token}"}
        self.conversations = {}
    
    def webhook_handler(self, payload):
        """Handle incoming messages from webhook"""
        if "messages" in payload:
            msg = payload["messages"]
            phone = msg["from"]
            text = msg.get("text", {}).get("body", "")
            timestamp = msg["timestamp"]
            
            if phone not in self.conversations:
                self.conversations[phone] = []
            
            self.conversations[phone].append({
                "id": msg["id"],
                "text": text,
                "timestamp": timestamp,
                "type": "incoming",
                "sender": phone
            })
    
    def send_reply(self, phone_number, message_text):
        """Send reply via session message API"""
        url = f"{self.base_url}/whatsapp-cloud/messages"
        payload = {
            "to": phone_number,
            "type": "text",
            "source": "crm",
            "text": {"body": message_text}
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            # Add to conversation history
            if phone_number not in self.conversations:
                self.conversations[phone_number] = []
            
            self.conversations[phone_number].append({
                "id": response.json().get("id"),
                "text": message_text,
                "timestamp": str(int(datetime.now().timestamp())),
                "type": "outgoing",
                "sender": "agent"
            })
            return True
        return False
    
    def get_conversations(self):
        """Get all conversations"""
        return self.conversations
    
    def get_conversation(self, phone_number):
        """Get specific conversation"""
        return self.conversations.get(phone_number, [])