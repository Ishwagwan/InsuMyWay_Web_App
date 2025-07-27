# ml_utils.py - Machine Learning Utilities and Helper Functions
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
from typing import List, Dict, Tuple, Optional, Any
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.model_selection import cross_val_score

logger = logging.getLogger(__name__)

class MLDataProcessor:
    """Utility class for processing ML data"""
    
    @staticmethod
    def normalize_interaction_scores(interactions: List[Dict]) -> List[Dict]:
        """Normalize interaction scores for better ML training"""
        if not interactions:
            return interactions
        
        # Extract scores
        scores = [interaction.get('interaction_value', 0) for interaction in interactions]
        
        if not scores or max(scores) == min(scores):
            return interactions
        
        # Min-max normalization
        min_score = min(scores)
        max_score = max(scores)
        score_range = max_score - min_score
        
        # Normalize scores
        for i, interaction in enumerate(interactions):
            original_score = interaction.get('interaction_value', 0)
            normalized_score = (original_score - min_score) / score_range
            interaction['normalized_score'] = normalized_score
        
        return interactions
    
    @staticmethod
    def create_user_feature_vector(user) -> List[float]:
        """Create a comprehensive feature vector for a user"""
        features = []
        
        # Basic demographics
        features.append(user.age or 25)  # Default age
        
        # Occupation encoding (one-hot)
        occupations = ['construction', 'office', 'teacher', 'healthcare', 'student', 'manager', 'other']
        user_occupation = (user.occupation or 'other').lower()
        for occ in occupations:
            features.append(1.0 if user_occupation == occ else 0.0)
        
        # Lifestyle encoding
        lifestyles = ['active', 'sedentary', 'moderate', 'family-oriented', 'professional']
        user_lifestyle = (user.lifestyle or 'moderate').lower()
        for lifestyle in lifestyles:
            features.append(1.0 if user_lifestyle == lifestyle else 0.0)
        
        # Health status
        health_statuses = ['excellent', 'good', 'fair', 'poor', 'smoker', 'non-smoker']
        user_health = (user.health_status or 'good').lower()
        for health in health_statuses:
            features.append(1.0 if user_health == health else 0.0)
        
        # Marital status
        marital_statuses = ['single', 'married', 'divorced', 'widowed']
        user_marital = (user.marital_status or 'single').lower()
        for status in marital_statuses:
            features.append(1.0 if user_marital == status else 0.0)
        
        # Income level (ordinal encoding)
        income_levels = {
            'under_1m': 1, '1m_3m': 2, '3m_5m': 3, '5m_10m': 4, 
            '10m_20m': 5, 'over_20m': 6
        }
        user_income = (user.annual_income or 'under_1m').lower()
        features.append(income_levels.get(user_income, 1))
        
        # Risk tolerance (ordinal)
        risk_levels = {'conservative': 1, 'moderate': 2, 'aggressive': 3}
        user_risk = (user.risk_tolerance or 'moderate').lower()
        features.append(risk_levels.get(user_risk, 2))
        
        # Dependents
        features.append(user.dependents or 0)
        
        # Boolean features
        features.append(1.0 if user.vehicle_ownership and user.vehicle_ownership != 'none' else 0.0)
        features.append(1.0 if user.smoking_status == 'current' else 0.0)
        features.append(1.0 if user.exercise_habits in ['regularly', 'daily'] else 0.0)
        
        return features
    
    @staticmethod
    def create_policy_feature_vector(policy) -> List[float]:
        """Create a comprehensive feature vector for a policy"""
        features = []
        
        # Basic policy features
        features.append(policy.premium)
        features.append(policy.min_age)
        features.append(policy.max_age)
        
        # Policy type encoding (one-hot)
        policy_types = ['health', 'life', 'auto', 'home', 'travel', 'business']
        user_type = (policy.type or 'health').lower()
        for ptype in policy_types:
            features.append(1.0 if user_type == ptype else 0.0)
        
        # Risk level encoding
        risk_levels = {'low': 1, 'medium': 2, 'high': 3}
        policy_risk = (policy.risk_level or 'medium').lower()
        features.append(risk_levels.get(policy_risk, 2))
        
        # Coverage amount (if available)
        coverage_amount = getattr(policy, 'coverage_amount', 0) or 0
        features.append(coverage_amount)
        
        # Text features (length-based)
        features.append(len(policy.name or ''))
        features.append(len(policy.coverage or ''))
        
        return features

