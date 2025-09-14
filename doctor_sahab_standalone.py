#!/usr/bin/env python3
"""
Standalone Doctor Sahab application - No external dependencies required!
This version uses only Python standard library to avoid all compilation issues.
"""

import json
import sqlite3
import re
import math
import os
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class DoctorSahabDB:
    """Simple database class using SQLite directly."""
    
    def __init__(self, db_path="doctor_sahab.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                display_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                sender TEXT NOT NULL CHECK (sender IN ('user','bot')),
                text TEXT NOT NULL,
                suggested_tests TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                test_name TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('suggested','in_progress','completed')),
                suggested_by_message_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                result_json TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Seed with sample hospitals
        cursor.execute('SELECT COUNT(*) FROM facilities')
        if cursor.fetchone()[0] == 0:
            hospitals = [
                ("City General Hospital", "123 Main Street, Downtown", 40.7128, -74.0060, "manual"),
                ("Metro Medical Center", "456 Oak Avenue, Midtown", 40.7589, -73.9851, "manual"),
                ("University Hospital", "789 University Drive, Uptown", 40.7505, -73.9934, "manual"),
                ("Community Health Center", "321 Elm Street, Suburbs", 40.6892, -74.0445, "manual"),
                ("Emergency Care Hospital", "654 Pine Street, East Side", 40.7282, -73.9942, "manual")
            ]
            cursor.executemany(
                "INSERT INTO facilities (name, address, lat, lng, source) VALUES (?, ?, ?, ?, ?)",
                hospitals
            )
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    
    def save_message(self, session_id, sender, text, suggested_tests=None):
        """Save a message to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        suggested_tests_json = json.dumps(suggested_tests) if suggested_tests else None
        
        cursor.execute(
            "INSERT INTO messages (session_id, sender, text, suggested_tests) VALUES (?, ?, ?, ?)",
            (session_id, sender, text, suggested_tests_json)
        )
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return message_id
    
    def get_chat_history(self, session_id):
        """Get chat history for a session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT sender, text, suggested_tests, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp ASC",
            (session_id,)
        )
        
        messages = []
        for row in cursor.fetchall():
            suggested_tests = json.loads(row[2]) if row[2] else None
            messages.append({
                "sender": row[0],
                "text": row[1],
                "suggested_tests": suggested_tests,
                "timestamp": row[3]
            })
        
        conn.close()
        return messages
    
    def save_test_suggestions(self, session_id, test_names, message_id):
        """Save test suggestions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for test_name in test_names:
            cursor.execute(
                "INSERT INTO tests (session_id, test_name, status, suggested_by_message_id) VALUES (?, ?, ?, ?)",
                (session_id, test_name, "suggested", message_id)
            )
        
        conn.commit()
        conn.close()
    
    def find_nearby_hospital(self, lat, lng):
        """Find the nearest hospital using simple distance calculation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, address, lat, lng FROM facilities")
        facilities = cursor.fetchall()
        conn.close()
        
        if not facilities:
            return None
        
        # Simple distance calculation (approximation)
        def calculate_distance(lat1, lng1, lat2, lng2):
            # Convert to radians
            lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
            # Haversine formula
            dlat = lat2 - lat1
            dlng = lng2 - lng1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
            c = 2 * math.asin(math.sqrt(a))
            # Radius of earth in meters
            r = 6371000
            return c * r
        
        nearest = None
        min_distance = float('inf')
        
        for facility in facilities:
            distance = calculate_distance(lat, lng, facility[2], facility[3])
            if distance < min_distance:
                min_distance = distance
                nearest = {
                    "name": facility[0],
                    "address": facility[1],
                    "lat": facility[2],
                    "lng": facility[3],
                    "distance_meters": round(distance, 2)
                }
        
        return nearest

