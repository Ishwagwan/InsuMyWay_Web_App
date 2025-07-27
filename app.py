import logging
import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy import func
from datetime import datetime, timezone, timedelta

# Optional Flask-Mail import
try:
    from flask_mail import Mail, Message as MailMessage
    MAIL_AVAILABLE = True
except ImportError:
    Mail = None
    MailMessage = None
    MAIL_AVAILABLE = False
# PDF generation imports - made optional to avoid dependency issues
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from io import BytesIO
    PDF_AVAILABLE = True
    print("✅ PDF generation available")
except ImportError as e:
    print(f"⚠️ PDF generation not available: {e}")
    PDF_AVAILABLE = False
    # Create dummy objects to prevent errors
    letter = None
    canvas = None
    BytesIO = None
from extensions import db
from models import User, Policy, Recommendation, Notification, TopUpLoan, LoanHistory
from recommendation import get_recommendations as get_ai_recommendations

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Email Service Functions
class EmailService:
    @staticmethod
    def send_loan_notification(user_email, user_name, status, loan_amount=None, rejection_reason=None, admin_notes=None):
        """Send loan application status notification email"""
        try:
            if status == 'approved':
                subject = "Loan Application Approved - InsureMyWay"
                body = f"""
Dear {user_name},

Congratulations! Your loan application has been approved.

Loan Details:
- Amount: {loan_amount:,.0f} RWF
- Status: Approved
- Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

The loan amount will be processed and credited to your account within 1-2 business days.

Thank you for choosing InsureMyWay!

Best regards,
InsureMyWay Team
                """
            elif status == 'rejected':
                subject = "Loan Application Update - InsureMyWay"
                reason_text = {
                    'age_ineligible': 'You must be at least 18 years old to apply for a loan.',
                    'low_income': 'Your monthly income does not meet the minimum requirement of 20,000 RWF.',
                    'poor_history': 'Your loan repayment history does not meet our current requirements.',
                    'admin_review': 'After careful review, your application does not meet our current requirements.'
                }.get(rejection_reason, 'Your application does not meet our current requirements.')

                body = f"""
Dear {user_name},

Thank you for your interest in our loan services. Unfortunately, we cannot approve your loan application at this time.

Reason: {reason_text}

{admin_notes if admin_notes else ''}

You may reapply after addressing the requirements mentioned above.

Best regards,
InsureMyWay Team
                """
            else:  # pending
                subject = "Loan Application Received - InsureMyWay"
                body = f"""
Dear {user_name},

We have received your loan application and it is currently under review.

Application Details:
- Amount: {loan_amount:,.0f} RWF
- Status: Pending Review
- Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Our team will review your application and notify you of the decision within 2-3 business days.

Thank you for choosing InsureMyWay!

Best regards,
InsureMyWay Team
                """

            if MAIL_AVAILABLE and mail:
                msg = MailMessage(subject=subject, recipients=[user_email], body=body)
                mail.send(msg)
                logger.info(f"Loan notification email sent to {user_email} for status: {status}")
                return True
            else:
                logger.warning(f"Email service not available. Would have sent email to {user_email} for status: {status}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email to {user_email}: {str(e)}")
            return False

def check_loan_history(user_id):
    """Check user's loan repayment history and return score"""
    loan_history = LoanHistory.query.filter_by(user_id=user_id).all()

    if not loan_history:
        return 'insufficient'  # No history available

    # Calculate score based on repayment history
    total_loans = len(loan_history)
    completed_loans = len([loan for loan in loan_history if loan.repayment_status == 'completed'])
    defaulted_loans = len([loan for loan in loan_history if loan.repayment_status == 'defaulted'])

    if defaulted_loans > 0:
        return 'poor'
    elif completed_loans >= 2 and (completed_loans / total_loans) >= 0.8:
        return 'good'
    else:
        return 'insufficient'

# TIMEZONE CONFIGURATION
# To fix timestamp display issues, modify the timezone in get_local_timezone() function below.
# The application stores all timestamps in UTC and converts them to your local timezone for display.

# Flask setup
app = Flask(__name__)
app.secret_key = 'your-secret-key-123'  # Replace in production

# Database configuration - Using SQLite (pointing to the correct database file)
import os
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "insuremyway.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'ishimwekevin108@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'beit mnui iibi pdqk')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'InsureMyWay <ishimwekevin108@gmail.com>')

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)

# Initialize Flask-Mail if available
if MAIL_AVAILABLE:
    mail = Mail(app)
else:
    mail = None

