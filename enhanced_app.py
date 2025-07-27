#!/usr/bin/env python3
"""
Enhanced InsureMyWay Application with Advanced AI Features
This version includes comprehensive AI recommendations and enhanced database models.
"""

import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import random

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask setup
app = Flask(__name__)
app.secret_key = 'your-secret-key-123'  # Replace in production

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///enhanced_insurance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Enhanced Models with AI Features
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    occupation = db.Column(db.String(100), nullable=True)
    lifestyle = db.Column(db.String(50), nullable=True)
    health_status = db.Column(db.String(50), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Policy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    premium = db.Column(db.Float, nullable=False)
    coverage = db.Column(db.String(500), nullable=False)
    min_age = db.Column(db.Integer, nullable=False)
    max_age = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(50), nullable=False)

class AIRecommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    ai_score = db.Column(db.Float, nullable=False)
    recommendation_text = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref='ai_recommendations')
    policy = db.relationship('Policy', backref='recommendations')

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref='purchases')
    policy = db.relationship('Policy', backref='purchases')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_from_admin = db.Column(db.Boolean, nullable=False, default=False)
    user = db.relationship('User', backref='messages')

# Enhanced AI Recommendation Engine
class AIRecommendationEngine:
    @staticmethod
    def calculate_compatibility_score(user, policy):
        """Advanced AI algorithm to calculate user-policy compatibility"""
        score = 0
        
        # Age compatibility (40 points max)
        if policy.min_age <= user.age <= policy.max_age:
            score += 40
            # Bonus for optimal age range
            optimal_range = (policy.max_age - policy.min_age) * 0.3
            if policy.min_age + optimal_range <= user.age <= policy.max_age - optimal_range:
                score += 10
        
        # Occupation-based scoring (25 points max)
        occupation_scores = {
            'construction': {'auto': 20, 'health': 15, 'life': 10},
            'office': {'health': 20, 'life': 15, 'travel': 10},
            'teacher': {'health': 18, 'life': 15, 'auto': 8},
            'student': {'health': 15, 'travel': 12, 'auto': 8},
            'manager': {'health': 18, 'life': 20, 'business': 25},
            'administrator': {'health': 15, 'life': 15, 'business': 20}
        }
        
        if user.occupation and user.occupation.lower() in occupation_scores:
            occ_scores = occupation_scores[user.occupation.lower()]
            score += occ_scores.get(policy.type, 5)
        
        # Lifestyle-based scoring (20 points max)
        if user.lifestyle:
            if user.lifestyle == 'active':
                lifestyle_bonus = {'health': 15, 'travel': 20, 'auto': 10}
                score += lifestyle_bonus.get(policy.type, 5)
            elif user.lifestyle == 'sedentary':
                lifestyle_bonus = {'health': 20, 'life': 15, 'home': 10}
                score += lifestyle_bonus.get(policy.type, 5)
        
        # Health status scoring (15 points max)
        if user.health_status:
            if user.health_status == 'smoker':
                health_bonus = {'health': 15, 'life': 10}
                score += health_bonus.get(policy.type, 0)
            elif user.health_status == 'non-smoker':
                health_bonus = {'health': 10, 'life': 15, 'travel': 8}
                score += health_bonus.get(policy.type, 5)
        
        # Risk level compatibility (10 points max)
        user_risk_profile = AIRecommendationEngine.assess_user_risk(user)
        if policy.risk_level == user_risk_profile:
            score += 10
        elif abs(['low', 'medium', 'high'].index(policy.risk_level) -
                ['low', 'medium', 'high'].index(user_risk_profile)) == 1:
            score += 5

        # Enhanced profile scoring using new fields
        score += AIRecommendationEngine.calculate_enhanced_profile_score(user, policy)

        return min(score, 100)  # Cap at 100
    
    @staticmethod
    def calculate_enhanced_profile_score(user, policy):
        """Calculate additional scoring based on enhanced profile fields"""
        score = 0
        policy_text = (policy.name + ' ' + policy.coverage).lower()

        # Family and dependents scoring (15 points max)
        if user.marital_status == 'married' or (user.dependents and user.dependents > 0):
            if 'family' in policy_text or 'life' in policy_text:
                score += 15
            elif user.dependents and user.dependents > 2 and 'health' in policy_text:
                score += 10

        # Income-based affordability (12 points max)
        if user.annual_income:
            if user.annual_income in ['under_1m', '1m_3m'] and policy.premium < 30:
                score += 12
            elif user.annual_income in ['3m_5m', '5m_10m'] and 30 <= policy.premium <= 70:
                score += 10
            elif user.annual_income in ['10m_20m', 'over_20m'] and policy.premium >= 50:
                score += 8

        # Vehicle ownership matching (10 points max)
        if user.vehicle_ownership and user.vehicle_ownership != 'none':
            if 'auto' in policy_text or 'vehicle' in policy_text or 'motorcycle' in policy_text:
                score += 10

        # Travel frequency matching (8 points max)
        if user.travel_frequency:
            if user.travel_frequency == 'frequent' and 'travel' in policy_text:
                score += 8
            elif user.travel_frequency == 'occasional' and 'travel' in policy_text:
                score += 5

        # Risk tolerance alignment (8 points max)
        if user.risk_tolerance:
            if user.risk_tolerance == 'conservative' and policy.risk_level == 'low':
                score += 8
            elif user.risk_tolerance == 'moderate' and policy.risk_level == 'medium':
                score += 8
            elif user.risk_tolerance == 'aggressive' and policy.risk_level == 'high':
                score += 8

        # Coverage priority matching (10 points max)
        if user.coverage_priority:
            if user.coverage_priority == 'cost' and policy.premium < 40:
                score += 10
            elif user.coverage_priority == 'coverage' and policy.premium >= 60:
                score += 10
            elif user.coverage_priority in ['service', 'flexibility', 'reputation']:
                score += 5

        # Insurance experience adjustment (5 points max)
        if user.insurance_experience:
            if user.insurance_experience == 'beginner' and policy.risk_level == 'low':
                score += 5
            elif user.insurance_experience == 'experienced' and policy.risk_level == 'high':
                score += 5
            elif user.insurance_experience == 'intermediate':
                score += 3

        return min(score, 50)  # Cap additional scoring at 50 points

    @staticmethod
    def assess_user_risk(user):
        """Enhanced user risk assessment using comprehensive profile"""
        risk_score = 0

        # Age-based risk
        if user.age:
            if user.age < 25 or user.age > 65:
                risk_score += 2
            elif 25 <= user.age <= 45:
                risk_score -= 1

        # Occupation-based risk
        if user.occupation:
            high_risk_jobs = ['construction', 'mining', 'aviation', 'police', 'military']
            medium_risk_jobs = ['driver', 'mechanic', 'chef', 'nurse']
            if any(job in user.occupation.lower() for job in high_risk_jobs):
                risk_score += 3
            elif any(job in user.occupation.lower() for job in medium_risk_jobs):
                risk_score += 1

        # Lifestyle risk
        if user.lifestyle == 'active':
            risk_score += 1
        elif user.lifestyle == 'sedentary':
            risk_score -= 1

        # Health status risk
        if user.health_status == 'smoker':
            risk_score += 3
        elif user.health_status in ['poor', 'fair']:
            risk_score += 2
        elif user.health_status in ['excellent', 'good', 'non-smoker']:
            risk_score -= 1

        # Family medical history risk
        if user.family_medical_history:
            if user.family_medical_history == 'major':
                risk_score += 2
            elif user.family_medical_history == 'chronic':
                risk_score += 3
            elif user.family_medical_history == 'minor':
                risk_score += 1

        # Vehicle ownership risk
        if user.vehicle_ownership:
            if 'motorcycle' in user.vehicle_ownership:
                risk_score += 2
            elif user.vehicle_ownership != 'none':
                risk_score += 1

        # Travel frequency risk
        if user.travel_frequency == 'frequent':
            risk_score += 1

        # Hobbies and activities risk
        if user.hobbies_activities:
            high_risk_activities = ['extreme sports', 'mountain climbing', 'skydiving', 'racing']
            if any(activity in user.hobbies_activities.lower() for activity in high_risk_activities):
                risk_score += 2

        if risk_score <= 0:
            return 'low'
        elif risk_score <= 4:
            return 'medium'
        else:
            return 'high'
    
    @staticmethod
    def generate_recommendations(user, limit=3):
        """Generate AI-powered recommendations for a user"""
        policies = Policy.query.all()
        recommendations = []
        
        for policy in policies:
            score = AIRecommendationEngine.calculate_compatibility_score(user, policy)
            if score > 30:  # Only recommend policies with good compatibility
                recommendations.append({
                    'policy': policy,
                    'score': score,
                    'recommendation_text': AIRecommendationEngine.generate_explanation(user, policy, score)
                })
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]
    
    @staticmethod
    def generate_explanation(user, policy, score):
        """Generate human-readable explanation for the recommendation"""
        explanations = []
        
        if policy.min_age <= user.age <= policy.max_age:
            explanations.append(f"Perfect age match for {policy.name}")
        
        if user.occupation:
            if user.occupation.lower() == 'construction' and policy.type == 'auto':
                explanations.append("Ideal for construction workers who need reliable vehicle coverage")
            elif user.occupation.lower() in ['office', 'teacher'] and policy.type == 'health':
                explanations.append("Excellent health coverage for professionals")
        
        if user.lifestyle == 'active' and policy.type in ['health', 'travel']:
            explanations.append("Great for active lifestyle")
        
        if score >= 80:
            prefix = "🌟 Highly recommended: "
        elif score >= 60:
            prefix = "✅ Good match: "
        else:
            prefix = "💡 Consider: "
        
        explanation = " • ".join(explanations) if explanations else f"Good compatibility with your profile"
        return f"{prefix}{explanation} (AI Score: {score}/100)"

