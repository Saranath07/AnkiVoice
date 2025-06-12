"""
Data models for AnkiVoice using Pydantic for validation.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class DifficultyLevel(int, Enum):
    """Difficulty levels for cards and questions."""
    VERY_EASY = 1
    EASY = 2
    MEDIUM = 3
    HARD = 4
    VERY_HARD = 5


class QuestionType(str, Enum):
    """Types of questions that can be generated."""
    STANDARD = "standard"
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    TRUE_FALSE = "true_false"


class StudyMode(str, Enum):
    """Different study modes available."""
    DEFAULT = "default"  # Full automation (TTS → ASR → LLM evaluation)
    CONTROLLED = "controlled"  # User reviews transcription before LLM evaluation
    NO_TTS = "no_tts"  # Visual questions with ASR + LLM evaluation
    MANUAL_DECISION = "manual_decision"  # User makes final scheduling decisions
    STUDY = "study"  # Batch question generation from study material
    REVIEW = "review"  # Traditional flashcard review with voice
    PERFORMANCE = "performance"  # Optimized for speed and efficiency


class Card(BaseModel):
    """Represents a flashcard with study material."""
    id: Optional[int] = None
    content: str = Field(..., min_length=1, max_length=2000)
    source_material: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Question(BaseModel):
    """Represents a generated question for a card."""
    id: Optional[int] = None
    card_id: int
    question_text: str = Field(..., min_length=1, max_length=2000)
    answer_text: str = Field(..., min_length=1, max_length=2000)
    question_type: QuestionType = QuestionType.STANDARD
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    generation_prompt: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserProgress(BaseModel):
    """Tracks user's progress on a specific card."""
    id: Optional[int] = None
    card_id: int
    question_id: Optional[int] = None
    ease_factor: float = Field(default=2.5, ge=1.3, le=4.0)
    interval_days: int = Field(default=1, ge=1)
    repetitions: int = Field(default=0, ge=0)
    last_review: Optional[datetime] = None
    next_review: Optional[datetime] = None
    total_reviews: int = Field(default=0, ge=0)
    correct_reviews: int = Field(default=0, ge=0)
    streak: int = Field(default=0, ge=0)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage."""
        if self.total_reviews == 0:
            return 0.0
        return (self.correct_reviews / self.total_reviews) * 100

    @property
    def is_due(self) -> bool:
        """Check if card is due for review."""
        if self.next_review is None:
            return True
        return datetime.now() >= self.next_review

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StudySession(BaseModel):
    """Represents a study session."""
    id: Optional[int] = None
    session_name: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    mode: StudyMode = StudyMode.DEFAULT
    cards_reviewed: int = Field(default=0, ge=0)
    correct_answers: int = Field(default=0, ge=0)
    average_response_time: Optional[float] = None
    session_data: Dict[str, Any] = Field(default_factory=dict)
    is_completed: bool = False

    @property
    def accuracy(self) -> float:
        """Calculate session accuracy percentage."""
        if self.cards_reviewed == 0:
            return 0.0
        return (self.correct_answers / self.cards_reviewed) * 100

    @property
    def duration_minutes(self) -> float:
        """Calculate session duration in minutes."""
        if self.end_time is None:
            end_time = datetime.now()
        else:
            end_time = self.end_time
        duration = end_time - self.start_time
        return duration.total_seconds() / 60

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionReview(BaseModel):
    """Represents a single card review within a session."""
    id: Optional[int] = None
    session_id: int
    card_id: int
    question_id: int
    user_response: str
    transcribed_response: Optional[str] = None
    is_correct: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    response_time_seconds: Optional[float] = None
    feedback: Optional[str] = None
    difficulty_rating: Optional[DifficultyLevel] = None
    review_timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QuestionGenerationRequest(BaseModel):
    """Request model for question generation."""
    content: str = Field(..., min_length=1, max_length=2000)
    num_questions: int = Field(default=3, ge=1, le=10)
    question_types: List[QuestionType] = Field(default=[QuestionType.STANDARD])
    difficulty_range: List[DifficultyLevel] = Field(default=[DifficultyLevel.EASY, DifficultyLevel.HARD])
    include_world_knowledge: bool = True


class QuestionGenerationResponse(BaseModel):
    """Response model for question generation."""
    questions: List[Dict[str, Any]]
    generation_time_ms: int
    model_used: str


class AnswerEvaluationRequest(BaseModel):
    """Request model for answer evaluation."""
    question: str
    expected_answer: str
    user_answer: str
    context: Optional[str] = None


class AnswerEvaluationResponse(BaseModel):
    """Response model for answer evaluation."""
    is_correct: bool
    confidence: float = Field(ge=0.0, le=1.0)
    feedback: str
    suggestions: Optional[str] = None
    evaluation_time_ms: int


class UserSettings(BaseModel):
    """User configuration settings."""
    setting_key: str
    setting_value: str
    setting_type: str = "string"  # string, integer, boolean, json
    description: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProgressOverview(BaseModel):
    """Overview of user's learning progress."""
    total_cards: int
    cards_mastered: int
    cards_learning: int
    cards_new: int
    daily_streak: int
    accuracy_last_week: float
    time_studied_minutes: float
    cards_due_today: int
    cards_overdue: int


class DueCard(BaseModel):
    """Card that is due for review."""
    id: int
    content: str
    due_date: datetime
    priority: str  # high, medium, low
    days_overdue: int = 0

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }