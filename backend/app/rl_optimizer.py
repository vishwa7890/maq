"""
Reinforcement Learning Optimizer for QuoteMaster
Automatically learns from user interactions to improve quote generation.
"""
import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import hashlib
import logging
from collections import defaultdict, deque
import random
import uuid
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class UserState(BaseModel):
    """Tracks the state of a user for RL optimization."""
    user_id: str
    preferences: Dict[str, float] = {}
    interaction_history: List[Dict[str, Any]] = []
    last_updated: datetime = datetime.utcnow()
    
    class Config:
        arbitrary_types_allowed = True

    def update_preferences(self, interaction_type: str, metadata: Dict[str, Any]):
        """Update user preferences based on interaction."""
        self.last_updated = datetime.utcnow()
        self.interaction_history.append({
            'timestamp': self.last_updated.isoformat(),
            'type': interaction_type,
            'metadata': metadata
        })
        
        # Update preference weights based on interaction type
        weight_updates = {
            'download': 0.1,
            'share': 0.15,
            'edit': -0.05,
            'ignore': -0.1,
            'quick_bounce': -0.2,
            'premium_feature_used': 0.2
        }
        
        # Apply weight updates
        feature = metadata.get('feature', 'general')
        self.preferences[feature] = self.preferences.get(feature, 0) + \
                                  weight_updates.get(interaction_type, 0)

class QuoteInteractionTracker:
    """Tracks user interactions with generated quotes."""
    
    def __init__(self, storage_path: str = "quote_interactions.json"):
        self.storage_path = Path(storage_path)
        self.interactions = self._load_interactions()
        
    def _load_interactions(self) -> List[dict]:
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load interactions: {e}")
        return []
    
    def _save_interactions(self):
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.interactions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save interactions: {e}")
    
    def track_interaction(self, quote_id: str, interaction_type: str, metadata: Optional[dict] = None):
        """Track a user interaction with a quote."""
        interaction = {
            'quote_id': quote_id,
            'timestamp': datetime.utcnow().isoformat(),
            'interaction_type': interaction_type,  # 'download', 'edit', 'ignore', 'share', etc.
            'metadata': metadata or {}
        }
        self.interactions.append(interaction)
        self._save_interactions()
        logger.info(f"Tracked {interaction_type} for quote {quote_id}")
        return interaction


class RewardModel:
    """Calculates rewards based on user interactions with premium features."""
    
    def __init__(self):
        # Base reward weights for different interaction types
        self.reward_weights = {
            # Basic interactions
            'download': 1.0,
            'share': 1.5,
            'edit': -0.3,
            'ignore': -0.5,
            'quick_bounce': -1.0,
            
            # Premium feature interactions
            'watermark_removed': 0.8,
            'custom_branding_used': 1.0,
            'high_quality_export': 0.7,
            'premium_template_used': 0.9,
            
            # Negative signals for premium features
            'premium_feature_failed': -1.5,
            'downgrade_requested': -2.0
        }
        
        # Time decay factor for rewards (older interactions matter less)
        self.decay_rate = 0.95  # 5% decay per day
        
    def _get_time_decay(self, timestamp: str) -> float:
        """Calculate time decay factor for an interaction."""
        try:
            event_time = datetime.fromisoformat(timestamp)
            days_old = (datetime.utcnow() - event_time).days
            return self.decay_rate ** days_old
        except Exception as e:
            logger.warning(f"Error calculating time decay: {e}")
            return 1.0
        
    def calculate_reward(self, interactions: List[dict], user_state: Optional[UserState] = None) -> float:
        """
        Calculate total reward from interactions with premium features.
        
        Args:
            interactions: List of interaction dictionaries
            user_state: Optional user state for personalized rewards
            
        Returns:
            float: Calculated reward score
        """
        total_reward = 0.0
        feature_weights = defaultdict(float)
        
        for interaction in interactions:
            interaction_type = interaction.get('interaction_type')
            metadata = interaction.get('metadata', {})
            
            # Get base reward for this interaction type
            base_reward = self.reward_weights.get(interaction_type, 0.0)
            
            # Apply time decay
            time_decay = self._get_time_decay(interaction.get('timestamp', datetime.utcnow().isoformat()))
            
            # Check for premium features in metadata
            premium_boost = 1.0
            if metadata.get('is_premium', False):
                premium_boost = 1.5  # Premium interactions are more valuable
                
                # Track which premium features were used
                for feature in ['watermark_removed', 'custom_branding_used', 'high_quality_export']:
                    if metadata.get(feature, False):
                        feature_weights[feature] += base_reward * premium_boost
            
            # Apply user preferences if available
            user_preference = 1.0
            if user_state and 'feature' in metadata:
                user_preference = 1.0 + user_state.preferences.get(metadata['feature'], 0.0)
            
            # Calculate final reward with all factors
            total_reward += base_reward * time_decay * premium_boost * user_preference
        
        # Add bonus for using premium features
        if feature_weights:
            total_reward += sum(feature_weights.values()) * 0.5
        
        return total_reward


