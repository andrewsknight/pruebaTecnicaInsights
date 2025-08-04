
"""Simple webhook receiver for testing Call Assignment System"""

import os
import json
from datetime import datetime
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI(title="Webhook Receiver")
received_webhooks = []

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        payload = await request.json()
        webhook_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload
        }
        received_webhooks.append(webhook_data)
        if len(received_webhooks) > 1000:
            received_webhooks.pop(0)
        event_type = payload.get("event_type", "unknown")
        print(f"[{datetime.utcnow()}] Received webhook: {event_type}")
        return {"status": "received", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"status": "error", "message": str(e)}, 400

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