# Default seed data
default_seed = {
    'policies': [
        {'name': 'Comprehensive Health Insurance', 'type': 'health', 'premium': 50.0, 'coverage': 'Full medical coverage including hospitalization, outpatient care, and emergency services', 'min_age': 18, 'max_age': 65, 'risk_level': 'medium'},
        {'name': 'Basic Health Insurance', 'type': 'health', 'premium': 25.0, 'coverage': 'Basic medical coverage for routine checkups and minor treatments', 'min_age': 18, 'max_age': 70, 'risk_level': 'low'},
        {'name': 'Premium Health Insurance', 'type': 'health', 'premium': 100.0, 'coverage': 'Premium medical coverage with private rooms, specialist consultations, and dental care', 'min_age': 25, 'max_age': 60, 'risk_level': 'high'},
        {'name': 'Comprehensive Auto Insurance', 'type': 'auto', 'premium': 30.0, 'coverage': 'Full vehicle coverage including collision, theft, and third-party liability', 'min_age': 21, 'max_age': 70, 'risk_level': 'medium'},
        {'name': 'Basic Auto Insurance', 'type': 'auto', 'premium': 15.0, 'coverage': 'Basic vehicle coverage for third-party liability only', 'min_age': 18, 'max_age': 75, 'risk_level': 'low'},
        {'name': 'Premium Auto Insurance', 'type': 'auto', 'premium': 60.0, 'coverage': 'Premium vehicle coverage with roadside assistance, rental car, and comprehensive protection', 'min_age': 25, 'max_age': 65, 'risk_level': 'high'},
        {'name': 'Home Insurance Standard', 'type': 'home', 'premium': 40.0, 'coverage': 'Standard home coverage for fire, theft, and natural disasters', 'min_age': 21, 'max_age': 80, 'risk_level': 'medium'},
        {'name': 'Home Insurance Basic', 'type': 'home', 'premium': 20.0, 'coverage': 'Basic home coverage for fire and theft protection', 'min_age': 18, 'max_age': 85, 'risk_level': 'low'},
        {'name': 'Home Insurance Premium', 'type': 'home', 'premium': 80.0, 'coverage': 'Premium home coverage with full replacement value and additional living expenses', 'min_age': 25, 'max_age': 75, 'risk_level': 'high'},
        {'name': 'Life Insurance Term', 'type': 'life', 'premium': 35.0, 'coverage': 'Term life insurance with death benefit for beneficiaries', 'min_age': 18, 'max_age': 65, 'risk_level': 'medium'},
        {'name': 'Travel Insurance', 'type': 'travel', 'premium': 12.0, 'coverage': 'Travel coverage for trip cancellation, medical emergencies abroad, and lost luggage', 'min_age': 16, 'max_age': 80, 'risk_level': 'low'},
    ],
    'admin': {'username': 'admin', 'password': 'adminpass', 'email': 'admin@example.com', 'is_admin': True}
}

# Additional models for backward compatibility
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_from_admin = db.Column(db.Boolean, nullable=False, default=False)
    user = db.relationship('User', backref='messages')

# Timezone helper functions
def get_local_timezone():
    """Get the local timezone. You can modify this based on your location."""
    # Common timezone offsets (modify as needed):
    # UTC+0: timezone.utc
    # UTC+1: timezone(timedelta(hours=1))  # Central European Time
    # UTC+2: timezone(timedelta(hours=2))  # Eastern European Time
    # UTC+3: timezone(timedelta(hours=3))  # East Africa Time
    # UTC+5: timezone(timedelta(hours=5))  # Pakistan Standard Time
    # UTC+8: timezone(timedelta(hours=8))  # China Standard Time
    # UTC-5: timezone(timedelta(hours=-5)) # Eastern Standard Time
    # UTC-8: timezone(timedelta(hours=-8)) # Pacific Standard Time

    # Set your local timezone here (example: UTC+3 for East Africa)
    return timezone(timedelta(hours=3))  # Change this to match your timezone

