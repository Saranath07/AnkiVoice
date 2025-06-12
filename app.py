"""
AnkiVoice - AI-Powered Flashcard Application
Main Streamlit application for the prototype.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json
import logging

from models import (
    Card, Question, UserProgress, StudySession, 
    QuestionGenerationRequest, AnswerEvaluationRequest,
    DifficultyLevel, QuestionType, StudyMode
)
from database import db
from llm_service import llm_service
from spaced_repetition import srs
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=config.STREAMLIT_PAGE_TITLE,
    page_icon=config.STREAMLIT_PAGE_ICON,
    layout=config.STREAMLIT_LAYOUT,
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_session' not in st.session_state:
    st.session_state.current_session = None
if 'current_card' not in st.session_state:
    st.session_state.current_card = None
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'study_cards' not in st.session_state:
    st.session_state.study_cards = []
if 'study_index' not in st.session_state:
    st.session_state.study_index = 0


def main():
    """Main application function."""
    st.title("🧠 AnkiVoice")
    st.markdown("*AI-Powered Voice-Driven Flashcards*")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Choose a page:",
            ["🏠 Dashboard", "📚 Card Management", "🎯 Study Session", "📊 Progress", "⚙️ Settings"]
        )
    
    # Route to appropriate page
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📚 Card Management":
        show_card_management()
    elif page == "🎯 Study Session":
        show_study_session()
    elif page == "📊 Progress":
        show_progress()
    elif page == "⚙️ Settings":
        show_settings()


def show_dashboard():
    """Display the main dashboard."""
    st.header("Dashboard")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_cards = len(db.get_all_cards())
        st.metric("Total Cards", total_cards)
    
    with col2:
        due_cards = db.get_due_cards()
        st.metric("Cards Due", len(due_cards))
    
    with col3:
        # Calculate today's reviews (placeholder)
        st.metric("Today's Reviews", 0)
    
    with col4:
        # Calculate accuracy (placeholder)
        st.metric("Overall Accuracy", "85%")
    
    # Quick actions
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎯 Start Study Session", use_container_width=True):
            st.session_state.page = "🎯 Study Session"
            st.rerun()
    
    with col2:
        if st.button("📚 Add New Card", use_container_width=True):
            st.session_state.page = "📚 Card Management"
            st.rerun()
    
    with col3:
        if st.button("🧪 Test LLM", use_container_width=True):
            test_llm_connection()
    
    # Recent activity (placeholder)
    st.subheader("Recent Activity")
    st.info("No recent activity to display.")


def show_card_management():
    """Display card management interface."""
    st.header("📚 Card Management")
    
    tab1, tab2, tab3 = st.tabs(["Add Card", "View Cards", "Generate Questions"])
    
    with tab1:
        show_add_card_form()
    
    with tab2:
        show_cards_list()
    
    with tab3:
        show_question_generation()


def show_add_card_form():
    """Show form to add new cards."""
    st.subheader("Add New Card")
    
    with st.form("add_card_form"):
        content = st.text_area(
            "Card Content",
            placeholder="Enter the statement, fact, or concept you want to study...",
            height=100
        )
        
        col1, col2 = st.columns(2)
        with col1:
            tags = st.text_input(
                "Tags (comma-separated)",
                placeholder="math, calculus, derivatives"
            )
        
        with col2:
            difficulty = st.selectbox(
                "Difficulty Level",
                options=[d for d in DifficultyLevel],
                format_func=lambda x: x.name.replace('_', ' ').title()
            )
        
        source_material = st.text_input(
            "Source Material (optional)",
            placeholder="Textbook chapter, lecture notes, etc."
        )
        
        submitted = st.form_submit_button("Add Card")
        
        if submitted and content.strip():
            try:
                # Create card
                card = Card(
                    content=content.strip(),
                    tags=[tag.strip() for tag in tags.split(',') if tag.strip()],
                    difficulty_level=difficulty,
                    source_material=source_material.strip() if source_material.strip() else None
                )
                
                # Save to database
                card_id = db.create_card(card)
                
                # Create initial progress entry
                db.get_or_create_progress(card_id)
                
                st.success(f"Card added successfully! ID: {card_id}")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error adding card: {e}")


def show_cards_list():
    """Show list of existing cards."""
    st.subheader("Your Cards")
    
    cards = db.get_all_cards()
    
    if not cards:
        st.info("No cards found. Add some cards to get started!")
        return
    
    # Bulk actions
    st.subheader("Bulk Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Add More Questions to All Cards"):
            progress_bar = st.progress(0)
            for i, card in enumerate(cards):
                st.write(f"Adding questions to Card {card.id}...")
                generate_questions_for_card(card, 2, True)  # Add 2 more questions to each card
                progress_bar.progress((i + 1) / len(cards))
            st.success(f"Added 2 more questions to all {len(cards)} cards!")
            st.rerun()
    
    with col2:
        if st.button("Generate Questions for Cards with Few Questions"):
            cards_needing_questions = []
            for card in cards:
                questions = db.get_questions_for_card(card.id)
                if len(questions) < 3:  # Cards with less than 3 questions
                    cards_needing_questions.append(card)
            
            if cards_needing_questions:
                progress_bar = st.progress(0)
                for i, card in enumerate(cards_needing_questions):
                    current_count = len(db.get_questions_for_card(card.id))
                    questions_to_add = 3 - current_count
                    st.write(f"Adding {questions_to_add} questions to Card {card.id}...")
                    generate_questions_for_card(card, questions_to_add, True)
                    progress_bar.progress((i + 1) / len(cards_needing_questions))
                st.success(f"Generated questions for {len(cards_needing_questions)} cards!")
                st.rerun()
            else:
                st.info("All cards already have at least 3 questions!")
    
    with col3:
        if st.button("Show Cards Without Questions"):
            cards_without_questions = [card for card in cards if len(db.get_questions_for_card(card.id)) == 0]
            if cards_without_questions:
                st.write(f"Found {len(cards_without_questions)} cards without questions:")
                for card in cards_without_questions:
                    st.write(f"- Card {card.id}: {card.content[:50]}...")
            else:
                st.success("All cards have questions!")
    
    # Search and filter
    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("Search cards", placeholder="Enter search term...")
    with col2:
        tag_filter = st.text_input("Filter by tag", placeholder="Enter tag...")
    
    # Filter cards
    filtered_cards = cards
    if search_term:
        filtered_cards = [c for c in filtered_cards if search_term.lower() in c.content.lower()]
    if tag_filter:
        filtered_cards = [c for c in filtered_cards if tag_filter.lower() in [t.lower() for t in c.tags]]
    
    # Display cards
    for card in filtered_cards:
        questions = db.get_questions_for_card(card.id)
        question_count = len(questions)
        
        with st.expander(f"Card {card.id}: {card.content[:80]}... ({question_count} questions)"):
            st.write(f"**Content:** {card.content}")
            st.write(f"**Tags:** {', '.join(card.tags) if card.tags else 'None'}")
            st.write(f"**Difficulty:** {card.difficulty_level.name.replace('_', ' ').title()}")
            st.write(f"**Created:** {card.created_at}")
            
            # Show questions for this card
            if questions:
                st.write(f"**All Questions ({question_count}):**")
                for i, q in enumerate(questions, 1):
                    st.write(f"**Q{i}:** {q.question_text}")
                    st.write(f"**A{i}:** {q.answer_text}")
                    st.write(f"*Difficulty: {q.difficulty.name.replace('_', ' ').title()}*")
                    if i < len(questions):  # Don't add separator after last question
                        st.write("---")
            else:
                st.write("**No questions generated yet.**")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"Generate Questions", key=f"gen_{card.id}"):
                    generate_questions_for_card(card)
            with col2:
                if st.button(f"Study This Card", key=f"study_{card.id}"):
                    st.info(f"Single card study for card {card.id} - feature coming soon!")
            with col3:
                if st.button(f"Delete Card", key=f"del_{card.id}", type="secondary"):
                    # Store card ID for deletion confirmation
                    st.session_state[f'delete_confirm_{card.id}'] = True
                    st.rerun()
                
                # Show confirmation dialog if delete was clicked
                if st.session_state.get(f'delete_confirm_{card.id}', False):
                    st.warning(f"⚠️ Are you sure you want to delete Card {card.id}?")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button(f"Yes, Delete", key=f"confirm_del_{card.id}", type="primary"):
                            if db.delete_card(card.id):
                                st.success(f"Card {card.id} deleted successfully!")
                                # Clear confirmation state
                                st.session_state[f'delete_confirm_{card.id}'] = False
                                st.rerun()
                            else:
                                st.error(f"Failed to delete card {card.id}")
                    with col_no:
                        if st.button(f"Cancel", key=f"cancel_del_{card.id}"):
                            st.session_state[f'delete_confirm_{card.id}'] = False
                            st.rerun()


def show_question_generation():
    """Show question generation interface."""
    st.subheader("Generate Questions")
    
    cards = db.get_all_cards()
    if not cards:
        st.info("No cards available. Add some cards first!")
        return
    
    # Select card
    card_options = {f"Card {c.id}: {c.content[:50]}...": c for c in cards}
    selected_card_key = st.selectbox("Select a card:", list(card_options.keys()))
    selected_card = card_options[selected_card_key]
    
    # Generation options
    col1, col2 = st.columns(2)
    with col1:
        num_questions = st.slider("Number of questions", 1, 10, 3)
    with col2:
        include_world_knowledge = st.checkbox("Include world knowledge", value=True)
    
    if st.button("Generate Questions"):
        generate_questions_for_card(selected_card, num_questions, include_world_knowledge)


def generate_questions_for_card(card: Card, num_questions: int = 3, include_world_knowledge: bool = True):
    """Generate questions for a specific card."""
    try:
        with st.spinner("Generating questions..."):
            # Create request
            request = QuestionGenerationRequest(
                content=card.content,
                num_questions=num_questions,
                question_types=[QuestionType.STANDARD],
                difficulty_range=[card.difficulty_level],
                include_world_knowledge=include_world_knowledge
            )
            
            # Generate questions
            response = llm_service.generate_questions(request)
            
            # Save questions to database and create progress entries
            new_question_ids = []
            for q_data in response.questions:
                question = Question(
                    card_id=card.id,
                    question_text=q_data['question'],
                    answer_text=q_data['answer'],
                    question_type=QuestionType(q_data.get('type', 'standard')),
                    difficulty=DifficultyLevel(q_data.get('difficulty', 3)),
                    generation_prompt=request.content
                )
                question_id = db.create_question(question)
                new_question_ids.append(question_id)
                
                # Create or update progress entry for the card (makes it due for review)
                progress = db.get_or_create_progress(card.id)
                # Set next_review to now so it becomes due immediately
                progress.next_review = datetime.now()
                db.update_progress(progress)
            
            st.success(f"Generated {len(response.questions)} questions in {response.generation_time_ms}ms")
            
            # Display generated questions
            st.subheader("Generated Questions:")
            for i, q_data in enumerate(response.questions, 1):
                st.write(f"**Q{i}:** {q_data['question']}")
                st.write(f"**A{i}:** {q_data['answer']}")
                st.write("---")
            
            st.rerun()
            
    except Exception as e:
        st.error(f"Error generating questions: {e}")


def show_study_session():
    """Display study session interface."""
    st.header("🎯 Study Session")
    
    # Check if session is active
    if st.session_state.current_session is None:
        show_session_setup()
    else:
        show_active_session()


def show_session_setup():
    """Show session setup interface."""
    st.subheader("Start New Study Session")
    
    # Get due cards
    due_cards = db.get_due_cards()
    all_cards = db.get_all_cards()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Cards Due for Review", len(due_cards))
    with col2:
        st.metric("Total Cards Available", len(all_cards))
    
    if not all_cards:
        st.warning("No cards available. Please add some cards first!")
        return
    
    # Session options
    with st.form("session_setup"):
        session_name = st.text_input("Session Name (optional)", placeholder="Morning Review")
        
        col1, col2 = st.columns(2)
        with col1:
            study_mode = st.selectbox(
                "Study Mode",
                options=[StudyMode.DEFAULT, StudyMode.CONTROLLED, StudyMode.NO_TTS],
                format_func=lambda x: x.value.replace('_', ' ').title()
            )
        
        with col2:
            max_cards = st.slider("Maximum Cards to Review", 1, min(50, len(all_cards)), 10)
        
        use_due_only = st.checkbox("Only review due cards", value=True)
        
        submitted = st.form_submit_button("Start Session")
        
        if submitted:
            start_study_session(session_name, study_mode, max_cards, use_due_only)


def start_study_session(session_name: str, mode: StudyMode, max_cards: int, due_only: bool):
    """Start a new study session."""
    try:
        # Get cards to study
        if due_only:
            cards_progress = db.get_due_cards(limit=max_cards)
        else:
            all_cards = db.get_all_cards(limit=max_cards)
            cards_progress = [(card, db.get_or_create_progress(card.id)) for card in all_cards]
        
        if not cards_progress:
            st.warning("No cards available for study!")
            return
        
        # Sort cards by priority
        cards_progress = srs.suggest_study_order(cards_progress)
        
        # Create session
        session = StudySession(
            session_name=session_name if session_name.strip() else None,
            mode=mode
        )
        
        # Store in session state
        st.session_state.current_session = session
        st.session_state.study_cards = cards_progress
        st.session_state.study_index = 0
        
        st.success(f"Started study session with {len(cards_progress)} cards!")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error starting session: {e}")


def show_active_session():
    """Show active study session interface."""
    session = st.session_state.current_session
    cards_progress = st.session_state.study_cards
    current_index = st.session_state.study_index
    
    # Session progress
    progress = current_index / len(cards_progress) if cards_progress else 0
    st.progress(progress, text=f"Progress: {current_index}/{len(cards_progress)} cards")
    
    # Session stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cards Reviewed", session.cards_reviewed)
    with col2:
        st.metric("Correct Answers", session.correct_answers)
    with col3:
        accuracy = session.accuracy if session.cards_reviewed > 0 else 0
        st.metric("Accuracy", f"{accuracy:.1f}%")
    
    # Check if session is complete
    if current_index >= len(cards_progress):
        show_session_complete()
        return
    
    # Current card
    current_card, current_progress = cards_progress[current_index]
    questions = db.get_questions_for_card(current_card.id)
    
    if not questions:
        st.warning(f"No questions available for card {current_card.id}. Generating questions...")
        generate_questions_for_card(current_card)
        st.rerun()
        return
    
    # Select a random question (refresh questions list to include newly generated ones)
    import random
    questions = db.get_questions_for_card(current_card.id)  # Refresh to get latest questions
    
    # Initialize question index in session state if not exists
    if f'question_index_{current_card.id}' not in st.session_state:
        st.session_state[f'question_index_{current_card.id}'] = 0
    
    question_index = st.session_state[f'question_index_{current_card.id}']
    current_question = questions[question_index % len(questions)]
    
    # Display question with navigation
    st.subheader("Current Question")
    st.write(f"**Card:** {current_card.content}")
    
    # Question navigation if multiple questions exist
    if len(questions) > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("← Previous Q"):
                st.session_state[f'question_index_{current_card.id}'] = (question_index - 1) % len(questions)
                # Clear evaluation state when navigating
                st.session_state.evaluation_complete = False
                st.session_state.evaluation_result = {}
                st.rerun()
        with col2:
            st.write(f"**Question {question_index + 1} of {len(questions)}:**")
        with col3:
            if st.button("Next Q →"):
                st.session_state[f'question_index_{current_card.id}'] = (question_index + 1) % len(questions)
                # Clear evaluation state when navigating
                st.session_state.evaluation_complete = False
                st.session_state.evaluation_result = {}
                st.rerun()
    
    st.write(f"**Question:** {current_question.question_text}")
    
    # Check if we have an evaluation result to display
    if st.session_state.get('evaluation_complete', False):
        show_evaluation_result()
    else:
        # Answer input
        with st.form("answer_form"):
            user_answer = st.text_area("Your Answer:", height=100)
            response_start_time = time.time()
            
            submitted = st.form_submit_button("Submit Answer")
            
            if submitted and user_answer.strip():
                response_time = time.time() - response_start_time
                evaluate_answer(current_card, current_question, user_answer.strip(), response_time)
    
    # Session controls
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Skip Card"):
            skip_current_card()
    with col2:
        if st.button("Generate More Questions"):
            generate_questions_for_card(current_card, 2, True)  # Generate 2 more questions
            st.success("Generated additional questions for this card!")
            
            # Update session to reflect new questions available
            session = st.session_state.current_session
            session.session_data = session.session_data or {}
            session.session_data['questions_generated'] = session.session_data.get('questions_generated', 0) + 2
            
            st.info("💡 New questions are now available for review! The card is due for study.")
            st.rerun()
    with col3:
        if st.button("End Session"):
            end_study_session()


def evaluate_answer(card: Card, question: Question, user_answer: str, response_time: float):
    """Evaluate user's answer."""
    try:
        with st.spinner("Evaluating answer..."):
            # Create evaluation request
            request = AnswerEvaluationRequest(
                question=question.question_text,
                expected_answer=question.answer_text,
                user_answer=user_answer,
                context=card.content
            )
            
            # Get LLM evaluation
            evaluation = llm_service.evaluate_answer(request)
            
            # Convert to quality score
            quality = srs.quality_from_evaluation(
                evaluation.is_correct,
                evaluation.confidence,
                response_time
            )
            
            # Update progress
            progress = db.get_or_create_progress(card.id)
            updated_progress, next_review = srs.calculate_next_review(
                progress, quality, response_time
            )
            db.update_progress(updated_progress)
            
            # Update session
            session = st.session_state.current_session
            session.cards_reviewed += 1
            if evaluation.is_correct:
                session.correct_answers += 1
            
            # Store evaluation result in session state for continuation
            st.session_state.evaluation_complete = True
            st.session_state.evaluation_result = {
                'is_correct': evaluation.is_correct,
                'feedback': evaluation.feedback,
                'confidence': evaluation.confidence,
                'quality': quality,
                'next_review': next_review,
                'expected_answer': question.answer_text,
                'user_answer': user_answer
            }
            
            # Force rerun to show evaluation result
            st.rerun()
            
    except Exception as e:
        st.error(f"Error evaluating answer: {e}")