# Enhanced seed data with comprehensive product offerings
enhanced_policies = [
    # Health Insurance - Comprehensive Options
    {'name': 'Basic Health Plan', 'type': 'health', 'premium': 25.0, 'coverage': 'Essential medical coverage for routine care, doctor visits, and emergency services', 'min_age': 18, 'max_age': 70, 'risk_level': 'low'},
    {'name': 'Family Health Shield', 'type': 'health', 'premium': 65.0, 'coverage': 'Comprehensive family medical coverage including pediatric care, maternity, and wellness programs', 'min_age': 18, 'max_age': 65, 'risk_level': 'medium'},
    {'name': 'Premium Health Plus', 'type': 'health', 'premium': 120.0, 'coverage': 'Premium medical coverage with private rooms, specialist consultations, dental, and vision care', 'min_age': 25, 'max_age': 60, 'risk_level': 'high'},
    {'name': 'Senior Health Care', 'type': 'health', 'premium': 85.0, 'coverage': 'Specialized health coverage for seniors with chronic disease management and home care services', 'min_age': 55, 'max_age': 85, 'risk_level': 'medium'},
    {'name': 'Student Health Basic', 'type': 'health', 'premium': 18.0, 'coverage': 'Affordable health coverage designed specifically for students and young adults', 'min_age': 16, 'max_age': 26, 'risk_level': 'low'},

    # Auto Insurance - Diverse Vehicle Coverage
    {'name': 'Basic Auto Coverage', 'type': 'auto', 'premium': 20.0, 'coverage': 'Essential vehicle protection with liability coverage and roadside assistance', 'min_age': 18, 'max_age': 75, 'risk_level': 'low'},
    {'name': 'Complete Auto Shield', 'type': 'auto', 'premium': 45.0, 'coverage': 'Full vehicle protection including collision, comprehensive, theft, and rental car coverage', 'min_age': 21, 'max_age': 70, 'risk_level': 'medium'},
    {'name': 'Luxury Auto Protection', 'type': 'auto', 'premium': 95.0, 'coverage': 'Premium vehicle coverage for luxury cars with gap insurance and concierge services', 'min_age': 25, 'max_age': 65, 'risk_level': 'high'},
    {'name': 'Commercial Vehicle Insurance', 'type': 'auto', 'premium': 75.0, 'coverage': 'Business vehicle coverage for fleets, delivery trucks, and commercial transportation', 'min_age': 21, 'max_age': 70, 'risk_level': 'medium'},
    {'name': 'Motorcycle Adventure', 'type': 'auto', 'premium': 35.0, 'coverage': 'Specialized motorcycle insurance with touring and adventure sports coverage', 'min_age': 18, 'max_age': 65, 'risk_level': 'medium'},

    # Home Insurance - Property Protection
    {'name': 'Basic Home Protection', 'type': 'home', 'premium': 30.0, 'coverage': 'Essential home coverage for fire, theft, and basic natural disasters', 'min_age': 21, 'max_age': 80, 'risk_level': 'low'},
    {'name': 'Complete Home Guard', 'type': 'home', 'premium': 60.0, 'coverage': 'Comprehensive home protection with full replacement cost and additional living expenses', 'min_age': 25, 'max_age': 75, 'risk_level': 'medium'},
    {'name': 'Luxury Home Estate', 'type': 'home', 'premium': 150.0, 'coverage': 'Premium home coverage for high-value properties with art, jewelry, and collectibles protection', 'min_age': 30, 'max_age': 75, 'risk_level': 'high'},
    {'name': 'Rental Property Shield', 'type': 'home', 'premium': 55.0, 'coverage': 'Landlord insurance covering rental properties, liability, and loss of rental income', 'min_age': 21, 'max_age': 80, 'risk_level': 'medium'},
    {'name': 'Condo Smart Coverage', 'type': 'home', 'premium': 25.0, 'coverage': 'Specialized condominium insurance covering personal property and liability', 'min_age': 18, 'max_age': 80, 'risk_level': 'low'},

    # Life Insurance - Financial Security
    {'name': 'Term Life Basic', 'type': 'life', 'premium': 25.0, 'coverage': 'Affordable term life insurance providing financial security for your family', 'min_age': 18, 'max_age': 65, 'risk_level': 'low'},
    {'name': 'Whole Life Investment', 'type': 'life', 'premium': 80.0, 'coverage': 'Permanent life insurance with cash value growth and investment opportunities', 'min_age': 25, 'max_age': 60, 'risk_level': 'medium'},
    {'name': 'Universal Life Flex', 'type': 'life', 'premium': 70.0, 'coverage': 'Flexible life insurance with adjustable premiums and death benefits', 'min_age': 25, 'max_age': 65, 'risk_level': 'medium'},
    {'name': 'Child Life Starter', 'type': 'life', 'premium': 15.0, 'coverage': 'Life insurance for children with guaranteed insurability and cash value growth', 'min_age': 0, 'max_age': 17, 'risk_level': 'low'},

    # Travel Insurance - Adventure & Protection
    {'name': 'Travel Essentials', 'type': 'travel', 'premium': 15.0, 'coverage': 'Basic travel protection for trips and medical emergencies abroad', 'min_age': 16, 'max_age': 80, 'risk_level': 'low'},
    {'name': 'Adventure Travel Pro', 'type': 'travel', 'premium': 35.0, 'coverage': 'Comprehensive travel coverage including adventure sports and high-value items', 'min_age': 18, 'max_age': 70, 'risk_level': 'medium'},
    {'name': 'Business Travel Elite', 'type': 'travel', 'premium': 50.0, 'coverage': 'Premium business travel insurance with executive services and equipment coverage', 'min_age': 21, 'max_age': 70, 'risk_level': 'medium'},
    {'name': 'Family Vacation Guard', 'type': 'travel', 'premium': 28.0, 'coverage': 'Family-focused travel insurance with child-specific benefits and group discounts', 'min_age': 0, 'max_age': 80, 'risk_level': 'low'},

    # Business Insurance - Professional Protection
    {'name': 'Small Business Shield', 'type': 'business', 'premium': 80.0, 'coverage': 'Complete business protection including liability, property, and cyber security', 'min_age': 21, 'max_age': 70, 'risk_level': 'medium'},
    {'name': 'Professional Liability Pro', 'type': 'business', 'premium': 90.0, 'coverage': 'Professional liability insurance for consultants, doctors, lawyers, and service providers', 'min_age': 25, 'max_age': 70, 'risk_level': 'medium'},
    {'name': 'Cyber Security Enterprise', 'type': 'business', 'premium': 120.0, 'coverage': 'Advanced cyber security insurance protecting against data breaches and cyber attacks', 'min_age': 21, 'max_age': 70, 'risk_level': 'high'},

    # Specialty Insurance - Unique Coverage
    {'name': 'Pet Health Guardian', 'type': 'specialty', 'premium': 40.0, 'coverage': 'Complete pet insurance covering veterinary care, surgeries, and wellness treatments', 'min_age': 18, 'max_age': 80, 'risk_level': 'low'},
    {'name': 'Disability Income Guard', 'type': 'specialty', 'premium': 50.0, 'coverage': 'Income protection insurance providing benefits if you become unable to work', 'min_age': 18, 'max_age': 65, 'risk_level': 'medium'},
    {'name': 'Critical Illness Shield', 'type': 'specialty', 'premium': 45.0, 'coverage': 'Coverage for major illnesses like cancer, heart attack, and stroke with lump sum benefits', 'min_age': 18, 'max_age': 70, 'risk_level': 'medium'},
    {'name': 'Identity Theft Protection', 'type': 'specialty', 'premium': 12.0, 'coverage': 'Digital protection against identity theft, cyber attacks, and online fraud', 'min_age': 16, 'max_age': 80, 'risk_level': 'low'},
    {'name': 'Wedding & Event Insurance', 'type': 'specialty', 'premium': 22.0, 'coverage': 'Special event insurance covering weddings, parties, and celebrations against cancellation', 'min_age': 18, 'max_age': 80, 'risk_level': 'low'},
]

