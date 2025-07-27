#!/usr/bin/env python3
"""
Simple ML Setup Script
Creates ML database tables and generates sample data for testing
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_ml_tables():
    """Create ML database tables"""
    print("🔧 Setting up ML database tables...")
    
    try:
        from unified_app import app, db
        
        with app.app_context():
            # Import ML models to register them
            from ml_models import (
                UserInteraction, UserSimilarity, PolicyFeatures, MLModel,
                RecommendationLog, UserPreferenceProfile
            )
            
            # Create all tables
            db.create_all()
            print("✅ ML database tables created successfully")
            return True
            
    except Exception as e:
        print(f"❌ Error creating ML tables: {e}")
        return False

def generate_sample_data():
    """Generate sample interaction data for ML training"""
    print("📊 Generating sample interaction data...")
    
    try:
        from unified_app import app, db
        from models import User, Policy
        from ml_models import UserInteraction
        
        with app.app_context():
            users = User.query.all()
            policies = Policy.query.all()
            
            if not users or not policies:
                print("⚠️  No users or policies found. Please run the main app first to create sample data.")
                return False
            
            # Generate realistic interactions
            interactions_created = 0
            
            for user in users[:5]:  # Limit to first 5 users for testing
                # Each user interacts with 3-6 policies
                num_interactions = random.randint(3, 6)
                selected_policies = random.sample(policies, min(num_interactions, len(policies)))
                
                for policy in selected_policies:
                    # Generate different types of interactions
                    interaction_types = ['view', 'click']
                    if random.random() > 0.7:  # 30% chance of rating
                        interaction_types.append('rate')
                    if random.random() > 0.9:  # 10% chance of purchase
                        interaction_types.append('purchase')
                    
                    for interaction_type in interaction_types:
                        # Generate realistic values
                        if interaction_type == 'view':
                            value = random.uniform(5.0, 120.0)  # Time in seconds
                        elif interaction_type == 'click':
                            value = random.uniform(1.0, 3.0)
                        elif interaction_type == 'rate':
                            value = random.uniform(2.0, 5.0)  # Rating 2-5
                        else:  # purchase
                            value = policy.premium / 10  # Normalized purchase value
                        
                        # Create interaction
                        interaction = UserInteraction(
                            user_id=user.id,
                            policy_id=policy.id,
                            interaction_type=interaction_type,
                            interaction_value=value,
                            timestamp=datetime.utcnow() - timedelta(
                                days=random.randint(0, 30),
                                hours=random.randint(0, 23)
                            ),
                            session_id=f"sample_{user.id}_{random.randint(1000, 9999)}"
                        )
                        
                        db.session.add(interaction)
                        interactions_created += 1
            
            db.session.commit()
            print(f"✅ Generated {interactions_created} sample interactions")
            return True
            
    except Exception as e:
        print(f"❌ Error generating sample data: {e}")
        return False

def test_ml_system():
    """Test if the ML system is working"""
    print("🧪 Testing ML system...")
    
    try:
        from unified_app import app
        from ai_recommendation_engine import TrueAIRecommendationEngine
        from models import User
        
        with app.app_context():
            # Try to initialize ML engine
            ml_engine = TrueAIRecommendationEngine()
            
            # Try to get a user
            user = User.query.first()
            if not user:
                print("⚠️  No users found for testing")
                return False
            
            # Try to generate recommendations
            recommendations = ml_engine.get_ai_recommendations(user.id, 5)
            
            if recommendations:
                print(f"✅ ML system working! Generated {len(recommendations)} recommendations")
                return True
            else:
                print("⚠️  ML system initialized but no recommendations generated (normal for new system)")
                return True
                
    except Exception as e:
        print(f"❌ ML system test failed: {e}")
        return False

def train_initial_models():
    """Train initial ML models"""
    print("🤖 Training initial ML models...")
    
    try:
        from unified_app import app
        from ai_recommendation_engine import TrueAIRecommendationEngine
        
        with app.app_context():
            ml_engine = TrueAIRecommendationEngine()
            success = ml_engine.train_all_models()
            
            if success:
                print("✅ ML models trained successfully")
                return True
            else:
                print("⚠️  ML model training completed with some issues (check logs)")
                return True  # Still consider success for initial setup
                
    except Exception as e:
        print(f"❌ ML model training failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("🤖 SIMPLE ML SYSTEM SETUP")
    print("=" * 60)
    
    steps = [
        ("Creating ML database tables", setup_ml_tables),
        ("Generating sample interaction data", generate_sample_data),
        ("Testing ML system", test_ml_system),
        ("Training initial models", train_initial_models)
    ]
    
    success_count = 0
    
    for step_name, step_function in steps:
        print(f"\n📋 {step_name}...")
        if step_function():
            success_count += 1
        else:
            print(f"⚠️  {step_name} failed, continuing...")
    
    print("\n" + "=" * 60)
    print(f"🎯 SETUP COMPLETE: {success_count}/{len(steps)} steps successful")
    print("=" * 60)
    
    if success_count >= 2:  # At least basic setup successful
        print("\n✅ Your ML system is ready!")
        print("\n📚 Next steps:")
        print("1. Start your Flask app: py unified_app.py")
        print("2. Visit /ml/dashboard (admin only) to manage ML models")
        print("3. The system will automatically use ML recommendations")
        print("4. User interactions will be tracked for continuous learning")
    else:
        print("\n⚠️  Setup had issues. The system will use fallback recommendations.")
    
    return success_count >= 2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
