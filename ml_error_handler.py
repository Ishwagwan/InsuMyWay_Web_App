# ml_error_handler.py - Error handling and fallback mechanisms for ML system
import logging
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class MLError(Exception):
    """Base exception for ML-related errors"""
    pass

class ModelNotTrainedError(MLError):
    """Raised when trying to use an untrained model"""
    pass

class InsufficientDataError(MLError):
    """Raised when there's insufficient data for ML operations"""
    pass

class ModelTrainingError(MLError):
    """Raised when model training fails"""
    pass

class PredictionError(MLError):
    """Raised when prediction fails"""
    pass

class MLErrorHandler:
    """Centralized error handling for ML operations"""
    
    def __init__(self):
        self.error_log = []
        self.fallback_enabled = True
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log ML errors with context"""
        error_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        self.error_log.append(error_entry)
        logger.error(f"ML Error: {error_entry}")
        
        # Keep only last 100 errors
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-100:]
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent ML errors"""
        return self.error_log[-limit:]
    
    def clear_error_log(self):
        """Clear the error log"""
        self.error_log = []

# Global error handler instance
ml_error_handler = MLErrorHandler()

def handle_ml_errors(fallback_value=None, log_context=None):
    """Decorator to handle ML errors gracefully"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log the error
                context = log_context or {}
                context.update({
                    'function': func.__name__,
                    'args': str(args)[:200],  # Truncate long args
                    'kwargs': str(kwargs)[:200]
                })
                ml_error_handler.log_error(e, context)
                
                # Return fallback value
                if fallback_value is not None:
                    return fallback_value
                
                # Re-raise if no fallback
                raise e
        return wrapper
    return decorator

class MLFallbackSystem:
    """Fallback system for when ML components fail"""
    
    @staticmethod
    @handle_ml_errors(fallback_value=[])
    def get_fallback_recommendations(user, limit: int = 10) -> List[Dict[str, Any]]:
        """Generate basic recommendations when ML system fails"""
        try:
            from models import Policy
            
            # Get all policies
            policies = Policy.query.all()
            if not policies:
                return []
            
            fallback_recommendations = []
            
            for policy in policies[:limit]:
                # Basic compatibility scoring
                score = 50  # Base score
                reason = "Basic recommendation (ML system temporarily unavailable)"
                
                # Simple age compatibility
                if user.age and policy.min_age <= user.age <= policy.max_age:
                    score += 20
                    reason = f"Age-appropriate for {user.age} years old"
                
                # Simple type matching based on user profile
                if user.occupation:
                    if user.occupation.lower() in ['construction', 'manual'] and policy.type == 'health':
                        score += 15
                    elif user.occupation.lower() in ['office', 'professional'] and policy.type in ['life', 'health']:
                        score += 10
                
                # Marital status matching
                if user.marital_status == 'married' and policy.type == 'life':
                    score += 10
                
                fallback_recommendations.append({
                    'policy': policy,
                    'score': min(score, 100),
                    'reason': reason,
                    'confidence': 0.3,  # Low confidence for fallback
                    'algorithm': 'Fallback_System',
                    'affordability': 'Unknown'
                })
            
            # Sort by score
            fallback_recommendations.sort(key=lambda x: x['score'], reverse=True)
            return fallback_recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Fallback system failed: {e}")
            return []
    
    @staticmethod
    @handle_ml_errors(fallback_value="Basic recommendation based on your profile")
    def get_fallback_explanation(user, policy, score: float) -> str:
        """Generate basic explanation when ML explanation fails"""
        explanations = []
        
        # Age-based explanation
        if user.age and policy.min_age <= user.age <= policy.max_age:
            explanations.append(f"Suitable for your age ({user.age} years)")
        
        # Occupation-based explanation
        if user.occupation:
            if policy.type == 'health':
                explanations.append("Health coverage recommended for your profession")
            elif policy.type == 'life' and user.marital_status == 'married':
                explanations.append("Life insurance important for married individuals")
        
        # Score-based explanation
        if score >= 70:
            explanations.append("Good match based on your profile")
        elif score >= 50:
            explanations.append("Reasonable option to consider")
        else:
            explanations.append("Basic coverage option")
        
        return "; ".join(explanations) if explanations else "Basic recommendation based on your profile"

class MLHealthChecker:
    """Health checker for ML system components"""
    
    def __init__(self):
        self.last_check = None
        self.health_status = {}
    
    def check_ml_system_health(self) -> Dict[str, Any]:
        """Comprehensive health check of ML system"""
        health_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'components': {},
            'recommendations': []
        }
        
        # Check ML engine availability
        try:
            from ai_recommendation_engine import TrueAIRecommendationEngine
            ml_engine = TrueAIRecommendationEngine()
            health_report['components']['ml_engine'] = 'available'
        except Exception as e:
            health_report['components']['ml_engine'] = f'unavailable: {str(e)}'
            health_report['overall_status'] = 'degraded'
        
        # Check database connectivity
        try:
            from extensions import db
            from ml_models import UserInteraction
            interaction_count = UserInteraction.query.count()
            health_report['components']['database'] = f'connected ({interaction_count} interactions)'
        except Exception as e:
            health_report['components']['database'] = f'error: {str(e)}'
            health_report['overall_status'] = 'unhealthy'
        
        # Check model files
        try:
            import os
            model_files = ['collaborative_model.pkl', 'content_model.pkl', 'hybrid_model.pkl']
            existing_models = [f for f in model_files if os.path.exists(f)]
            health_report['components']['model_files'] = f'{len(existing_models)}/{len(model_files)} available'
            
            if len(existing_models) == 0:
                health_report['recommendations'].append('Train initial ML models')
        except Exception as e:
            health_report['components']['model_files'] = f'error: {str(e)}'
        
        # Check data quality
        try:
            from ml_utils import MLDataValidator
            from models import User
            
            users = User.query.limit(10).all()
            if users:
                sample_user = users[0]
                validation = MLDataValidator.validate_user_data(sample_user)
                health_report['components']['data_quality'] = f"score: {validation['completeness_score']:.2f}"
                
                if validation['completeness_score'] < 0.5:
                    health_report['recommendations'].append('Improve user profile completion')
            else:
                health_report['components']['data_quality'] = 'no_users'
                health_report['recommendations'].append('Add user data for ML training')
                
        except Exception as e:
            health_report['components']['data_quality'] = f'error: {str(e)}'
        
        # Check recent errors
        recent_errors = ml_error_handler.get_recent_errors(5)
        if recent_errors:
            health_report['components']['recent_errors'] = len(recent_errors)
            if len(recent_errors) > 3:
                health_report['overall_status'] = 'degraded'
                health_report['recommendations'].append('Investigate recent ML errors')
        else:
            health_report['components']['recent_errors'] = 0
        
        self.last_check = datetime.utcnow()
        self.health_status = health_report
        
        return health_report
    
    def is_ml_system_healthy(self) -> bool:
        """Quick check if ML system is healthy"""
        if not self.last_check or (datetime.utcnow() - self.last_check).seconds > 300:
            self.check_ml_system_health()
        
        return self.health_status.get('overall_status') in ['healthy', 'degraded']

# Global health checker instance
ml_health_checker = MLHealthChecker()

class MLCircuitBreaker:
    """Circuit breaker pattern for ML operations"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
    
    def call(self, func, *args, **kwargs):
        """Call function with circuit breaker protection"""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
            else:
                raise MLError("Circuit breaker is open - ML system temporarily disabled")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker"""
        if self.last_failure_time is None:
            return True
        
        return (datetime.utcnow() - self.last_failure_time).seconds > self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        self.state = 'closed'
    
    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'

# Global circuit breaker instance
ml_circuit_breaker = MLCircuitBreaker()

def with_circuit_breaker(func):
    """Decorator to apply circuit breaker to ML functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return ml_circuit_breaker.call(func, *args, **kwargs)
    return wrapper
