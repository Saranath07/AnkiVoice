# AnkiVoice Database Schema & API Design

## Database Schema (SQLite)

### Core Tables

#### 1. Cards Table
```sql
CREATE TABLE cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    source_material TEXT,
    tags TEXT, -- JSON array of tags
    difficulty_level INTEGER DEFAULT 1, -- 1-5 scale
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### 2. Questions Table
```sql
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    question_type TEXT DEFAULT 'standard', -- standard, multiple_choice, fill_blank
    difficulty INTEGER DEFAULT 1,
    generation_prompt TEXT, -- Store the prompt used to generate this question
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
);
```

#### 3. User Progress Table
```sql
CREATE TABLE user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    question_id INTEGER,
    ease_factor REAL DEFAULT 2.5, -- Anki's ease factor
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
);
```

#### 4. Study Sessions Table
```sql
CREATE TABLE study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_name TEXT,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    mode TEXT NOT NULL, -- default, controlled, no_tts, manual_decision
    cards_reviewed INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    average_response_time REAL,
    session_data TEXT, -- JSON data for session metrics
    is_completed BOOLEAN DEFAULT FALSE
);
```

#### 5. Session Reviews Table
```sql
CREATE TABLE session_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    card_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    user_response TEXT,
    transcribed_response TEXT,
    is_correct BOOLEAN,
    confidence_score REAL, -- LLM confidence in evaluation
    response_time_seconds REAL,
    feedback TEXT,
    difficulty_rating INTEGER, -- User's perceived difficulty 1-4
    review_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES study_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);
```

#### 6. User Settings Table
```sql
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    setting_type TEXT DEFAULT 'string', -- string, integer, boolean, json
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes for Performance
```sql
CREATE INDEX idx_cards_tags ON cards(tags);
CREATE INDEX idx_cards_created_at ON cards(created_at);
CREATE INDEX idx_questions_card_id ON questions(card_id);
CREATE INDEX idx_user_progress_card_id ON user_progress(card_id);
CREATE INDEX idx_user_progress_next_review ON user_progress(next_review);
CREATE INDEX idx_session_reviews_session_id ON session_reviews(session_id);
CREATE INDEX idx_session_reviews_timestamp ON session_reviews(review_timestamp);
```

## API Endpoints Specification

### Base URL: `http://localhost:5000/api/v1`

### 1. Cards Management

#### GET /cards
```json
{
  "description": "Get all cards with optional filtering",
  "parameters": {
    "tags": "string (optional) - Filter by tags",
    "difficulty": "integer (optional) - Filter by difficulty level",
    "limit": "integer (optional) - Limit results",
    "offset": "integer (optional) - Pagination offset"
  },
  "response": {
    "cards": [
      {
        "id": 1,
        "content": "Gradients point to the direction of the steepest ascent",
        "tags": ["math", "calculus"],
        "difficulty_level": 2,
        "created_at": "2024-01-01T10:00:00Z",
        "question_count": 3
      }
    ],
    "total": 50,
    "page": 1
  }
}
```

#### POST /cards
```json
{
  "description": "Create a new card",
  "request": {
    "content": "The mitochondria is the powerhouse of the cell",
    "tags": ["biology", "cell"],
    "difficulty_level": 1,
    "source_material": "Biology textbook chapter 3"
  },
  "response": {
    "id": 123,
    "message": "Card created successfully"
  }
}
```

#### PUT /cards/{id}
```json
{
  "description": "Update an existing card",
  "request": {
    "content": "Updated content",
    "tags": ["updated", "tags"],
    "difficulty_level": 3
  },
  "response": {
    "message": "Card updated successfully"
  }
}
```

#### DELETE /cards/{id}
```json
{
  "description": "Delete a card and all associated data",
  "response": {
    "message": "Card deleted successfully"
  }
}
```

### 2. Question Generation

#### POST /cards/{id}/generate-questions
```json
{
  "description": "Generate questions for a specific card",
  "request": {
    "num_questions": 3,
    "question_types": ["standard", "multiple_choice"],
    "difficulty_range": [1, 3]
  },
  "response": {
    "questions": [
      {
        "id": 456,
        "question_text": "In which direction do gradients point?",
        "answer_text": "Steepest ascent",
        "question_type": "standard",
        "difficulty": 2
      }
    ],
    "generation_time_ms": 1500
  }
}
```