class PromptOptimizer:
    """Optimizes prompts based on interaction rewards."""
    
    def __init__(self, base_prompt: str):
        self.base_prompt = base_prompt
        self.prompt_variations = []
        self.best_prompt = base_prompt
        self.best_score = 0.0
        
    def generate_variations(self, num_variations: int = 3) -> List[str]:
        """Generate variations of the base prompt."""
        # In a real implementation, this would use techniques like:
        # 1. Paraphrasing
        # 2. Adding/removing constraints
        # 3. Adjusting formatting instructions
        # 4. Varying the level of detail
        
        # For now, we'll just add some simple variations
        variations = [self.base_prompt]
        
        # Variation 1: More concise
        concise = self.base_prompt.replace("be professional, helpful, and concise", "be extremely concise and direct")
        variations.append(concise)
        
        # Variation 2: More detailed
        detailed = self.base_prompt.replace("be professional, helpful, and concise", 
                                          "be extremely detailed and thorough in your explanations")
        variations.append(detailed)
        
        # Variation 3: Different format emphasis
        formatted = self.base_prompt.replace("CRITICAL FORMATTING RULES", 
                                           "**ABSOLUTELY CRITICAL** FORMATTING RULES THAT MUST BE FOLLOWED")
        variations.append(formatted)
        
        return variations[:num_variations]
    
    def update_prompt(self, prompt: str, score: float):
        """Update the best prompt if this one performs better."""
        if score > self.best_score:
            self.best_prompt = prompt
            self.best_score = score
            logger.info(f"New best prompt with score {score:.2f}")
            return True
        return False


