"""
Database management for AnkiVoice using SQLite.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import logging

from models import (
    Card, Question, UserProgress, StudySession, SessionReview, 
    UserSettings, DifficultyLevel, QuestionType, StudyMode
)
from config import config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for AnkiVoice."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager."""
        self.db_path = db_path or config.DATABASE_PATH
        self.ensure_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def ensure_database(self):
        """Create database and tables if they don't exist."""
        config.ensure_directories()
        
        with self.get_connection() as conn:
            self._create_tables(conn)
            self._create_indexes(conn)
            conn.commit()
    
    def _create_tables(self, conn: sqlite3.Connection):
        """Create all required tables."""
        
        # Cards table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                source_material TEXT,
                tags TEXT, -- JSON array of tags
                difficulty_level INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Questions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                question_type TEXT DEFAULT 'standard',
                difficulty INTEGER DEFAULT 3,
                generation_prompt TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
            )
        """)
        
        # User progress table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER NOT NULL,
                question_id INTEGER,
                ease_factor REAL DEFAULT 2.5,
                interval_days INTEGER DEFAULT 1,
                repetitions INTEGER DEFAULT 0,
                last_review TIMESTAMP,
                next_review TIMESTAMP,
                total_reviews INTEGER DEFAULT 0,
                correct_reviews INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE SET NULL
            )
        """)
        
        # Study sessions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_name TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                mode TEXT NOT NULL DEFAULT 'default',
                cards_reviewed INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                average_response_time REAL,
                session_data TEXT, -- JSON data
                is_completed BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Session reviews table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                card_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                user_response TEXT,
                transcribed_response TEXT,
                is_correct BOOLEAN,
                confidence_score REAL,
                response_time_seconds REAL,
                feedback TEXT,
                difficulty_rating INTEGER,
                review_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES study_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            )
        """)
        
        # User settings table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                setting_type TEXT DEFAULT 'string',
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def _create_indexes(self, conn: sqlite3.Connection):
        """Create indexes for better performance."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_cards_tags ON cards(tags)",
            "CREATE INDEX IF NOT EXISTS idx_cards_created_at ON cards(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_questions_card_id ON questions(card_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_progress_card_id ON user_progress(card_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_progress_next_review ON user_progress(next_review)",
            "CREATE INDEX IF NOT EXISTS idx_session_reviews_session_id ON session_reviews(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_session_reviews_timestamp ON session_reviews(review_timestamp)"
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
    
    # Card operations
    def create_card(self, card: Card) -> int:
        """Create a new card and return its ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO cards (content, source_material, tags, difficulty_level)
                VALUES (?, ?, ?, ?)
            """, (
                card.content,
                card.source_material,
                json.dumps(card.tags),
                card.difficulty_level.value
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_card(self, card_id: int) -> Optional[Card]:
        """Get a card by ID."""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
            if row:
                return self._row_to_card(row)
            return None
    
    def get_all_cards(self, limit: Optional[int] = None, offset: int = 0) -> List[Card]:
        """Get all cards with optional pagination."""
        with self.get_connection() as conn:
            sql = "SELECT * FROM cards WHERE is_active = TRUE ORDER BY created_at DESC"
            params = []
            
            if limit:
                sql += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_card(row) for row in rows]
    
    def update_card(self, card: Card) -> bool:
        """Update an existing card."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                UPDATE cards 
                SET content = ?, source_material = ?, tags = ?, difficulty_level = ?, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                card.content,
                card.source_material,
                json.dumps(card.tags),
                card.difficulty_level.value,
                card.id
            ))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_card(self, card_id: int) -> bool:
        """Soft delete a card."""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE cards SET is_active = FALSE WHERE id = ?", 
                (card_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    # Question operations
    def create_question(self, question: Question) -> int:
        """Create a new question and return its ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO questions (card_id, question_text, answer_text, question_type, difficulty, generation_prompt)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                question.card_id,
                question.question_text,
                question.answer_text,
                question.question_type.value,
                question.difficulty.value,
                question.generation_prompt
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_questions_for_card(self, card_id: int) -> List[Question]:
        """Get all questions for a specific card."""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM questions WHERE card_id = ? ORDER BY created_at",
                (card_id,)
            ).fetchall()
            return [self._row_to_question(row) for row in rows]
    
    def get_question(self, question_id: int) -> Optional[Question]:
        """Get a question by ID."""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
            if row:
                return self._row_to_question(row)
            return None
    
    # User progress operations
    def get_or_create_progress(self, card_id: int) -> UserProgress:
        """Get existing progress or create new one for a card."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM user_progress WHERE card_id = ?", 
                (card_id,)
            ).fetchone()
            
            if row:
                return self._row_to_progress(row)
            else:
                # Create new progress
                cursor = conn.execute("""
                    INSERT INTO user_progress (card_id, next_review)
                    VALUES (?, ?)
                """, (card_id, datetime.now()))
                conn.commit()
                
                # Return the newly created progress
                row = conn.execute(
                    "SELECT * FROM user_progress WHERE id = ?", 
                    (cursor.lastrowid,)
                ).fetchone()
                return self._row_to_progress(row)
    
    def update_progress(self, progress: UserProgress) -> bool:
        """Update user progress."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                UPDATE user_progress 
                SET ease_factor = ?, interval_days = ?, repetitions = ?, 
                    last_review = ?, next_review = ?, total_reviews = ?, 
                    correct_reviews = ?, streak = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                progress.ease_factor,
                progress.interval_days,
                progress.repetitions,
                progress.last_review,
                progress.next_review,
                progress.total_reviews,
                progress.correct_reviews,
                progress.streak,
                progress.id
            ))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_due_cards(self, limit: Optional[int] = None) -> List[Tuple[Card, UserProgress]]:
        """Get cards that are due for review."""
        with self.get_connection() as conn:
            sql = """
                SELECT c.id as card_id, c.content, c.source_material, c.tags, c.difficulty_level,
                       c.created_at as card_created_at, c.updated_at as card_updated_at, c.is_active,
                       p.id as progress_id, p.card_id as p_card_id, p.question_id, p.ease_factor,
                       p.interval_days, p.repetitions, p.last_review, p.next_review,
                       p.total_reviews, p.correct_reviews, p.streak,
                       p.created_at as progress_created_at, p.updated_at as progress_updated_at
                FROM cards c
                JOIN user_progress p ON c.id = p.card_id
                WHERE c.is_active = TRUE AND (p.next_review IS NULL OR p.next_review <= ?)
                ORDER BY p.next_review ASC
            """
            params = [datetime.now()]
            
            if limit:
                sql += " LIMIT ?"
                params.append(limit)
            
            rows = conn.execute(sql, params).fetchall()
            results = []
            
            for row in rows:
                # Create card from row data
                card = Card(
                    id=row['card_id'],
                    content=row['content'],
                    source_material=row['source_material'],
                    tags=json.loads(row['tags']) if row['tags'] else [],
                    difficulty_level=DifficultyLevel(row['difficulty_level']),
                    created_at=datetime.fromisoformat(row['card_created_at']) if row['card_created_at'] else None,
                    updated_at=datetime.fromisoformat(row['card_updated_at']) if row['card_updated_at'] else None,
                    is_active=bool(row['is_active'])
                )
                
                # Create progress from row data
                progress = UserProgress(
                    id=row['progress_id'],
                    card_id=row['p_card_id'],
                    question_id=row['question_id'],
                    ease_factor=row['ease_factor'],
                    interval_days=row['interval_days'],
                    repetitions=row['repetitions'],
                    last_review=datetime.fromisoformat(row['last_review']) if row['last_review'] else None,
                    next_review=datetime.fromisoformat(row['next_review']) if row['next_review'] else None,
                    total_reviews=row['total_reviews'],
                    correct_reviews=row['correct_reviews'],
                    streak=row['streak'],
                    created_at=datetime.fromisoformat(row['progress_created_at']) if row['progress_created_at'] else None,
                    updated_at=datetime.fromisoformat(row['progress_updated_at']) if row['progress_updated_at'] else None
                )
                
                results.append((card, progress))
            
            return results
    
    # Helper methods to convert database rows to models
    def _row_to_card(self, row) -> Card:
        """Convert database row to Card model."""
        return Card(
            id=row['id'],
            content=row['content'],
            source_material=row['source_material'],
            tags=json.loads(row['tags']) if row['tags'] else [],
            difficulty_level=DifficultyLevel(row['difficulty_level']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            is_active=bool(row['is_active'])
        )
    
    def _row_to_question(self, row) -> Question:
        """Convert database row to Question model."""
        return Question(
            id=row['id'],
            card_id=row['card_id'],
            question_text=row['question_text'],
            answer_text=row['answer_text'],
            question_type=QuestionType(row['question_type']),
            difficulty=DifficultyLevel(row['difficulty']),
            generation_prompt=row['generation_prompt'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )
    
    def _row_to_progress(self, row) -> UserProgress:
        """Convert database row to UserProgress model."""
        return UserProgress(
            id=row['id'],
            card_id=row['card_id'],
            question_id=row['question_id'],
            ease_factor=row['ease_factor'],
            interval_days=row['interval_days'],
            repetitions=row['repetitions'],
            last_review=datetime.fromisoformat(row['last_review']) if row['last_review'] else None,
            next_review=datetime.fromisoformat(row['next_review']) if row['next_review'] else None,
            total_reviews=row['total_reviews'],
            correct_reviews=row['correct_reviews'],
            streak=row['streak'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )


# Global database instance
db = DatabaseManager()