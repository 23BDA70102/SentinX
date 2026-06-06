# app.py - Smart Tourist Safety Monitoring System
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import hashlib
import json
import random
from datetime import datetime
import threading
import secrets
import time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Data storage
tourists = {}
incidents = {}

# ============================================================
# BLOCKCHAIN DIGITAL ID SYSTEM
# ============================================================
class BlockchainDigitalID:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()
    
    def create_genesis_block(self):
        genesis = {
            'index': 0,
            'timestamp': datetime.now().isoformat(),
            'data': {'type': 'GENESIS'},
            'previous_hash': '0',
            'hash': self.calculate_hash(0, datetime.now().isoformat(), {}, '0')
        }
        self.chain.append(genesis)
    
    def calculate_hash(self, index, timestamp, data, previous_hash):
        block_string = f"{index}{timestamp}{json.dumps(data)}{previous_hash}"
        return hashlib.sha256(block_string.encode()).hexdigest()[:16]
    
    def generate_digital_id(self, tourist_data):
        timestamp = datetime.now().isoformat()
        digital_id = {
            'id': f"DID-{secrets.token_hex(6).upper()}",
            'name': tourist_data['name'],
            'passport': tourist_data['passport'][-4:],
            'phone': tourist_data.get('phone', ''),
            'issued': timestamp,
            'status': 'ACTIVE'
        }
        block = {
            'index': len(self.chain),
            'timestamp': timestamp,
            'data': digital_id,
            'previous_hash': self.chain[-1]['hash'],
            'hash': self.calculate_hash(len(self.chain), timestamp, digital_id, self.chain[-1]['hash'])
        }
        self.chain.append(block)
        return digital_id
    
    def verify_id(self, digital_id):
        for block in self.chain:
            if block['data'].get('id') == digital_id:
                return True, block['data']
        return False, None

blockchain = BlockchainDigitalID()

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/digital-id')
def digital_id():
    return render_template('digital_id.html')

@app.route('/dashboard/police')
def police_dashboard():
    return render_template('police_dashboard.html')

@app.route('/dashboard/tourism')
def tourism_dashboard():
    return render_template('tourism_dashboard.html')

@app.route('/verify/<digital_id>')
def verify_tourist_id(digital_id):
    verified, data = blockchain.verify_id(digital_id)
    if verified:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>✓ Verified</title>
        <style>
            body {{ font-family: Arial; background: #0B1120; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
            .card {{ background: rgba(255,255,255,0.1); border-radius: 20px; padding: 30px; text-align: center; border: 1px solid #10B981; }}
            .verified {{ color: #10B981; font-size: 3rem; }}
        </style>
        </head>
        <body>
            <div class="card">
                <div class="verified">✓</div>
                <h2>VERIFIED</h2>
                <p>Digital ID: {digital_id}</p>
                <p>Name: {data.get('name', 'Unknown')}</p>
                <p>Passport: {data.get('passport', '****')}</p>
                <button onclick="window.close()">Close</button>
            </div>
        </body>
        </html>
        """
    else:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">
        <title>✗ Invalid</title>
        <style>
            body {{ font-family: Arial; background: #0B1120; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
            .card {{ background: rgba(255,255,255,0.1); border-radius: 20px; padding: 30px; text-align: center; border: 1px solid #EF4444; }}
            .invalid {{ color: #EF4444; font-size: 3rem; }}
        </style>
        </head>
        <body>
            <div class="card">
                <div class="invalid">✗</div>
                <h2>INVALID ID</h2>
                <p>ID could not be verified.</p>
                <button onclick="window.close()">Close</button>
            </div>
        </body>
        </html>
        """

# ============================================================
# API ROUTES
# ============================================================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    digital_id = blockchain.generate_digital_id(data)
    tourists[digital_id['id']] = digital_id
    return jsonify({'digital_id': digital_id['id'], 'message': 'ID Generated!'})

@app.route('/api/dashboard/stats', methods=['GET'])
def stats():
    return jsonify({'active_tourists': len(tourists), 'active_incidents': len(incidents)})

@app.route('/api/dashboard/incidents', methods=['GET'])
def get_incidents():
    incident_list = []
    for inc_id, inc in incidents.items():
        incident_list.append({
            'id': inc_id,
            'tourist_id': inc.get('tourist_id', 'Unknown'),
            'type': inc.get('type', 'Unknown'),
            'severity': inc.get('severity', 'CRITICAL'),
            'location': inc.get('location', 'Unknown'),
            'timestamp': inc.get('timestamp', datetime.now().isoformat())
        })
    return jsonify(incident_list)

@app.route('/api/dashboard/tourists', methods=['GET'])
def get_tourists():
    tourist_list = []
    for t_id, t in tourists.items():
        tourist_list.append({
            'id': t_id,
            'name': t['name'],
            'status': 'ACTIVE',
            'blockchain_id': t_id
        })
    return jsonify(tourist_list)

@app.route('/api/resolve-incident/<incident_id>', methods=['POST'])
def resolve(incident_id):
    if incident_id in incidents:
        del incidents[incident_id]
    return jsonify({'status': 'resolved'})

@app.route('/api/emergency', methods=['POST'])
def emergency():
    data = request.json
    incident_id = f"INC-{secrets.token_hex(4).upper()}"
    incidents[incident_id] = {
        'id': incident_id,
        'tourist_id': data.get('tourist_id', 'Unknown'),
        'type': data.get('type', 'SOS'),
        'severity': 'CRITICAL',
        'location': data.get('location', 'Unknown'),
        'timestamp': datetime.now().isoformat()
    }
    socketio.emit('emergency_alert', {'incident_id': incident_id})
    return jsonify({'status': 'alert_sent'})

@app.route('/api/safety-tips', methods=['GET'])
def tips():
    return jsonify({'tips': ['Keep digital ID handy', 'Share location', 'Use SOS in emergencies']})

@app.route('/api/ai-detect', methods=['POST'])
def ai_detect():
    data = request.json
    hr = data.get('heart_rate', 70)
    speed = data.get('velocity', 1.0)
    risk = 0
    if hr > 100:
        risk += 0.3
    if hr > 120:
        risk += 0.2
    if speed > 3:
        risk += 0.2
    if speed > 5:
        risk += 0.2
    risk = min(1.0, risk)
    level = "CRITICAL" if risk > 0.7 else ("ELEVATED" if risk > 0.4 else "NORMAL")
    return jsonify({'risk_score': risk, 'threat_level': level, 'anomalies': []})

@app.route('/api/get-ip', methods=['GET'])
def get_ip():
    return jsonify({'ip': 'render.com', 'success': True})

# ============================================================
# BACKGROUND ALERTS
# ============================================================

def generate_alerts():
    while True:
        time.sleep(10)
        if random.random() < 0.3:
            alert_id = f"INC-{secrets.token_hex(4).upper()}"
            incidents[alert_id] = {
                'id': alert_id,
                'tourist_id': f"DID-{secrets.token_hex(4).upper()}",
                'type': random.choice(['SOS', 'Medical', 'Lost']),
                'severity': 'CRITICAL',
                'location': f"Zone {random.randint(1,5)}",
                'timestamp': datetime.now().isoformat()
            }
            socketio.emit('emergency_alert', {'incident_id': alert_id})

threading.Thread(target=generate_alerts, daemon=True).start()

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 50)
    print("Smart Tourist Safety System Running!")
    print("=" * 50)
    print(f"Access at: http://0.0.0.0:{port}")
    print("=" * 50)
    socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
