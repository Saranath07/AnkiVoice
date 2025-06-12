"""
Spaced repetition system for AnkiVoice based on the SM-2 algorithm.
"""

import math
from datetime import datetime, timedelta
from typing import Tuple
import logging

from models import UserProgress, DifficultyLevel
from config import config

logger = logging.getLogger(__name__)


class SpacedRepetitionSystem:
    """Implements the SM-2 spaced repetition algorithm."""
    
    def __init__(self):
        """Initialize the spaced repetition system."""
        self.initial_interval = config.SR_INITIAL_INTERVAL
        self.ease_factor_min = config.SR_EASE_FACTOR_MIN
        self.ease_factor_max = config.SR_EASE_FACTOR_MAX
        self.ease_factor_default = config.SR_EASE_FACTOR_DEFAULT
        self.interval_multiplier = config.SR_INTERVAL_MULTIPLIER
        self.max_interval = config.SR_MAX_INTERVAL
    
    def calculate_next_review(
        self, 
        progress: UserProgress, 
        quality: int, 
        response_time_seconds: float = None
    ) -> Tuple[UserProgress, datetime]:
        """
        Calculate the next review date based on SM-2 algorithm.
        
        Args:
            progress: Current user progress
            quality: Quality of response (0-5 scale)
                    0: Complete blackout
                    1: Incorrect response; correct one remembered
                    2: Incorrect response; correct one seemed easy to recall
                    3: Correct response recalled with serious difficulty
                    4: Correct response after a hesitation
                    5: Perfect response
            response_time_seconds: Time taken to respond (optional)
        
        Returns:
            Tuple of (updated_progress, next_review_date)
        """
        # Validate quality
        quality = max(0, min(5, quality))
        
        # Update basic statistics
        progress.total_reviews += 1
        progress.last_review = datetime.now()
        
        # Update streak and correct reviews
        if quality >= 3:  # Correct answer
            progress.correct_reviews += 1
            progress.streak += 1
        else:  # Incorrect answer
            progress.streak = 0
        
        # Calculate new ease factor
        new_ease_factor = self._calculate_ease_factor(progress.ease_factor, quality)
        progress.ease_factor = max(self.ease_factor_min, min(self.ease_factor_max, new_ease_factor))
        
        # Calculate new interval
        if quality < 3:  # Incorrect answer - reset to beginning
            progress.repetitions = 0
            progress.interval_days = 1
        else:  # Correct answer - increase interval
            progress.repetitions += 1
            
            if progress.repetitions == 1:
                progress.interval_days = 1
            elif progress.repetitions == 2:
                progress.interval_days = 6
            else:
                # Use ease factor for subsequent repetitions
                new_interval = progress.interval_days * progress.ease_factor
                progress.interval_days = min(int(new_interval), self.max_interval)
        
        # Adjust interval based on response time if provided
        if response_time_seconds is not None:
            progress.interval_days = self._adjust_for_response_time(
                progress.interval_days, 
                response_time_seconds, 
                quality
            )
        
        # Calculate next review date
        next_review = progress.last_review + timedelta(days=progress.interval_days)
        progress.next_review = next_review
        
        # Update timestamp
        progress.updated_at = datetime.now()
        
        logger.info(f"Updated progress: quality={quality}, interval={progress.interval_days} days, "
                   f"ease_factor={progress.ease_factor:.2f}, next_review={next_review}")
        
        return progress, next_review
    
    def _calculate_ease_factor(self, current_ease: float, quality: int) -> float:
        """
        Calculate new ease factor based on SM-2 algorithm.
        
        EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
        where q is quality of response (0-5)
        """
        return current_ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    
    def _adjust_for_response_time(
        self, 
        base_interval: int, 
        response_time: float, 
        quality: int
    ) -> int:
        """
        Adjust interval based on response time.
        
        Fast responses might indicate the card is too easy.
        Slow responses might indicate the card is still challenging.
        """
        # Define expected response times (in seconds) for different qualities
        expected_times = {
            5: 2.0,   # Perfect response - very fast
            4: 4.0,   # Good response - fast
            3: 8.0,   # OK response - moderate
            2: 15.0,  # Poor response - slow
            1: 20.0,  # Very poor - very slow
            0: 30.0   # Complete failure - very slow
        }
        
        expected_time = expected_times.get(quality, 8.0)
        
        # Calculate adjustment factor
        if response_time < expected_time * 0.5:
            # Very fast response - might be too easy, increase interval slightly
            adjustment = 1.2
        elif response_time < expected_time:
            # Fast response - slight increase
            adjustment = 1.1
        elif response_time > expected_time * 2:
            # Very slow response - decrease interval
            adjustment = 0.8
        elif response_time > expected_time:
            # Slow response - slight decrease
            adjustment = 0.9
        else:
            # Normal response time
            adjustment = 1.0
        
        adjusted_interval = int(base_interval * adjustment)
        return max(1, min(adjusted_interval, self.max_interval))
    
    def quality_from_evaluation(
        self, 
        is_correct: bool, 
        confidence: float, 
        response_time: float = None
    ) -> int:
        """
        Convert LLM evaluation to SM-2 quality score.
        
        Args:
            is_correct: Whether the answer was correct
            confidence: LLM confidence score (0.0-1.0)
            response_time: Response time in seconds (optional)
        
        Returns:
            Quality score (0-5)
        """
        if not is_correct:
            # Incorrect answers: 0-2 based on confidence
            if confidence < 0.3:
                return 0  # Complete blackout
            elif confidence < 0.6:
                return 1  # Incorrect but some understanding
            else:
                return 2  # Incorrect but close
        else:
            # Correct answers: 3-5 based on confidence and response time
            base_quality = 3  # Minimum for correct answer
            
            # Adjust based on confidence
            if confidence >= 0.9:
                confidence_bonus = 2  # Very confident
            elif confidence >= 0.8:
                confidence_bonus = 1  # Confident
            else:
                confidence_bonus = 0  # Less confident
            
            # Adjust based on response time if available
            time_bonus = 0
            if response_time is not None:
                if response_time <= 3.0:
                    time_bonus = 1  # Very fast
                elif response_time <= 6.0:
                    time_bonus = 0  # Normal
                else:
                    time_bonus = -1  # Slow
            
            quality = base_quality + confidence_bonus + time_bonus
            return max(3, min(5, quality))  # Ensure correct answers are at least 3
    
    def get_difficulty_adjustment(self, user_difficulty: DifficultyLevel) -> float:
        """
        Get adjustment factor based on user-perceived difficulty.
        
        Args:
            user_difficulty: User's rating of question difficulty
        
        Returns:
            Adjustment factor for interval (0.5 to 1.5)
        """
        difficulty_adjustments = {
            DifficultyLevel.VERY_EASY: 1.3,   # Increase interval more
            DifficultyLevel.EASY: 1.1,       # Slight increase
            DifficultyLevel.MEDIUM: 1.0,     # No adjustment
            DifficultyLevel.HARD: 0.9,       # Slight decrease
            DifficultyLevel.VERY_HARD: 0.7   # Significant decrease
        }
        
        return difficulty_adjustments.get(user_difficulty, 1.0)
    
    def calculate_retention_rate(self, progress: UserProgress) -> float:
        """
        Calculate estimated retention rate for a card.
        
        Args:
            progress: User progress data
        
        Returns:
            Estimated retention rate (0.0-1.0)
        """
        if progress.total_reviews == 0:
            return 0.0
        
        # Base retention rate from accuracy
        base_rate = progress.accuracy / 100.0
        
        # Adjust for recency (more recent reviews are more reliable)
        if progress.last_review:
            days_since_review = (datetime.now() - progress.last_review).days
            recency_factor = math.exp(-days_since_review / 30.0)  # Decay over 30 days
        else:
            recency_factor = 0.0
        
        # Adjust for streak (longer streaks indicate better retention)
        streak_factor = min(progress.streak / 10.0, 0.2)  # Max 20% bonus
        
        # Combine factors
        retention_rate = base_rate * (0.8 + 0.2 * recency_factor) + streak_factor
        
        return max(0.0, min(1.0, retention_rate))
    
    def suggest_study_order(self, cards_progress: list) -> list:
        """
        Suggest optimal study order based on spaced repetition principles.
        
        Args:
            cards_progress: List of (Card, UserProgress) tuples
        
        Returns:
            Sorted list prioritized for study
        """
        def priority_score(card_progress_tuple):
            card, progress = card_progress_tuple
            
            # Higher priority for overdue cards
            if progress.next_review and progress.next_review < datetime.now():
                days_overdue = (datetime.now() - progress.next_review).days
                overdue_score = min(days_overdue * 10, 100)  # Max 100 points
            else:
                overdue_score = 0
            
            # Higher priority for cards with low retention
            retention_rate = self.calculate_retention_rate(progress)
            retention_score = (1.0 - retention_rate) * 50  # Max 50 points
            
            # Higher priority for cards with low streak
            streak_score = max(0, 20 - progress.streak)  # Max 20 points
            
            # Combine scores
            total_score = overdue_score + retention_score + streak_score
            
            return total_score
        
        # Sort by priority score (descending)
        return sorted(cards_progress, key=priority_score, reverse=True)


# Global spaced repetition system instance
srs = SpacedRepetitionSystem()