# Database initialization and seeding
def init_enhanced_database():
    """Initialize database with enhanced AI features"""
    with app.app_context():
        db.create_all()

        # Seed policies if none exist
        if not Policy.query.first():
            for policy_data in enhanced_policies:
                policy = Policy(**policy_data)
                db.session.add(policy)

            # Create admin user
            admin_password = bcrypt.generate_password_hash('adminpass').decode('utf-8')
            admin = User(
                username='admin',
                password=admin_password,
                email='admin@insuremyway.com',
                is_admin=True,
                age=35,
                occupation='administrator',
                lifestyle='active',
                health_status='non-smoker'
            )
            db.session.add(admin)

            # Create sample users
            sample_users = [
                {'username': 'john_doe', 'email': 'john@example.com', 'age': 28, 'occupation': 'office', 'lifestyle': 'active', 'health_status': 'non-smoker'},
                {'username': 'jane_smith', 'email': 'jane@example.com', 'age': 35, 'occupation': 'construction', 'lifestyle': 'active', 'health_status': 'smoker'},
                {'username': 'bob_wilson', 'email': 'bob@example.com', 'age': 45, 'occupation': 'teacher', 'lifestyle': 'sedentary', 'health_status': 'non-smoker'},
            ]

            for user_data in sample_users:
                password = bcrypt.generate_password_hash('password123').decode('utf-8')
                user = User(
                    username=user_data['username'],
                    password=password,
                    email=user_data['email'],
                    age=user_data['age'],
                    occupation=user_data['occupation'],
                    lifestyle=user_data['lifestyle'],
                    health_status=user_data['health_status'],
                    is_admin=False
                )
                db.session.add(user)

            db.session.commit()
            logger.info("Enhanced database initialized with AI features")