def show_evaluation_result():
    """Show evaluation result and continue button outside of form."""
    result = st.session_state.get('evaluation_result', {})
    
    st.subheader("Feedback")
    if result.get('is_correct', False):
        st.success("✅ Correct!")
    else:
        st.error("❌ Incorrect")
    
    st.write(f"**Expected Answer:** {result.get('expected_answer', 'N/A')}")
    st.write(f"**Your Answer:** {result.get('user_answer', 'N/A')}")
    st.write(f"**Feedback:** {result.get('feedback', 'No feedback available')}")
    st.write(f"**Confidence:** {result.get('confidence', 0):.2f}")
    st.write(f"**Quality Score:** {result.get('quality', 0)}/5")
    
    if result.get('next_review'):
        st.write(f"**Next Review:** {result['next_review'].strftime('%Y-%m-%d %H:%M')}")
    
    # Continue button outside of form
    if st.button("Continue to Next Card"):
        st.session_state.study_index += 1
        st.session_state.evaluation_complete = False
        st.session_state.evaluation_result = {}
        st.rerun()


def skip_current_card():
    """Skip the current card."""
    st.session_state.study_index += 1
    st.rerun()


def end_study_session():
    """End the current study session."""
    session = st.session_state.current_session
    session.end_time = datetime.now()
    session.is_completed = True
    
    # Clear session state
    st.session_state.current_session = None
    st.session_state.study_cards = []
    st.session_state.study_index = 0
    
    st.success("Study session completed!")
    st.rerun()


