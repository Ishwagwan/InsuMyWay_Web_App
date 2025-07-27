# interaction_tracker.py - Track User Interactions for ML Training
from flask import request, session
from datetime import datetime
import uuid
import logging
from typing import Optional

from extensions import db
from ml_models import UserInteraction, RecommendationLog
from models import User, Policy

logger = logging.getLogger(__name__)

class InteractionTracker:
    """Track user interactions for machine learning training"""
    
    @staticmethod
    def track_page_view(user_id: int, policy_id: int, time_spent: float = 1.0):
        """Track when user views a policy page"""
        try:
            interaction = UserInteraction(
                user_id=user_id,
                policy_id=policy_id,
                interaction_type='view',
                interaction_value=min(time_spent, 300),  # Cap at 5 minutes
                session_id=InteractionTracker._get_session_id()
            )
            db.session.add(interaction)
            db.session.commit()
            logger.debug(f"Tracked page view: user {user_id}, policy {policy_id}")
            
        except Exception as e:
            logger.error(f"Error tracking page view: {e}")
    
    @staticmethod
    def track_click(user_id: int, policy_id: int, click_type: str = 'general'):
        """Track when user clicks on a policy or related element"""
        try:
            # Different click types have different values
            click_values = {
                'general': 1.0,
                'details': 2.0,
                'compare': 1.5,
                'quote': 3.0,
                'purchase_button': 4.0
            }
            
            interaction = UserInteraction(
                user_id=user_id,
                policy_id=policy_id,
                interaction_type='click',
                interaction_value=click_values.get(click_type, 1.0),
                session_id=InteractionTracker._get_session_id()
            )
            db.session.add(interaction)
            db.session.commit()
            logger.debug(f"Tracked click: user {user_id}, policy {policy_id}, type {click_type}")
            
        except Exception as e:
            logger.error(f"Error tracking click: {e}")
    
    @staticmethod
    def track_purchase(user_id: int, policy_id: int, purchase_amount: float):
        """Track when user purchases a policy"""
        try:
            interaction = UserInteraction(
                user_id=user_id,
                policy_id=policy_id,
                interaction_type='purchase',
                interaction_value=min(purchase_amount / 100, 10.0),  # Normalize purchase amount
                session_id=InteractionTracker._get_session_id()
            )
            db.session.add(interaction)
            db.session.commit()
            logger.info(f"Tracked purchase: user {user_id}, policy {policy_id}, amount {purchase_amount}")
            
        except Exception as e:
            logger.error(f"Error tracking purchase: {e}")
    
    @staticmethod
    def track_rating(user_id: int, policy_id: int, rating: float):
        """Track when user rates a policy or recommendation"""
        try:
            interaction = UserInteraction(
                user_id=user_id,
                policy_id=policy_id,
                interaction_type='rate',
                interaction_value=rating,  # Rating from 1-5
                session_id=InteractionTracker._get_session_id()
            )
            db.session.add(interaction)
            db.session.commit()
            logger.debug(f"Tracked rating: user {user_id}, policy {policy_id}, rating {rating}")
            
        except Exception as e:
            logger.error(f"Error tracking rating: {e}")
    
    @staticmethod
    def track_dismissal(user_id: int, policy_id: int, reason: str = 'not_interested'):
        """Track when user dismisses or shows negative interest in a policy"""
        try:
            # Different dismissal reasons have different negative values
            dismissal_values = {
                'not_interested': -1.0,
                'too_expensive': -0.5,
                'wrong_type': -0.8,
                'bad_reviews': -1.5
            }
            
            interaction = UserInteraction(
                user_id=user_id,
                policy_id=policy_id,
                interaction_type='dismiss',
                interaction_value=dismissal_values.get(reason, -1.0),
                session_id=InteractionTracker._get_session_id()
            )
            db.session.add(interaction)
            db.session.commit()
            logger.debug(f"Tracked dismissal: user {user_id}, policy {policy_id}, reason {reason}")
            
        except Exception as e:
            logger.error(f"Error tracking dismissal: {e}")
    
    @staticmethod
    def track_recommendation_click(user_id: int, policy_id: int, position: int):
        """Track when user clicks on a recommendation"""
        try:
            # Update recommendation log
            rec_log = RecommendationLog.query.filter_by(
                user_id=user_id,
                policy_id=policy_id
            ).order_by(RecommendationLog.timestamp.desc()).first()
            
            if rec_log:
                rec_log.was_clicked = True
                rec_log.position_in_list = position
            
            # Also track as regular interaction
            InteractionTracker.track_click(user_id, policy_id, 'recommendation')
            
            db.session.commit()
            logger.debug(f"Tracked recommendation click: user {user_id}, policy {policy_id}, position {position}")
            
        except Exception as e:
            logger.error(f"Error tracking recommendation click: {e}")
    
    @staticmethod
    def track_recommendation_purchase(user_id: int, policy_id: int):
        """Track when user purchases a recommended policy"""
        try:
            # Update recommendation log
            rec_log = RecommendationLog.query.filter_by(
                user_id=user_id,
                policy_id=policy_id
            ).order_by(RecommendationLog.timestamp.desc()).first()
            
            if rec_log:
                rec_log.was_purchased = True
            
            db.session.commit()
            logger.info(f"Tracked recommendation purchase: user {user_id}, policy {policy_id}")
            
        except Exception as e:
            logger.error(f"Error tracking recommendation purchase: {e}")
    
    @staticmethod
    def track_search_interaction(user_id: int, search_query: str, clicked_policy_id: Optional[int] = None):
        """Track user search behavior"""
        try:
            if clicked_policy_id:
                # Track the click on search result
                InteractionTracker.track_click(user_id, clicked_policy_id, 'search_result')
            
            # You could also store search queries for analysis
            logger.debug(f"Tracked search: user {user_id}, query '{search_query}'")
            
        except Exception as e:
            logger.error(f"Error tracking search interaction: {e}")
    
    @staticmethod
    def _get_session_id() -> str:
        """Get or create session ID for tracking"""
        try:
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())
            return session['session_id']
        except:
            return str(uuid.uuid4())
    
    @staticmethod
    def get_user_interaction_summary(user_id: int) -> dict:
        """Get summary of user interactions for analysis"""
        try:
            interactions = UserInteraction.query.filter_by(user_id=user_id).all()
            
            summary = {
                'total_interactions': len(interactions),
                'views': len([i for i in interactions if i.interaction_type == 'view']),
                'clicks': len([i for i in interactions if i.interaction_type == 'click']),
                'purchases': len([i for i in interactions if i.interaction_type == 'purchase']),
                'ratings': len([i for i in interactions if i.interaction_type == 'rate']),
                'dismissals': len([i for i in interactions if i.interaction_type == 'dismiss']),
                'avg_rating': 0,
                'most_viewed_policies': [],
                'preferred_policy_types': []
            }
            
            # Calculate average rating
            ratings = [i.interaction_value for i in interactions if i.interaction_type == 'rate']
            if ratings:
                summary['avg_rating'] = sum(ratings) / len(ratings)
            
            # Find most viewed policies
            policy_views = {}
            for interaction in interactions:
                if interaction.interaction_type == 'view':
                    policy_views[interaction.policy_id] = policy_views.get(interaction.policy_id, 0) + 1
            
            summary['most_viewed_policies'] = sorted(
                policy_views.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting user interaction summary: {e}")
            return {}

# Decorator for automatic interaction tracking
def track_interaction(interaction_type: str):
    """Decorator to automatically track interactions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Extract user_id and policy_id from function context
                # This would need to be customized based on your route structure
                user_id = getattr(request, 'user_id', None)
                policy_id = kwargs.get('policy_id') or request.args.get('policy_id')
                
                if user_id and policy_id:
                    if interaction_type == 'view':
                        InteractionTracker.track_page_view(user_id, policy_id)
                    elif interaction_type == 'click':
                        InteractionTracker.track_click(user_id, policy_id)
                
                return result
                
            except Exception as e:
                logger.error(f"Error in interaction tracking decorator: {e}")
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

    @staticmethod
    def track_api_usage(user_id, endpoint, result_count):
        """Track API usage for monitoring"""
        try:
            interaction = UserInteraction(
                user_id=user_id,
                policy_id=0,  # Special ID for API calls
                interaction_type='api_call',
                interaction_value=result_count,
                session_id=f"api_{endpoint}",
                metadata={'endpoint': endpoint, 'result_count': result_count}
            )

            db.session.add(interaction)
            db.session.commit()
            logger.debug(f"API usage tracked for user {user_id}: {endpoint}")

        except Exception as e:
            logger.error(f"Error tracking API usage: {e}")
            db.session.rollback()

    @staticmethod
    def track_feedback(user_id, policy_id, feedback_type, rating, comment='', metadata=None):
        """Track user feedback on recommendations"""
        try:
            interaction = UserInteraction(
                user_id=user_id,
                policy_id=policy_id,
                interaction_type='feedback',
                interaction_value=rating,
                session_id=f"feedback_{datetime.utcnow().timestamp()}",
                metadata={
                    'feedback_type': feedback_type,
                    'comment': comment,
                    **(metadata or {})
                }
            )

            db.session.add(interaction)
            db.session.commit()
            logger.debug(f"Feedback tracked for user {user_id}, policy {policy_id}: {feedback_type}")

        except Exception as e:
            logger.error(f"Error tracking feedback: {e}")
            db.session.rollback()
