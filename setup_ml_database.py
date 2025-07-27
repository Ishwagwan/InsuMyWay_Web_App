#!/usr/bin/env python3
"""
Setup ML Database Tables and Initialize System
Run this script to set up the machine learning database tables and initialize the system.
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_app import app, db
from models import User, Policy
from ml_models import (
    UserInteraction, UserSimilarity, PolicyFeatures, MLModel,
    RecommendationLog, UserPreferenceProfile
)
from interaction_tracker import InteractionTracker

def create_ml_tables():
    """Create all ML-related database tables"""
    print("Creating ML database tables...")
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✓ ML database tables created successfully")
            return True
        except Exception as e:
            print(f"✗ Error creating ML tables: {e}")
            return False

def generate_sample_interactions():
    """Generate sample user interactions for testing ML algorithms"""
    print("Generating sample user interactions...")
    
    with app.app_context():
        try:
            users = User.query.all()
            policies = Policy.query.all()
            
            if not users or not policies:
                print("✗ No users or policies found. Please ensure basic data exists first.")
                return False
            
            # Generate realistic interactions
            interaction_types = ['view', 'click', 'rate', 'dismiss']
            interaction_weights = {'view': 1.0, 'click': 2.0, 'rate': 4.0, 'dismiss': -1.0}
            
            interactions_created = 0
            
            for user in users:
                # Each user interacts with 3-8 policies
                num_interactions = random.randint(3, 8)
                selected_policies = random.sample(policies, min(num_interactions, len(policies)))
                
                for policy in selected_policies:
                    # Generate multiple interaction types for each policy
                    for _ in range(random.randint(1, 3)):
                        interaction_type = random.choice(interaction_types)
                        
                        # Generate realistic interaction values
                        if interaction_type == 'view':
                            interaction_value = random.uniform(1.0, 300.0)  # Time spent in seconds
                        elif interaction_type == 'click':
                            interaction_value = random.uniform(1.0, 4.0)  # Click importance
                        elif interaction_type == 'rate':
                            interaction_value = random.uniform(1.0, 5.0)  # Rating 1-5
                        else:  # dismiss
                            interaction_value = random.uniform(0.5, 2.0)  # Dismissal strength
                        
                        # Create interaction with timestamp in the past 30 days
                        timestamp = datetime.utcnow() - timedelta(
                            days=random.randint(0, 30),
                            hours=random.randint(0, 23),
                            minutes=random.randint(0, 59)
                        )
                        
                        interaction = UserInteraction(
                            user_id=user.id,
                            policy_id=policy.id,
                            interaction_type=interaction_type,
                            interaction_value=interaction_value,
                            timestamp=timestamp,
                            session_id=f"sample_session_{user.id}_{random.randint(1000, 9999)}"
                        )
                        
                        db.session.add(interaction)
                        interactions_created += 1
            
            db.session.commit()
            print(f"✓ Generated {interactions_created} sample interactions")
            return True
            
        except Exception as e:
            print(f"✗ Error generating sample interactions: {e}")
            db.session.rollback()
            return False

def initialize_ml_system():
    """Initialize the ML system with basic configuration"""
    print("Initializing ML system...")
    
    with app.app_context():
        try:
            # Create initial ML model entries
            model_configs = [
                {
                    'model_name': 'collaborative_filtering',
                    'model_type': 'collaborative',
                    'model_params': '{"n_components": 50, "algorithm": "randomized"}',
                    'is_active': False
                },
                {
                    'model_name': 'content_based_filtering',
                    'model_type': 'content_based',
                    'model_params': '{"max_features": 1000, "stop_words": "english"}',
                    'is_active': False
                },
                {
                    'model_name': 'hybrid_model',
                    'model_type': 'hybrid',
                    'model_params': '{"n_estimators": 100, "max_depth": 10}',
                    'is_active': False
                }
            ]
            
            for config in model_configs:
                existing_model = MLModel.query.filter_by(
                    model_name=config['model_name'],
                    model_type=config['model_type']
                ).first()
                
                if not existing_model:
                    ml_model = MLModel(
                        model_name=config['model_name'],
                        model_type=config['model_type'],
                        model_params=config['model_params'],
                        is_active=config['is_active']
                    )
                    db.session.add(ml_model)
            
            db.session.commit()
            print("✓ ML system initialized successfully")
            return True
            
        except Exception as e:
            print(f"✗ Error initializing ML system: {e}")
            db.session.rollback()
            return False

def train_initial_models():
    """Train initial ML models with sample data"""
    print("Training initial ML models...")
    
    try:
        from ai_recommendation_engine import TrueAIRecommendationEngine
        
        with app.app_context():
            ai_engine = TrueAIRecommendationEngine()
            success = ai_engine.train_all_models()
            
            if success:
                print("✓ Initial ML models trained successfully")
                return True
            else:
                print("✗ ML model training failed")
                return False
                
    except ImportError as e:
        print(f"✗ ML components not available: {e}")
        return False
    except Exception as e:
        print(f"✗ Error training initial models: {e}")
        return False

def verify_ml_setup():
    """Verify that the ML system is set up correctly"""
    print("Verifying ML setup...")
    
    with app.app_context():
        try:
            # Check tables exist
            tables_to_check = [
                'user_interactions', 'user_similarities', 'policy_features',
                'ml_models', 'recommendation_logs', 'user_preference_profiles'
            ]
            
            for table_name in tables_to_check:
                result = db.engine.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                if not result.fetchone():
                    print(f"✗ Table {table_name} not found")
                    return False
            
            # Check sample data
            interaction_count = UserInteraction.query.count()
            model_count = MLModel.query.count()
            
            print(f"✓ ML setup verified:")
            print(f"  - All required tables exist")
            print(f"  - {interaction_count} user interactions")
            print(f"  - {model_count} ML model configurations")
            
            return True
            
        except Exception as e:
            print(f"✗ Error verifying ML setup: {e}")
            return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("🤖 SETTING UP TRUE AI/ML RECOMMENDATION SYSTEM")
    print("=" * 60)
    
    steps = [
        ("Creating ML database tables", create_ml_tables),
        ("Generating sample interactions", generate_sample_interactions),
        ("Initializing ML system", initialize_ml_system),
        ("Training initial models", train_initial_models),
        ("Verifying ML setup", verify_ml_setup)
    ]
    
    success_count = 0
    
    for step_name, step_function in steps:
        print(f"\n📋 {step_name}...")
        if step_function():
            success_count += 1
        else:
            print(f"⚠️  {step_name} failed, but continuing...")
    
    print("\n" + "=" * 60)
    print(f"🎯 SETUP COMPLETE: {success_count}/{len(steps)} steps successful")
    print("=" * 60)
    
    if success_count >= 3:  # At least basic setup successful
        print("\n✅ Your AI/ML recommendation system is ready!")
        print("\n📚 Next steps:")
        print("1. Visit /ml/dashboard (admin only) to manage ML models")
        print("2. Use /ml/train to retrain models with real data")
        print("3. Monitor /ml/analytics for system performance")
        print("4. The system will automatically use ML when available")
        print("\n🔄 The system will fall back to rule-based recommendations")
        print("   if ML models are not available or fail.")
    else:
        print("\n⚠️  Setup had issues. Check the errors above.")
        print("   The system will use rule-based recommendations as fallback.")
    
    return success_count >= 3

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