class MLModelEvaluator:
    """Utility class for evaluating ML models"""
    
    @staticmethod
    def evaluate_recommendation_model(model, X_test, y_test) -> Dict[str, float]:
        """Evaluate a recommendation model"""
        try:
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Convert to binary classification (relevant/not relevant)
            y_test_binary = (y_test > np.median(y_test)).astype(int)
            y_pred_binary = (y_pred > np.median(y_pred)).astype(int)
            
            # Calculate metrics
            precision = precision_score(y_test_binary, y_pred_binary, average='weighted', zero_division=0)
            recall = recall_score(y_test_binary, y_pred_binary, average='weighted', zero_division=0)
            f1 = f1_score(y_test_binary, y_pred_binary, average='weighted', zero_division=0)
            
            # RMSE for regression
            rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
            
            # Mean Absolute Error
            mae = np.mean(np.abs(y_test - y_pred))
            
            return {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'rmse': rmse,
                'mae': mae
            }
            
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            return {
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'rmse': float('inf'),
                'mae': float('inf')
            }
    
    @staticmethod
    def calculate_recommendation_metrics(recommendations: List[Dict], actual_purchases: List[int]) -> Dict[str, float]:
        """Calculate recommendation system metrics"""
        if not recommendations or not actual_purchases:
            return {'precision_at_k': 0.0, 'recall_at_k': 0.0, 'ndcg': 0.0}
        
        # Extract recommended policy IDs
        recommended_ids = [rec['policy'].id for rec in recommendations]
        
        # Calculate precision@k
        relevant_recommended = len(set(recommended_ids) & set(actual_purchases))
        precision_at_k = relevant_recommended / len(recommended_ids) if recommended_ids else 0.0
        
        # Calculate recall@k
        recall_at_k = relevant_recommended / len(actual_purchases) if actual_purchases else 0.0
        
        # Simple NDCG approximation
        dcg = sum(1 / np.log2(i + 2) for i, rec_id in enumerate(recommended_ids) if rec_id in actual_purchases)
        idcg = sum(1 / np.log2(i + 2) for i in range(min(len(actual_purchases), len(recommended_ids))))
        ndcg = dcg / idcg if idcg > 0 else 0.0
        
        return {
            'precision_at_k': precision_at_k,
            'recall_at_k': recall_at_k,
            'ndcg': ndcg
        }

