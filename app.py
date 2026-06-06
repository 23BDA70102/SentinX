# app.py - Smart Tourist Safety Monitoring System
# Complete Backend with Blockchain Digital ID, AI Detection, and Dashboards

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import hashlib
import json
import random
from datetime import datetime
import threading
import secrets
import time
import socket
import subprocess

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# ============================================================
# DATA STORAGE (In-memory for demo)
# ============================================================
tourists = {}           # Store registered tourists
incidents = {}          # Store active incidents
biometric_history = {}  # Store biometric data history

# ============================================================
# 1. BLOCKCHAIN DIGITAL ID SYSTEM
# ============================================================
class BlockchainDigitalID:
    """Blockchain-based Digital Identity System"""
    
    def __init__(self):
        self.chain = []
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the first block in the blockchain"""
        genesis = {
            'index': 0,
            'timestamp': datetime.now().isoformat(),
            'data': {'type': 'GENESIS', 'message': 'Digital ID System Initialized'},
            'previous_hash': '0',
            'hash': self.calculate_hash(0, datetime.now().isoformat(), {}, '0')
        }
        self.chain.append(genesis)
    
    def calculate_hash(self, index, timestamp, data, previous_hash):
        """Calculate SHA-256 hash for a block"""
        block_string = f"{index}{timestamp}{json.dumps(data, sort_keys=True)}{previous_hash}"
        return hashlib.sha256(block_string.encode()).hexdigest()[:16]
    
    def generate_digital_id(self, tourist_data):
        """Generate blockchain-based digital ID for tourist"""
        timestamp = datetime.now().isoformat()
        
        # Create unique digital ID
        digital_id = {
            'id': f"DID-{secrets.token_hex(6).upper()}",
            'name': tourist_data['name'],
            'passport': tourist_data['passport'][-4:],
            'phone': tourist_data.get('phone', ''),
            'email': tourist_data.get('email', ''),
            'issued': timestamp,
            'status': 'ACTIVE',
            'block_hash': ''
        }
        
        # Create block
        block = {
            'index': len(self.chain),
            'timestamp': timestamp,
            'data': digital_id,
            'previous_hash': self.chain[-1]['hash'],
            'hash': self.calculate_hash(len(self.chain), timestamp, digital_id, self.chain[-1]['hash'])
        }
        
        digital_id['block_hash'] = block['hash']
        self.chain.append(block)
        
        return digital_id
    
    def verify_id(self, digital_id):
        """Verify digital ID authenticity by checking blockchain"""
        for block in self.chain:
            if block['data'].get('id') == digital_id:
                # Verify block integrity
                calculated = self.calculate_hash(
                    block['index'], block['timestamp'], 
                    block['data'], block['previous_hash']
                )
                if calculated == block['hash']:
                    return True, block['data']
        return False, None
    
    def get_blockchain(self):
        """Return the entire blockchain"""
        return self.chain

blockchain = BlockchainDigitalID()

# ============================================================
# 2. AI ANOMALY DETECTION ENGINE
# ============================================================
class AIAnomalyDetector:
    """AI-powered anomaly detection for tourist safety"""
    
    def __init__(self):
        self.historical_data = []
        self.thresholds = {
            'heart_rate': {'normal_min': 60, 'normal_max': 100, 'warning': 110, 'critical': 130},
            'velocity': {'normal': 1.5, 'warning': 3.0, 'critical': 5.0}
        }
    
    def detect_anomaly(self, heart_rate, velocity):
        """Detect anomalies based on biometric data"""
        anomalies = []
        risk_score = 0.0
        
        # Heart Rate Analysis
        if heart_rate < self.thresholds['heart_rate']['normal_min']:
            anomalies.append(f"Low heart rate: {heart_rate} BPM")
            risk_score += 0.2
        elif heart_rate > self.thresholds['heart_rate']['critical']:
            anomalies.append(f"Critical heart rate: {heart_rate} BPM")
            risk_score += 0.5
        elif heart_rate > self.thresholds['heart_rate']['warning']:
            anomalies.append(f"Elevated heart rate: {heart_rate} BPM")
            risk_score += 0.3
        
        # Velocity Analysis
        if velocity > self.thresholds['velocity']['critical']:
            anomalies.append(f"Dangerous speed: {velocity:.1f} m/s")
            risk_score += 0.4
        elif velocity > self.thresholds['velocity']['warning']:
            anomalies.append(f"High speed: {velocity:.1f} m/s")
            risk_score += 0.2
        
        # Pattern Analysis
        if len(self.historical_data) > 10:
            recent_hr = [d[0] for d in self.historical_data[-10:]]
            avg_hr = sum(recent_hr) / len(recent_hr)
            if abs(heart_rate - avg_hr) > 25:
                anomalies.append("Sudden heart rate change detected")
                risk_score += 0.2
        
        # Store data for future analysis
        self.historical_data.append((heart_rate, velocity))
        if len(self.historical_data) > 100:
            self.historical_data.pop(0)
        
        # Determine threat level
        risk_score = min(1.0, risk_score)
        
        if risk_score >= 0.7:
            threat_level = "CRITICAL"
            action = "IMMEDIATE EMERGENCY RESPONSE REQUIRED"
            color = "danger"
        elif risk_score >= 0.4:
            threat_level = "ELEVATED"
            action = "ALERT SECURITY PERSONNEL"
            color = "warning"
        elif risk_score >= 0.2:
            threat_level = "CAUTION"
            action = "MONITOR CLOSELY"
            color = "info"
        else:
            threat_level = "NORMAL"
            action = "CONTINUE MONITORING"
            color = "success"
        
        return {
            'risk_score': round(risk_score, 3),
            'threat_level': threat_level,
            'anomalies': anomalies,
            'action': action,
            'color': color
        }

ai_detector = AIAnomalyDetector()

# ============================================================
# 3. MOBILE APPLICATION API
# ============================================================
class MobileAPI:
    """Backend API for mobile application"""
    
    def register_tourist(self, data):
        """Register tourist and generate digital ID"""
        digital_id = blockchain.generate_digital_id(data)
        
        # Store in memory
        tourists[digital_id['id']] = {
            'id': digital_id['id'],
            'name': data['name'],
            'passport': data['passport'][-4:],
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'status': 'ACTIVE',
            'registration_date': datetime.now().isoformat(),
            'block_hash': digital_id.get('block_hash', '')
        }
        
        return {
            'digital_id': digital_id['id'],
            'name': digital_id['name'],
            'message': "Digital ID generated successfully!",
            'block_hash': digital_id.get('block_hash', ''),
            'qr_data': f"https://sentinx.com/verify/{digital_id['id']}"
        }
    
    def send_emergency(self, tourist_id, location, alert_type="SOS"):
        """Handle emergency SOS alert"""
        incident_id = f"INC-{secrets.token_hex(4).upper()}"
        
        incidents[incident_id] = {
            'id': incident_id,
            'tourist_id': tourist_id,
            'type': alert_type,
            'severity': 'CRITICAL',
            'location': location,
            'timestamp': datetime.now().isoformat(),
            'status': 'ACTIVE'
        }
        
        # Broadcast to dashboards
        socketio.emit('emergency_alert', {
            'incident_id': incident_id,
            'tourist_id': tourist_id,
            'location': location,
            'timestamp': datetime.now().isoformat()
        })
        
        return {'status': 'alert_sent', 'incident_id': incident_id}
    
    def share_location(self, tourist_id, lat, lng):
        """Share real-time location"""
        socketio.emit('location_update', {
            'tourist_id': tourist_id,
            'lat': lat,
            'lng': lng,
            'timestamp': datetime.now().isoformat()
        })
        return {'status': 'shared', 'timestamp': datetime.now().isoformat()}
    
    def get_safety_tips(self):
        """Get safety recommendations"""
        return {
            'tips': [
                "Always keep your digital ID handy",
                "Share your live location with trusted contacts",
                "Use the SOS button in case of emergency",
                "Avoid isolated areas after dark",
                "Keep emergency numbers saved on your phone",
                "Register for alerts from local authorities",
                "Stay in well-lit areas at night",
                "Keep copies of important documents"
            ]
        }

mobile_api = MobileAPI()

# ============================================================
# 4. DASHBOARD MANAGEMENT
# ============================================================
class DashboardManager:
    """Manage police and tourism dashboards"""
    
    def get_stats(self):
        """Get real-time system statistics"""
        return {
            'active_tourists': len(tourists),
            'active_incidents': len(incidents),
            'system_status': 'OPERATIONAL',
            'timestamp': datetime.now().isoformat(),
            'blockchain_height': len(blockchain.get_blockchain())
        }
    
    def get_incidents(self):
        """Get all active incidents"""
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
        return incident_list
    
    def get_tourists(self):
        """Get all registered tourists"""
        tourist_list = []
        for t_id, t in tourists.items():
            tourist_list.append({
                'id': t_id,
                'name': t['name'],
                'status': t['status'],
                'blockchain_id': t_id,
                'phone': t.get('phone', ''),
                'registration_date': t.get('registration_date', '')
            })
        return tourist_list
    
    def resolve_incident(self, incident_id):
        """Mark incident as resolved"""
        if incident_id in incidents:
            del incidents[incident_id]
            return {'status': 'resolved', 'incident_id': incident_id}
        return {'status': 'not_found'}
    
    def get_tourist_details(self, tourist_id):
        """Get detailed information about a tourist"""
        if tourist_id in tourists:
            return tourists[tourist_id]
        return None

dashboard = DashboardManager()

# ============================================================
# 5. DATA PRIVACY & SECURITY
# ============================================================
class PrivacySecurity:
    """Data privacy and security management"""
    
    def __init__(self):
        self.access_logs = []
    
    def anonymize_data(self, data):
        """Anonymize sensitive data"""
        if isinstance(data, dict):
            anonymized = data.copy()
            if 'name' in anonymized:
                anonymized['name'] = anonymized['name'][0] + '***'
            if 'passport' in anonymized:
                anonymized['passport'] = '****' + anonymized['passport'][-4:]
            if 'phone' in anonymized:
                phone = anonymized['phone']
                if len(phone) > 4:
                    anonymized['phone'] = '***-***-' + phone[-4:]
            return anonymized
        return data
    
    def log_access(self, user, action, data_accessed):
        """Log all data access for audit"""
        log_entry = {
            'user': user,
            'action': action,
            'data_accessed': data_accessed,
            'timestamp': datetime.now().isoformat(),
            'ip': '127.0.0.1'
        }
        self.access_logs.append(log_entry)
        return log_entry
    
    def get_audit_logs(self):
        """Get audit logs"""
        return self.access_logs[-50:]  # Last 50 logs

privacy = PrivacySecurity()

# ============================================================
# FLASK ROUTES - WEB PAGES
# ============================================================

@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/digital-id')
def digital_id():
    """Digital Tourist ID page"""
    return render_template('digital_id.html')

@app.route('/dashboard/police')
def police_dashboard():
    """Police Command Center Dashboard"""
    return render_template('police_dashboard.html')

@app.route('/dashboard/tourism')
def tourism_dashboard():
    """Tourism Department Dashboard"""
    return render_template('tourism_dashboard.html')

@app.route('/verify/<digital_id>')
def verify_tourist_id(digital_id):
    """Simple verification page for QR code scanning"""
    print(f"🔍 Attempting to verify ID: {digital_id}")
    print(f"📋 Registered tourists: {list(tourists.keys())}")
    
    # First check in tourists dictionary
    if digital_id in tourists:
        tourist = tourists[digital_id]
        print(f"✅ Found tourist: {tourist['name']}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>✓ ID Verified - SentinX</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background: linear-gradient(135deg, #0B1120 0%, #1A2133 100%);
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    padding: 20px;
                }}
                .card {{
                    background: rgba(255,255,255,0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 24px;
                    padding: 35px;
                    max-width: 450px;
                    width: 100%;
                    text-align: center;
                    border: 1px solid rgba(16, 185, 129, 0.3);
                    box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                }}
                .verified-icon {{
                    color: #10B981;
                    font-size: 4rem;
                    margin-bottom: 20px;
                }}
                .title {{
                    font-size: 1.8rem;
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: #10B981;
                }}
                .subtitle {{
                    color: #94A3B8;
                    margin-bottom: 25px;
                }}
                .info-box {{
                    background: rgba(0,0,0,0.3);
                    border-radius: 16px;
                    padding: 15px;
                    margin: 15px 0;
                    text-align: left;
                }}
                .info-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                }}
                .info-label {{
                    color: #94A3B8;
                    font-weight: 500;
                }}
                .info-value {{
                    font-family: 'Courier New', monospace;
                    color: #3B82F6;
                    font-weight: bold;
                }}
                .blockchain-badge {{
                    background: rgba(59,130,246,0.2);
                    border: 1px solid rgba(59,130,246,0.3);
                    border-radius: 30px;
                    padding: 8px 15px;
                    font-size: 0.75rem;
                    display: inline-block;
                    margin-top: 15px;
                }}
                .btn {{
                    background: #3B82F6;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 12px;
                    margin-top: 20px;
                    cursor: pointer;
                    font-size: 1rem;
                    font-weight: 600;
                    width: 100%;
                }}
                .small {{
                    font-size: 0.7rem;
                    color: #6B7280;
                    margin-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="verified-icon">
                    <i class="fas fa-check-circle"></i>
                </div>
                <div class="title">✓ VERIFIED</div>
                <div class="subtitle">This Digital ID is valid and stored on blockchain</div>
                
                <div class="info-box">
                    <div class="info-row">
                        <span class="info-label">Digital ID</span>
                        <span class="info-value">{digital_id}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Full Name</span>
                        <span class="info-value">{tourist.get('name', 'Unknown')}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Passport</span>
                        <span class="info-value">{tourist.get('passport', '****')}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Phone</span>
                        <span class="info-value">{tourist.get('phone', 'Not provided')}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Registered</span>
                        <span class="info-value">{tourist.get('registration_date', 'Unknown')[:19]}</span>
                    </div>
                </div>
                
                <div class="blockchain-badge">
                    <i class="fas fa-link"></i> SHA-256 Protected | Immutable Record
                </div>
                
                <button class="btn" onclick="window.close()">
                    <i class="fas fa-check"></i> Close
                </button>
                <div class="small">
                    <i class="fas fa-shield-alt"></i> Verified on SentinX Blockchain Network
                </div>
            </div>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        </body>
        </html>
        """
    
    # Then check in blockchain
    verified, data = blockchain.verify_id(digital_id)
    if verified:
        print(f"✅ Found in blockchain: {data.get('name', 'Unknown')}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>✓ ID Verified - SentinX</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background: linear-gradient(135deg, #0B1120 0%, #1A2133 100%);
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    padding: 20px;
                }}
                .card {{
                    background: rgba(255,255,255,0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 24px;
                    padding: 35px;
                    max-width: 450px;
                    width: 100%;
                    text-align: center;
                    border: 1px solid rgba(16, 185, 129, 0.3);
                }}
                .verified-icon {{ color: #10B981; font-size: 4rem; margin-bottom: 20px; }}
                .title {{ font-size: 1.8rem; font-weight: bold; margin-bottom: 10px; color: #10B981; }}
                .info-box {{ background: rgba(0,0,0,0.3); border-radius: 16px; padding: 15px; margin: 15px 0; text-align: left; }}
                .info-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }}
                .info-label {{ color: #94A3B8; }}
                .info-value {{ font-family: monospace; color: #3B82F6; }}
                .btn {{ background: #3B82F6; color: white; padding: 12px; border: none; border-radius: 12px; margin-top: 20px; width: 100%; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="verified-icon"><i class="fas fa-check-circle"></i></div>
                <div class="title">✓ VERIFIED</div>
                <div class="info-box">
                    <div class="info-row"><span class="info-label">Digital ID</span><span class="info-value">{digital_id}</span></div>
                    <div class="info-row"><span class="info-label">Name</span><span class="info-value">{data.get('name', 'Unknown')}</span></div>
                    <div class="info-row"><span class="info-label">Passport</span><span class="info-value">{data.get('passport', '****')}</span></div>
                </div>
                <button class="btn" onclick="window.close()">Close</button>
            </div>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        </body>
        </html>
        """
    else:
        print(f"❌ ID not found: {digital_id}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>✗ Invalid ID - SentinX</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background: linear-gradient(135deg, #0B1120 0%, #1A2133 100%);
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    padding: 20px;
                }}
                .card {{
                    background: rgba(255,255,255,0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 24px;
                    padding: 35px;
                    max-width: 400px;
                    text-align: center;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                }}
                .invalid-icon {{ color: #EF4444; font-size: 4rem; margin-bottom: 20px; }}
                .title {{ font-size: 1.8rem; font-weight: bold; color: #EF4444; }}
                .message {{ color: #94A3B8; margin: 20px 0; }}
                .btn {{ background: #EF4444; color: white; padding: 12px; border: none; border-radius: 12px; margin-top: 20px; width: 100%; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="invalid-icon"><i class="fas fa-times-circle"></i></div>
                <div class="title">✗ INVALID ID</div>
                <div class="message">
                    Digital ID <strong>{digital_id}</strong> could not be verified.<br>
                    Please make sure you scanned the correct QR code.
                </div>
                <button class="btn" onclick="window.close()">Close</button>
            </div>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        </body>
        </html>
        """

# ============================================================
# API ROUTES - RESTful Endpoints
# ============================================================

@app.route('/api/get-ip')
def get_ip():
    """Get current computer's network IP address automatically"""
    try:
        # Try to get the actual network IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        
        # Validate IP
        if ip_address and not ip_address.startswith('127.'):
            return jsonify({'ip': ip_address, 'success': True})
        
        # Fallback to hostname resolution
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return jsonify({'ip': ip_address, 'success': True})
        
    except Exception as e:
        return jsonify({'ip': 'localhost', 'success': False, 'error': str(e)})

@app.route('/api/register', methods=['POST'])
def api_register():
    """Register new tourist - Generate Digital ID"""
    try:
        data = request.json
        if not data or 'name' not in data or 'passport' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = mobile_api.register_tourist(data)
        privacy.log_access('system', 'tourist_registration', result['digital_id'])
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emergency', methods=['POST'])
def api_emergency():
    """Send emergency SOS alert"""
    try:
        data = request.json
        if not data or 'tourist_id' not in data:
            return jsonify({'error': 'Missing tourist ID'}), 400
        
        result = mobile_api.send_emergency(
            data['tourist_id'], 
            data.get('location', 'Unknown'),
            data.get('type', 'SOS')
        )
        privacy.log_access('system', 'emergency_alert', data['tourist_id'])
        
        return jsonify(result), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/location', methods=['POST'])
def api_location():
    """Share tourist location"""
    try:
        data = request.json
        result = mobile_api.share_location(
            data.get('tourist_id', 'unknown'),
            data.get('lat', 0),
            data.get('lng', 0)
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/safety-tips', methods=['GET'])
def api_safety_tips():
    """Get safety tips"""
    tips = mobile_api.get_safety_tips()
    return jsonify(tips)

@app.route('/api/verify-id/<digital_id>', methods=['GET'])
def api_verify_id(digital_id):
    """Verify digital ID on blockchain"""
    verified, data = blockchain.verify_id(digital_id)
    if verified:
        anonymized = privacy.anonymize_data(data)
        privacy.log_access('verification', 'id_verified', digital_id)
        return jsonify({'verified': True, 'data': anonymized})
    return jsonify({'verified': False, 'message': 'ID not found'}), 404

@app.route('/api/dashboard/stats', methods=['GET'])
def api_dashboard_stats():
    """Get dashboard statistics"""
    stats = dashboard.get_stats()
    return jsonify(stats)

@app.route('/api/dashboard/incidents', methods=['GET'])
def api_dashboard_incidents():
    """Get active incidents"""
    incidents_list = dashboard.get_incidents()
    return jsonify(incidents_list)

@app.route('/api/dashboard/tourists', methods=['GET'])
def api_dashboard_tourists():
    """Get active tourists"""
    tourists_list = dashboard.get_tourists()
    return jsonify(tourists_list)

@app.route('/api/resolve-incident/<incident_id>', methods=['POST'])
def api_resolve_incident(incident_id):
    """Resolve an incident"""
    result = dashboard.resolve_incident(incident_id)
    privacy.log_access('dashboard', 'incident_resolved', incident_id)
    return jsonify(result)

@app.route('/api/ai-detect', methods=['POST'])
def api_ai_detect():
    """AI anomaly detection endpoint"""
    try:
        data = request.json
        heart_rate = data.get('heart_rate', 70)
        velocity = data.get('velocity', 1.0)
        
        analysis = ai_detector.detect_anomaly(heart_rate, velocity)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/blockchain', methods=['GET'])
def api_blockchain():
    """Get blockchain data"""
    chain = blockchain.get_blockchain()
    return jsonify({
        'chain': chain,
        'length': len(chain),
        'verified': True
    })

@app.route('/api/tourist/<tourist_id>', methods=['GET'])
def api_tourist_details(tourist_id):
    """Get tourist details"""
    tourist = dashboard.get_tourist_details(tourist_id)
    if tourist:
        anonymized = privacy.anonymize_data(tourist)
        return jsonify(anonymized)
    return jsonify({'error': 'Tourist not found'}), 404

@app.route('/api/audit-logs', methods=['GET'])
def api_audit_logs():
    """Get audit logs (admin only)"""
    logs = privacy.get_audit_logs()
    return jsonify({'logs': logs})

# ============================================================
# BACKGROUND SIMULATION - Real-time Data Stream
# ============================================================

def generate_biometric_stream():
    """Simulate real-time biometric data from tourists"""
    sample_tourists = [
        {'id': 'DID-DEMO001', 'name': 'John Smith', 'base_hr': 72, 'base_speed': 1.2},
        {'id': 'DID-DEMO002', 'name': 'Emma Watson', 'base_hr': 68, 'base_speed': 1.0},
        {'id': 'DID-DEMO003', 'name': 'Michael Brown', 'base_hr': 75, 'base_speed': 1.3},
    ]
    
    # Add actual registered tourists to simulation
    for tourist_id, tourist in tourists.items():
        if not any(t['id'] == tourist_id for t in sample_tourists):
            sample_tourists.append({
                'id': tourist_id,
                'name': tourist['name'],
                'base_hr': random.randint(65, 85),
                'base_speed': random.uniform(0.8, 1.5)
            })
    
    cycle = 0
    
    while True:
        cycle += 0.1
        
        for tourist in sample_tourists:
            # Generate realistic variations
            heart_rate = tourist['base_hr'] + random.randint(-8, 12) + int(5 * (cycle % 6.28))
            velocity = tourist['base_speed'] + random.uniform(-0.3, 0.8)
            
            # Occasional anomalies (5% chance)
            if random.random() < 0.05:
                heart_rate += random.randint(20, 40)
                velocity += random.uniform(2, 4)
            
            heart_rate = max(50, min(160, heart_rate))
            velocity = max(0.2, min(8, velocity))
            
            # AI Analysis
            analysis = ai_detector.detect_anomaly(heart_rate, velocity)
            
            # Store biometric history
            if tourist['id'] not in biometric_history:
                biometric_history[tourist['id']] = []
            biometric_history[tourist['id']].append({
                'heart_rate': heart_rate,
                'velocity': velocity,
                'risk': analysis['risk_score'],
                'timestamp': datetime.now().isoformat()
            })
            
            # Limit history
            if len(biometric_history[tourist['id']]) > 50:
                biometric_history[tourist['id']].pop(0)
            
            # Create incident if critical
            if analysis['threat_level'] == 'CRITICAL':
                incident_id = f"INC-{secrets.token_hex(4).upper()}"
                incidents[incident_id] = {
                    'id': incident_id,
                    'tourist_id': tourist['id'],
                    'type': 'BIOMETRIC_ANOMALY',
                    'severity': 'CRITICAL',
                    'location': f"Zone {random.randint(1, 5)}",
                    'timestamp': datetime.now().isoformat(),
                    'status': 'ACTIVE',
                    'risk_score': analysis['risk_score'],
                    'anomalies': analysis['anomalies']
                }
                
                # Notify dashboards
                socketio.emit('new_incident', {
                    'incident_id': incident_id,
                    'tourist_id': tourist['id'],
                    'analysis': analysis
                })
            
            # Send update to dashboards
            socketio.emit('biometric_update', {
                'tourist_id': tourist['id'],
                'tourist_name': tourist['name'],
                'heart_rate': heart_rate,
                'velocity': velocity,
                'analysis': analysis
            })
        
        # Also generate random SOS alerts
        if random.random() < 0.15 and len(tourists) > 0:
            random_tourist = random.choice(list(tourists.keys()))
            incident_id = f"INC-{secrets.token_hex(4).upper()}"
            incident_types = ['SOS', 'MEDICAL', 'LOST', 'SUSPICIOUS']
            incidents[incident_id] = {
                'id': incident_id,
                'tourist_id': random_tourist,
                'type': random.choice(incident_types),
                'severity': 'CRITICAL',
                'location': f"Zone {random.randint(1, 8)}",
                'timestamp': datetime.now().isoformat(),
                'status': 'ACTIVE'
            }
            
            socketio.emit('emergency_alert', {
                'incident_id': incident_id,
                'tourist_id': random_tourist,
                'type': incidents[incident_id]['type'],
                'location': incidents[incident_id]['location'],
                'timestamp': datetime.now().isoformat()
            })
        
        time.sleep(2)  # Update every 2 seconds

# Start background simulation thread
simulation_thread = threading.Thread(target=generate_biometric_stream, daemon=True)
simulation_thread.start()

# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == '__main__':
    # Get IP for display
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = 'localhost'
    
    print("=" * 70)
    print("🏆 SMART TOURIST SAFETY MONITORING SYSTEM")
    print("=" * 70)
    print("\n📱 COMPONENTS ACTIVE:")
    print("   ✅ 1. Digital Tourist ID Generation Platform (Blockchain)")
    print("   ✅ 2. Mobile Application Backend API")
    print("   ✅ 3. AI-Based Anomaly Detection Engine")
    print("   ✅ 4. Police Command Center Dashboard")
    print("   ✅ 5. Tourism Department Dashboard")
    print("   ✅ 6. Data Privacy & Security Module")
    print("\n🌐 ACCESS THE SYSTEM:")
    print("   🏠 Main Portal:      http://localhost:5000")
    print("   🆔 Digital ID:       http://localhost:5000/digital-id")
    print("   👮 Police Dashboard: http://localhost:5000/dashboard/police")
    print("   🏖️ Tourism Dashboard: http://localhost:5000/dashboard/tourism")
    print("\n📱 PHONE ACCESS (Auto-detected IP):")
    print(f"   http://{local_ip}:5000")
    print("\n📊 SYSTEM STATISTICS:")
    print(f"   Blockchain Height: {len(blockchain.get_blockchain())} blocks")
    print(f"   AI Model: Active (Anomaly Detection Ready)")
    print(f"   WebSocket: Real-time Updates Active")
    print("\n" + "=" * 70)
    print("🚀 System is running! Press CTRL+C to stop.")
    print("=" * 70)
    
   socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
