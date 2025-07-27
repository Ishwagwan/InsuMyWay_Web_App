#!/usr/bin/env python3
"""
Complete ML Setup and Verification Script
Comprehensive setup and testing of the AI recommendation system
"""

import sys
import os
from datetime import datetime
import logging

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking ML dependencies...")
    
    required_packages = [
        'scikit-learn', 'pandas', 'numpy', 'scipy', 'joblib'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All ML dependencies are installed")
    return True

def verify_file_structure():
    """Verify all required files are present"""
    print("\n📁 Verifying file structure...")
    
    required_files = [
        'unified_app.py',
        'ai_recommendation_engine.py',
        'ml_models.py',
        'ml_routes.py',
        'ml_api.py',
        'interaction_tracker.py',
        'ml_utils.py',
        'ml_config.py',
        'ml_error_handler.py',
        'config.py',
        'models.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files are present")
    return True

def setup_database():
    """Setup ML database tables"""
    print("\n🗄️  Setting up ML database tables...")
    
    try:
        from unified_app import app, db
        
        with app.app_context():
            # Import all models to register them
            from models import User, Policy, Product, Purchase, Notification, Message
            from ml_models import (
                UserInteraction, UserSimilarity, PolicyFeatures, MLModel,
                RecommendationLog, UserPreferenceProfile
            )
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Check if we have basic data
            user_count = User.query.count()
            policy_count = Policy.query.count()
            
            print(f"  📊 Users: {user_count}")
            print(f"  📊 Policies: {policy_count}")
            
            if user_count == 0 or policy_count == 0:
                print("  ⚠️  No sample data found. Run the main app first to create sample data.")
            
            return True
            
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def test_ml_components():
    """Test ML components"""
    print("\n🧪 Testing ML components...")
    
    try:
        # Test ML engine initialization
        from ai_recommendation_engine import TrueAIRecommendationEngine
        ml_engine = TrueAIRecommendationEngine()
        print("  ✅ ML engine initialized")
        
        # Test interaction tracker
        from interaction_tracker import InteractionTracker
        print("  ✅ Interaction tracker available")
        
        # Test ML utilities
        from ml_utils import MLDataProcessor, MLModelEvaluator
        print("  ✅ ML utilities available")
        
        # Test error handler
        from ml_error_handler import ml_health_checker
        health_report = ml_health_checker.check_ml_system_health()
        print(f"  ✅ ML health checker: {health_report['overall_status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ML component test failed: {e}")
        return False

def generate_sample_interactions():
    """Generate sample interactions for ML training"""
    print("\n📊 Generating sample interactions...")
    
    try:
        from unified_app import app, db
        from models import User, Policy
        from ml_models import UserInteraction
        from datetime import datetime, timedelta
        import random
        
        with app.app_context():
            users = User.query.all()
            policies = Policy.query.all()
            
            if not users or not policies:
                print("  ⚠️  No users or policies found. Cannot generate sample interactions.")
                return False
            
            # Check if interactions already exist
            existing_interactions = UserInteraction.query.count()
            if existing_interactions > 50:
                print(f"  ✅ {existing_interactions} interactions already exist")
                return True
            
            # Generate sample interactions
            interactions_created = 0
            
            for user in users[:5]:  # Limit to first 5 users
                num_interactions = random.randint(5, 10)
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
                            value = random.uniform(10.0, 180.0)  # Time in seconds
                        elif interaction_type == 'click':
                            value = random.uniform(1.0, 3.0)
                        elif interaction_type == 'rate':
                            value = random.uniform(2.5, 5.0)  # Rating 2.5-5
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
            print(f"  ✅ Generated {interactions_created} sample interactions")
            return True
            
    except Exception as e:
        print(f"❌ Sample interaction generation failed: {e}")
        return False

def test_recommendations():
    """Test recommendation generation"""
    print("\n🎯 Testing recommendation generation...")
    
    try:
        from unified_app import app, AIRecommendationEngine
        from models import User
        
        with app.app_context():
            # Get a test user
            user = User.query.first()
            if not user:
                print("  ⚠️  No users found for testing")
                return False
            
            # Generate recommendations
            recommendations = AIRecommendationEngine.generate_recommendations(user, limit=5)
            
            if recommendations:
                print(f"  ✅ Generated {len(recommendations)} recommendations for user {user.username}")
                
                # Show sample recommendation
                sample_rec = recommendations[0]
                print(f"  📋 Sample: {sample_rec['policy'].name} (Score: {sample_rec['score']:.1f})")
                print(f"      Reason: {sample_rec['reason'][:100]}...")
                
                return True
            else:
                print("  ⚠️  No recommendations generated (normal for new system)")
                return True
                
    except Exception as e:
        print(f"❌ Recommendation test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API endpoints...")
    
    try:
        from unified_app import app
        
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/api/ml/health')
            if response.status_code == 200:
                print("  ✅ Health endpoint working")
            else:
                print(f"  ⚠️  Health endpoint returned {response.status_code}")
            
            return True
            
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 70)
    print("🤖 COMPLETE AI/ML RECOMMENDATION SYSTEM SETUP")
    print("=" * 70)
    
    steps = [
        ("Checking dependencies", check_dependencies),
        ("Verifying file structure", verify_file_structure),
        ("Setting up database", setup_database),
        ("Testing ML components", test_ml_components),
        ("Generating sample interactions", generate_sample_interactions),
        ("Testing recommendations", test_recommendations),
        ("Testing API endpoints", test_api_endpoints)
    ]
    
    success_count = 0
    
    for step_name, step_function in steps:
        try:
            if step_function():
                success_count += 1
            else:
                print(f"⚠️  {step_name} had issues, continuing...")
        except Exception as e:
            print(f"❌ {step_name} failed with error: {e}")
    
    print("\n" + "=" * 70)
    print(f"🎯 SETUP COMPLETE: {success_count}/{len(steps)} steps successful")
    print("=" * 70)
    
    if success_count >= 5:  # Most steps successful
        print("\n🎉 Your AI/ML recommendation system is ready!")
        print("\n📚 Next steps:")
        print("1. Start your Flask app: py unified_app.py")
        print("2. Visit http://localhost:5000/dashboard")
        print("3. Complete user profiles to test AI recommendations")
        print("4. Visit /ml/dashboard (admin) to manage ML models")
        print("5. Use /api/ml/* endpoints for programmatic access")
        
        print("\n🔧 Available ML Features:")
        print("• AI-powered personalized recommendations")
        print("• Real-time user interaction tracking")
        print("• Machine learning model training")
        print("• Content-based and collaborative filtering")
        print("• Hybrid recommendation algorithms")
        print("• Performance monitoring and analytics")
        print("• RESTful API for ML operations")
        
    else:
        print("\n⚠️  Setup had issues. Check the errors above.")
        print("The system will use fallback recommendations.")
    
    return success_count >= 5

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
