# ml_models.py - Enhanced Database Models for Machine Learning
from extensions import db
from datetime import datetime
from sqlalchemy import Index

class UserInteraction(db.Model):
    """Track user interactions for ML training"""
    __tablename__ = 'user_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    interaction_type = db.Column(db.String(50), nullable=False)  # view, click, purchase, rate, dismiss
    interaction_value = db.Column(db.Float, default=1.0)  # rating score, time spent, etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(100))  # Track user sessions
    
    # Relationships
    user = db.relationship('User', backref='interactions')
    policy = db.relationship('Policy', backref='interactions')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_policy', 'user_id', 'policy_id'),
        Index('idx_interaction_type', 'interaction_type'),
        Index('idx_timestamp', 'timestamp'),
    )

class UserSimilarity(db.Model):
    """Store computed user similarity scores"""
    __tablename__ = 'user_similarities'
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    algorithm_used = db.Column(db.String(50), nullable=False)  # cosine, pearson, jaccard
    computed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user1 = db.relationship('User', foreign_keys=[user1_id])
    user2 = db.relationship('User', foreign_keys=[user2_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_user_pair', 'user1_id', 'user2_id'),
        Index('idx_similarity_score', 'similarity_score'),
    )

class PolicyFeatures(db.Model):
    """Store computed policy feature vectors for content-based filtering"""
    __tablename__ = 'policy_features'
    
    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    feature_vector = db.Column(db.Text)  # JSON string of feature vector
    feature_names = db.Column(db.Text)  # JSON string of feature names
    algorithm_used = db.Column(db.String(50), nullable=False)  # tfidf, word2vec, etc.
    computed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    policy = db.relationship('Policy', backref='features')

class MLModel(db.Model):
    """Store trained ML models and their metadata"""
    __tablename__ = 'ml_models'
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)  # collaborative, content_based, hybrid
    model_data = db.Column(db.LargeBinary)  # Serialized model
    model_params = db.Column(db.Text)  # JSON string of model parameters
    training_data_size = db.Column(db.Integer)
    accuracy_score = db.Column(db.Float)
    precision_score = db.Column(db.Float)
    recall_score = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_trained = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_model_name', 'model_name'),
        Index('idx_is_active', 'is_active'),
    )

class RecommendationLog(db.Model):
    """Log all recommendations made for analysis and improvement"""
    __tablename__ = 'recommendation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    policy_id = db.Column(db.Integer, db.ForeignKey('policy.id'), nullable=False)
    recommendation_score = db.Column(db.Float, nullable=False)
    algorithm_used = db.Column(db.String(50), nullable=False)
    model_version = db.Column(db.String(50))
    position_in_list = db.Column(db.Integer)  # Position in recommendation list
    was_clicked = db.Column(db.Boolean, default=False)
    was_purchased = db.Column(db.Boolean, default=False)
    user_rating = db.Column(db.Float)  # If user rates the recommendation
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='recommendation_logs')
    policy = db.relationship('Policy', backref='recommendation_logs')
    
    # Indexes
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_was_clicked', 'was_clicked'),
        Index('idx_was_purchased', 'was_purchased'),
    )

class UserPreferenceProfile(db.Model):
    """Store learned user preference profiles"""
    __tablename__ = 'user_preference_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    preference_vector = db.Column(db.Text)  # JSON string of preference weights
    preference_categories = db.Column(db.Text)  # JSON string of category preferences
    risk_preference_learned = db.Column(db.String(20))  # ML-learned risk preference
    price_sensitivity = db.Column(db.Float)  # Learned price sensitivity
    feature_importance = db.Column(db.Text)  # JSON string of feature importance weights
    confidence_score = db.Column(db.Float)  # How confident we are in this profile
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='ml_preference_profile', uselist=False)
    
    # Index
    __table_args__ = (
        Index('idx_user_confidence', 'user_id', 'confidence_score'),
    )
