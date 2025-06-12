"""
Test script for AnkiVoice prototype to verify all components work correctly.
"""

import sys
import traceback
from datetime import datetime

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from models import Card, Question, UserProgress, DifficultyLevel, QuestionType
        print("✅ Models imported successfully")
    except Exception as e:
        print(f"❌ Models import failed: {e}")
        return False
    
    try:
        from config import config
        print("✅ Config imported successfully")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from database import db
        print("✅ Database imported successfully")
    except Exception as e:
        print(f"❌ Database import failed: {e}")
        return False
    
    try:
        from llm_service import llm_service
        print("✅ LLM service imported successfully")
    except Exception as e:
        print(f"❌ LLM service import failed: {e}")
        return False
    
    try:
        from spaced_repetition import srs
        print("✅ Spaced repetition imported successfully")
    except Exception as e:
        print(f"❌ Spaced repetition import failed: {e}")
        return False
    
    return True


def test_database():
    """Test database operations."""
    print("\nTesting database operations...")
    
    try:
        from database import db
        from models import Card, DifficultyLevel
        
        # Test database initialization
        db.ensure_database()
        print("✅ Database initialized successfully")
        
        # Test card creation
        test_card = Card(
            content="The mitochondria is the powerhouse of the cell",
            tags=["biology", "cell"],
            difficulty_level=DifficultyLevel.MEDIUM
        )
        
        card_id = db.create_card(test_card)
        print(f"✅ Card created successfully with ID: {card_id}")
        
        # Test card retrieval
        retrieved_card = db.get_card(card_id)
        if retrieved_card and retrieved_card.content == test_card.content:
            print("✅ Card retrieved successfully")
        else:
            print("❌ Card retrieval failed")
            return False
        
        # Test progress creation
        progress = db.get_or_create_progress(card_id)
        print(f"✅ Progress created successfully with ID: {progress.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        traceback.print_exc()
        return False


def test_llm_service():
    """Test LLM service connection."""
    print("\nTesting LLM service...")
    
    try:
        from llm_service import llm_service
        
        # Test model connection
        result = llm_service.test_model()
        
        if result['success']:
            print(f"✅ LLM connection successful")
            print(f"   Model: {result['model']}")
            print(f"   Response time: {result['response_time_ms']}ms")
        else:
            print(f"❌ LLM connection failed: {result['error']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ LLM service test failed: {e}")
        traceback.print_exc()
        return False


def test_question_generation():
    """Test question generation functionality."""
    print("\nTesting question generation...")
    
    try:
        from llm_service import llm_service
        from models import QuestionGenerationRequest, DifficultyLevel, QuestionType
        
        # Create test request
        request = QuestionGenerationRequest(
            content="Gradients point to the direction of the steepest ascent",
            num_questions=2,
            question_types=[QuestionType.STANDARD],
            difficulty_range=[DifficultyLevel.MEDIUM],
            include_world_knowledge=True
        )
        
        # Generate questions
        response = llm_service.generate_questions(request)
        
        if response.questions and len(response.questions) > 0:
            print(f"✅ Generated {len(response.questions)} questions in {response.generation_time_ms}ms")
            for i, q in enumerate(response.questions, 1):
                print(f"   Q{i}: {q['question']}")
                print(f"   A{i}: {q['answer']}")
        else:
            print("❌ No questions generated")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Question generation test failed: {e}")
        traceback.print_exc()
        return False


def test_answer_evaluation():
    """Test answer evaluation functionality."""
    print("\nTesting answer evaluation...")
    
    try:
        from llm_service import llm_service
        from models import AnswerEvaluationRequest
        
        # Create test request
        request = AnswerEvaluationRequest(
            question="In which direction do gradients point?",
            expected_answer="Steepest ascent",
            user_answer="I forgot"
        )
        
        # Evaluate answer
        response = llm_service.evaluate_answer(request)
        
        print(f"✅ Answer evaluation completed in {response.evaluation_time_ms}ms")
        print(f"   Correct: {response.is_correct}")
        print(f"   Confidence: {response.confidence:.2f}")
        print(f"   Feedback: {response.feedback}")
        
        return True
        
    except Exception as e:
        print(f"❌ Answer evaluation test failed: {e}")
        traceback.print_exc()
        return False


def test_spaced_repetition():
    """Test spaced repetition system."""
    print("\nTesting spaced repetition system...")
    
    try:
        from spaced_repetition import srs
        from models import UserProgress
        from datetime import datetime
        
        # Create test progress
        progress = UserProgress(
            card_id=1,
            ease_factor=2.5,
            interval_days=1,
            repetitions=0
        )
        
        # Test quality conversion
        quality = srs.quality_from_evaluation(True, 0.9, 3.0)
        print(f"✅ Quality score calculated: {quality}")
        
        # Test next review calculation
        updated_progress, next_review = srs.calculate_next_review(progress, quality, 3.0)
        print(f"✅ Next review calculated: {next_review}")
        print(f"   New interval: {updated_progress.interval_days} days")
        print(f"   New ease factor: {updated_progress.ease_factor:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Spaced repetition test failed: {e}")
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests."""
    print("🧪 AnkiVoice Prototype Test Suite")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Database", test_database),
        ("LLM Service", test_llm_service),
        ("Question Generation", test_question_generation),
        ("Answer Evaluation", test_answer_evaluation),
        ("Spaced Repetition", test_spaced_repetition)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The prototype is ready to use.")
        print("\nTo run the application:")
        print("  streamlit run app.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)