# AnkiVoice - AI-Powered Voice-Driven Flashcards

AnkiVoice is a smart, voice-driven application that transforms the traditional flashcard experience by combining Generative AI with speech recognition and synthesis — all running on the edge.

## 🚀 Features

- **AI-Powered Question Generation**: Automatically generate multiple questions from study material using local LLM
- **Intelligent Answer Evaluation**: Use AI to evaluate responses with confidence scoring and feedback
- **Spaced Repetition System**: Implement SM-2 algorithm for optimal learning scheduling
- **Multiple Study Modes**: Support various interaction modes for different learning preferences
- **Local Processing**: All AI operations run locally using Ollama for privacy and offline capability
- **Progress Tracking**: Monitor learning progress with detailed analytics

## 🏗️ Architecture

The application follows a modular architecture designed for edge AI deployment:

- **Frontend**: Streamlit web interface
- **Backend**: Python Flask API (future)
- **AI Engine**: Ollama with Gemma 3:4B model
- **Database**: SQLite for local data storage
- **Algorithms**: SM-2 spaced repetition system

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## 📋 Prerequisites

- Python 3.11+
- Ollama installed and running
- Gemma 3:4B model downloaded in Ollama

### Install Ollama and Model

1. Install Ollama from [https://ollama.ai](https://ollama.ai)
2. Download the Gemma 3:4B model:
   ```bash
   ollama pull gemma3:4b
   ```
3. Verify the model is available:
   ```bash
   ollama list
   ```

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd AnkiVoice
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Test the installation:
   ```bash
   python test_prototype.py
   ```

## 🚀 Usage

### Running the Application

Start the Streamlit application:
```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

### Basic Workflow

1. **Add Cards**: Create flashcards with study material
2. **Generate Questions**: Use AI to create multiple questions per card
3. **Study Session**: Start a review session with spaced repetition
4. **Answer Evaluation**: Get AI feedback on your responses
5. **Progress Tracking**: Monitor your learning progress

### Study Modes

- **Default Mode**: Full automation (TTS → ASR → LLM evaluation) - *Future*
- **Controlled Mode**: User reviews transcription before LLM evaluation - *Future*
- **No TTS Mode**: Visual questions with ASR + LLM evaluation - *Future*
- **Manual Decision Mode**: User makes final scheduling decisions
- **Text Mode**: Current implementation with text-based interaction

## 📁 Project Structure

```
AnkiVoice/
├── app.py                 # Main Streamlit application
├── models.py             # Pydantic data models
├── database.py           # SQLite database management
├── llm_service.py        # Ollama LLM integration
├── spaced_repetition.py  # SM-2 algorithm implementation
├── config.py             # Application configuration
├── test_prototype.py     # Test suite
├── requirements.txt      # Python dependencies
├── ARCHITECTURE.md       # Architecture documentation
├── DATABASE_SCHEMA.md    # Database and API documentation
├── PROTOTYPE_PLAN.md     # Implementation plan
└── README.md            # This file
```

## 🧪 Testing

Run the test suite to verify all components:
```bash
python test_prototype.py
```

The test suite verifies:
- Module imports
- Database operations
- LLM service connection
- Question generation
- Answer evaluation
- Spaced repetition calculations

## 🔧 Configuration

Key configuration options in `config.py`:

- **Ollama Settings**: Host, model, temperature
- **Database**: SQLite path and settings
- **Spaced Repetition**: Algorithm parameters
- **UI**: Streamlit configuration

## 📊 Database Schema

The application uses SQLite with the following main tables:

- `cards`: Study material and metadata
- `questions`: Generated questions for each card
- `user_progress`: Spaced repetition progress tracking
- `study_sessions`: Session history and statistics
- `session_reviews`: Individual review records

See [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) for complete schema documentation.

## 🎯 Current Prototype Features

### ✅ Implemented
- Card management (CRUD operations)
- AI question generation using Ollama
- Answer evaluation with confidence scoring
- Spaced repetition scheduling (SM-2 algorithm)
- Progress tracking and statistics
- Streamlit web interface
- SQLite database with full schema

### 🚧 Future Enhancements
- Voice input/output (TTS/ASR integration)
- Advanced study modes
- Mobile-responsive interface
- Export/import functionality
- Multi-user support
- Performance optimizations for ARM processors

## 🔮 Roadmap

### Phase 1: Core Functionality ✅
- [x] Basic card management
- [x] Question generation
- [x] Answer evaluation
- [x] Spaced repetition
- [x] Web interface

### Phase 2: Voice Integration
- [ ] Text-to-Speech (TTS) integration
- [ ] Automatic Speech Recognition (ASR)
- [ ] Voice-driven study sessions
- [ ] Audio quality optimization

### Phase 3: Advanced Features
- [ ] Multiple study modes
- [ ] Advanced analytics
- [ ] Mobile app
- [ ] Cloud synchronization
- [ ] Collaborative features

### Phase 4: Optimization
- [ ] ARM processor optimization
- [ ] NPU utilization
- [ ] Performance benchmarking
- [ ] Rust migration for critical components

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Ollama team for the excellent local LLM platform
- Streamlit for the rapid prototyping framework
- Anki for inspiration on spaced repetition
- The open-source AI community

## 📞 Support

For questions, issues, or contributions:
- Create an issue on GitHub
- Check the documentation in the `docs/` folder
- Run the test suite for troubleshooting

---

**Note**: This is a prototype implementation. The voice features and advanced study modes are planned for future releases. The current version focuses on demonstrating the core AI-powered flashcard functionality with local LLM processing.