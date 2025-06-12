"""
LLM service for AnkiVoice using Ollama with Gemma 3:4B model.
"""

import json
import time
import logging
from typing import List, Dict, Any, Optional
import ollama

from models import (
    QuestionGenerationRequest, QuestionGenerationResponse,
    AnswerEvaluationRequest, AnswerEvaluationResponse,
    QuestionType, DifficultyLevel
)
from config import config

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Ollama LLM."""
    
    def __init__(self):
        """Initialize LLM service."""
        self.model = config.DEFAULT_MODEL
        self.client = ollama
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to Ollama server."""
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': 'Hello'}],
                options={'num_predict': 10}
            )
            logger.info(f"Successfully connected to Ollama with model {self.model}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise ConnectionError(f"Cannot connect to Ollama server: {e}")
    
    def generate_questions(self, request: QuestionGenerationRequest) -> QuestionGenerationResponse:
        """Generate questions from study material."""
        start_time = time.time()
        
        try:
            prompt = self._build_question_generation_prompt(request)
            
            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    'temperature': config.LLM_TEMPERATURE,
                    'num_predict': config.LLM_MAX_TOKENS
                }
            )
            
            # Parse the response
            content = response['message']['content']
            questions = self._parse_question_response(content, request.num_questions)
            
            generation_time = int((time.time() - start_time) * 1000)
            
            return QuestionGenerationResponse(
                questions=questions,
                generation_time_ms=generation_time,
                model_used=self.model
            )
            
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            raise RuntimeError(f"Failed to generate questions: {e}")
    
    def evaluate_answer(self, request: AnswerEvaluationRequest) -> AnswerEvaluationResponse:
        """Evaluate user's answer against expected answer."""
        start_time = time.time()
        
        try:
            # Pre-check for obvious non-answers
            user_answer_lower = request.user_answer.lower().strip()
            non_answers = ['i forgot', 'i don\'t know', 'no idea', 'not sure', 'dunno', 'idk', '???']
            
            if (not request.user_answer.strip() or
                len(request.user_answer.strip()) < 3 or
                any(non_answer in user_answer_lower for non_answer in non_answers)):
                
                evaluation_time = int((time.time() - start_time) * 1000)
                return AnswerEvaluationResponse(
                    is_correct=False,
                    confidence=0.95,
                    feedback="No valid answer provided. Please try to answer based on your understanding of the concept.",
                    suggestions="Review the study material and provide a substantive answer that demonstrates your knowledge.",
                    evaluation_time_ms=evaluation_time
                )
            
            prompt = self._build_answer_evaluation_prompt(request)
            
            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    'temperature': 0.3,  # Lower temperature for more consistent evaluation
                    'num_predict': 500
                }
            )
            
            # Parse the response
            content = response['message']['content']
            evaluation = self._parse_evaluation_response(content)
            
            evaluation_time = int((time.time() - start_time) * 1000)
            evaluation['evaluation_time_ms'] = evaluation_time
            
            return AnswerEvaluationResponse(**evaluation)
            
        except Exception as e:
            logger.error(f"Answer evaluation failed: {e}")
            raise RuntimeError(f"Failed to evaluate answer: {e}")
    
    def _build_question_generation_prompt(self, request: QuestionGenerationRequest) -> str:
        """Build prompt for question generation."""
        difficulty_text = self._get_difficulty_text(request.difficulty_range)
        types_text = ", ".join([t.value for t in request.question_types])
        
        prompt = f"""You are an expert educator creating study questions from learning material.

Given this statement: "{request.content}"

Generate {request.num_questions} different questions that test understanding of this concept. Each question should:
1. Have the same core answer but ask from different perspectives
2. Be clear and unambiguous
3. Test genuine understanding, not just memorization
4. Be at {difficulty_text} difficulty level
5. Use question types: {types_text}
6. Keep answers concise (under 200 words)

{"Include world knowledge and context where relevant." if request.include_world_knowledge else "Focus only on the given statement."}

Format your response as valid JSON:
{{
  "questions": [
    {{
      "question": "Question text here",
      "answer": "Brief, concise answer (under 200 words)",
      "difficulty": 1-5,
      "type": "standard"
    }}
  ]
}}

Statement: {request.content}"""
        
        return prompt
    
    def _build_answer_evaluation_prompt(self, request: AnswerEvaluationRequest) -> str:
        """Build prompt for answer evaluation."""
        context_text = f"\nContext: {request.context}" if request.context else ""
        
        prompt = f"""You are evaluating a student's answer to a study question. BE VERY STRICT.

Question: {request.question}
Expected Answer: {request.expected_answer}
Student's Answer: "{request.user_answer}"{context_text}

CRITICAL EVALUATION RULES - FOLLOW EXACTLY:
1. If student says "I forgot", "I don't know", "No idea", "Not sure", or any variation = INCORRECT (false)
2. If student gives empty, meaningless, or placeholder responses = INCORRECT (false)
3. If student doesn't demonstrate understanding of key concepts = INCORRECT (false)
4. Only mark CORRECT (true) if student shows genuine understanding

EXAMPLES OF INCORRECT RESPONSES:
- "I forgot" = INCORRECT
- "I don't know" = INCORRECT
- "No idea" = INCORRECT
- "" (empty) = INCORRECT
- "???" = INCORRECT

Evaluate the student's response and provide:
1. Whether the answer is correct (true/false) - BE STRICT
2. Confidence score (0.0-1.0) - how certain you are about your evaluation
3. Brief feedback explaining the evaluation
4. Suggestions for improvement if incorrect (or null if correct)

Format as valid JSON:
{{
  "is_correct": boolean,
  "confidence": float,
  "feedback": "string",
  "suggestions": "string or null"
}}"""
        
        return prompt
    
    def _parse_question_response(self, content: str, expected_count: int) -> List[Dict[str, Any]]:
        """Parse LLM response for question generation."""
        try:
            # Try to extract JSON from the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = content[json_start:json_end]
            data = json.loads(json_str)
            
            questions = data.get('questions', [])
            
            # Validate and clean questions
            validated_questions = []
            for q in questions[:expected_count]:  # Limit to expected count
                if 'question' in q and 'answer' in q:
                    # Truncate if too long to prevent validation errors
                    question_text = str(q['question']).strip()
                    answer_text = str(q['answer']).strip()
                    
                    if len(question_text) > 1800:
                        question_text = question_text[:1800] + "..."
                    if len(answer_text) > 1800:
                        answer_text = answer_text[:1800] + "..."
                    
                    validated_q = {
                        'question': question_text,
                        'answer': answer_text,
                        'difficulty': int(q.get('difficulty', 3)),
                        'type': str(q.get('type', 'standard'))
                    }
                    validated_questions.append(validated_q)
            
            if not validated_questions:
                raise ValueError("No valid questions found in response")
            
            return validated_questions
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse question response: {e}")
            # Fallback: create a simple question from the content
            return self._create_fallback_questions(expected_count)
    
    def _parse_evaluation_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response for answer evaluation."""
        try:
            # Try to extract JSON from the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = content[json_start:json_end]
            data = json.loads(json_str)
            
            # Validate required fields
            evaluation = {
                'is_correct': bool(data.get('is_correct', False)),
                'confidence': float(data.get('confidence', 0.5)),
                'feedback': str(data.get('feedback', 'Unable to evaluate answer')),
                'suggestions': data.get('suggestions')
            }
            
            # Ensure confidence is in valid range
            evaluation['confidence'] = max(0.0, min(1.0, evaluation['confidence']))
            
            return evaluation
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse evaluation response: {e}")
            # Fallback evaluation - check for common non-answers
            user_answer_lower = content.lower().strip()  # Use the raw content since we don't have request here
            non_answers = ['i forgot', 'i don\'t know', 'no idea', 'not sure', 'dunno']
            
            if any(non_answer in user_answer_lower for non_answer in non_answers) or len(user_answer_lower) < 3:
                return {
                    'is_correct': False,
                    'confidence': 0.9,
                    'feedback': 'No valid answer provided. Please try to answer the question based on your understanding.',
                    'suggestions': 'Review the study material and try to provide a substantive answer.'
                }
            else:
                return {
                    'is_correct': False,
                    'confidence': 0.3,
                    'feedback': 'Unable to properly evaluate the answer due to parsing error.',
                    'suggestions': 'Please try rephrasing your answer.'
                }
    
    def _create_fallback_questions(self, count: int) -> List[Dict[str, Any]]:
        """Create fallback questions when parsing fails."""
        return [{
            'question': f'What is the key concept in the given statement? (Question {i+1})',
            'answer': 'Please refer to the original statement',
            'difficulty': 3,
            'type': 'standard'
        } for i in range(count)]
    
    def _get_difficulty_text(self, difficulty_range: List[DifficultyLevel]) -> str:
        """Convert difficulty range to text description."""
        if not difficulty_range:
            return "medium"
        
        min_diff = min(difficulty_range)
        max_diff = max(difficulty_range)
        
        if min_diff == max_diff:
            difficulty_map = {
                DifficultyLevel.VERY_EASY: "very easy",
                DifficultyLevel.EASY: "easy",
                DifficultyLevel.MEDIUM: "medium",
                DifficultyLevel.HARD: "hard",
                DifficultyLevel.VERY_HARD: "very hard"
            }
            return difficulty_map.get(min_diff, "medium")
        else:
            return f"ranging from {min_diff.name.lower().replace('_', ' ')} to {max_diff.name.lower().replace('_', ' ')}"
    
    def test_model(self) -> Dict[str, Any]:
        """Test the model with a simple query."""
        try:
            start_time = time.time()
            
            response = self.client.chat(
                model=self.model,
                messages=[{
                    'role': 'user', 
                    'content': 'Generate one simple math question and its answer in JSON format: {"question": "...", "answer": "..."}'
                }],
                options={'temperature': 0.7, 'num_predict': 100}
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            return {
                'success': True,
                'model': self.model,
                'response_time_ms': response_time,
                'response': response['message']['content']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'model': self.model
            }


# Global LLM service instance
llm_service = LLMService()