class QuoteGenerator:
    """
    Generates quotes with automatic improvement using reinforcement learning.
    
    Features:
    - Tracks user interactions with quotes
    - Optimizes prompts based on rewards
    - Personalizes quotes based on user preferences
    - Supports premium features
    """
    
    def __init__(self, base_prompt: str):
        self.tracker = QuoteInteractionTracker()
        self.reward_model = RewardModel()
        self.prompt_optimizer = PromptOptimizer(base_prompt)
        self.quote_history = {}  # quote_id: {prompt: str, interactions: List[dict]}
        self.user_states = {}    # user_id: UserState
        self.feature_importance = defaultdict(float)  # Tracks which features drive success
        
    def generate_quote_id(self, prompt: str, user_query: str) -> str:
        """Generate a unique ID for a quote."""
        unique_str = f"{prompt[:50]}_{user_query[:50]}_{datetime.utcnow().isoformat()}"
        return hashlib.md5(unique_str.encode()).hexdigest()
    
    def get_best_prompt(self) -> str:
        """Get the best performing prompt so far."""
        return self.prompt_optimizer.best_prompt
    
    def track_quote_interaction(
        self, 
        quote_id: str, 
        interaction_type: str, 
        metadata: dict = None,
        user_id: Optional[str] = None
    ) -> dict:
        """
        Track how users interact with a generated quote.
        
        Args:
            quote_id: Unique identifier for the quote
            interaction_type: Type of interaction (download, edit, etc.)
            metadata: Additional data about the interaction
            user_id: Optional user ID for personalization
            
        Returns:
            dict: The recorded interaction
        """
        if quote_id not in self.quote_history:
            self.quote_history[quote_id] = {'interactions': []}
        
        # Add user and timestamp to metadata
        if metadata is None:
            metadata = {}
            
        metadata.update({
            'tracked_at': datetime.utcnow().isoformat(),
            'user_id': user_id
        })
        
        # Track the interaction
        interaction = self.tracker.track_interaction(quote_id, interaction_type, metadata)
        self.quote_history[quote_id]['interactions'].append(interaction)
        
        # Update user state if user_id is provided
        if user_id:
            self._update_user_state(user_id, interaction_type, metadata)
        
        # Update optimization based on this interaction
        self._update_optimization(quote_id, user_id)
        
        return interaction
        
    def _update_user_state(self, user_id: str, interaction_type: str, metadata: dict):
        """Update the user's state based on their interaction."""
        if user_id not in self.user_states:
            self.user_states[user_id] = UserState(user_id=user_id)
            
        user_state = self.user_states[user_id]
        user_state.update_preferences(interaction_type, metadata)
        
        # Update feature importance based on this interaction
        if 'feature' in metadata:
            feature = metadata['feature']
            reward = self.reward_model.reward_weights.get(interaction_type, 0)
            self.feature_importance[feature] = (
                0.9 * self.feature_importance.get(feature, 0) + 0.1 * abs(reward)
            )
    
    def _update_optimization(self, quote_id: str, user_id: Optional[str] = None):
        """Update prompt optimization based on quote interactions."""
        quote_data = self.quote_history[quote_id]
        interactions = quote_data['interactions']
        
        # Calculate reward for this quote
        reward = self.reward_model.calculate_reward(interactions, self.user_states.get(user_id))
        
        # Update prompt optimization
        self.prompt_optimizer.update_prompt(quote_data['prompt'], reward)
        
        # Periodically generate new prompt variations
        if len(self.quote_history) % 10 == 0:  # Every 10 quotes
            self._explore_new_variations()
    
    def _explore_new_variations(self):
        """Generate and test new prompt variations."""
        new_variations = self.prompt_optimizer.generate_variations()
        for variation in new_variations:
            if variation not in [v['prompt'] for v in self.quote_history.values()]:
                # In a real implementation, we would generate a quote with this variation
                # and track its performance
                logger.info(f"Testing new prompt variation: {variation[:100]}...")
                
    def generate_quote(
        self, 
        user_query: str, 
        user_id: Optional[str] = None,
        is_premium: bool = False,
        preferred_features: Optional[List[str]] = None
    ) -> dict:
        """
        Generate a quote using the current best prompt with personalization.
        
        Args:
            user_query: The user's query or requirements
            user_id: Optional user ID for personalization
            is_premium: Whether the user has premium features
            preferred_features: List of preferred premium features
            
        Returns:
            dict: Generated quote with metadata
        """
        # Get user state if available
        user_state = self.user_states.get(user_id) if user_id else None
        
        # Get the best performing prompt, potentially personalized
        prompt = self._get_personalized_prompt(user_state, is_premium, preferred_features)
        
        # Generate a unique ID for this quote
        quote_id = self.generate_quote_id(prompt, user_query)
        
        # Store the prompt and initial metadata
        if quote_id not in self.quote_history:
            self.quote_history[quote_id] = {
                'prompt': prompt,
                'interactions': [],
                'metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'is_premium': is_premium,
                    'features_used': preferred_features or []
                }
            }
        
        # Track this generation for analytics
        self.track_quote_interaction(
            quote_id=quote_id,
            interaction_type='generate',
            metadata={
                'is_premium': is_premium,
                'features': preferred_features or [],
                'user_query': user_query[:100]  # Store first 100 chars for context
            },
            user_id=user_id
        )
            
        # In a real implementation, you would use an LLM to generate the quote
        # For now, we'll return a placeholder with premium features if applicable
        quote_data = {
            'id': quote_id,
            'content': f"Generated quote for: {user_query}",
            'prompt_used': prompt,
            'metadata': {
                'is_premium': is_premium,
                'features': preferred_features or [],
                'generated_at': datetime.utcnow().isoformat()
            }
        }
        
        # Add premium features if applicable
        if is_premium and preferred_features:
            quote_data['premium_features'] = {
                feature: True for feature in preferred_features
            }
            
            # Add watermarks only if not explicitly disabled
            if 'watermark_removed' in preferred_features:
                quote_data['watermark'] = False
            else:
                quote_data['watermark'] = True
                
            # Add branding if specified
            if 'custom_branding' in preferred_features:
                quote_data['branding'] = {
                    'logo_url': '/path/to/logo.png',
                    'company_name': 'Your Company',
                    'contact_info': 'support@yourcompany.com'
                }
        
        return quote_data
        
    def _get_personalized_prompt(
        self, 
        user_state: Optional[UserState],
        is_premium: bool,
        preferred_features: Optional[List[str]] = None
    ) -> str:
        """
        Get a personalized prompt based on user preferences and features.
        
        Args:
            user_state: The user's state and preferences
            is_premium: Whether the user has premium features
            preferred_features: List of preferred premium features
            
        Returns:
            str: Personalized prompt
        """
        base_prompt = self.prompt_optimizer.get_best_prompt()
        
        # If no user state or premium features, return base prompt
        if not user_state and not is_premium:
            return base_prompt
            
        # Start with the base prompt
        prompt_parts = [base_prompt]
        
        # Add premium features if applicable
        if is_premium and preferred_features:
            prompt_parts.append("\n\nPremium features enabled:")
            for feature in preferred_features:
                if feature == 'watermark_removed':
                    prompt_parts.append("- Generate without watermarks")
                elif feature == 'custom_branding':
                    prompt_parts.append("- Include professional branding")
                elif feature == 'high_quality_export':
                    prompt_parts.append("- Optimize for high-quality PDF export")
        
        # Add user preferences if available
        if user_state and user_state.preferences:
            prompt_parts.append("\nUser preferences:")
            for feature, weight in sorted(
                user_state.preferences.items(), 
                key=lambda x: abs(x[1]), 
                reverse=True
            )[:3]:  # Top 3 preferences
                if weight > 0:
                    prompt_parts.append(f"- Prefers {feature}")
                else:
                    prompt_parts.append(f"- Avoids {feature}")
        
        return "\n".join(prompt_parts)
