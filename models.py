# models.py
from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    age = db.Column(db.Integer)
    occupation = db.Column(db.String(50))
    lifestyle = db.Column(db.String(50))
    health_status = db.Column(db.String(50))

    # Enhanced profile fields for better insurance matching
    marital_status = db.Column(db.String(20))  # single, married, divorced, widowed
    dependents = db.Column(db.Integer, default=0)  # number of dependents
    annual_income = db.Column(db.String(20))  # income range
    education_level = db.Column(db.String(30))  # education background
    employment_type = db.Column(db.String(30))  # full-time, part-time, self-employed, etc.
    residence_type = db.Column(db.String(30))  # own, rent, family home
    vehicle_ownership = db.Column(db.String(20))  # own, lease, none
    travel_frequency = db.Column(db.String(20))  # frequent, occasional, rare, never
    risk_tolerance = db.Column(db.String(20))  # conservative, moderate, aggressive
    insurance_experience = db.Column(db.String(20))  # beginner, intermediate, experienced
    coverage_priority = db.Column(db.String(30))  # cost, coverage, service, flexibility
    family_medical_history = db.Column(db.String(20))  # none, minor, major
    hobbies_activities = db.Column(db.String(100))  # sports, travel, etc.
    location = db.Column(db.String(50))  # city/region for location-based recommendations

    recommendations = db.relationship('Recommendation', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)

    @property
    def is_authenticated(self):
        return True

class Policy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    premium = db.Column(db.Float, nullable=False)
    coverage = db.Column(db.String(200), nullable=False)
    min_age = db.Column(db.Integer, nullable=False)
    max_age = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(50), nullable=False)

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'))
    recommendation_text = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
