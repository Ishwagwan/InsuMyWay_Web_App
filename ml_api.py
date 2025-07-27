# ml_api.py - API endpoints for ML recommendation system
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any

from ml_error_handler import handle_ml_errors, ml_health_checker
from ml_utils import MLPerformanceMonitor, MLDataValidator
from interaction_tracker import InteractionTracker

logger = logging.getLogger(__name__)

# Create ML API blueprint
ml_api = Blueprint('ml_api', __name__, url_prefix='/api/ml')

@ml_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for ML system"""
    try:
        health_report = ml_health_checker.check_ml_system_health()
        return jsonify({
            'status': 'success',
            'data': health_report
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Health check failed',
            'error': str(e)
        }), 500

@ml_api.route('/recommendations/<int:user_id>', methods=['GET'])
@login_required
@handle_ml_errors(fallback_value={'status': 'error', 'message': 'ML system unavailable'})
def get_user_recommendations(user_id: int):
    """Get AI recommendations for a specific user"""
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), 403
        
        # Get parameters
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 50)  # Cap at 50 recommendations
        
        # Get user
        from models import User
        user = User.query.get_or_404(user_id)
        
        # Generate recommendations
        from unified_app import AIRecommendationEngine
        recommendations = AIRecommendationEngine.generate_recommendations(user, limit=limit)
        
        # Format response
        formatted_recommendations = []
        for rec in recommendations:
            formatted_recommendations.append({
                'policy_id': rec['policy'].id,
                'policy_name': rec['policy'].name,
                'policy_type': rec['policy'].type,
                'premium': rec['policy'].premium,
                'score': rec['score'],
                'reason': rec['reason'],
                'confidence': rec.get('confidence', 0.5),
                'algorithm': rec.get('algorithm', 'Unknown'),
                'affordability': rec.get('affordability', 'Unknown')
            })
        
        # Track API usage
        InteractionTracker.track_api_usage(user_id, 'recommendations', len(formatted_recommendations))
        
        return jsonify({
            'status': 'success',
            'data': {
                'user_id': user_id,
                'recommendations': formatted_recommendations,
                'total_count': len(formatted_recommendations),
                'generated_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting recommendations for user {user_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate recommendations',
            'error': str(e)
        }), 500

@ml_api.route('/track/interaction', methods=['POST'])
@login_required
@handle_ml_errors(fallback_value={'status': 'error', 'message': 'Tracking failed'})
def track_interaction():
    """Track user interaction for ML learning"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['policy_id', 'interaction_type']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Track the interaction
        interaction_id = InteractionTracker.track_interaction(
            user_id=current_user.id,
            policy_id=data['policy_id'],
            interaction_type=data['interaction_type'],
            interaction_value=data.get('interaction_value', 1.0),
            session_id=data.get('session_id'),
            metadata=data.get('metadata', {})
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'interaction_id': interaction_id,
                'message': 'Interaction tracked successfully'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error tracking interaction: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to track interaction',
            'error': str(e)
        }), 500

@ml_api.route('/user/profile/validate', methods=['POST'])
@login_required
@handle_ml_errors(fallback_value={'status': 'error', 'message': 'Validation failed'})
def validate_user_profile():
    """Validate user profile for ML quality"""
    try:
        user_id = request.json.get('user_id', current_user.id)
        
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), 403
        
        # Get user
        from models import User
        user = User.query.get_or_404(user_id)
        
        # Validate profile
        validation_result = MLDataValidator.validate_user_data(user)
        
        return jsonify({
            'status': 'success',
            'data': validation_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating user profile: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Profile validation failed',
            'error': str(e)
        }), 500