def utc_now():
    """Get current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc)

def local_now():
    """Get current local time as timezone-aware datetime"""
    return datetime.now(get_local_timezone())

def utc_to_local(utc_dt):
    """Convert UTC datetime to local timezone"""
    if utc_dt.tzinfo is None:
        # If datetime is naive, assume it's UTC
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(get_local_timezone())

def format_local_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """Format datetime in local timezone"""
    if dt is None:
        return 'N/A'
    local_dt = utc_to_local(dt)
    return local_dt.strftime(format_str)

def format_local_time(dt, format_str='%H:%M'):
    """Format time in local timezone"""
    if dt is None:
        return 'N/A'
    local_dt = utc_to_local(dt)
    return local_dt.strftime(format_str)

# Helper function
def validate_input(username, password, email=None):
    if not username or len(username) < 3:
        return "Username must be at least 3 characters long"
    if not password or len(password) < 6:
        return "Password must be at least 6 characters long"
    if email and '@' not in email:
        return "Invalid email format"
    return None

# Enhanced AI Recommendation logic
def get_recommendations(user):
    # Try to use advanced AI recommendations first
    try:
        ai_recs = get_ai_recommendations(user)
        if ai_recs:
            return ai_recs
    except Exception as e:
        logger.warning(f"AI recommendations failed, falling back to basic: {e}")

    # Enhanced recommendations using comprehensive user profile
    products = Product.query.all()
    recs = []
    for product in products:
        score = 5  # Base score for all products

        # Age-based scoring
        if user.age:
            if user.age < 25:
                score += 15 if 'student' in product.name.lower() or product.price < 30 else 0
            elif user.age < 35:
                score += 10 if product.price < 50 else 0
            elif user.age < 50:
                score += 10 if product.price >= 40 else 0
            else:
                score += 15 if 'senior' in product.name.lower() or product.price >= 60 else 0

        # Occupation-based scoring
        if user.occupation:
            occupation_lower = user.occupation.lower()
            if 'construction' in occupation_lower or 'manual' in occupation_lower:
                score += 10 if 'vehicle' in product.description.lower() or 'disability' in product.description.lower() else 0
            elif 'office' in occupation_lower or 'desk' in occupation_lower:
                score += 8 if 'health' in product.description.lower() else 0
            elif 'teacher' in occupation_lower or 'education' in occupation_lower:
                score += 8 if 'health' in product.description.lower() or 'family' in product.description.lower() else 0
            elif 'business' in occupation_lower or 'entrepreneur' in occupation_lower:
                score += 10 if 'business' in product.description.lower() or 'professional' in product.description.lower() else 0

        # Lifestyle-based scoring
        if user.lifestyle:
            if user.lifestyle == 'active':
                score += 8 if 'travel' in product.description.lower() or 'adventure' in product.description.lower() else 0
            elif user.lifestyle == 'sedentary':
                score += 8 if 'health' in product.description.lower() else 0

        # Health status scoring
        if user.health_status:
            if user.health_status == 'smoker':
                score += 12 if 'health' in product.description.lower() or 'medical' in product.description.lower() else 0
            elif user.health_status in ['excellent', 'good']:
                score += 5 if product.price < 60 else 0

        # Marital status and dependents scoring
        if user.marital_status == 'married' or (user.dependents and user.dependents > 0):
            score += 15 if 'family' in product.description.lower() or 'life' in product.description.lower() else 0

        # Income-based scoring
        if user.annual_income:
            if user.annual_income in ['under_1m', '1m_3m']:
                score += 10 if product.price < 40 else 0
            elif user.annual_income in ['3m_5m', '5m_10m']:
                score += 8 if 40 <= product.price <= 80 else 0
            elif user.annual_income in ['10m_20m', 'over_20m']:
                score += 10 if product.price >= 60 else 0

        # Vehicle ownership scoring
        if user.vehicle_ownership and user.vehicle_ownership != 'none':
            score += 15 if 'auto' in product.description.lower() or 'vehicle' in product.description.lower() or 'motorcycle' in product.description.lower() else 0

        # Travel frequency scoring
        if user.travel_frequency:
            if user.travel_frequency == 'frequent':
                score += 15 if 'travel' in product.description.lower() else 0
            elif user.travel_frequency == 'occasional':
                score += 8 if 'travel' in product.description.lower() else 0

        # Risk tolerance scoring
        if user.risk_tolerance:
            if user.risk_tolerance == 'conservative':
                score += 8 if product.price < 50 else 0
            elif user.risk_tolerance == 'aggressive':
                score += 8 if product.price >= 70 else 0

        # Coverage priority scoring
        if user.coverage_priority:
            if user.coverage_priority == 'cost':
                score += 12 if product.price < 40 else 0
            elif user.coverage_priority == 'coverage':
                score += 12 if product.price >= 60 else 0
        recs.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'score': score,
            'type': 'insurance',
            'premium': product.price,
            'coverage': product.description,
            'min_age': 18,
            'max_age': 65,
            'risk_level': 'medium'
        })
    recs.sort(key=lambda x: x['score'], reverse=True)
    return recs[:3]

# Inject current_user into templates
class AnonymousUser:
    is_authenticated = False
    is_admin = False

# Template filters for timezone conversion
@app.template_filter('local_datetime')
def local_datetime_filter(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """Template filter to convert UTC datetime to local timezone"""
    return format_local_datetime(dt, format_str)

@app.template_filter('local_time')
def local_time_filter(dt, format_str='%H:%M'):
    """Template filter to convert UTC datetime to local time"""
    return format_local_time(dt, format_str)

# Template filter for currency conversion
@app.template_filter('to_frw')
def to_frw_filter(usd_amount):
    """Template filter to convert USD to Rwandan Francs"""
    if usd_amount is None:
        return "0 FRW"
    frw_amount = usd_amount * 1300  # 1 USD = 1300 FRW (approximate exchange rate)
    return f"{frw_amount:,.0f} FRW"

@app.context_processor
def inject_user():
    user = None
    if session.get('user_id'):
        user = User.query.get(session['user_id'])
    return dict(current_user=user or AnonymousUser())

# Routes
@app.route('/')
def index():
    products = Product.query.all()
    policies = [{
        'id': p.id,
        'name': p.name,
        'type': 'insurance',
        'premium': p.price,
        'coverage': p.description,
        'min_age': 18,
        'max_age': 65,
        'risk_level': 'medium'
    } for p in products]
    return render_template('index.html', policies=policies)

@app.route('/products')
def products():
    items = Product.query.all()
    # Fetch purchased products for the current user
    user = User.query.get(session.get('user_id'))
    purchased_products = []
    if user:
        purchases = (
            db.session.query(Purchase, Product)
            .join(Product, Purchase.product_id == Product.id)
            .filter(Purchase.user_id == user.id)
            .all()
        )
        purchased_products = [product for _, product in purchases]
    return render_template('products.html', products=items, purchased_products=purchased_products)

@app.route('/register', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        err = validate_input(username, password, email)
        if err:
            return render_template('register.html', error=err)
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed, email=email)
        try:
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return render_template('register.html', error='Username or email already exists')
        # Registration successful - redirect to login page
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        logger.debug(f"Login attempt for username: {username}")
        err = validate_input(username, password)
        if err:
            logger.error(f"Validation error: {err}")
            return render_template('login.html', error=err)
        user = User.query.filter(func.lower(User.username) == func.lower(username)).first()
        if user:
            logger.debug(f"User found: {user.username}, hashed password: {user.password}")
            if bcrypt.check_password_hash(user.password, password):
                logger.info(f"Login successful for {username}")
                session['user_id'] = user.id

                # Check if user is admin and redirect accordingly
                if user.is_admin:
                    logger.info(f"Admin user {username} redirected to admin panel")
                    return redirect(url_for('admin'))
                else:
                    logger.info(f"Regular user {username} redirected to dashboard")
                    return redirect(url_for('dashboard'))
            else:
                logger.warning(f"Password mismatch for {username}")
        else:
            logger.warning(f"No user found for username: {username}")
        return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    purchases = (
        db.session.query(Purchase, Product)
        .join(Product, Purchase.product_id == Product.id)
        .filter(Purchase.user_id == session['user_id'])
        .all()
    )

    # Create purchase data that matches template expectations
    purchase_data = []
    for pur, prod in purchases:
        # Create an object-like structure that the template can access
        purchase_obj = type('Purchase', (), {
            'product': type('Product', (), {
                'name': prod.name,
                'price': prod.price
            })(),
            'amount': prod.price,
            'purchase_date': pur.purchase_date
        })()
        purchase_data.append(purchase_obj)

    # Also keep the original format for other uses
    purchase_data_dict = [{
        'user_name': user.username,
        'product_name': prod.name,
        'price': prod.price,
        'date': format_local_datetime(pur.purchase_date)
    } for pur, prod in purchases]

    messages = Message.query.filter_by(user_id=session['user_id']).order_by(Message.timestamp.asc()).all()

    # NEW: Calculate spending over time (SQLite compatible)
    try:
        spending_query = (
            db.session.query(
                func.strftime('%Y-%m', Purchase.purchase_date).label('month'),
                func.sum(Product.price).label('total')
            )
            .join(Product, Purchase.product_id == Product.id)
            .filter(Purchase.user_id == session['user_id'])
            .group_by(func.strftime('%Y-%m', Purchase.purchase_date))
            .order_by('month')
            .all()
        )
        spending_labels = [f"{datetime.strptime(month, '%Y-%m').strftime('%b %Y')}" for month, _ in spending_query if month]
        spending_data = [float(total) for _, total in spending_query if total]
    except Exception as e:
        logger.error(f"Error calculating spending data: {e}")
        spending_labels = []
        spending_data = []

    # NEW: Calculate product type distribution
    type_counts = {'health': 0, 'auto': 0, 'home': 0}
    for _, product in purchases:
        desc = product.description.lower()
        if 'medical' in desc:
            type_counts['health'] += 1
        elif 'vehicle' in desc:
            type_counts['auto'] += 1
        elif 'property' in desc:
            type_counts['home'] += 1
    product_type_labels = [key.capitalize() for key, value in type_counts.items() if value > 0]
    product_type_data = [value for key, value in type_counts.items() if value > 0]

    # Calculate profile completion percentage
    profile_fields = [
        user.email, user.age, user.occupation, user.lifestyle, user.health_status,
        user.marital_status, user.dependents, user.annual_income, user.education_level,
        user.employment_type, user.residence_type, user.vehicle_ownership,
        user.travel_frequency, user.risk_tolerance, user.insurance_experience,
        user.coverage_priority, user.family_medical_history, user.hobbies_activities,
        user.location
    ]

    # Count non-empty fields (excluding username and password which are always required)
    completed_fields = sum(1 for field in profile_fields if field is not None and str(field).strip() != '')
    total_fields = len(profile_fields)
    completion_percentage = int((completed_fields / total_fields) * 100) if total_fields > 0 else 0

    return render_template(
        'dashboard.html',
        user=user,
        purchases=purchase_data,
        messages=messages,
        spending_labels=spending_labels,
        spending_data=spending_data,
        product_type_labels=product_type_labels,
        product_type_data=product_type_data,
        completion_percentage=completion_percentage
    )

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if request.method == 'POST':
        # Basic profile fields
        user.age = request.form.get('age', type=int)
        user.occupation = request.form.get('occupation')
        user.lifestyle = request.form.get('lifestyle')
        user.health_status = request.form.get('health_status')

        # Enhanced profile fields
        user.marital_status = request.form.get('marital_status')
        user.dependents = request.form.get('dependents', type=int) or 0
        user.annual_income = request.form.get('annual_income')
        user.education_level = request.form.get('education_level')
        user.employment_type = request.form.get('employment_type')
        user.residence_type = request.form.get('residence_type')
        user.vehicle_ownership = request.form.get('vehicle_ownership')
        user.travel_frequency = request.form.get('travel_frequency')
        user.risk_tolerance = request.form.get('risk_tolerance')
        user.insurance_experience = request.form.get('insurance_experience')
        user.coverage_priority = request.form.get('coverage_priority')
        user.family_medical_history = request.form.get('family_medical_history')
        user.hobbies_activities = request.form.get('hobbies_activities')
        user.location = request.form.get('location')

        try:
            db.session.commit()
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            return render_template('profile.html', error=str(e), user=user)

    return render_template('profile.html', user=user)

@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('login'))

    if not all([user.age, user.occupation, user.lifestyle, user.health_status]):
        return redirect(url_for('profile'))

    insurance_type = request.form.get('insurance_type', 'all')
    max_budget = request.form.get('max_budget', type=float) or float('inf')

    recs = get_recommendations(user)

    for r in recs:
        # Use coverage or recommendation field if description doesn't exist
        desc_text = r.get('description', r.get('coverage', r.get('recommendation', ''))).lower()
        if 'medical' in desc_text or 'health' in desc_text:
            r['type'] = 'health'
        elif 'vehicle' in desc_text or 'auto' in desc_text:
            r['type'] = 'auto'
        elif 'property' in desc_text or 'home' in desc_text:
            r['type'] = 'home'
        else:
            r['type'] = r.get('type', 'insurance')
        # Ensure both price and premium fields exist
        price_value = r.get('price', r.get('premium', 0))
        r['premium'] = price_value
        r['price'] = price_value
        r['coverage'] = r.get('description', r.get('coverage', 'Standard coverage'))

        # Add missing attributes that the template expects
        r['min_age'] = r.get('min_age', 18)
        r['max_age'] = r.get('max_age', 65)

        # Ensure description field exists
        if 'description' not in r:
            r['description'] = r.get('coverage', r.get('recommendation', 'Standard insurance coverage'))

        # Determine risk level based on price and type
        price = r.get('price', r.get('premium', 0))
        if price < 30:
            r['risk_level'] = 'low'
        elif price < 60:
            r['risk_level'] = 'medium'
        else:
            r['risk_level'] = 'high'

    if insurance_type != 'all':
        recs = [r for r in recs if r['type'] == insurance_type]
    recs = [r for r in recs if r['premium'] <= max_budget]

    chart_labels = [r['name'] for r in recs] if recs else []
    chart_data = [r['score'] for r in recs] if recs else []

    # Calculate profile completion percentage
    profile_fields = [
        user.email, user.age, user.occupation, user.lifestyle, user.health_status,
        user.marital_status, user.dependents, user.annual_income, user.education_level,
        user.employment_type, user.residence_type, user.vehicle_ownership,
        user.travel_frequency, user.risk_tolerance, user.insurance_experience,
        user.coverage_priority, user.family_medical_history, user.hobbies_activities,
        user.location
    ]

    # Count non-empty fields (excluding username and password which are always required)
    completed_fields = sum(1 for field in profile_fields if field is not None and str(field).strip() != '')
    total_fields = len(profile_fields)
    completion_percentage = int((completed_fields / total_fields) * 100) if total_fields > 0 else 0

    # Determine recommendation quality level and message based on completion percentage
    if completion_percentage >= 90:
        rec_quality_level = 'excellent'
        rec_quality_message = 'Excellent! Your complete profile enables our AI to provide highly accurate recommendations.'
    elif completion_percentage >= 70:
        rec_quality_level = 'good'
        rec_quality_message = 'Good profile completeness. AI recommendations are quite accurate.'
    elif completion_percentage >= 50:
        rec_quality_level = 'fair'
        rec_quality_message = 'Fair profile data. Complete more fields for better AI recommendations.'
    else:
        rec_quality_level = 'poor'
        rec_quality_message = 'Limited profile data. Please complete your profile for accurate AI recommendations.'

    return render_template(
        'recommendations.html',
        recommendations=recs,
        chart_labels=chart_labels,
        chart_data=chart_data,
        insurance_type=insurance_type,
        max_budget=None if max_budget == float('inf') else max_budget,
        completion_percentage=completion_percentage,
        rec_quality_level=rec_quality_level,
        rec_quality_message=rec_quality_message,
        user=user
    )

@app.route('/purchase/<int:product_id>', methods=['GET', 'POST'])
def purchase(product_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            purchase = Purchase(user_id=session['user_id'], product_id=product_id, purchase_date=utc_now())
            db.session.add(purchase)
            db.session.commit()
            flash('Purchase successful!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Purchase failed: {str(e)}', 'error')
            return redirect(url_for('recommendations'))
    
    return render_template('purchase.html', product=product)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    logger.debug(f"Session user_id: {session.get('user_id')}")
    if not session.get('user_id'):
        logger.warning("No user_id in session, redirecting to login.")
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        logger.warning("User not found, redirecting to login.")
        return redirect(url_for('login'))
    
    logger.debug(f"User: {user.username}, is_admin: {user.is_admin}")
    if not user.is_admin:
        flash('Access denied: Admin privileges required.', 'error')
        logger.warning("User is not admin, redirecting to dashboard.")
        return redirect(url_for('dashboard'))

    logger.info("Admin dashboard accessed successfully.")

    users = User.query.all()

    purchase_stats = (
        db.session.query(Purchase, User, Product)
        .join(User, Purchase.user_id == User.id)
        .join(Product, Purchase.product_id == Product.id)
        .all()
    )
    purchase_data = [{
        'user_name': purchase_user.username,
        'product_name': product.name,
        'price': product.price,
        'purchase_date': format_local_datetime(purchase.purchase_date)
    } for purchase, purchase_user, product in purchase_stats]

    products = Product.query.all()

    messages = Message.query.join(User).order_by(Message.timestamp.asc()).all()

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'reply':
            message_id = request.form.get('message_id', type=int)
            reply_content = request.form.get('reply_content')
            if message_id and reply_content:
                message = Message.query.get_or_404(message_id)
                admin_reply = Message(
                    user_id=user.id,
                    content=reply_content,
                    is_from_admin=True
                )
                db.session.add(admin_reply)
                db.session.commit()
                flash('Reply sent successfully!', 'success')
            else:
                flash('Reply content cannot be empty.', 'error')
            return redirect(url_for('admin'))

        elif action == 'add':
            name = request.form.get('name')
            description = request.form.get('description')
            price = request.form.get('price', type=float)
            if name and description and price is not None:
                product = Product(name=name, description=description, price=price)
                db.session.add(product)
                db.session.commit()
                flash('Product added successfully!', 'success')
            else:
                flash('All fields are required to add a product.', 'error')

        elif action == 'edit':
            product_id = request.form.get('product_id', type=int)
            product = Product.query.get_or_404(product_id)
            product.name = request.form.get('name', product.name)
            product.description = request.form.get('description', product.description)
            product.price = request.form.get('price', type=float, default=product.price)
            db.session.commit()
            flash('Product updated successfully!', 'success')

        elif action == 'delete':
            product_id = request.form.get('product_id', type=int)
            product = Product.query.get_or_404(product_id)
            Purchase.query.filter_by(product_id=product_id).delete()
            db.session.delete(product)
            db.session.commit()
            flash('Product deleted successfully!', 'success')

        return redirect(url_for('admin'))

    total_users = User.query.count()
    total_purchases = Purchase.query.count()
    total_revenue = db.session.query(func.sum(Product.price)).join(Purchase, Product.id == Purchase.product_id).scalar() or 0.0
    most_purchased_product = (
        db.session.query(Product.name, func.count(Purchase.id).label('count'))
        .join(Purchase, Product.id == Purchase.product_id)
        .group_by(Product.id)
        .order_by(func.count(Purchase.id).desc())
        .first()
    )

    analytics = {
        'total_users': total_users,
        'total_purchases': total_purchases,
        'total_revenue': total_revenue,
        'most_purchased_product': most_purchased_product[0] if most_purchased_product else 'N/A',
        'most_purchased_count': most_purchased_product[1] if most_purchased_product else 0
    }

    return render_template(
        'admin.html',
        users=users,
        purchase_stats=purchase_data,
        products=products,
        analytics=analytics,
        messages=messages
    )
@app.route('/about')
def about():
    return "About Page (Placeholder)"

@app.route('/contact')
def contact():
    return "Contact Page (Placeholder)"

@app.route('/privacy')
def privacy():
    return "Privacy Policy (Placeholder)"

@app.route('/terms')
def terms():
    return "Terms of Service (Placeholder)"

@app.route('/chat')
def chat():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    messages = Message.query.filter_by(user_id=session['user_id']).order_by(Message.timestamp.asc()).all()
    return render_template('chat.html', user=user, messages=messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    if not session.get('user_id'):
        return jsonify({'error': 'Please log in'}), 401
    user = User.query.get(session['user_id'])
    content = request.json.get('message')
    if not content:
        return jsonify({'error': 'Message cannot be empty'}), 400

    user_message = Message(user_id=user.id, content=content, is_from_admin=False)
    db.session.add(user_message)

    auto_reply = Message(
        user_id=user.id,
        content="Please be patient, an admin will respond soon.",
        is_from_admin=True
    )
    db.session.add(auto_reply)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': user_message.content,
        'auto_reply': auto_reply.content,
        'timestamp': format_local_datetime(user_message.timestamp)
    })

@app.route('/get_response', methods=['POST'])
def get_response():
    if not session.get('user_id'):
        return jsonify({'error': 'Please log in'}), 401
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({'response': 'Please provide your needs or ask for help!'})

    user = User.query.get(session['user_id'])
    if not user or not all([user.age, user.occupation, user.lifestyle, user.health_status]):
        return jsonify({'response': 'Please complete your profile with age, occupation, lifestyle, and health status to get personalized recommendations.'})

    recommendations = get_recommendations(user)
    response = "Based on your profile and input, here are some tailored recommendations:\n"
    if recommendations:
        for rec in recommendations:
            frw_price = f"{rec['price'] * 1300:,.0f} FRW"
            response += f"- {rec['name']} ({frw_price}): {rec['description']} (Score: {rec['score']})\n"
    else:
        response += "No specific recommendations match your input. Please provide more details (e.g., 'I need health insurance') or update your profile.\n"

    if 'health' in user_input.lower() or 'medical' in user_input.lower():
        response += "- Consider exploring our Health Insurance plans.\n"
    if 'car' in user_input.lower() or 'vehicle' in user_input.lower():
        response += "- Our Car Insurance might suit your needs.\n"
    if 'home' in user_input.lower() or 'property' in user_input.lower():
        response += "- Home Insurance could be a good option.\n"

    return jsonify({'response': response})

@app.route('/apply_topup_loan', methods=['GET', 'POST'])
def apply_topup_loan():
    """Handle top-up loan applications"""
    if not session.get('user_id'):
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            data = request.get_json()
            age = int(data.get('age', 0))
            monthly_income = float(data.get('monthly_income', 0))
            loan_amount = float(data.get('loan_amount', 50000))  # Default loan amount

            # Step 1: Age validation - reject if under 18
            if age < 18:
                return jsonify({
                    'success': False,
                    'status': 'rejected',
                    'reason': 'age_ineligible',
                    'message': 'You must be at least 18 years old to apply for a loan.'
                })

            # Step 2: Income validation - reject if below 20,000 RWF
            if monthly_income < 20000:
                return jsonify({
                    'success': False,
                    'status': 'rejected',
                    'reason': 'low_income',
                    'message': 'Your monthly income must be at least 20,000 RWF to qualify for a loan.'
                })

            # Step 3: Check loan history
            loan_history_score = check_loan_history(user.id)

            # Create loan application record
            loan_application = TopUpLoan(
                user_id=user.id,
                age=age,
                monthly_income=monthly_income,
                loan_amount=loan_amount,
                loan_history_score=loan_history_score
            )

            # Step 4: Determine loan status based on history
            if loan_history_score == 'good':
                loan_application.status = 'approved'
                status_message = f'Congratulations! Your loan application for {loan_amount:,.0f} RWF has been approved instantly due to your excellent repayment history.'
            elif loan_history_score == 'poor':
                loan_application.status = 'rejected'
                loan_application.rejection_reason = 'poor_history'
                status_message = 'Your loan application has been rejected due to poor repayment history.'
            else:  # insufficient history
                loan_application.status = 'pending'
                status_message = f'Your loan application for {loan_amount:,.0f} RWF is under review. You will be notified within 2-3 business days.'

            db.session.add(loan_application)
            db.session.commit()

            # Send email notification
            EmailService.send_loan_notification(
                user_email=user.email,
                user_name=user.username,
                status=loan_application.status,
                loan_amount=loan_amount,
                rejection_reason=loan_application.rejection_reason
            )

            # Create system notification
            notification = Notification(
                user_id=user.id,
                title=f'Loan Application {loan_application.status.title()}',
                message=status_message,
                type='success' if loan_application.status == 'approved' else 'warning' if loan_application.status == 'pending' else 'error'
            )
            db.session.add(notification)
            db.session.commit()

            return jsonify({
                'success': True,
                'status': loan_application.status,
                'message': status_message,
                'loan_amount': loan_amount,
                'application_id': loan_application.id
            })

        except Exception as e:
            db.session.rollback()
            logger.error(f"Loan application error: {str(e)}")
            return jsonify({
                'success': False,
                'status': 'error',
                'message': 'An error occurred while processing your application. Please try again.'
            })

    return render_template('topup_loan.html', user=user)

@app.route('/admin/loan_applications')
def admin_loan_applications():
    """Admin interface for reviewing loan applications"""
    if not session.get('user_id'):
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

    # Get all loan applications
    applications = TopUpLoan.query.order_by(TopUpLoan.application_date.desc()).all()

    # Get statistics
    total_applications = len(applications)
    pending_applications = len([app for app in applications if app.status == 'pending'])
    approved_applications = len([app for app in applications if app.status == 'approved'])
    rejected_applications = len([app for app in applications if app.status == 'rejected'])

    stats = {
        'total': total_applications,
        'pending': pending_applications,
        'approved': approved_applications,
        'rejected': rejected_applications
    }

    return render_template('admin_loan_applications.html',
                         applications=applications,
                         stats=stats,
                         user=user)

@app.route('/admin/review_loan/<int:loan_id>', methods=['POST'])
def review_loan_application(loan_id):
    """Admin route to approve/reject loan applications"""
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Please log in'}), 401

    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    try:
        loan_application = TopUpLoan.query.get_or_404(loan_id)
        data = request.get_json()

        action = data.get('action')  # 'approve' or 'reject'
        admin_notes = data.get('notes', '')

        if action == 'approve':
            loan_application.status = 'approved'
            message = 'Loan application approved successfully.'
        elif action == 'reject':
            loan_application.status = 'rejected'
            loan_application.rejection_reason = 'admin_review'
            message = 'Loan application rejected.'
        else:
            return jsonify({'success': False, 'message': 'Invalid action'})

        loan_application.admin_review_notes = admin_notes
        loan_application.review_date = datetime.utcnow()

        db.session.commit()

        # Send email notification to the user
        applicant = User.query.get(loan_application.user_id)
        EmailService.send_loan_notification(
            user_email=applicant.email,
            user_name=applicant.username,
            status=loan_application.status,
            loan_amount=loan_application.loan_amount,
            rejection_reason=loan_application.rejection_reason,
            admin_notes=admin_notes
        )

        # Create system notification for the user
        notification = Notification(
            user_id=applicant.id,
            title=f'Loan Application {loan_application.status.title()}',
            message=f'Your loan application has been {loan_application.status}.',
            type='success' if loan_application.status == 'approved' else 'error'
        )
        db.session.add(notification)
        db.session.commit()

        return jsonify({'success': True, 'message': message})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error reviewing loan application: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while processing the review.'})

@app.route('/download_form')
def download_form():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    # Check if PDF generation is available
    if not PDF_AVAILABLE:
        flash('PDF generation is currently unavailable. Please contact support.', 'error')
        return redirect(url_for('dashboard'))

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Fetch purchased products
    purchases = (
        db.session.query(Purchase, Product)
        .join(Product, Purchase.product_id == Product.id)
        .filter(Purchase.user_id == user.id)
        .all()
    )
    purchased_products = [product for _, product in purchases]

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, f"Purchased Products Form for {user.username}")
    p.drawString(100, 730, "Purchased Products:")
    y = 710
    for product in purchased_products:
        frw_price = f"{product.price * 1300:,.0f} FRW"
        p.drawString(120, y, f"- {product.name} ({frw_price})")
        y -= 20
    p.showPage()
    p.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="purchased_products_form.pdf", mimetype="application/pdf")

@app.route('/download_user_details')
def download_user_details():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    # Check if PDF generation is available
    if not PDF_AVAILABLE:
        flash('PDF generation is currently unavailable. Please contact support.', 'error')
        return redirect(url_for('dashboard'))

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, f"User Details Form for {user.username}")
    p.drawString(100, 730, f"Username: {user.username}")
    p.drawString(100, 710, f"Email: {user.email if user.email else 'Not provided'}")
    p.drawString(100, 690, f"Age: {user.age if user.age else 'Not provided'}")
    p.drawString(100, 670, f"Occupation: {user.occupation if user.occupation else 'Not provided'}")
    p.drawString(100, 650, f"Lifestyle: {user.lifestyle if user.lifestyle else 'Not provided'}")
    p.drawString(100, 630, f"Health Status: {user.health_status if user.health_status else 'Not provided'}")
    p.showPage()
    p.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="user_details_form.pdf", mimetype="application/pdf")

# Enhanced database seeding with AI features
def seed_database():
    try:
        # Seed policies (advanced AI features)
        if not Policy.query.first():
            for policy_data in default_seed['policies']:
                policy = Policy(**policy_data)
                db.session.add(policy)
            db.session.commit()
            logger.debug("Default policies seeded successfully.")

        # Seed comprehensive products for better user engagement
        if not Product.query.first():
            comprehensive_products = [
                # Health Insurance Options
                {'name': 'Basic Health Plan', 'description': 'Essential medical coverage for routine care, doctor visits, and emergency services', 'price': 25000.0},
                {'name': 'Family Health Shield', 'description': 'Comprehensive family medical coverage including pediatric care, maternity, and wellness programs', 'price': 65000.0},
                {'name': 'Premium Health Plus', 'description': 'Premium medical coverage with private rooms, specialist consultations, dental, and vision care', 'price': 120000.0},
                {'name': 'Senior Health Care', 'description': 'Specialized health coverage for seniors with chronic disease management and home care services', 'price': 85000.0},

                # Auto Insurance Options
                {'name': 'Basic Auto Coverage', 'description': 'Essential vehicle protection with liability coverage and roadside assistance', 'price': 20000.0},
                {'name': 'Complete Auto Shield', 'description': 'Full vehicle protection including collision, comprehensive, theft, and rental car coverage', 'price': 45000.0},
                {'name': 'Luxury Auto Protection', 'description': 'Premium vehicle coverage for luxury cars with gap insurance and concierge services', 'price': 95000.0},
                {'name': 'Commercial Vehicle Insurance', 'description': 'Business vehicle coverage for fleets, delivery trucks, and commercial transportation', 'price': 75.0},

                # Home Insurance Options
                {'name': 'Basic Home Protection', 'description': 'Essential home coverage for fire, theft, and basic natural disasters', 'price': 30000.0},
                {'name': 'Complete Home Guard', 'description': 'Comprehensive home protection with full replacement cost and additional living expenses', 'price': 60000.0},
                {'name': 'Luxury Home Estate', 'description': 'Premium home coverage for high-value properties with art, jewelry, and collectibles protection', 'price': 150000.0},
                {'name': 'Rental Property Shield', 'description': 'Landlord insurance covering rental properties, liability, and loss of rental income', 'price': 55000.0},

                # Life Insurance Options
                {'name': 'Term Life Basic', 'description': 'Affordable term life insurance providing financial security for your family', 'price': 25000.0},
                {'name': 'Whole Life Investment', 'description': 'Permanent life insurance with cash value growth and investment opportunities', 'price': 80000.0},
                {'name': 'Universal Life Flex', 'description': 'Flexible life insurance with adjustable premiums and death benefits', 'price': 70000.0},

                # Specialty Insurance Options
                {'name': 'Travel Adventure Pro', 'description': 'Comprehensive travel insurance covering trips, medical emergencies, and adventure sports', 'price': 35000.0},
                {'name': 'Pet Health Guardian', 'description': 'Complete pet insurance covering veterinary care, surgeries, and wellness treatments', 'price': 40000.0},
                {'name': 'Cyber Security Shield', 'description': 'Digital protection against identity theft, cyber attacks, and online fraud', 'price': 15000.0},
                {'name': 'Business Liability Pro', 'description': 'Professional liability insurance for businesses, consultants, and service providers', 'price': 90000.0},
                {'name': 'Student Protection Plan', 'description': 'Affordable insurance for students covering health, personal property, and liability', 'price': 18000.0},
                {'name': 'Disability Income Guard', 'description': 'Income protection insurance providing benefits if you become unable to work', 'price': 50000.0},
                {'name': 'Critical Illness Shield', 'description': 'Coverage for major illnesses like cancer, heart attack, and stroke with lump sum benefits', 'price': 45000.0},
            ]
            for prod in comprehensive_products:
                db.session.add(Product(**prod))
            db.session.commit()
            logger.debug("Comprehensive products seeded successfully.")

        # Seed admin user
        admin_conf = default_seed['admin']
        if not User.query.filter_by(username=admin_conf['username']).first():
            hashed = bcrypt.generate_password_hash(admin_conf['password']).decode('utf-8')
            admin = User(
                username=admin_conf['username'],
                password=hashed,
                email=admin_conf['email'],
                is_admin=admin_conf.get('is_admin', True)
            )
            db.session.add(admin)
            db.session.commit()
            logger.debug("Admin user created successfully.")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during seeding: {str(e)}")
        raise

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist (preserve existing data)
        logger.debug("Creating tables if they don't exist...")
        db.create_all()

        # Verify table creation
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        logger.debug(f"Tables in database: {tables}")
        if 'user' in tables:
            columns = [col['name'] for col in inspector.get_columns('user')]
            logger.debug(f"Columns in 'user' table: {columns}")

        # Only seed if database is empty (preserve existing users)
        seed_database()
    app.run(debug=True, port=5000, host='0.0.0.0')