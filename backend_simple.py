#!/usr/bin/env python3
"""
Simple standalone Doctor Sahab backend without complex imports.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from datetime import datetime
import re
from haversine import haversine
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database setup
Base = declarative_base()
database_url = os.getenv("DATABASE_URL", "sqlite:///./doctor_sahab.db")
engine = create_engine(database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    sender = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    suggested_tests = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (CheckConstraint("sender IN ('user','bot')", name='check_sender'),)

class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    test_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    suggested_by_message_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    result_json = Column(Text, nullable=True)
    __table_args__ = (CheckConstraint("status IN ('suggested','in_progress','completed')", name='check_status'),)

class Facility(Base):
    __tablename__ = "facilities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Simple AI Responder
class SimpleResponder:
    def __init__(self):
        self.intent_patterns = {
            'greeting': [r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b'],
            'symptom_check': [r'\b(fever|temperature|hot|cough|coughing|breath|breathing|headache|head pain)\b'],
            'small_talk': [r'\b(what are you up to|how are you|thank you|thanks)\b']
        }
        
        self.test_suggestions = {
            'fever': ['CBC (Complete Blood Count)', 'CRP (C-Reactive Protein)'],
            'cough': ['Chest X-Ray', 'Sputum Culture'],
            'breath': ['Chest X-Ray', 'Pulmonary Function Test'],
            'headache': ['CT Scan of Head', 'Blood Pressure Check']
        }
    
    def identify_intent(self, message):
        message_lower = message.lower().strip()
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return intent
        return 'unknown'
    
    def extract_symptoms(self, message):
        message_lower = message.lower()
        symptoms = []
        if 'fever' in message_lower or 'temperature' in message_lower:
            symptoms.append('fever')
        if 'cough' in message_lower:
            symptoms.append('cough')
        if 'breath' in message_lower:
            symptoms.append('breath')
        if 'headache' in message_lower:
            symptoms.append('headache')
        return symptoms
    
    def suggest_tests(self, symptoms):
        suggested_tests = set()
        for symptom in symptoms:
            if symptom in self.test_suggestions:
                suggested_tests.update(self.test_suggestions[symptom])
        if not suggested_tests:
            suggested_tests.update(['CBC', 'Basic Metabolic Panel'])
        return list(suggested_tests)
    
    def generate_response(self, message, session_id):
        intent = self.identify_intent(message)
        symptoms = self.extract_symptoms(message)
        suggested_tests = self.suggest_tests(symptoms)
        
        if intent == 'greeting':
            reply = "Hello! I'm Doctor Sahab, your AI health assistant. How can I help you today?"
        elif intent == 'symptom_check':
            if symptoms:
                symptom_text = ", ".join(symptoms)
                reply = f"I see you're experiencing {symptom_text}. I'd recommend consulting with a healthcare professional and suggest some tests."
            else:
                reply = "I understand you're not feeling well. Could you describe your symptoms in more detail?"
        elif intent == 'small_talk':
            reply = "I'm doing well, thank you! I'm here to help with your health questions. Is there anything specific you'd like to know?"
        else:
            reply = "I'm not sure I understand that. Could you please rephrase your question or tell me about any symptoms you're experiencing?"
        
        return {
            'reply': reply,
            'suggested_tests': suggested_tests,
            'intent': intent,
            'timestamp': datetime.utcnow().isoformat()
        }

responder = SimpleResponder()

# Pydantic models
class ChatMessage(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    suggested_tests: List[str]
    intent: str
    timestamp: str

class NearbyPlace(BaseModel):
    name: str
    address: str
    lat: float
    lng: float
    distance_meters: float

# Create FastAPI app
app = FastAPI(title="Doctor Sahab API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed database with sample hospitals
def seed_database():
    db = SessionLocal()
    try:
        if db.query(Facility).count() == 0:
            hospitals = [
                {"name": "City General Hospital", "address": "123 Main Street", "lat": 40.7128, "lng": -74.0060},
                {"name": "Metro Medical Center", "address": "456 Oak Avenue", "lat": 40.7589, "lng": -73.9851},
                {"name": "University Hospital", "address": "789 University Drive", "lat": 40.7505, "lng": -73.9934},
            ]
            for hospital in hospitals:
                facility = Facility(**hospital)
                db.add(facility)
            db.commit()
            print("✅ Database seeded with sample hospitals")
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
    finally:
        db.close()

# Seed database on startup
seed_database()

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to Doctor Sahab API", "version": "1.0.0", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "doctor-sahab-api"}

@app.post("/api/chat/send", response_model=ChatResponse)
async def send_message(chat_message: ChatMessage, db: Session = Depends(get_db)):
    try:
        # Save user message
        user_message = Message(
            session_id=chat_message.session_id,
            sender="user",
            text=chat_message.message,
            timestamp=datetime.utcnow()
        )
        db.add(user_message)
        db.flush()
        
        # Generate bot response
        response_data = responder.generate_response(chat_message.message, chat_message.session_id)
        
        # Save bot response
        bot_message = Message(
            session_id=chat_message.session_id,
            sender="bot",
            text=response_data['reply'],
            suggested_tests=json.dumps(response_data['suggested_tests']),
            timestamp=datetime.fromisoformat(response_data['timestamp'].replace('Z', '+00:00'))
        )
        db.add(bot_message)
        
        # Create test suggestions
        if response_data['suggested_tests']:
            for test_name in response_data['suggested_tests']:
                test = Test(
                    session_id=chat_message.session_id,
                    test_name=test_name,
                    status="suggested",
                    suggested_by_message_id=user_message.id
                )
                db.add(test)
        
        db.commit()
        
        return ChatResponse(
            reply=response_data['reply'],
            suggested_tests=response_data['suggested_tests'],
            intent=response_data['intent'],
            timestamp=response_data['timestamp']
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/api/places/nearby", response_model=NearbyPlace)
async def get_nearby_hospital(lat: float, lng: float, db: Session = Depends(get_db)):
    try:
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            raise HTTPException(status_code=400, detail="Invalid coordinates")
        
        facilities = db.query(Facility).all()
        if not facilities:
            raise HTTPException(status_code=404, detail="No hospitals found")
        
        nearest_facility = None
        min_distance = float('inf')
        
        for facility in facilities:
            distance = haversine((lat, lng), (facility.lat, facility.lng), unit='m')
            if distance < min_distance:
                min_distance = distance
                nearest_facility = facility
        
        if not nearest_facility:
            raise HTTPException(status_code=404, detail="No nearby hospitals found")
        
        return NearbyPlace(
            name=nearest_facility.name,
            address=nearest_facility.address or "Address not available",
            lat=nearest_facility.lat,
            lng=nearest_facility.lng,
            distance_meters=round(min_distance, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding nearby hospital: {str(e)}")

@app.get("/api/emergency/number")
async def get_emergency_number():
    emergency_number = os.getenv("EMERGENCY_NUMBER", "911")
    return {"number": emergency_number}

if __name__ == "__main__":
    import uvicorn
    print("🏥 Starting Doctor Sahab Backend...")
    print("📍 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="localhost", port=8000)


