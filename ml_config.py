# ml_config.py - Machine Learning Configuration Settings
import os
from datetime import timedelta

class MLConfig:
    """Configuration settings for the ML recommendation system"""
    
    # Model Training Settings
    COLLABORATIVE_FILTERING = {
        'n_components': 50,  # Number of latent factors for SVD
        'random_state': 42,
        'algorithm': 'randomized',
        'n_iter': 5
    }
    
    CONTENT_BASED_FILTERING = {
        'max_features': 1000,  # Maximum features for TF-IDF
        'stop_words': 'english',
        'ngram_range': (1, 2),  # Unigrams and bigrams
        'min_df': 2,  # Minimum document frequency
        'max_df': 0.95  # Maximum document frequency
    }
    
    HYBRID_MODEL = {
        'n_estimators': 100,  # Number of trees in Random Forest
        'max_depth': 10,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'random_state': 42,
        'n_jobs': -1  # Use all available cores
    }
    
    # Recommendation Settings
    RECOMMENDATION_SETTINGS = {
        'default_limit': 10,
        'max_limit': 50,
        'min_confidence_threshold': 0.1,
        'diversity_factor': 0.3,  # Balance between accuracy and diversity
        'freshness_weight': 0.1,  # Weight for newer policies
        'popularity_weight': 0.05  # Weight for popular policies
    }
    
    # Data Processing Settings
    DATA_PROCESSING = {
        'min_interactions_per_user': 3,
        'min_interactions_per_policy': 5,
        'interaction_decay_days': 90,  # Days after which interactions lose weight
        'batch_size': 1000,
        'max_training_samples': 10000
    }
    
    # Model Evaluation Settings
    EVALUATION = {
        'test_size': 0.2,
        'validation_size': 0.1,
        'cross_validation_folds': 5,
        'metrics': ['precision', 'recall', 'f1_score', 'rmse', 'mae'],
        'evaluation_frequency_hours': 24
    }
    
    # Caching Settings
    CACHING = {
        'model_cache_ttl': 3600,  # 1 hour in seconds
        'recommendation_cache_ttl': 1800,  # 30 minutes
        'user_profile_cache_ttl': 7200,  # 2 hours
        'enable_redis_cache': False,  # Set to True if Redis is available
        'redis_url': os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    }
    
    # Training Schedule Settings
    TRAINING_SCHEDULE = {
        'auto_retrain': True,
        'retrain_interval_hours': 24,
        'min_new_interactions_for_retrain': 50,
        'retrain_on_startup': False,
        'backup_models': True,
        'max_model_backups': 5
    }
    
    # Feature Engineering Settings
    FEATURE_ENGINEERING = {
        'user_features': [
            'age', 'occupation', 'lifestyle', 'health_status', 'marital_status',
            'annual_income', 'risk_tolerance', 'dependents', 'vehicle_ownership',
            'smoking_status', 'exercise_habits', 'education_level', 'employment_type'
        ],
        'policy_features': [
            'premium', 'min_age', 'max_age', 'type', 'risk_level', 'coverage_amount'
        ],
        'interaction_features': [
            'interaction_type', 'interaction_value', 'timestamp', 'session_duration'
        ],
        'derived_features': [
            'user_activity_score', 'policy_popularity_score', 'seasonal_factor'
        ]
    }
    
    # Logging and Monitoring Settings
    MONITORING = {
        'log_level': 'INFO',
        'log_predictions': True,
        'log_training_metrics': True,
        'performance_tracking': True,
        'alert_thresholds': {
            'low_precision': 0.3,
            'low_recall': 0.3,
            'high_error_rate': 0.1
        }
    }
    
    # A/B Testing Settings
    AB_TESTING = {
        'enabled': False,
        'test_groups': ['control', 'treatment_a', 'treatment_b'],
        'traffic_split': [0.5, 0.25, 0.25],  # Control, Treatment A, Treatment B
        'test_duration_days': 14,
        'minimum_sample_size': 1000
    }
    
    # Security Settings
    SECURITY = {
        'encrypt_user_data': False,  # Set to True for production
        'anonymize_logs': True,
        'data_retention_days': 365,
        'gdpr_compliance': True
    }
    
    # Performance Settings
    PERFORMANCE = {
        'max_concurrent_training': 2,
        'training_timeout_minutes': 60,
        'prediction_timeout_seconds': 5,
        'memory_limit_gb': 4,
        'enable_gpu': False  # Set to True if GPU is available
    }
    
    # Database Settings
    DATABASE = {
        'connection_pool_size': 10,
        'connection_pool_timeout': 30,
        'query_timeout': 30,
        'batch_insert_size': 1000
    }
    
    # API Settings
    API = {
        'rate_limit_per_minute': 100,
        'max_recommendations_per_request': 50,
        'enable_api_key_auth': False,
        'api_version': 'v1'
    }

