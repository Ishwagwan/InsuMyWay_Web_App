from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
import logging
import os
from config import config

# Import ML components (will be imported after models are defined)
# from ai_recommendation_engine import TrueAIRecommendationEngine
# from interaction_tracker import InteractionTracker

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    return app

app = create_app()

# Add custom template filters
@app.template_filter('to_frw')
def to_frw_filter(value):
    """Convert price to FRW currency format"""
    try:
        return f"FRW {float(value):,.0f}"
    except (ValueError, TypeError):
        return f"FRW {value}"

@app.template_filter('local_time')
def local_time_filter(value):
    """Convert datetime to local time format"""
    try:
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)
    except (ValueError, TypeError):
        return str(value)

@app.template_filter('local_datetime')
def local_datetime_filter(value):
    """Convert datetime to local datetime format (alias for local_time)"""
    return local_time_filter(value)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Enhanced User Model with comprehensive profile fields
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Basic profile fields
    age = db.Column(db.Integer)
    occupation = db.Column(db.String(100))
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

    # Additional critical fields for enhanced insurance matching
    savings_level = db.Column(db.String(20))  # low, moderate, high, substantial
    debt_status = db.Column(db.String(20))  # none, low, moderate, high
    exercise_habits = db.Column(db.String(20))  # never, rarely, regularly, daily
    smoking_status = db.Column(db.String(20))  # never, former, current
    chronic_conditions = db.Column(db.String(100))  # diabetes, hypertension, etc.
    business_ownership = db.Column(db.String(20))  # none, small, medium, large

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)

class Policy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    coverage = db.Column(db.Text, nullable=False)
    premium = db.Column(db.Float, nullable=False)
    min_age = db.Column(db.Integer, default=18)
    max_age = db.Column(db.Integer, default=80)
    risk_level = db.Column(db.String(20), default='medium')

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='active')
    
    user = db.relationship('User', backref='purchases')
    product = db.relationship('Product', backref='purchases')

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='recommendations')
    policy = db.relationship('Policy', backref='recommendations')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='notifications')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='messages')

# Pure AI/ML Recommendation Engine
class AIRecommendationEngine:
    # Initialize ML engine (will be None if ML components not available)
    _ml_engine = None

    @classmethod
    def get_ml_engine(cls):
        """Get or initialize ML engine"""
        if cls._ml_engine is None:
            try:
                from ai_recommendation_engine import TrueAIRecommendationEngine
                cls._ml_engine = TrueAIRecommendationEngine()
                logger.info("True AI/ML recommendation engine initialized")
            except ImportError as e:
                logger.warning(f"ML components not available: {e}")
                cls._ml_engine = False  # Mark as unavailable
        return cls._ml_engine if cls._ml_engine is not False else None

    # Legacy methods removed - now using pure ML approach

    @staticmethod
    def generate_recommendations(user, limit=9):
        """Generate personalized insurance recommendations using pure AI/ML"""
        if not user or not user.age:
            return []

        # Use ML engine for recommendations
        ml_engine = AIRecommendationEngine.get_ml_engine()
        if ml_engine:
            try:
                ml_recommendations = ml_engine.get_ai_recommendations(user.id, limit)
                if ml_recommendations:
                    logger.info(f"Generated {len(ml_recommendations)} ML recommendations for user {user.id}")
                    return ml_recommendations
                else:
                    logger.warning(f"ML engine returned no recommendations for user {user.id}")
            except Exception as e:
                logger.error(f"ML recommendations failed: {e}")

        # Emergency fallback: return basic policy list with minimal scoring
        logger.warning(f"Using emergency fallback for user {user.id} - ML system unavailable")
        policies = Policy.query.all()
        fallback_recommendations = []

        for policy in policies[:limit]:
            # Very basic compatibility check
            basic_score = 50  # Base score
            if policy.min_age <= (user.age or 25) <= policy.max_age:
                basic_score += 20

            fallback_recommendations.append({
                'policy': policy,
                'score': basic_score,
                'reason': f"Basic match for {user.age or 25} year old. ML system temporarily unavailable.",
                'affordability': 'Unknown',
                'algorithm': 'Emergency_Fallback'
            })

        return fallback_recommendations

    # Removed rule-based affordability calculation - now handled by ML system

    # Removed rule-based recommendation reason generation - now handled by ML system