class MLDataValidator:
    """Utility class for validating ML data quality"""
    
    @staticmethod
    def validate_user_data(user) -> Dict[str, Any]:
        """Validate user data quality for ML"""
        validation_result = {
            'is_valid': True,
            'completeness_score': 0.0,
            'issues': [],
            'recommendations': []
        }
        
        # Check required fields
        required_fields = ['age', 'occupation', 'lifestyle']
        missing_required = [field for field in required_fields if not getattr(user, field, None)]
        
        if missing_required:
            validation_result['is_valid'] = False
            validation_result['issues'].append(f"Missing required fields: {', '.join(missing_required)}")
        
        # Calculate completeness
        all_fields = [
            'age', 'occupation', 'lifestyle', 'health_status', 'marital_status',
            'annual_income', 'risk_tolerance', 'dependents', 'vehicle_ownership',
            'smoking_status', 'exercise_habits'
        ]
        
        completed_fields = sum(1 for field in all_fields if getattr(user, field, None))
        validation_result['completeness_score'] = completed_fields / len(all_fields)
        
        # Provide recommendations
        if validation_result['completeness_score'] < 0.5:
            validation_result['recommendations'].append("Complete more profile fields for better recommendations")
        
        if not user.age or user.age < 18 or user.age > 100:
            validation_result['issues'].append("Invalid age value")
        
        return validation_result
    
    @staticmethod
    def validate_interaction_data(interactions: List[Dict]) -> Dict[str, Any]:
        """Validate interaction data quality"""
        validation_result = {
            'is_valid': True,
            'data_quality_score': 0.0,
            'issues': [],
            'statistics': {}
        }
        
        if not interactions:
            validation_result['is_valid'] = False
            validation_result['issues'].append("No interaction data available")
            return validation_result
        
        # Calculate statistics
        interaction_types = [i.get('interaction_type') for i in interactions]
        unique_users = len(set(i.get('user_id') for i in interactions))
        unique_policies = len(set(i.get('policy_id') for i in interactions))
        
        validation_result['statistics'] = {
            'total_interactions': len(interactions),
            'unique_users': unique_users,
            'unique_policies': unique_policies,
            'interaction_types': dict(pd.Series(interaction_types).value_counts())
        }
        
        # Quality checks
        if unique_users < 5:
            validation_result['issues'].append("Insufficient user diversity for ML training")
        
        if unique_policies < 10:
            validation_result['issues'].append("Insufficient policy diversity for ML training")
        
        # Calculate quality score
        diversity_score = min(unique_users / 10, 1.0) * min(unique_policies / 20, 1.0)
        volume_score = min(len(interactions) / 100, 1.0)
        validation_result['data_quality_score'] = (diversity_score + volume_score) / 2
        
        return validation_result

class MLPerformanceMonitor:
    """Utility class for monitoring ML performance"""
    
    @staticmethod
    def track_recommendation_performance(recommendations: List[Dict], user_id: int) -> Dict[str, Any]:
        """Track recommendation performance metrics"""
        performance_data = {
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'num_recommendations': len(recommendations),
            'avg_confidence': 0.0,
            'algorithm_distribution': {},
            'score_distribution': {}
        }
        
        if not recommendations:
            return performance_data
        
        # Calculate average confidence
        confidences = [rec.get('confidence', 0.5) for rec in recommendations]
        performance_data['avg_confidence'] = np.mean(confidences)
        
        # Algorithm distribution
        algorithms = [rec.get('algorithm', 'unknown') for rec in recommendations]
        performance_data['algorithm_distribution'] = dict(pd.Series(algorithms).value_counts())
        
        # Score distribution
        scores = [rec.get('score', 0) for rec in recommendations]
        performance_data['score_distribution'] = {
            'min': min(scores),
            'max': max(scores),
            'mean': np.mean(scores),
            'std': np.std(scores)
        }
        
        return performance_data
    
    @staticmethod
    def generate_performance_report(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate a comprehensive performance report"""
        try:
            from ml_models import RecommendationLog, UserInteraction
            from extensions import db
            
            # Query data within date range
            recommendations = RecommendationLog.query.filter(
                RecommendationLog.timestamp.between(start_date, end_date)
            ).all()
            
            interactions = UserInteraction.query.filter(
                UserInteraction.timestamp.between(start_date, end_date)
            ).all()
            
            report = {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'recommendations': {
                    'total': len(recommendations),
                    'clicked': sum(1 for r in recommendations if r.was_clicked),
                    'purchased': sum(1 for r in recommendations if r.was_purchased),
                    'click_rate': 0.0,
                    'conversion_rate': 0.0
                },
                'interactions': {
                    'total': len(interactions),
                    'unique_users': len(set(i.user_id for i in interactions)),
                    'by_type': {}
                }
            }
            
            # Calculate rates
            if recommendations:
                report['recommendations']['click_rate'] = (
                    report['recommendations']['clicked'] / report['recommendations']['total']
                ) * 100
                report['recommendations']['conversion_rate'] = (
                    report['recommendations']['purchased'] / report['recommendations']['total']
                ) * 100
            
            # Interaction breakdown
            if interactions:
                interaction_types = [i.interaction_type for i in interactions]
                report['interactions']['by_type'] = dict(pd.Series(interaction_types).value_counts())
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {'error': str(e)}
