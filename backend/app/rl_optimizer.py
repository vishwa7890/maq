"""
Reinforcement Learning Optimizer for QuoteMaster
Automatically learns from user interactions to improve quote generation.
"""
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import hashlib
import logging

logger = logging.getLogger(__name__)

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
    """Calculates rewards based on user interactions."""
    
    def __init__(self):
        # Define reward weights for different interaction types
        self.reward_weights = {
            'download': 1.0,      # Positive signal
            'share': 1.2,         # Very positive signal
            'edit': -0.5,         # Slightly negative (needs improvement)
            'ignore': -0.3,       # Negative signal
            'quick_bounce': -0.8  # Very negative (immediate rejection)
        }
        
    def calculate_reward(self, interactions: List[dict]) -> float:
        """Calculate total reward from a list of interactions."""
        if not interactions:
            return 0.0
            
        total_reward = 0.0
        for interaction in interactions:
            interaction_type = interaction['interaction_type']
            weight = self.reward_weights.get(interaction_type, 0.0)
            
            # Apply time decay (recent interactions matter more)
            if 'timestamp' in interaction:
                days_old = (datetime.utcnow() - datetime.fromisoformat(interaction['timestamp'])).days
                decay = max(0.1, 1.0 - (days_old / 30))  # Linear decay over 30 days
                weight *= decay
                
            total_reward += weight
            
        return total_reward / len(interactions)  # Normalize by number of interactions


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
    """Generates quotes with automatic improvement."""
    
    def __init__(self, base_prompt: str):
        self.tracker = QuoteInteractionTracker()
        self.reward_model = RewardModel()
        self.prompt_optimizer = PromptOptimizer(base_prompt)
        self.quote_history = {}  # quote_id: {prompt: str, interactions: List[dict]}
        
    def generate_quote_id(self, prompt: str, user_query: str) -> str:
        """Generate a unique ID for a quote."""
        unique_str = f"{prompt[:50]}_{user_query[:50]}_{datetime.utcnow().isoformat()}"
        return hashlib.md5(unique_str.encode()).hexdigest()
    
    def get_best_prompt(self) -> str:
        """Get the best performing prompt so far."""
        return self.prompt_optimizer.best_prompt
    
    def track_quote_interaction(self, quote_id: str, interaction_type: str, metadata: dict = None):
        """Track how users interact with a generated quote."""
        if quote_id not in self.quote_history:
            logger.warning(f"Unknown quote_id: {quote_id}")
            return
            
        interaction = self.tracker.track_interaction(quote_id, interaction_type, metadata)
        self.quote_history[quote_id]['interactions'].append(interaction)
        
        # Update prompt optimization based on new feedback
        self._update_optimization(quote_id)
    
    def _update_optimization(self, quote_id: str):
        """Update prompt optimization based on quote interactions."""
        quote_data = self.quote_history[quote_id]
        interactions = quote_data['interactions']
        
        # Calculate reward for this quote
        reward = self.reward_model.calculate_reward(interactions)
        
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
                
    def generate_quote(self, user_query: str) -> dict:
        """Generate a quote using the current best prompt."""
        prompt = self.get_best_prompt()
        
        # In a real implementation, this would call your LLM
        # For now, we'll just return a placeholder
        quote_id = self.generate_quote_id(prompt, user_query)
        
        # Store this quote in history
        self.quote_history[quote_id] = {
            'prompt': prompt,
            'user_query': user_query,
            'generated_at': datetime.utcnow().isoformat(),
            'interactions': []
        }
        
        return {
            'quote_id': quote_id,
            'content': f"Generated quote for: {user_query}",
            'prompt_version': hash(prompt)  # Simple way to track prompt versions
        }