# Template filter for currency conversion
@app.template_filter('to_frw')
def to_frw_filter(usd_amount):
    """Template filter to convert USD to Rwandan Francs"""
    if usd_amount is None:
        return "0 FRW"
    frw_amount = usd_amount * 1300  # 1 USD = 1300 FRW (approximate exchange rate)
    return f"{frw_amount:,.0f} FRW"

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')
        age = request.form.get('age', type=int)
        occupation = request.form.get('occupation', '')
        lifestyle = request.form.get('lifestyle', '')
        health_status = request.form.get('health_status', '')

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            username=username,
            password=hashed_password,
            email=email,
            age=age,
            occupation=occupation,
            lifestyle=lifestyle,
            health_status=health_status
        )

        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Generate AI recommendations
    ai_recommendations = AIRecommendationEngine.generate_recommendations(current_user)

    # Get user's purchases
    purchases = Purchase.query.filter_by(user_id=current_user.id).all()

    return render_template('dashboard.html',
                         user=current_user,
                         recommendations=ai_recommendations,
                         purchases=purchases)

@app.route('/ai-recommendations')
@login_required
def ai_recommendations():
    recommendations = AIRecommendationEngine.generate_recommendations(current_user, limit=5)

    return render_template('ai_recommendations.html',
                         user=current_user,
                         recommendations=recommendations)