@ml_api.route('/models/train', methods=['POST'])
@login_required
@handle_ml_errors(fallback_value={'status': 'error', 'message': 'Training failed'})
def train_models():
    """Trigger ML model training (admin only)"""
    try:
        if not current_user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        # Get training parameters
        data = request.get_json() or {}
        force_retrain = data.get('force_retrain', False)
        
        # Initialize ML engine and train
        from ai_recommendation_engine import TrueAIRecommendationEngine
        ml_engine = TrueAIRecommendationEngine()
        
        training_result = ml_engine.train_all_models(force_retrain=force_retrain)
        
        return jsonify({
            'status': 'success',
            'data': {
                'training_result': training_result,
                'message': 'Model training completed',
                'trained_at': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error training models: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Model training failed',
            'error': str(e)
        }), 500

@ml_api.route('/analytics/performance', methods=['GET'])
@login_required
@handle_ml_errors(fallback_value={'status': 'error', 'message': 'Analytics unavailable'})
def get_performance_analytics():
    """Get ML system performance analytics (admin only)"""
    try:
        if not current_user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin access required'
            }), 403
        
        # Get date range
        days = request.args.get('days', 7, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Generate performance report
        performance_report = MLPerformanceMonitor.generate_performance_report(start_date, end_date)
        
        return jsonify({
            'status': 'success',
            'data': performance_report
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting performance analytics: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get analytics',
            'error': str(e)
        }), 500

@ml_api.route('/user/<int:user_id>/insights', methods=['GET'])
@login_required
@handle_ml_errors(fallback_value={'status': 'error', 'message': 'Insights unavailable'})
def get_user_insights(user_id: int):
    """Get ML insights for a specific user"""
    try:
        # Validate user access
        if current_user.id != user_id and not current_user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), 403
        
        # Get user interactions
        from ml_models import UserInteraction
        interactions = UserInteraction.query.filter_by(user_id=user_id).all()
        
        # Calculate insights
        insights = {
            'total_interactions': len(interactions),
            'interaction_types': {},
            'most_viewed_policies': [],
            'engagement_score': 0.0,
            'profile_completeness': 0.0,
            'recommendation_accuracy': 0.0
        }
        
        if interactions:
            # Interaction type breakdown
            interaction_types = {}
            for interaction in interactions:
                interaction_type = interaction.interaction_type
                interaction_types[interaction_type] = interaction_types.get(interaction_type, 0) + 1
            insights['interaction_types'] = interaction_types
            
            # Most viewed policies
            policy_views = {}
            for interaction in interactions:
                if interaction.interaction_type == 'view':
                    policy_id = interaction.policy_id
                    policy_views[policy_id] = policy_views.get(policy_id, 0) + 1
            
            # Get top 5 most viewed policies
            top_policies = sorted(policy_views.items(), key=lambda x: x[1], reverse=True)[:5]
            insights['most_viewed_policies'] = [{'policy_id': pid, 'views': views} for pid, views in top_policies]
            
            # Calculate engagement score (simplified)
            total_value = sum(i.interaction_value for i in interactions)
            insights['engagement_score'] = min(total_value / 100, 1.0)  # Normalize to 0-1
        
        # Get user profile completeness
        from models import User
        user = User.query.get(user_id)
        if user:
            validation = MLDataValidator.validate_user_data(user)
            insights['profile_completeness'] = validation['completeness_score']
        
        return jsonify({
            'status': 'success',
            'data': insights
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user insights for {user_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get user insights',
            'error': str(e)
        }), 500

@ml_api.route('/policies/similar/<int:policy_id>', methods=['GET'])
@login_required
@handle_ml_errors(fallback_value={'status': 'error', 'message': 'Similar policies unavailable'})
def get_similar_policies(policy_id: int):
    """Get policies similar to the specified policy"""
    try:
        limit = request.args.get('limit', 5, type=int)
        limit = min(limit, 20)  # Cap at 20 similar policies
        
        # Get the target policy
        from models import Policy
        target_policy = Policy.query.get_or_404(policy_id)
        
        # Get ML engine
        from ai_recommendation_engine import TrueAIRecommendationEngine
        ml_engine = TrueAIRecommendationEngine()
        
        # Get similar policies using content-based filtering
        similar_policies = ml_engine.get_similar_policies(policy_id, limit)
        
        # Format response
        formatted_policies = []
        for policy_data in similar_policies:
            policy = policy_data['policy']
            formatted_policies.append({
                'policy_id': policy.id,
                'policy_name': policy.name,
                'policy_type': policy.type,
                'premium': policy.premium,
                'similarity_score': policy_data['similarity_score'],
                'reason': policy_data.get('reason', 'Similar features and coverage')
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'target_policy_id': policy_id,
                'similar_policies': formatted_policies,
                'total_count': len(formatted_policies)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting similar policies for {policy_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get similar policies',
            'error': str(e)
        }), 500

@ml_api.route('/feedback', methods=['POST'])
@login_required
@handle_ml_errors(fallback_value={'status': 'error', 'message': 'Feedback submission failed'})
def submit_feedback():
    """Submit feedback on recommendations for ML improvement"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Validate required fields
        required_fields = ['policy_id', 'feedback_type', 'rating']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Track feedback as interaction
        InteractionTracker.track_feedback(
            user_id=current_user.id,
            policy_id=data['policy_id'],
            feedback_type=data['feedback_type'],
            rating=data['rating'],
            comment=data.get('comment', ''),
            metadata=data.get('metadata', {})
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'message': 'Feedback submitted successfully',
                'note': 'Your feedback helps improve our AI recommendations'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to submit feedback',
            'error': str(e)
        }), 500

# Error handlers for the ML API blueprint
@ml_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404

@ml_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

@ml_api.errorhandler(403)
def forbidden(error):
    return jsonify({
        'status': 'error',
        'message': 'Access forbidden'
    }), 403
