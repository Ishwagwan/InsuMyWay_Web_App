# ml_routes.py - Routes for ML Model Management and Training
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import logging
from datetime import datetime, timedelta
from sqlalchemy import func

from extensions import db
from ai_recommendation_engine import TrueAIRecommendationEngine
from interaction_tracker import InteractionTracker
from ml_models import MLModel, UserInteraction, RecommendationLog, UserPreferenceProfile
from models import User, Policy

logger = logging.getLogger(__name__)

# Create blueprint
ml_bp = Blueprint('ml', __name__, url_prefix='/ml')

# Initialize AI engine
ai_engine = TrueAIRecommendationEngine()

@ml_bp.route('/dashboard')
@login_required
def ml_dashboard():
    """ML system dashboard for admins"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Get ML system statistics
        stats = {
            'total_interactions': UserInteraction.query.count(),
            'total_users_with_interactions': db.session.query(UserInteraction.user_id).distinct().count(),
            'total_recommendations_made': RecommendationLog.query.count(),
            'recommendation_click_rate': 0,
            'recommendation_purchase_rate': 0,
            'active_models': MLModel.query.filter_by(is_active=True).count(),
            'total_models': MLModel.query.count(),
            'last_training_date': None
        }
        
        # Calculate click and purchase rates
        total_recs = RecommendationLog.query.count()
        if total_recs > 0:
            clicked_recs = RecommendationLog.query.filter_by(was_clicked=True).count()
            purchased_recs = RecommendationLog.query.filter_by(was_purchased=True).count()
            stats['recommendation_click_rate'] = (clicked_recs / total_recs) * 100
            stats['recommendation_purchase_rate'] = (purchased_recs / total_recs) * 100
        
        # Get last training date
        last_model = MLModel.query.order_by(MLModel.last_trained.desc()).first()
        if last_model:
            stats['last_training_date'] = last_model.last_trained
        
        # Get recent interactions
        recent_interactions = UserInteraction.query.order_by(
            UserInteraction.timestamp.desc()
        ).limit(10).all()
        
        # Get model performance
        models = MLModel.query.all()
        
        return render_template('ml_dashboard.html', 
                             stats=stats, 
                             recent_interactions=recent_interactions,
                             models=models)
        
    except Exception as e:
        logger.error(f"Error loading ML dashboard: {e}")
        flash('Error loading ML dashboard', 'error')
        return redirect(url_for('dashboard'))

@ml_bp.route('/train', methods=['POST'])
@login_required
def train_models():
    """Train all ML models"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        logger.info(f"Starting ML model training initiated by user {current_user.id}")
        
        # Train all models
        success = ai_engine.train_all_models()
        
        if success:
            flash('ML models trained successfully!', 'success')
            return jsonify({'success': True, 'message': 'Models trained successfully'})
        else:
            flash('Model training failed. Check logs for details.', 'error')
            return jsonify({'success': False, 'message': 'Training failed'})
        
    except Exception as e:
        logger.error(f"Error training models: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@ml_bp.route('/recommendations/<int:user_id>')
@login_required
def get_ai_recommendations(user_id):
    """Get AI recommendations for a user"""
    try:
        # Check if user can access these recommendations
        if not current_user.is_admin and current_user.id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get AI recommendations
        recommendations = ai_engine.get_ai_recommendations(user_id, n_recommendations=10)
        
        # Convert to JSON-serializable format
        rec_data = []
        for rec in recommendations:
            rec_data.append({
                'policy_id': rec['policy'].id,
                'policy_name': rec['policy'].name,
                'policy_type': rec['policy'].type,
                'premium': rec['policy'].premium,
                'score': rec['score'],
                'reason': rec['reason'],
                'algorithm': rec['algorithm'],
                'confidence': rec['confidence']
            })
        
        return jsonify({
            'success': True,
            'recommendations': rec_data,
            'algorithm': 'AI_ML_Hybrid',
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting AI recommendations: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@ml_bp.route('/track/view', methods=['POST'])
@login_required
def track_view():
    """Track page view interaction"""
    try:
        data = request.get_json()
        policy_id = data.get('policy_id')
        time_spent = data.get('time_spent', 1.0)
        
        if not policy_id:
            return jsonify({'error': 'Policy ID required'}), 400
        
        InteractionTracker.track_page_view(current_user.id, policy_id, time_spent)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error tracking view: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@ml_bp.route('/track/click', methods=['POST'])
@login_required
def track_click():
    """Track click interaction"""
    try:
        data = request.get_json()
        policy_id = data.get('policy_id')
        click_type = data.get('click_type', 'general')
        
        if not policy_id:
            return jsonify({'error': 'Policy ID required'}), 400
        
        InteractionTracker.track_click(current_user.id, policy_id, click_type)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error tracking click: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@ml_bp.route('/track/rating', methods=['POST'])
@login_required
def track_rating():
    """Track rating interaction"""
    try:
        data = request.get_json()
        policy_id = data.get('policy_id')
        rating = data.get('rating')
        
        if not policy_id or rating is None:
            return jsonify({'error': 'Policy ID and rating required'}), 400
        
        if not (1 <= rating <= 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        InteractionTracker.track_rating(current_user.id, policy_id, rating)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error tracking rating: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@ml_bp.route('/track/dismiss', methods=['POST'])
@login_required
def track_dismiss():
    """Track dismissal interaction"""
    try:
        data = request.get_json()
        policy_id = data.get('policy_id')
        reason = data.get('reason', 'not_interested')
        
        if not policy_id:
            return jsonify({'error': 'Policy ID required'}), 400
        
        InteractionTracker.track_dismissal(current_user.id, policy_id, reason)
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error tracking dismissal: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@ml_bp.route('/user-profile/<int:user_id>')
@login_required
def get_user_ml_profile(user_id):
    """Get user's ML-generated profile"""
    try:
        # Check access
        if not current_user.is_admin and current_user.id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get interaction summary
        interaction_summary = InteractionTracker.get_user_interaction_summary(user_id)
        
        # Get ML preference profile if exists
        ml_profile = UserPreferenceProfile.query.filter_by(user_id=user_id).first()
        
        profile_data = {
            'user_id': user_id,
            'interaction_summary': interaction_summary,
            'ml_profile': None
        }
        
        if ml_profile:
            profile_data['ml_profile'] = {
                'risk_preference_learned': ml_profile.risk_preference_learned,
                'price_sensitivity': ml_profile.price_sensitivity,
                'confidence_score': ml_profile.confidence_score,
                'last_updated': ml_profile.last_updated.isoformat()
            }
        
        return jsonify({
            'success': True,
            'profile': profile_data
        })
        
    except Exception as e:
        logger.error(f"Error getting user ML profile: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@ml_bp.route('/analytics')
@login_required
def ml_analytics():
    """ML system analytics and insights"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Get analytics data
        analytics = {
            'interaction_trends': [],
            'recommendation_performance': {},
            'user_engagement': {},
            'model_accuracy': {}
        }
        
        # Get interaction trends (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_interactions = db.session.query(
            func.date(UserInteraction.timestamp).label('date'),
            func.count(UserInteraction.id).label('count')
        ).filter(
            UserInteraction.timestamp >= thirty_days_ago
        ).group_by(
            func.date(UserInteraction.timestamp)
        ).all()
        
        analytics['interaction_trends'] = [
            {'date': str(date), 'count': count} 
            for date, count in daily_interactions
        ]
        
        # Get recommendation performance
        total_recs = RecommendationLog.query.count()
        if total_recs > 0:
            clicked_recs = RecommendationLog.query.filter_by(was_clicked=True).count()
            purchased_recs = RecommendationLog.query.filter_by(was_purchased=True).count()
            
            analytics['recommendation_performance'] = {
                'total_recommendations': total_recs,
                'click_through_rate': (clicked_recs / total_recs) * 100,
                'conversion_rate': (purchased_recs / total_recs) * 100,
                'effectiveness_score': ((clicked_recs * 0.3 + purchased_recs * 0.7) / total_recs) * 100
            }
        
        # Get model accuracy data
        models = MLModel.query.all()
        for model in models:
            analytics['model_accuracy'][model.model_name] = {
                'accuracy_score': model.accuracy_score,
                'precision_score': model.precision_score,
                'training_data_size': model.training_data_size,
                'last_trained': model.last_trained.isoformat() if model.last_trained else None
            }
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        logger.error(f"Error getting ML analytics: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
