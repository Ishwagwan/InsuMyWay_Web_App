#!/usr/bin/env python3
"""
Enhanced Database Population Script for InsureMyWay AI Features
This script populates the database with comprehensive insurance data and AI features.
"""

from app import app, db
from models import User, Policy, Recommendation, Notification
from flask_bcrypt import Bcrypt
import random
from datetime import datetime, timedelta

bcrypt = Bcrypt()

def populate_enhanced_data():
    """Populate database with enhanced AI-ready data"""
    
    with app.app_context():
        print("🚀 Starting enhanced database population...")
        
        # Clear existing data
        db.drop_all()
        db.create_all()
        print("✅ Database tables created")
        
        # Create comprehensive policies
        policies_data = [
            # Health Insurance Policies
            {'name': 'Basic Health Plan', 'type': 'health', 'premium': 25.0, 'coverage': 'Basic medical coverage for routine checkups and minor treatments', 'min_age': 18, 'max_age': 70, 'risk_level': 'low'},
            {'name': 'Standard Health Plan', 'type': 'health', 'premium': 50.0, 'coverage': 'Comprehensive medical coverage including hospitalization and outpatient care', 'min_age': 18, 'max_age': 65, 'risk_level': 'medium'},
            {'name': 'Premium Health Plan', 'type': 'health', 'premium': 100.0, 'coverage': 'Premium medical coverage with private rooms, specialist consultations, and dental care', 'min_age': 25, 'max_age': 60, 'risk_level': 'high'},
            {'name': 'Senior Health Plan', 'type': 'health', 'premium': 75.0, 'coverage': 'Specialized health coverage for seniors with chronic condition support', 'min_age': 55, 'max_age': 80, 'risk_level': 'medium'},
            
            # Auto Insurance Policies
            {'name': 'Basic Auto Coverage', 'type': 'auto', 'premium': 15.0, 'coverage': 'Basic vehicle coverage for third-party liability only', 'min_age': 18, 'max_age': 75, 'risk_level': 'low'},
            {'name': 'Standard Auto Coverage', 'type': 'auto', 'premium': 30.0, 'coverage': 'Comprehensive vehicle coverage including collision, theft, and liability', 'min_age': 21, 'max_age': 70, 'risk_level': 'medium'},
            {'name': 'Premium Auto Coverage', 'type': 'auto', 'premium': 60.0, 'coverage': 'Premium vehicle coverage with roadside assistance, rental car, and full protection', 'min_age': 25, 'max_age': 65, 'risk_level': 'high'},
            {'name': 'Young Driver Auto Plan', 'type': 'auto', 'premium': 45.0, 'coverage': 'Specialized auto coverage for young drivers with safety monitoring', 'min_age': 18, 'max_age': 25, 'risk_level': 'high'},
            
            # Home Insurance Policies
            {'name': 'Basic Home Protection', 'type': 'home', 'premium': 20.0, 'coverage': 'Basic home coverage for fire and theft protection', 'min_age': 18, 'max_age': 85, 'risk_level': 'low'},
            {'name': 'Standard Home Protection', 'type': 'home', 'premium': 40.0, 'coverage': 'Comprehensive home coverage for fire, theft, and natural disasters', 'min_age': 21, 'max_age': 80, 'risk_level': 'medium'},
            {'name': 'Premium Home Protection', 'type': 'home', 'premium': 80.0, 'coverage': 'Premium home coverage with full replacement value and additional living expenses', 'min_age': 25, 'max_age': 75, 'risk_level': 'high'},
            
            # Life Insurance Policies
            {'name': 'Term Life Insurance', 'type': 'life', 'premium': 35.0, 'coverage': 'Term life insurance with death benefit for beneficiaries', 'min_age': 18, 'max_age': 65, 'risk_level': 'medium'},
            {'name': 'Whole Life Insurance', 'type': 'life', 'premium': 65.0, 'coverage': 'Whole life insurance with investment component and guaranteed cash value', 'min_age': 25, 'max_age': 60, 'risk_level': 'medium'},
            
            # Travel Insurance Policies
            {'name': 'Basic Travel Coverage', 'type': 'travel', 'premium': 12.0, 'coverage': 'Basic travel coverage for trip cancellation and medical emergencies', 'min_age': 16, 'max_age': 80, 'risk_level': 'low'},
            {'name': 'Premium Travel Coverage', 'type': 'travel', 'premium': 25.0, 'coverage': 'Comprehensive travel coverage with adventure sports and high-value item protection', 'min_age': 18, 'max_age': 70, 'risk_level': 'medium'},
            
            # Business Insurance Policies
            {'name': 'Small Business Insurance', 'type': 'business', 'premium': 90.0, 'coverage': 'Comprehensive business coverage for liability, property, and business interruption', 'min_age': 21, 'max_age': 70, 'risk_level': 'medium'},
            {'name': 'Professional Liability', 'type': 'business', 'premium': 55.0, 'coverage': 'Professional liability coverage for consultants and service providers', 'min_age': 25, 'max_age': 65, 'risk_level': 'medium'},
        ]
        
        # Add policies to database
        for policy_data in policies_data:
            policy = Policy(**policy_data)
            db.session.add(policy)
        
        db.session.commit()
        print(f"✅ Added {len(policies_data)} comprehensive insurance policies")
        
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
        
        # Create sample users with diverse profiles
        sample_users = [
            {'username': 'john_doe', 'email': 'john@example.com', 'age': 28, 'occupation': 'office', 'lifestyle': 'active', 'health_status': 'non-smoker'},
            {'username': 'jane_smith', 'email': 'jane@example.com', 'age': 35, 'occupation': 'construction', 'lifestyle': 'active', 'health_status': 'smoker'},
            {'username': 'bob_wilson', 'email': 'bob@example.com', 'age': 45, 'occupation': 'teacher', 'lifestyle': 'sedentary', 'health_status': 'non-smoker'},
            {'username': 'alice_brown', 'email': 'alice@example.com', 'age': 22, 'occupation': 'student', 'lifestyle': 'active', 'health_status': 'non-smoker'},
            {'username': 'mike_davis', 'email': 'mike@example.com', 'age': 55, 'occupation': 'manager', 'lifestyle': 'sedentary', 'health_status': 'smoker'},
        ]
        
        users = []
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
            users.append(user)
        
        db.session.commit()
        print(f"✅ Added admin and {len(sample_users)} sample users")
        
        # Generate AI recommendations for users
        policies = Policy.query.all()
        for user in users:
            # Generate 2-3 recommendations per user
            user_policies = random.sample(policies, min(3, len(policies)))
            for policy in user_policies:
                # Calculate AI score based on user profile
                score = calculate_ai_score(user, policy)
                if score > 20:  # Only add good recommendations
                    recommendation = Recommendation(
                        user_id=user.id,
                        policy_id=policy.id,
                        recommendation_text=f"AI recommends {policy.name} for your {user.age}-year-old {user.occupation} profile. Score: {score}/100"
                    )
                    db.session.add(recommendation)
        
        db.session.commit()
        print("✅ Generated AI recommendations for all users")
        
        # Add sample notifications
        for user in users:
            notifications = [
                f"Welcome to InsureMyWay! Your AI-powered insurance assistant is ready.",
                f"New policy recommendations available based on your {user.occupation} profile.",
                f"Reminder: Review your insurance coverage annually for optimal protection."
            ]
            for msg in notifications:
                notification = Notification(
                    user_id=user.id,
                    message=msg
                )
                db.session.add(notification)
        
        db.session.commit()
        print("✅ Added personalized notifications")
        
        print("\n🎉 Enhanced database population completed successfully!")
        print(f"📊 Database now contains:")
        print(f"   • {Policy.query.count()} insurance policies")
        print(f"   • {User.query.count()} users (including admin)")
        print(f"   • {Recommendation.query.count()} AI recommendations")
        print(f"   • {Notification.query.count()} notifications")

def calculate_ai_score(user, policy):
    """Calculate AI recommendation score for user-policy combination"""
    score = 10  # Base score
    
    # Age compatibility
    if policy.min_age <= user.age <= policy.max_age:
        score += 40
    
    # Occupation-based scoring
    if user.occupation == 'construction' and policy.type == 'auto':
        score += 20
    elif user.occupation == 'office' and policy.type == 'health':
        score += 15
    elif user.occupation == 'teacher' and policy.type in ['health', 'life']:
        score += 15
    
    # Lifestyle-based scoring
    if user.lifestyle == 'active' and policy.type in ['health', 'travel']:
        score += 10
    elif user.lifestyle == 'sedentary' and policy.type == 'health':
        score += 5
    
    # Health status scoring
    if user.health_status == 'smoker' and policy.type == 'health':
        score += 15
    elif user.health_status == 'non-smoker' and policy.type == 'life':
        score += 10
    
    # Risk level matching
    if policy.risk_level == 'low' and user.age < 30:
        score += 10
    elif policy.risk_level == 'medium':
        score += 5
    
    return min(score, 100)  # Cap at 100

if __name__ == '__main__':
    populate_enhanced_data()