# Database initialization function
def init_database():
    """Initialize database with sample data"""
    try:
        logger.debug("Creating all tables...")
        db.create_all()
        
        # Check if data already exists
        if User.query.first() is not None:
            logger.debug("Database already contains data, skipping initialization")
            return
        
        logger.debug("Seeding database with initial data...")
        
        # Create admin user
        admin_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = User(
            username='admin',
            password=admin_password,
            email='admin@insuremyway.com',
            is_admin=True,
            age=35,
            occupation='administrator',
            lifestyle='moderate',
            health_status='good'
        )
        db.session.add(admin)
        
        # Add comprehensive products (30 products for better variety)
        products_data = [
            # Health Insurance
            ("Comprehensive Health Insurance", "Complete medical coverage including hospitalization, outpatient care, and emergency services", 75.0, "health"),
            ("Basic Health Plan", "Essential health coverage for routine medical care and basic treatments", 35.0, "health"),
            ("Family Health Package", "Health insurance covering entire family with preventive care benefits", 120.0, "health"),
            ("Senior Health Care", "Specialized health insurance for seniors with chronic condition coverage", 95.0, "health"),
            ("Student Health Plan", "Affordable health coverage designed specifically for students", 25.0, "health"),
            ("Maternity Care Package", "Comprehensive coverage for pregnancy, delivery, and newborn care", 85.0, "health"),
            
            # Life Insurance
            ("Term Life Insurance", "Affordable life insurance providing financial security for your family", 45.0, "life"),
            ("Whole Life Insurance", "Permanent life insurance with cash value accumulation", 125.0, "life"),
            ("Family Life Protection", "Life insurance covering multiple family members", 180.0, "life"),
            ("Business Life Insurance", "Life insurance for business owners and key employees", 200.0, "life"),
            
            # Auto Insurance
            ("Comprehensive Auto Insurance", "Full coverage for your vehicle including collision and theft", 65.0, "auto"),
            ("Third Party Auto Insurance", "Basic liability coverage required by law", 30.0, "auto"),
            ("Motorcycle Insurance", "Specialized coverage for motorcycles and scooters", 40.0, "auto"),
            ("Commercial Vehicle Insurance", "Insurance for business vehicles and fleets", 150.0, "auto"),
            
            # Travel Insurance
            ("International Travel Insurance", "Coverage for overseas travel including medical emergencies", 55.0, "travel"),
            ("Domestic Travel Insurance", "Protection for travel within Rwanda", 20.0, "travel"),
            ("Business Travel Insurance", "Comprehensive coverage for business trips", 80.0, "travel"),
            ("Adventure Travel Insurance", "Specialized coverage for extreme sports and adventure activities", 90.0, "travel"),
            
            # Property Insurance
            ("Home Insurance", "Protection for your home and personal belongings", 110.0, "property"),
            ("Renters Insurance", "Coverage for tenants' personal property and liability", 35.0, "property"),
            ("Business Property Insurance", "Protection for commercial property and equipment", 250.0, "property"),
            
            # Specialty Insurance
            ("Disability Insurance", "Income protection in case of disability", 70.0, "disability"),
            ("Critical Illness Insurance", "Coverage for major illnesses like cancer and heart disease", 100.0, "health"),
            ("Dental Insurance", "Comprehensive dental care coverage", 30.0, "health"),
            ("Vision Insurance", "Eye care and vision correction coverage", 25.0, "health"),
            ("Pet Insurance", "Health coverage for your pets", 40.0, "specialty"),
            ("Cyber Security Insurance", "Protection against cyber threats and data breaches", 120.0, "business"),
            ("Professional Liability Insurance", "Coverage for professional services and errors", 180.0, "business"),
            ("Event Insurance", "Protection for weddings, parties, and special events", 60.0, "specialty"),
            ("Agricultural Insurance", "Coverage for crops, livestock, and farming equipment", 85.0, "agriculture")
        ]
        
        for name, desc, price, category in products_data:
            product = Product(name=name, description=desc, price=price, category=category)
            db.session.add(product)

        # Add comprehensive policies for AI recommendations
        policies_data = [
            # Health Policies
            ("Basic Health Coverage", "health", "Essential medical care including doctor visits and basic treatments", 35.0, 18, 65, "low"),
            ("Comprehensive Health Plan", "health", "Complete medical coverage with hospitalization and specialist care", 75.0, 18, 80, "medium"),
            ("Premium Health Insurance", "health", "Top-tier health coverage with international treatment options", 150.0, 25, 75, "high"),
            ("Family Health Package", "health", "Health insurance covering entire family with preventive care", 120.0, 18, 80, "medium"),
            ("Senior Health Care", "health", "Specialized health insurance for seniors with chronic conditions", 95.0, 60, 85, "high"),
            ("Student Health Plan", "health", "Affordable health coverage designed for students", 25.0, 18, 30, "low"),

            # Life Policies
            ("Term Life Insurance", "life", "Affordable life insurance providing financial security", 45.0, 18, 70, "low"),
            ("Whole Life Insurance", "life", "Permanent life insurance with investment component", 125.0, 25, 80, "medium"),
            ("Family Life Protection", "life", "Life insurance covering multiple family members", 180.0, 25, 75, "medium"),
            ("Business Life Insurance", "life", "Life insurance for business owners and key employees", 200.0, 30, 70, "high"),

            # Auto Policies
            ("Basic Auto Insurance", "auto", "Third-party liability coverage required by law", 30.0, 18, 80, "low"),
            ("Comprehensive Auto Coverage", "auto", "Full vehicle protection including collision and theft", 65.0, 18, 80, "medium"),
            ("Premium Auto Insurance", "auto", "Luxury vehicle coverage with roadside assistance", 120.0, 25, 75, "high"),
            ("Motorcycle Insurance", "auto", "Specialized coverage for motorcycles and scooters", 40.0, 18, 70, "medium"),

            # Travel Policies
            ("Domestic Travel Insurance", "travel", "Protection for travel within Rwanda", 20.0, 18, 80, "low"),
            ("International Travel Coverage", "travel", "Comprehensive coverage for overseas travel", 55.0, 18, 80, "medium"),
            ("Business Travel Insurance", "travel", "Coverage for business trips and conferences", 80.0, 25, 70, "medium"),
            ("Adventure Travel Protection", "travel", "Specialized coverage for extreme sports", 90.0, 21, 65, "high"),

            # Business Policies
            ("Small Business Insurance", "business", "Basic coverage for small businesses", 100.0, 25, 70, "medium"),
            ("Professional Liability", "business", "Coverage for professional services", 180.0, 25, 70, "high"),
            ("Commercial Property Insurance", "business", "Protection for business property", 250.0, 30, 70, "high"),
        ]

        for name, policy_type, coverage, premium, min_age, max_age, risk_level in policies_data:
            policy = Policy(
                name=name,
                type=policy_type,
                coverage=coverage,
                premium=premium,
                min_age=min_age,
                max_age=max_age,
                risk_level=risk_level
            )
            db.session.add(policy)

        db.session.commit()
        logger.debug("Database initialized successfully with comprehensive data")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        db.session.rollback()
        raise

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return render_template('register.html')

        # Create new user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password, email=email)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')

    return render_template('register.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Alias for register function"""
    return register()

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
            flash('Invalid username or password!', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's recommendations
    recommendations = AIRecommendationEngine.generate_recommendations(current_user, limit=5)

    # Get user's purchases
    purchases = Purchase.query.filter_by(user_id=current_user.id).order_by(Purchase.purchase_date.desc()).limit(5).all()

    # Get unread notifications
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()

    # Calculate profile completion with enhanced fields
    profile_fields = [
        current_user.age, current_user.occupation, current_user.lifestyle,
        current_user.health_status, current_user.marital_status, current_user.annual_income,
        current_user.employment_type, current_user.residence_type, current_user.vehicle_ownership,
        current_user.risk_tolerance, current_user.insurance_experience, current_user.coverage_priority,
        current_user.savings_level, current_user.debt_status, current_user.exercise_habits,
        current_user.smoking_status, current_user.dependents, current_user.travel_frequency
    ]
    completed_fields = sum(1 for field in profile_fields if field)
    completion_percentage = int((completed_fields / len(profile_fields)) * 100)

    return render_template('dashboard.html',
                         user=current_user,
                         recommendations=recommendations,
                         purchases=purchases,
                         notifications=notifications,
                         completion_percentage=completion_percentage)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
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

            # New enhanced fields
            current_user.savings_level = request.form.get('savings_level')
            current_user.debt_status = request.form.get('debt_status')
            current_user.exercise_habits = request.form.get('exercise_habits')
            current_user.smoking_status = request.form.get('smoking_status')
            current_user.chronic_conditions = request.form.get('chronic_conditions')
            current_user.business_ownership = request.form.get('business_ownership')

            db.session.commit()
            flash('Profile updated successfully!', 'success')

            # Check if profile is complete and trigger recommendations
            profile_fields = [
                current_user.age, current_user.occupation, current_user.lifestyle,
                current_user.health_status, current_user.marital_status, current_user.annual_income,
                current_user.employment_type, current_user.residence_type, current_user.vehicle_ownership,
                current_user.risk_tolerance, current_user.insurance_experience, current_user.coverage_priority,
                current_user.savings_level, current_user.debt_status, current_user.exercise_habits,
                current_user.smoking_status, current_user.dependents, current_user.travel_frequency
            ]
            completed_fields = sum(1 for field in profile_fields if field)
            completion_percentage = int((completed_fields / len(profile_fields)) * 100)

            # Redirect to recommendations based on completion level
            if completion_percentage >= 100:
                flash('🎉 Profile completed! Here are your AI-powered personalized recommendations.', 'success')
                return redirect(url_for('recommendations'))
            elif completion_percentage >= 70:
                flash('✨ Great progress! Your profile is detailed enough for AI recommendations.', 'success')
                return redirect(url_for('recommendations'))
            elif completion_percentage >= 50:
                flash('📊 Profile updated! Add more details for better AI recommendations.', 'info')
                return redirect(url_for('recommendations'))
            else:
                flash('📝 Profile updated! Complete more fields to unlock AI recommendations.', 'info')
                return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')

    return render_template('profile.html', user=current_user)

@app.route('/products')
def products():
    category = request.args.get('category', 'all')
    search = request.args.get('search', '')

    query = Product.query

    if category != 'all':
        query = query.filter_by(category=category)

    if search:
        query = query.filter(Product.name.contains(search) | Product.description.contains(search))

    products = query.all()
    categories = db.session.query(Product.category).distinct().all()
    categories = [cat[0] for cat in categories]

    # Track search interaction if user is logged in
    if current_user.is_authenticated and search:
        try:
            from interaction_tracker import InteractionTracker
            InteractionTracker.track_search_interaction(current_user.id, search)
        except ImportError:
            logger.warning("Interaction tracker not available")

    return render_template('products.html', products=products, categories=categories,
                         current_category=category, search_term=search)

@app.route('/recommendations')
@login_required
def recommendations():
    """Get AI-powered insurance recommendations for the current user"""

    # Calculate profile completion for context
    profile_fields = [
        current_user.age, current_user.occupation, current_user.lifestyle,
        current_user.health_status, current_user.marital_status, current_user.annual_income,
        current_user.employment_type, current_user.residence_type, current_user.vehicle_ownership,
        current_user.risk_tolerance, current_user.insurance_experience, current_user.coverage_priority,
        current_user.savings_level, current_user.debt_status, current_user.exercise_habits,
        current_user.smoking_status, current_user.dependents, current_user.travel_frequency
    ]
    completed_fields = sum(1 for field in profile_fields if field)
    completion_percentage = int((completed_fields / len(profile_fields)) * 100)

    # Generate AI recommendations
    recommendations = AIRecommendationEngine.generate_recommendations(current_user, limit=12)

    # Determine recommendation quality message based on profile completion
    if completion_percentage >= 100:
        rec_quality_message = "🎯 Perfect! Your complete profile enables our AI to provide highly accurate recommendations."
        rec_quality_level = "excellent"
    elif completion_percentage >= 70:
        rec_quality_message = "✨ Great! Your detailed profile allows our AI to provide personalized recommendations."
        rec_quality_level = "good"
    elif completion_percentage >= 50:
        rec_quality_message = "📊 Good start! Complete more profile fields for even better AI recommendations."
        rec_quality_level = "fair"
    else:
        rec_quality_message = "📝 Basic recommendations shown. Complete your profile for AI-powered personalization."
        rec_quality_level = "basic"

    # Track that user viewed recommendations page
    try:
        from interaction_tracker import InteractionTracker
        # Track each recommended policy as a view
        for rec in recommendations:
            InteractionTracker.track_page_view(current_user.id, rec['policy'].id, 0.5)
    except ImportError:
        logger.warning("Interaction tracker not available")

    return render_template('recommendations.html',
                         user=current_user,
                         recommendations=recommendations,
                         completion_percentage=completion_percentage,
                         rec_quality_message=rec_quality_message,
                         rec_quality_level=rec_quality_level)

@app.route('/chat')
@login_required
def chat():
    """Customer support chat interface"""
    return render_template('chat.html', user=current_user)

@app.route('/purchase/<int:product_id>', methods=['GET', 'POST'])
@login_required
def purchase(product_id):
    """Handle product purchase"""
    product = Product.query.get_or_404(product_id)

    # Track page view for ML
    try:
        from interaction_tracker import InteractionTracker
        InteractionTracker.track_page_view(current_user.id, product_id, 1.0)
    except ImportError:
        logger.warning("Interaction tracker not available")

    if request.method == 'POST':
        try:
            # Create purchase record
            purchase = Purchase(
                user_id=current_user.id,
                product_id=product.id,
                amount=product.price,
                status='completed'
            )
            db.session.add(purchase)

            # Create notification
            notification = Notification(
                user_id=current_user.id,
                title='Purchase Successful',
                message=f'You have successfully purchased {product.name}',
                type='success'
            )
            db.session.add(notification)

            db.session.commit()

            # Track purchase for ML
            try:
                from interaction_tracker import InteractionTracker
                InteractionTracker.track_purchase(current_user.id, product_id, product.price)
                InteractionTracker.track_recommendation_purchase(current_user.id, product_id)
            except ImportError:
                logger.warning("Interaction tracker not available")

            flash(f'Successfully purchased {product.name}!', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error processing purchase: {str(e)}', 'error')

    return render_template('purchase.html', product=product)

@app.route('/notifications')
@login_required
def notifications():
    """View all notifications"""
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', user=current_user, notifications=notifications)

@app.route('/mark_notification_read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first_or_404()
    notification.is_read = True
    db.session.commit()
    return redirect(url_for('notifications'))

@app.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('privacy.html')

@app.route('/admin')
@login_required
def admin():
    """Admin dashboard - only accessible to admin users"""
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

    # Get all users
    users = User.query.all()

    # Get purchase statistics
    purchases = Purchase.query.join(User).all()

    # Get all products
    products = Product.query.all()

    # Get all messages for admin review
    messages = Message.query.join(User).order_by(Message.timestamp.desc()).all()

    # Calculate analytics
    total_revenue = db.session.query(db.func.sum(Purchase.amount)).scalar() or 0

    # Get most purchased product
    most_purchased = db.session.query(
        Product.name,
        db.func.count(Purchase.id).label('count')
    ).join(Purchase).group_by(Product.id).order_by(db.func.count(Purchase.id).desc()).first()

    analytics = {
        'total_users': User.query.count(),
        'total_purchases': Purchase.query.count(),
        'total_products': Product.query.count(),
        'total_messages': Message.query.count(),
        'total_revenue': total_revenue,
        'admin_users': User.query.filter_by(is_admin=True).count(),
        'recent_users': User.query.order_by(User.id.desc()).limit(5).all(),
        'most_purchased_product': most_purchased[0] if most_purchased else 'N/A',
        'most_purchased_count': most_purchased[1] if most_purchased else 0
    }

    return render_template('admin.html',
                         users=users,
                         purchases=purchases,
                         products=products,
                         messages=messages,
                         analytics=analytics)

# Register ML blueprints
try:
    from ml_routes import ml_bp
    from ml_api import ml_api
    app.register_blueprint(ml_bp)
    app.register_blueprint(ml_api)
    logger.info("ML routes and API registered successfully")
except ImportError as e:
    logger.warning(f"ML components not available: {e}")

# Initialize ML health monitoring
try:
    from ml_error_handler import ml_health_checker
    # Perform initial health check
    health_status = ml_health_checker.check_ml_system_health()
    logger.info(f"ML system health: {health_status['overall_status']}")
except ImportError as e:
    logger.warning(f"ML health monitoring not available: {e}")

if __name__ == '__main__':
    with app.app_context():
        init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)
