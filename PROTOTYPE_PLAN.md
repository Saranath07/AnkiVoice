# AnkiVoice Prototype Implementation Plan

## Overview
This document outlines the implementation plan for a minimal working prototype of AnkiVoice that demonstrates the core functionality using the existing Ollama Gemma 3:4B model.

## Prototype Scope

### Core Features to Implement
1. **Question Generation**: Convert study material into Q&A pairs using Ollama
2. **Answer Evaluation**: Use LLM to evaluate user responses
3. **Basic Spaced Repetition**: Simple scheduling algorithm
4. **Streamlit Interface**: Web-based UI for interaction
5. **SQLite Database**: Basic data persistence

### Files to Create

#### 1. `app.py` - Main Streamlit Application
```python
# Main entry point for the Streamlit app
# Features:
# - Card management interface
# - Study session controls
# - Question generation demo
# - Answer evaluation demo
```

#### 2. `database.py` - Database Management
```python
# SQLite database operations
# - Initialize database with schema
# - CRUD operations for cards, questions, progress
# - Connection management
```

#### 3. `llm_service.py` - Ollama Integration
```python
# LLM service wrapper
# - Question generation prompts
# - Answer evaluation prompts
# - Error handling and retries
# - Model management
```

#### 4. `spaced_repetition.py` - SR Algorithm
```python
# Simplified spaced repetition system
# - SM-2 algorithm implementation
# - Schedule calculation
# - Progress tracking
```

#### 5. `models.py` - Data Models
```python
# Pydantic models for data validation
# - Card model
# - Question model
# - UserProgress model
# - Session model
```

#### 6. `config.py` - Configuration
```python
# Application configuration
# - Database settings
# - Ollama settings
# - Default parameters
```

## Implementation Steps

### Phase 1: Core Infrastructure
1. Set up SQLite database with basic schema
2. Create Ollama service wrapper
3. Implement basic data models
4. Create simple Streamlit interface

### Phase 2: Question Generation
1. Implement question generation prompts
2. Create batch processing for multiple questions
3. Add question validation and filtering
4. Test with sample study material

### Phase 3: Answer Evaluation
1. Implement answer evaluation prompts
2. Add confidence scoring
3. Create feedback generation
4. Test with various answer types

### Phase 4: Spaced Repetition
1. Implement SM-2 algorithm
2. Add scheduling logic
3. Create progress tracking
4. Test review cycles

### Phase 5: User Interface
1. Create card management interface
2. Add study session controls
3. Implement progress visualization
4. Add configuration options

## Sample Prompts for LLM

### Question Generation Prompt
```
You are an expert educator creating study questions from learning material.

Given this statement: "{content}"

Generate 3 different questions that test understanding of this concept. Each question should:
1. Have the same core answer but ask from different perspectives
2. Be clear and unambiguous
3. Test genuine understanding, not just memorization

Format your response as JSON:
{
  "questions": [
    {
      "question": "Question text here",
      "answer": "Expected answer",
      "difficulty": 1-5,
      "type": "standard"
    }
  ]
}

Statement: {content}
```

### Answer Evaluation Prompt
```
You are evaluating a student's answer to a study question.

Question: {question}
Expected Answer: {expected_answer}
Student's Answer: {user_answer}

Evaluate the student's response and provide:
1. Whether the answer is correct (true/false)
2. Confidence score (0.0-1.0)
3. Brief feedback explaining the evaluation
4. Suggestions for improvement if incorrect

Format as JSON:
{
  "is_correct": boolean,
  "confidence": float,
  "feedback": "string",
  "suggestions": "string or null"
}
```

## Database Schema (Simplified for Prototype)

```sql
-- Cards table
CREATE TABLE cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Questions table
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    difficulty INTEGER DEFAULT 1,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

-- User progress table
CREATE TABLE user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL,
    ease_factor REAL DEFAULT 2.5,
    interval_days INTEGER DEFAULT 1,
    repetitions INTEGER DEFAULT 0,
    last_review TIMESTAMP,
    next_review TIMESTAMP,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);
```

## Streamlit Interface Structure

### Main Page Layout
```
┌─────────────────────────────────────┐
│           AnkiVoice Prototype       │
├─────────────────────────────────────┤
│  📚 Card Management                 │
│  ├─ Add New Card                    │
│  ├─ View All Cards                  │
│  └─ Generate Questions              │
├─────────────────────────────────────┤
│  🎯 Study Session                   │
│  ├─ Start Review Session            │
│  ├─ Practice Mode                   │
│  └─ View Progress                   │
├─────────────────────────────────────┤
│  ⚙️  Settings                       │
│  ├─ Ollama Configuration            │
│  ├─ Model Selection                 │
│  └─ SR Parameters                   │
└─────────────────────────────────────┘
```

## Testing Strategy

### Unit Tests
- Database operations
- LLM service functions
- Spaced repetition calculations
- Data model validation

### Integration Tests
- End-to-end question generation
- Answer evaluation accuracy
- Database persistence
- Streamlit interface functionality

### Performance Tests
- LLM response times
- Database query performance
- Memory usage monitoring
- Concurrent user handling

## Dependencies

```txt
# Core dependencies
streamlit>=1.28.0
ollama>=0.1.7
sqlite3 (built-in)
pydantic>=2.0.0

# Optional enhancements
pandas>=2.0.0
plotly>=5.0.0
python-dateutil>=2.8.0
```

## Configuration Options

### Ollama Settings
- Model selection (gemma3:4b, llama3.2:3b, etc.)
- Temperature settings
- Max tokens
- Timeout values

### Spaced Repetition Settings
- Initial interval
- Ease factor bounds
- Maximum interval
- Difficulty multipliers

### UI Settings
- Theme selection
- Default page layout
- Progress visualization options

## Success Metrics

### Functional Metrics
- Question generation accuracy (>80% relevant questions)
- Answer evaluation accuracy (>85% correct assessments)
- Response time (<3 seconds for generation, <1 second for evaluation)
- Database operations (<100ms for typical queries)

### User Experience Metrics
- Interface responsiveness
- Error handling coverage
- Data persistence reliability
- Configuration flexibility

## Next Steps After Prototype

1. **Audio Integration**: Add TTS and ASR capabilities
2. **Advanced UI**: Enhance Streamlit interface with custom components
3. **Performance Optimization**: Implement caching and async processing
4. **Multi-user Support**: Add user authentication and data isolation
5. **Mobile Compatibility**: Optimize for mobile devices
6. **Export/Import**: Add data backup and restore functionality

## Implementation Timeline

- **Week 1**: Core infrastructure and database setup
- **Week 2**: LLM integration and question generation
- **Week 3**: Answer evaluation and spaced repetition
- **Week 4**: Streamlit interface and testing
- **Week 5**: Polish, documentation, and deployment preparation

This prototype will serve as a solid foundation for the full AnkiVoice application, demonstrating all core concepts while remaining simple enough to implement quickly.