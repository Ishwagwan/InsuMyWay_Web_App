# ai_recommendation_engine.py - True AI/ML Recommendation Engine
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, linear_kernel
from sklearn.decomposition import TruncatedSVD
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any
import logging

from extensions import db
from models import User, Policy
from ml_models import (
    UserInteraction, UserSimilarity, PolicyFeatures, MLModel,
    RecommendationLog, UserPreferenceProfile
)

logger = logging.getLogger(__name__)

class TrueAIRecommendationEngine:
    """
    Advanced Machine Learning Recommendation Engine
    Implements multiple ML algorithms for insurance recommendations
    """
    
    def __init__(self):
        self.collaborative_model = None
        self.content_model = None
        self.hybrid_model = None
        self.scaler = StandardScaler()
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.policy_features_matrix = None
        self.user_item_matrix = None
        
    def collect_training_data(self) -> pd.DataFrame:
        """Collect and prepare training data from user interactions"""
        try:
            # Get user interactions
            interactions = db.session.query(
                UserInteraction.user_id,
                UserInteraction.policy_id,
                UserInteraction.interaction_type,
                UserInteraction.interaction_value,
                UserInteraction.timestamp
            ).all()
            
            if not interactions:
                logger.warning("No interaction data found for training")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(interactions, columns=[
                'user_id', 'policy_id', 'interaction_type', 'interaction_value', 'timestamp'
            ])
            
            # Weight different interaction types
            interaction_weights = {
                'view': 1.0,
                'click': 2.0,
                'add_to_cart': 3.0,
                'purchase': 5.0,
                'rate': 4.0,
                'dismiss': -1.0
            }
            
            df['weighted_score'] = df.apply(
                lambda row: row['interaction_value'] * interaction_weights.get(row['interaction_type'], 1.0),
                axis=1
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error collecting training data: {e}")
            return pd.DataFrame()
    
    def build_user_item_matrix(self, interactions_df: pd.DataFrame) -> np.ndarray:
        """Build user-item interaction matrix for collaborative filtering"""
        try:
            # Create pivot table
            user_item_df = interactions_df.pivot_table(
                index='user_id',
                columns='policy_id',
                values='weighted_score',
                aggfunc='sum',
                fill_value=0
            )
            
            self.user_item_matrix = user_item_df.values
            self.user_ids = user_item_df.index.tolist()
            self.policy_ids = user_item_df.columns.tolist()
            
            return self.user_item_matrix
            
        except Exception as e:
            logger.error(f"Error building user-item matrix: {e}")
            return np.array([])
    
    def train_collaborative_filtering(self, user_item_matrix: np.ndarray) -> bool:
        """Train collaborative filtering model using Matrix Factorization"""
        try:
            if user_item_matrix.size == 0:
                logger.warning("Empty user-item matrix, cannot train collaborative filtering")
                return False
            
            # Use Truncated SVD for matrix factorization
            n_components = min(50, min(user_item_matrix.shape) - 1)
            self.collaborative_model = TruncatedSVD(n_components=n_components, random_state=42)
            
            # Fit the model
            self.collaborative_model.fit(user_item_matrix)
            
            # Save model to database
            self._save_model_to_db(
                model_name="collaborative_filtering",
                model_type="collaborative",
                model_obj=self.collaborative_model,
                training_data_size=user_item_matrix.shape[0]
            )
            
            logger.info(f"Collaborative filtering model trained with {n_components} components")
            return True
            
        except Exception as e:
            logger.error(f"Error training collaborative filtering: {e}")
            return False
    
    def extract_policy_features(self) -> bool:
        """Extract features from policies for content-based filtering"""
        try:
            policies = Policy.query.all()
            if not policies:
                logger.warning("No policies found for feature extraction")
                return False
            
            # Combine text features
            policy_texts = []
            policy_ids = []
            
            for policy in policies:
                text_features = f"{policy.name} {policy.coverage} {policy.type} {policy.risk_level}"
                policy_texts.append(text_features)
                policy_ids.append(policy.id)
            
            # Create TF-IDF features
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(policy_texts)
            
            # Store features in database
            for i, policy_id in enumerate(policy_ids):
                feature_vector = tfidf_matrix[i].toarray().flatten()
                feature_names = self.tfidf_vectorizer.get_feature_names_out()
                
                # Check if features already exist
                existing_features = PolicyFeatures.query.filter_by(
                    policy_id=policy_id,
                    algorithm_used='tfidf'
                ).first()
                
                if existing_features:
                    existing_features.feature_vector = json.dumps(feature_vector.tolist())
                    existing_features.feature_names = json.dumps(feature_names.tolist())
                    existing_features.computed_at = datetime.utcnow()
                else:
                    policy_features = PolicyFeatures(
                        policy_id=policy_id,
                        feature_vector=json.dumps(feature_vector.tolist()),
                        feature_names=json.dumps(feature_names.tolist()),
                        algorithm_used='tfidf'
                    )
                    db.session.add(policy_features)
            
            db.session.commit()
            self.policy_features_matrix = tfidf_matrix
            
            logger.info(f"Extracted features for {len(policies)} policies")
            return True
            
        except Exception as e:
            logger.error(f"Error extracting policy features: {e}")
            return False
    
    def train_content_based_model(self) -> bool:
        """Train content-based filtering model"""
        try:
            if self.policy_features_matrix is None:
                if not self.extract_policy_features():
                    return False
            
            # For content-based, we use the TF-IDF matrix directly
            # The model is essentially the cosine similarity computation
            self.content_model = "tfidf_cosine"  # Placeholder for the approach
            
            # Save model metadata
            self._save_model_to_db(
                model_name="content_based_filtering",
                model_type="content_based",
                model_obj=self.tfidf_vectorizer,
                training_data_size=self.policy_features_matrix.shape[0]
            )
            
            logger.info("Content-based filtering model trained")
            return True
            
        except Exception as e:
            logger.error(f"Error training content-based model: {e}")
            return False
    
    def train_hybrid_model(self, interactions_df: pd.DataFrame) -> bool:
        """Train hybrid model combining collaborative and content-based approaches"""
        try:
            if interactions_df.empty:
                logger.warning("No interaction data for hybrid model training")
                return False
            
            # Prepare features for hybrid model
            features = []
            targets = []
            
            for _, interaction in interactions_df.iterrows():
                user_id = interaction['user_id']
                policy_id = interaction['policy_id']
                
                # Get user features
                user = User.query.get(user_id)
                if not user:
                    continue
                
                # Get policy features
                policy = Policy.query.get(policy_id)
                if not policy:
                    continue
                
                # Create feature vector
                feature_vector = self._create_hybrid_features(user, policy)
                if feature_vector:
                    features.append(feature_vector)
                    targets.append(interaction['weighted_score'])
            
            if not features:
                logger.warning("No features created for hybrid model")
                return False
            
            # Convert to numpy arrays
            X = np.array(features)
            y = np.array(targets)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train Random Forest model
            self.hybrid_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.hybrid_model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.hybrid_model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            
            # Save model
            self._save_model_to_db(
                model_name="hybrid_model",
                model_type="hybrid",
                model_obj=self.hybrid_model,
                training_data_size=len(X_train),
                accuracy_metrics={'mse': mse, 'mae': mae}
            )
            
            logger.info(f"Hybrid model trained. MSE: {mse:.4f}, MAE: {mae:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"Error training hybrid model: {e}")
            return False
    
    def _create_hybrid_features(self, user: User, policy: Policy) -> Optional[List[float]]:
        """Create feature vector for hybrid model"""
        try:
            features = []
            
            # User features
            features.extend([
                user.age or 0,
                1 if user.occupation == 'construction' else 0,
                1 if user.occupation == 'office' else 0,
                1 if user.occupation == 'teacher' else 0,
                1 if user.lifestyle == 'active' else 0,
                1 if user.lifestyle == 'sedentary' else 0,
                1 if user.health_status == 'smoker' else 0,
                1 if user.marital_status == 'married' else 0,
                user.dependents or 0,
            ])
            
            # Policy features
            features.extend([
                policy.premium,
                policy.min_age,
                policy.max_age,
                1 if policy.type == 'health' else 0,
                1 if policy.type == 'life' else 0,
                1 if policy.type == 'auto' else 0,
                1 if policy.risk_level == 'low' else 0,
                1 if policy.risk_level == 'medium' else 0,
                1 if policy.risk_level == 'high' else 0,
            ])
            
            return features
            
        except Exception as e:
            logger.error(f"Error creating hybrid features: {e}")
            return None
    
    def _save_model_to_db(self, model_name: str, model_type: str, model_obj, 
                         training_data_size: int, accuracy_metrics: Dict = None):
        """Save trained model to database"""
        try:
            # Serialize model
            model_data = joblib.dumps(model_obj)
            
            # Check if model exists
            existing_model = MLModel.query.filter_by(
                model_name=model_name,
                model_type=model_type
            ).first()
            
            if existing_model:
                existing_model.model_data = model_data
                existing_model.training_data_size = training_data_size
                existing_model.last_trained = datetime.utcnow()
                if accuracy_metrics:
                    existing_model.accuracy_score = accuracy_metrics.get('mse')
                    existing_model.precision_score = accuracy_metrics.get('mae')
            else:
                ml_model = MLModel(
                    model_name=model_name,
                    model_type=model_type,
                    model_data=model_data,
                    training_data_size=training_data_size
                )
                if accuracy_metrics:
                    ml_model.accuracy_score = accuracy_metrics.get('mse')
                    ml_model.precision_score = accuracy_metrics.get('mae')
                
                db.session.add(ml_model)
            
            db.session.commit()
            logger.info(f"Model {model_name} saved to database")
            
        except Exception as e:
            logger.error(f"Error saving model to database: {e}")

    def get_collaborative_recommendations(self, user_id: int, n_recommendations: int = 10) -> List[Tuple[int, float]]:
        """Generate recommendations using collaborative filtering"""
        try:
            if self.collaborative_model is None or self.user_item_matrix is None:
                logger.warning("Collaborative model not trained")
                return []

            # Find user index
            if user_id not in self.user_ids:
                logger.warning(f"User {user_id} not found in training data")
                return []

            user_index = self.user_ids.index(user_id)

            # Get user's latent factors
            user_factors = self.collaborative_model.transform(self.user_item_matrix[user_index:user_index+1])

            # Reconstruct user preferences for all items
            reconstructed_preferences = self.collaborative_model.inverse_transform(user_factors)[0]

            # Get items user hasn't interacted with
            user_interactions = set(np.where(self.user_item_matrix[user_index] > 0)[0])

            # Create recommendations
            recommendations = []
            for item_index, score in enumerate(reconstructed_preferences):
                if item_index not in user_interactions and score > 0:
                    policy_id = self.policy_ids[item_index]
                    recommendations.append((policy_id, float(score)))

            # Sort by score and return top N
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return recommendations[:n_recommendations]

        except Exception as e:
            logger.error(f"Error generating collaborative recommendations: {e}")
            return []

    def get_content_based_recommendations(self, user_id: int, n_recommendations: int = 10) -> List[Tuple[int, float]]:
        """Generate recommendations using content-based filtering"""
        try:
            if self.policy_features_matrix is None:
                if not self.extract_policy_features():
                    return []

            # Get user's interaction history
            user_interactions = UserInteraction.query.filter_by(user_id=user_id).all()

            if not user_interactions:
                logger.warning(f"No interaction history for user {user_id}")
                return []

            # Build user profile based on interacted policies
            user_profile = np.zeros(self.policy_features_matrix.shape[1])
            total_weight = 0

            for interaction in user_interactions:
                policy_features = PolicyFeatures.query.filter_by(
                    policy_id=interaction.policy_id,
                    algorithm_used='tfidf'
                ).first()

                if policy_features:
                    feature_vector = np.array(json.loads(policy_features.feature_vector))
                    weight = interaction.interaction_value
                    user_profile += feature_vector * weight
                    total_weight += weight

            if total_weight > 0:
                user_profile /= total_weight

            # Calculate similarity with all policies
            similarities = cosine_similarity([user_profile], self.policy_features_matrix)[0]

            # Get policies user hasn't interacted with
            interacted_policies = {interaction.policy_id for interaction in user_interactions}

            # Create recommendations
            recommendations = []
            for i, similarity in enumerate(similarities):
                policy_id = self.policy_ids[i] if i < len(self.policy_ids) else i + 1
                if policy_id not in interacted_policies and similarity > 0:
                    recommendations.append((policy_id, float(similarity)))

            # Sort by similarity and return top N
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return recommendations[:n_recommendations]

        except Exception as e:
            logger.error(f"Error generating content-based recommendations: {e}")
            return []

    def get_hybrid_recommendations(self, user_id: int, n_recommendations: int = 10) -> List[Tuple[int, float]]:
        """Generate recommendations using hybrid approach"""
        try:
            if self.hybrid_model is None:
                logger.warning("Hybrid model not trained")
                return []

            user = User.query.get(user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return []

            # Get all policies
            policies = Policy.query.all()
            recommendations = []

            # Get user's interaction history
            interacted_policies = {
                interaction.policy_id
                for interaction in UserInteraction.query.filter_by(user_id=user_id).all()
            }

            for policy in policies:
                if policy.id in interacted_policies:
                    continue

                # Create feature vector
                features = self._create_hybrid_features(user, policy)
                if features:
                    # Scale features
                    features_scaled = self.scaler.transform([features])

                    # Predict score
                    score = self.hybrid_model.predict(features_scaled)[0]

                    if score > 0:
                        recommendations.append((policy.id, float(score)))

            # Sort by score and return top N
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return recommendations[:n_recommendations]

        except Exception as e:
            logger.error(f"Error generating hybrid recommendations: {e}")
            return []

    def get_ai_recommendations(self, user_id: int, n_recommendations: int = 10) -> List[Dict]:
        """Main method to get AI-powered recommendations"""
        try:
            # Get recommendations from all approaches
            collaborative_recs = self.get_collaborative_recommendations(user_id, n_recommendations)
            content_recs = self.get_content_based_recommendations(user_id, n_recommendations)
            hybrid_recs = self.get_hybrid_recommendations(user_id, n_recommendations)

            # Combine recommendations with weighted scores
            combined_scores = {}

            # Weight the different approaches
            for policy_id, score in collaborative_recs:
                combined_scores[policy_id] = combined_scores.get(policy_id, 0) + score * 0.4

            for policy_id, score in content_recs:
                combined_scores[policy_id] = combined_scores.get(policy_id, 0) + score * 0.3

            for policy_id, score in hybrid_recs:
                combined_scores[policy_id] = combined_scores.get(policy_id, 0) + score * 0.3

            # Sort by combined score
            sorted_recommendations = sorted(
                combined_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:n_recommendations]

            # Convert to recommendation objects
            recommendations = []
            for policy_id, score in sorted_recommendations:
                policy = Policy.query.get(policy_id)
                if policy:
                    # Generate AI explanation
                    explanation = self._generate_ai_explanation(user_id, policy, score)

                    recommendations.append({
                        'policy': policy,
                        'score': min(100, max(0, score * 100)),  # Convert to percentage
                        'reason': explanation,
                        'algorithm': 'AI_ML_Hybrid',
                        'confidence': min(1.0, score)
                    })

                    # Log the recommendation
                    self._log_recommendation(user_id, policy_id, score, 'AI_ML_Hybrid')

            return recommendations

        except Exception as e:
            logger.error(f"Error generating AI recommendations: {e}")
            return []

    def _generate_ai_explanation(self, user_id: int, policy: Policy, score: float) -> str:
        """Generate AI-powered explanation for recommendation"""
        try:
            user = User.query.get(user_id)
            if not user:
                return "Recommended based on AI analysis"

            explanations = []

            # Age-based explanation
            if policy.min_age <= (user.age or 25) <= policy.max_age:
                explanations.append(f"Perfect age match for {policy.type} insurance")

            # Occupation-based explanation
            if user.occupation:
                explanations.append(f"Tailored for {user.occupation} professionals")

            # Lifestyle-based explanation
            if user.lifestyle:
                explanations.append(f"Matches your {user.lifestyle} lifestyle")

            # AI confidence explanation
            if score > 0.8:
                explanations.append("High AI confidence based on similar user patterns")
            elif score > 0.6:
                explanations.append("Good match based on ML analysis")
            else:
                explanations.append("Potential match identified by AI")

            return ". ".join(explanations[:2]) + "."

        except Exception as e:
            logger.error(f"Error generating AI explanation: {e}")
            return "AI-recommended based on your profile"

    def _log_recommendation(self, user_id: int, policy_id: int, score: float, algorithm: str):
        """Log recommendation for future analysis"""
        try:
            log_entry = RecommendationLog(
                user_id=user_id,
                policy_id=policy_id,
                recommendation_score=score,
                algorithm_used=algorithm,
                model_version="v1.0"
            )
            db.session.add(log_entry)
            db.session.commit()

        except Exception as e:
            logger.error(f"Error logging recommendation: {e}")

    def train_all_models(self) -> bool:
        """Train all ML models"""
        try:
            logger.info("Starting AI model training...")

            # Collect training data
            interactions_df = self.collect_training_data()
            if interactions_df.empty:
                logger.warning("No training data available")
                return False

            # Build user-item matrix
            user_item_matrix = self.build_user_item_matrix(interactions_df)

            # Train models
            success_count = 0

            if self.train_collaborative_filtering(user_item_matrix):
                success_count += 1
                logger.info("✓ Collaborative filtering model trained")

            if self.train_content_based_model():
                success_count += 1
                logger.info("✓ Content-based model trained")

            if self.train_hybrid_model(interactions_df):
                success_count += 1
                logger.info("✓ Hybrid model trained")

            logger.info(f"Training completed. {success_count}/3 models trained successfully")
            return success_count > 0

        except Exception as e:
            logger.error(f"Error training models: {e}")
            return False

    def get_similar_policies(self, policy_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get policies similar to the specified policy using content-based filtering"""
        try:
            from models import Policy

            # Get the target policy
            target_policy = Policy.query.get(policy_id)
            if not target_policy:
                return []

            # Get all policies except the target
            all_policies = Policy.query.filter(Policy.id != policy_id).all()
            if not all_policies:
                return []

            # Use simple similarity based on policy attributes
            similar_policies = []

            for policy in all_policies:
                similarity_score = 0.0
                reasons = []

                # Type similarity (highest weight)
                if policy.type == target_policy.type:
                    similarity_score += 0.5
                    reasons.append("Same insurance type")

                # Premium similarity
                premium_diff = abs(policy.premium - target_policy.premium)
                max_premium = max(policy.premium, target_policy.premium)
                if max_premium > 0:
                    premium_similarity = 1 - (premium_diff / max_premium)
                    similarity_score += premium_similarity * 0.3
                    if premium_similarity > 0.8:
                        reasons.append("Similar premium range")

                # Age range similarity
                target_age_range = target_policy.max_age - target_policy.min_age
                policy_age_range = policy.max_age - policy.min_age
                age_overlap = max(0, min(target_policy.max_age, policy.max_age) - max(target_policy.min_age, policy.min_age))

                if target_age_range > 0 and policy_age_range > 0:
                    age_similarity = age_overlap / max(target_age_range, policy_age_range)
                    similarity_score += age_similarity * 0.2
                    if age_similarity > 0.7:
                        reasons.append("Similar age coverage")

                # Only include if similarity is above threshold
                if similarity_score > 0.3:
                    similar_policies.append({
                        'policy': policy,
                        'similarity_score': similarity_score,
                        'reason': "; ".join(reasons) if reasons else "Basic similarity detected"
                    })

            # Sort by similarity score and return top results
            similar_policies.sort(key=lambda x: x['similarity_score'], reverse=True)
            return similar_policies[:limit]

        except Exception as e:
            logger.error(f"Error getting similar policies: {e}")
            return []