def show_session_complete():
    """Show session completion summary."""
    session = st.session_state.current_session
    
    st.subheader("🎉 Session Complete!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cards Reviewed", session.cards_reviewed)
    with col2:
        st.metric("Correct Answers", session.correct_answers)
    with col3:
        st.metric("Accuracy", f"{session.accuracy:.1f}%")
    
    st.write(f"**Duration:** {session.duration_minutes:.1f} minutes")
    
    if st.button("Start New Session"):
        st.session_state.current_session = None
        st.session_state.study_cards = []
        st.session_state.study_index = 0
        st.rerun()


def show_progress():
    """Display progress and analytics."""
    st.header("📊 Progress & Analytics")
    
    # Placeholder for progress visualization
    st.info("Progress analytics will be implemented in the next iteration.")


def show_settings():
    """Display settings page."""
    st.header("⚙️ Settings")
    
    # LLM Settings
    st.subheader("LLM Configuration")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Ollama Host", value=config.OLLAMA_HOST, disabled=True)
    with col2:
        st.text_input("Model", value=config.DEFAULT_MODEL, disabled=True)
    
    # Test LLM connection
    if st.button("Test LLM Connection"):
        test_llm_connection()
    
    # Database info
    st.subheader("Database Information")
    st.text_input("Database Path", value=config.DATABASE_PATH, disabled=True)
    
    # Clear data (dangerous)
    st.subheader("⚠️ Danger Zone")
    if st.button("Clear All Data", type="secondary"):
        st.warning("Clear data functionality not implemented yet.")


def test_llm_connection():
    """Test connection to LLM service."""
    try:
        with st.spinner("Testing LLM connection..."):
            result = llm_service.test_model()
            
            if result['success']:
                st.success(f"✅ LLM connection successful!")
                st.write(f"**Model:** {result['model']}")
                st.write(f"**Response Time:** {result['response_time_ms']}ms")
                st.write(f"**Sample Response:** {result['response']}")
            else:
                st.error(f"❌ LLM connection failed: {result['error']}")
                
    except Exception as e:
        st.error(f"Error testing LLM: {e}")


if __name__ == "__main__":
    main()