### 3. Study Sessions

#### POST /sessions/start
```json
{
  "description": "Start a new study session",
  "request": {
    "mode": "default",
    "session_name": "Morning Review",
    "card_filters": {
      "tags": ["math"],
      "due_only": true
    }
  },
  "response": {
    "session_id": 789,
    "cards_due": 15,
    "estimated_time_minutes": 10
  }
}
```

#### GET /sessions/{id}/next-card
```json
{
  "description": "Get the next card for review",
  "response": {
    "card": {
      "id": 123,
      "content": "Gradients point to the direction of the steepest ascent"
    },
    "question": {
      "id": 456,
      "question_text": "In which direction do gradients point?",
      "answer_text": "Steepest ascent"
    },
    "progress": {
      "current": 5,
      "total": 15,
      "percentage": 33.3
    }
  }
}
```

#### POST /sessions/{id}/submit-answer
```json
{
  "description": "Submit an answer for evaluation",
  "request": {
    "question_id": 456,
    "user_response": "They point upward in the steepest direction",
    "response_time_seconds": 3.5,
    "audio_file": "base64_encoded_audio_data (optional)"
  },
  "response": {
    "is_correct": true,
    "confidence_score": 0.92,
    "feedback": "Excellent! Your answer captures the key concept correctly.",
    "next_review_date": "2024-01-03T10:00:00Z",
    "ease_factor": 2.6
  }
}
```

#### POST /sessions/{id}/complete
```json
{
  "description": "Complete a study session",
  "response": {
    "session_summary": {
      "cards_reviewed": 15,
      "correct_answers": 12,
      "accuracy": 80.0,
      "total_time_minutes": 8.5,
      "average_response_time": 2.3
    }
  }
}
```

### 4. Audio Processing

#### POST /audio/transcribe
```json
{
  "description": "Transcribe audio to text",
  "request": {
    "audio_data": "base64_encoded_audio",
    "format": "wav",
    "language": "en"
  },
  "response": {
    "transcription": "They point upward in the steepest direction",
    "confidence": 0.95,
    "processing_time_ms": 800
  }
}
```

#### POST /audio/synthesize
```json
{
  "description": "Convert text to speech",
  "request": {
    "text": "In which direction do gradients point?",
    "voice": "default",
    "speed": 1.0
  },
  "response": {
    "audio_data": "base64_encoded_audio",
    "duration_seconds": 2.5,
    "format": "wav"
  }
}
```

### 5. Analytics & Progress

#### GET /progress/overview
```json
{
  "description": "Get user's learning progress overview",
  "response": {
    "total_cards": 150,
    "cards_mastered": 45,
    "cards_learning": 80,
    "cards_new": 25,
    "daily_streak": 7,
    "accuracy_last_week": 85.5,
    "time_studied_minutes": 120
  }
}
```

#### GET /progress/due-cards
```json
{
  "description": "Get cards due for review",
  "response": {
    "due_now": 12,
    "due_today": 25,
    "overdue": 3,
    "cards": [
      {
        "id": 123,
        "content": "Sample card content",
        "due_date": "2024-01-01T10:00:00Z",
        "priority": "high"
      }
    ]
  }
}
```

## WebSocket Events (Real-time Features)

### Connection: `ws://localhost:5000/ws`

#### Client → Server Events
```json
{
  "event": "join_session",
  "data": {"session_id": 789}
}

{
  "event": "audio_stream",
  "data": {"chunk": "base64_audio_chunk"}
}

{
  "event": "request_next_card",
  "data": {"session_id": 789}
}
```

#### Server → Client Events
```json
{
  "event": "transcription_update",
  "data": {"partial_text": "They point upward..."}
}

{
  "event": "evaluation_complete",
  "data": {
    "is_correct": true,
    "feedback": "Great job!",
    "next_card_ready": true
  }
}

{
  "event": "session_progress",
  "data": {
    "current": 5,
    "total": 15,
    "time_elapsed": 300
  }
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "difficulty_level",
      "issue": "Must be between 1 and 5"
    },
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Invalid input parameters
- `NOT_FOUND`: Resource not found
- `UNAUTHORIZED`: Authentication required
- `RATE_LIMITED`: Too many requests
- `MODEL_ERROR`: LLM processing error
- `AUDIO_ERROR`: Audio processing failed
- `DATABASE_ERROR`: Database operation failed