class DoctorSahabAI:
    """Simple AI responder using only standard library."""
    
    def __init__(self):
        self.intent_patterns = {
            'greeting': [r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b'],
            'symptom_check': [
                r'\b(fever|temperature|hot|burning)\b',
                r'\b(cough|coughing|hack)\b',
                r'\b(breath|breathing|shortness of breath|wheeze)\b',
                r'\b(headache|head pain|migraine)\b',
                r'\b(chest pain|chest discomfort)\b',
                r'\b(nausea|vomit|throwing up)\b',
                r'\b(diarrhea|diarrhoea|loose stool)\b',
                r'\b(fatigue|tired|exhausted|weak)\b'
            ],
            'small_talk': [
                r'\b(what are you up to|how are you|thank you|thanks)\b',
                r'\b(what can you do|what are your capabilities)\b'
            ]
        }
        
        self.test_suggestions = {
            'fever': ['CBC (Complete Blood Count)', 'CRP (C-Reactive Protein)', 'Blood Culture'],
            'cough': ['Chest X-Ray', 'Sputum Culture', 'Pulmonary Function Test'],
            'breath': ['Chest X-Ray', 'Pulmonary Function Test', 'Arterial Blood Gas'],
            'headache': ['CT Scan of Head', 'MRI Brain', 'Blood Pressure Check'],
            'chest_pain': ['ECG', 'Chest X-Ray', 'Troponin Test'],
            'nausea': ['Basic Metabolic Panel', 'Liver Function Tests', 'Pregnancy Test'],
            'diarrhea': ['Stool Culture', 'CBC', 'Electrolyte Panel'],
            'fatigue': ['CBC', 'Thyroid Function Tests', 'Vitamin D Level']
        }
    
    def identify_intent(self, message):
        """Identify the intent of the user's message."""
        message_lower = message.lower().strip()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return intent
        return 'unknown'
    
    def extract_symptoms(self, message):
        """Extract symptoms from the user's message."""
        message_lower = message.lower()
        symptoms = []
        
        symptom_keywords = {
            'fever': ['fever', 'temperature', 'hot', 'burning', 'chills'],
            'cough': ['cough', 'coughing', 'hack', 'hacking'],
            'breath': ['breath', 'breathing', 'shortness of breath', 'wheeze', 'wheezing'],
            'headache': ['headache', 'head pain', 'migraine', 'head ache'],
            'chest_pain': ['chest pain', 'chest discomfort', 'chest tightness'],
            'nausea': ['nausea', 'nauseous', 'vomit', 'throwing up', 'sick to stomach'],
            'diarrhea': ['diarrhea', 'diarrhoea', 'loose stool', 'loose stools'],
            'fatigue': ['fatigue', 'tired', 'exhausted', 'weak', 'weakness']
        }
        
        for symptom_category, keywords in symptom_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    symptoms.append(symptom_category)
                    break
        
        return symptoms
    
    def suggest_tests(self, symptoms):
        """Suggest medical tests based on identified symptoms."""
        suggested_tests = set()
        
        for symptom in symptoms:
            if symptom in self.test_suggestions:
                suggested_tests.update(self.test_suggestions[symptom])
        
        # If no specific symptoms, suggest general tests
        if not suggested_tests:
            suggested_tests.update(['CBC', 'Basic Metabolic Panel', 'Urinalysis'])
        
        return list(suggested_tests)
    
    def generate_response(self, message, session_id):
        """Generate a response to the user's message."""
        intent = self.identify_intent(message)
        symptoms = self.extract_symptoms(message)
        suggested_tests = self.suggest_tests(symptoms)
        
        if intent == 'greeting':
            replies = [
                "Hello! I'm Doctor Sahab, your AI health assistant. How can I help you today?",
                "Hi there! I'm here to help with your health concerns. What's on your mind?",
                "Good day! I'm Doctor Sahab. Please tell me about any symptoms or health questions you have.",
                "Hello! Welcome to Doctor Sahab. I'm ready to assist you with your health needs."
            ]
            reply = replies[hash(message) % len(replies)]
        elif intent == 'symptom_check':
            if symptoms:
                symptom_text = ", ".join(symptoms)
                reply = f"I see you're experiencing {symptom_text}. Based on your symptoms, I'd recommend consulting with a healthcare professional. I can suggest some tests that might be helpful for your condition."
            else:
                reply = "I understand you're not feeling well. Could you please describe your symptoms in more detail so I can better assist you?"
        elif intent == 'small_talk':
            if 'thank' in message.lower():
                reply = "You're very welcome! I'm here to help whenever you need assistance with your health concerns."
            elif 'what' in message.lower() and 'do' in message.lower():
                reply = "I'm Doctor Sahab, an AI health assistant. I can help you understand symptoms, suggest relevant medical tests, and provide general health guidance. However, I always recommend consulting with a real healthcare professional for proper diagnosis and treatment."
            else:
                reply = "I'm doing well, thank you for asking! I'm here to help with your health questions and concerns. Is there anything specific you'd like to know about your health?"
        else:
            reply = "I'm not sure I understand that. Could you please rephrase your question or tell me about any symptoms you're experiencing? I'm here to help with your health concerns."
        
        return {
            'reply': reply,
            'suggested_tests': suggested_tests,
            'intent': intent,
            'timestamp': datetime.utcnow().isoformat()
        }

class DoctorSahabHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Doctor Sahab API."""
    
    def __init__(self, *args, **kwargs):
        self.db = DoctorSahabDB()
        self.ai = DoctorSahabAI()
        super().__init__(*args, **kwargs)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        if path == '/health':
            self.send_json_response({'status': 'healthy', 'service': 'doctor-sahab-api'})
        elif path == '/':
            self.send_json_response({'message': 'Welcome to Doctor Sahab API', 'version': '1.0.0', 'status': 'healthy'})
        elif path == '/api/emergency/number':
            self.send_json_response({'number': '911'})
        elif path == '/api/places/nearby':
            try:
                lat = float(query_params.get('lat', [0])[0])
                lng = float(query_params.get('lng', [0])[0])
                hospital = self.db.find_nearby_hospital(lat, lng)
                if hospital:
                    self.send_json_response(hospital)
                else:
                    self.send_error_response(404, "No nearby hospitals found")
            except (ValueError, IndexError):
                self.send_error_response(400, "Invalid coordinates")
        else:
            self.send_error_response(404, "Not found")
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/api/chat/send':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                session_id = data.get('session_id')
                message = data.get('message')
                
                if not session_id or not message:
                    self.send_error_response(400, "Missing session_id or message")
                    return
                
                # Save user message
                user_message_id = self.db.save_message(session_id, 'user', message)
                
                # Generate AI response
                response_data = self.ai.generate_response(message, session_id)
                
                # Save bot response
                bot_message_id = self.db.save_message(
                    session_id, 'bot', response_data['reply'], response_data['suggested_tests']
                )
                
                # Save test suggestions
                if response_data['suggested_tests']:
                    self.db.save_test_suggestions(session_id, response_data['suggested_tests'], user_message_id)
                
                self.send_json_response(response_data)
                
            except Exception as e:
                self.send_error_response(500, f"Error processing message: {str(e)}")
        else:
            self.send_error_response(404, "Not found")
    
    def send_json_response(self, data):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def send_error_response(self, code, message):
        """Send error response."""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to reduce logging noise."""
        pass

def start_backend():
    """Start the Doctor Sahab backend server."""
    print("🏥 Starting Doctor Sahab Backend...")
    print("📍 Server: http://localhost:8000")
    print("📚 Health Check: http://localhost:8000/health")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 50)
    
    server = HTTPServer(('localhost', 8000), DoctorSahabHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        server.shutdown()

if __name__ == "__main__":
    start_backend()