class DevelopmentMLConfig(MLConfig):
    """Development-specific ML configuration"""
    
    # Smaller models for faster development
    COLLABORATIVE_FILTERING = {
        **MLConfig.COLLABORATIVE_FILTERING,
        'n_components': 20,
        'n_iter': 3
    }
    
    HYBRID_MODEL = {
        **MLConfig.HYBRID_MODEL,
        'n_estimators': 50,
        'max_depth': 5
    }
    
    # More frequent retraining for development
    TRAINING_SCHEDULE = {
        **MLConfig.TRAINING_SCHEDULE,
        'retrain_interval_hours': 6,
        'min_new_interactions_for_retrain': 10
    }
    
    # Shorter cache times for development
    CACHING = {
        **MLConfig.CACHING,
        'model_cache_ttl': 300,  # 5 minutes
        'recommendation_cache_ttl': 180  # 3 minutes
    }

class ProductionMLConfig(MLConfig):
    """Production-specific ML configuration"""
    
    # Larger models for better accuracy
    COLLABORATIVE_FILTERING = {
        **MLConfig.COLLABORATIVE_FILTERING,
        'n_components': 100,
        'n_iter': 10
    }
    
    HYBRID_MODEL = {
        **MLConfig.HYBRID_MODEL,
        'n_estimators': 200,
        'max_depth': 15
    }
    
    # Enable security features
    SECURITY = {
        **MLConfig.SECURITY,
        'encrypt_user_data': True,
        'anonymize_logs': True
    }
    
    # Enable caching
    CACHING = {
        **MLConfig.CACHING,
        'enable_redis_cache': True
    }
    
    # Enable A/B testing
    AB_TESTING = {
        **MLConfig.AB_TESTING,
        'enabled': True
    }

class TestingMLConfig(MLConfig):
    """Testing-specific ML configuration"""
    
    # Minimal models for fast testing
    COLLABORATIVE_FILTERING = {
        **MLConfig.COLLABORATIVE_FILTERING,
        'n_components': 5,
        'n_iter': 1
    }
    
    HYBRID_MODEL = {
        **MLConfig.HYBRID_MODEL,
        'n_estimators': 10,
        'max_depth': 3
    }
    
    # Disable caching for testing
    CACHING = {
        **MLConfig.CACHING,
        'model_cache_ttl': 0,
        'recommendation_cache_ttl': 0
    }
    
    # Shorter data retention for testing
    SECURITY = {
        **MLConfig.SECURITY,
        'data_retention_days': 7
    }

# Configuration mapping
ml_config = {
    'development': DevelopmentMLConfig,
    'production': ProductionMLConfig,
    'testing': TestingMLConfig,
    'default': DevelopmentMLConfig
}

def get_ml_config(config_name: str = None):
    """Get ML configuration based on environment"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return ml_config.get(config_name, ml_config['default'])

# Export commonly used configurations
CURRENT_ML_CONFIG = get_ml_config()