@app.route('/policies')
def policies():
    all_policies = Policy.query.all()
    return render_template('policies.html', policies=all_policies)

@app.route('/purchase/<int:policy_id>')
@login_required
def purchase_policy(policy_id):
    policy = Policy.query.get_or_404(policy_id)

    # Check if already purchased
    existing_purchase = Purchase.query.filter_by(user_id=current_user.id, policy_id=policy_id).first()
    if existing_purchase:
        flash('You have already purchased this policy!', 'warning')
        return redirect(url_for('dashboard'))

    # Create purchase
    purchase = Purchase(user_id=current_user.id, policy_id=policy_id)
    db.session.add(purchase)
    db.session.commit()

    flash(f'Successfully purchased {policy.name}!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/recommendations')
@login_required
def recommendations():
    return redirect(url_for('ai_recommendations'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Basic profile fields
        current_user.age = request.form.get('age', type=int)
        current_user.occupation = request.form.get('occupation')
        current_user.lifestyle = request.form.get('lifestyle')
        current_user.health_status = request.form.get('health_status')

        # Enhanced profile fields
        current_user.marital_status = request.form.get('marital_status')
        current_user.dependents = request.form.get('dependents', type=int) or 0
        current_user.annual_income = request.form.get('annual_income')
        current_user.education_level = request.form.get('education_level')
        current_user.employment_type = request.form.get('employment_type')
        current_user.residence_type = request.form.get('residence_type')
        current_user.vehicle_ownership = request.form.get('vehicle_ownership')
        current_user.travel_frequency = request.form.get('travel_frequency')
        current_user.risk_tolerance = request.form.get('risk_tolerance')
        current_user.insurance_experience = request.form.get('insurance_experience')
        current_user.coverage_priority = request.form.get('coverage_priority')
        current_user.family_medical_history = request.form.get('family_medical_history')
        current_user.hobbies_activities = request.form.get('hobbies_activities')
        current_user.location = request.form.get('location')

        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
            return render_template('profile.html', user=current_user)

    return render_template('profile.html', user=current_user)

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', user=current_user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return register()

@app.route('/products')
def products():
    policies = Policy.query.all()
    return render_template('products.html', policies=policies)

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_enhanced_database()
    app.run(debug=True, host='0.0.0.0', port=5001)
