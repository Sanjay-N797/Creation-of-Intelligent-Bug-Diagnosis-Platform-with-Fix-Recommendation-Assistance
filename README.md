# Smart Bug Analyzer

> **Intelligent Bug Diagnosis Platform with Automated Fix Recommendation & AI Mentorship Assistance**

Smart Bug Analyzer is an enterprise-grade, Multi-Agent AI coding platform designed to streamline defect diagnosis, root cause analysis, fix strategy generation, and automated code review. Powered by **Python FastAPI**, **SQLAlchemy ORM**, **Sentence-Transformers**, **FAISS**, and **Streamlit**, the platform transforms raw error reports and stack traces into actionable engineering insights and verified fix strategies.

---

## 📌 Problem Statement

In modern software engineering, diagnosing application defects, stack traces, and unexpected runtime failures is often time-consuming and fragmented. Engineers frequently face:
- **High Triage Overhead**: Manual categorization and severity/priority assignment delay issue resolution.
- **Unstructured Diagnostic Workflows**: Lack of automated stack trace parsing and historical duplicate detection leads to redundant debugging effort.
- **Single-Option Fixes**: Developers rarely receive structured trade-off analyses (e.g., Quick Hotfix vs. Structural Refactoring).
- **Onboarding & Mentorship Gaps**: Junior developers lack real-time guidance on complex software architecture, security vulnerabilities, and testing best practices.

**Smart Bug Analyzer** solves these challenges by combining a 5-agent AI diagnostic pipeline, vector-similarity RAG retrieval, an interactive AI coding mentor, and automated code quality auditing.

---

## ✨ Key Features

### 🤖 1. Multi-Agent AI Diagnostic Pipeline
- **Triage Agent**: Automatically assigns severity (Critical, High, Medium, Low), priority (P1-P4), and domain classification with confidence scoring. Automatically triggers clarification questions if report context is low.
- **Log Analysis Agent**: Parses complex multi-language stack traces, isolates root exceptions, and pinpoints exact failure modules.
- **Root Cause Agent**: Correlates error patterns against historic bug taxonomies and vector knowledge embeddings. Includes a dedicated **Mentor Mode** offering beginner-friendly analogies and concept dictionaries.
- **Duplicate Detection Agent**: Employs TF-IDF and Cosine Similarity vector matching against previously resolved bug cases to prevent redundant work.
- **Remediation Agent**: Computes a 3-tier Fix Strategy Matrix (**Hotfix**, **Refactor**, **Architectural Redesign**) complete with effort scores, risk ratings, and trade-off summaries.

### 🩺 2. Code Doctor (Static Analysis Engine)
- Executes 17+ static analysis rules on code snippets.
- Highlights security vulnerabilities (SQL injection, hardcoded credentials, unsafe `eval()`), performance bottlenecks, and anti-patterns.
- Generates a **Health Score (0–100)** and actionable refactoring code diffs.

### 🧪 3. Automated Fix Verification & Test Generator
- **AI Auto-Fix**: Automatically produces patched code blocks addressing identified root causes.
- **Fix Verification Engine**: Validates candidate fixes against syntax and structural correctness criteria.
- **Test Case Generator**: Automatically creates executable Python `unittest` / `pytest` test suites to verify fix efficacy.

### 💬 4. Interactive AI Mentor Chat
- Context-aware conversational assistant trained on software design patterns, testing strategies, database optimization, Git workflows, and DevOps.
- Integrates seamlessly with active bug context to provide customized engineering advice.

### 📊 5. Defect Intelligence & Dual Dashboards
- **Web SPA Interface**: Responsive Single Page Application (HTML5 / Vanilla CSS3 / JS) served directly by FastAPI.
- **Streamlit Analytics Dashboard**: Rich analytics interface with component risk heatmaps, priority distributions, and sample bug loaders powered by Plotly.

---

## 🛠️ System Architecture & Workflow

```
                               ┌────────────────────────────────────────┐
                               │           User / Client UI             │
                               │   (Web SPA  /  Streamlit Dashboard)    │
                               └───────────────────┬────────────────────┘
                                                   │ HTTP / REST API
                                                   ▼
                               ┌────────────────────────────────────────┐
                               │            FastAPI Backend             │
                               │        (backend/app/main.py)           │
                               └───────────────────┬────────────────────┘
                                                   │
                ┌──────────────────────────────────┼──────────────────────────────────┐
                ▼                                  ▼                                  ▼
      ┌───────────────────┐              ┌───────────────────┐              ┌───────────────────┐
      │ REST API Routers  │              │  Agent Pipeline   │              │ SQLite Database   │
      │  (/api/v1/bugs,   │              │   Coordinator     │              │  (SQLAlchemy ORM) │
      │   /analyze, etc.) │              └─────────┬─────────┘              └───────────────────┘
      └───────────────────┘                        │
                                                   │ Coordinates Execution
                                                   ▼
       ┌────────────────────────────────────────────────────────────────────────────────────────┐
       │                               Multi-Agent AI Engine                                    │
       ├──────────────┬───────────────────┬──────────────────┬─────────────────┬────────────────┤
       │ TriageAgent  │ LogAnalysisAgent  │ RootCauseAgent   │ DuplicateAgent  │ Remediation    │
       │ (Severity/   │ (Stack Trace      │ (RAG + Mentor    │ (TF-IDF Cosine  │ Agent          │
       │ Priority)    │  Parser)          │  Analogies)      │  Similarity)    │ (3-Tier Fix)   │
       └──────────────┴───────────────────┴──────────────────┴─────────────────┴────────────────┘
```

---

## 💻 Technologies Used

| Category | Technology / Library | Usage in Project |
|:---|:---|:---|
| **Backend Framework** | Python 3.9+, FastAPI, Uvicorn | High-performance async REST API web server |
| **Data & ORM** | SQLAlchemy 2.0, SQLite | Database modeling, queries, schema creation, seeding |
| **Data Validation** | Pydantic v2, Pydantic-Settings | Type safety, settings management, request/response validation |
| **Security & Auth** | Bcrypt, Python-Jose (PyJWT) | Password hashing, JWT token creation and validation |
| **AI / NLP & RAG** | Sentence-Transformers, FAISS, scikit-learn | Semantic embedding generation, vector similarity, TF-IDF cosine matching |
| **Frontend UI** | HTML5, CSS3 (Glassmorphism), Vanilla JS | Fast, responsive single-page web dashboard |
| **Analytics UI** | Streamlit, Plotly | Interactive analytics, risk heatmaps, defect statistics |
| **Testing** | Python `unittest`, FastAPI `TestClient` | Integration test suite (16 automated tests) |

---

## 📁 Project Structure

```
smart-bug-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry point & static file routing
│   │   ├── config.py               # Environment & settings configuration (Pydantic)
│   │   ├── database.py             # SQLAlchemy engine & session setup
│   │   ├── seed.py                 # Database initialization & sample bug seeder
│   │   ├── api/                    # REST API endpoint routers
│   │   │   ├── analyze.py          # /analyze pipeline endpoint
│   │   │   ├── auth.py             # User authentication & JWT endpoints
│   │   │   ├── bugs.py             # Bug CRUD, stats, auto-fix, test generator
│   │   │   ├── chat.py             # AI mentor chat endpoints
│   │   │   └── code_review.py      # Code Doctor static analysis endpoint
│   │   ├── agents/                 # Multi-Agent AI System
│   │   │   ├── pipeline.py         # Agent pipeline orchestrator
│   │   │   ├── triage.py           # Severity/Priority classifier & clarification generator
│   │   │   ├── log_analysis.py     # Stack trace & error log parser
│   │   │   ├── root_cause.py       # Root cause analysis & Mentor Mode explanation engine
│   │   │   ├── duplicate.py        # TF-IDF duplicate detection engine
│   │   │   ├── remediation.py      # 3-tier fix strategy generator
│   │   │   ├── auto_fix.py         # Automated code patch generator
│   │   │   ├── fix_verification.py # Candidate fix verification engine
│   │   │   ├── test_generator.py   # Unit test suite synthesizer
│   │   │   ├── code_review.py      # 17-rule static analysis code checker
│   │   │   └── chat.py             # Contextual AI mentor advisor
│   │   ├── models/                 # SQLAlchemy ORM models (Bug, AnalysisResult, User, etc.)
│   │   ├── schemas/                # Pydantic data validation models
│   │   └── utils/                  # Authentication, logging, RAG retrieval, similarity logic
│   └── tests/
│       └── test_app.py             # Comprehensive unittest suite (16 tests)
├── database/
│   ├── schema.sql                  # Database DDL schema definitions
│   ├── seed.sql                    # SQL seed data (15 sample production bugs)
│   └── app.db                      # SQLite runtime database (auto-created)
├── frontend/
│   ├── index.html                  # Single-page web interface
│   ├── css/style.css               # Modern glassmorphism UI styles
│   └── js/                         # Vanilla JS API client & UI controllers
│       ├── api.js
│       └── app.js
├── app.py                          # Streamlit interactive analytics dashboard
├── requirements.txt                # Python package dependencies
├── .env.example                    # Environment variable configuration template
├── .gitignore                      # Git ignore patterns
├── LICENSE                         # MIT License
├── run.sh                          # One-command backend startup script
└── run_streamlit.sh                # Streamlit dashboard startup script
```

---

## 📋 Prerequisites

Ensure you have the following installed on your system:
- **Python**: Version `3.8+` (Python `3.9` or `3.10` recommended)
- **pip**: Python package manager
- **Web Browser**: Chrome, Firefox, Safari, or Edge

---

## 🚀 Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Sanjay-N797/smart-bug-analyzer.git
   cd smart-bug-analyzer
   ```

2. **Create & Activate Virtual Environment**
   ```bash
   # On macOS / Linux
   python3 -m venv venv
   source venv/bin/activate

   # On Windows (Command Prompt)
   venv\Scripts\activate

   # On Windows (PowerShell)
   venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Environment Variables Setup

Copy `.env.example` to `.env` to configure application settings:

```bash
cp .env.example .env
```

Contents of `.env`:
```env
APP_NAME="Smart Bug Analyzer Platform"
API_V1_STR="/api/v1"
SECRET_KEY="replace-this-with-a-secure-random-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# SQLite default for local development:
DATABASE_URL="sqlite:///./database/app.db"

# Optional: PostgreSQL connection string
# DATABASE_URL="postgresql://user:password@localhost:5432/bug_analyzer"

# Optional: MySQL connection string
# DATABASE_URL="mysql+pymysql://user:password@localhost:3306/bug_analyzer"
```

---

## ▶️ Running the Application

### Option 1: Automated One-Command Startup (FastAPI + Web SPA)

Run the backend startup script:
```bash
chmod +x run.sh && ./run.sh
```

This will automatically create `venv`, install dependencies, seed the database with 15 sample bug reports, and start FastAPI at `http://localhost:8000`.

### Option 2: Manual Backend Startup

```bash
# Activate virtual environment
source venv/bin/activate

# Seed database
python3 -m backend.app.seed

# Start FastAPI server
python3 -m backend.app.main
```

### Option 3: Running the Streamlit Analytics Dashboard

To launch the Streamlit frontend dashboard:
```bash
chmod +x run_streamlit.sh && ./run_streamlit.sh
```
Or manually:
```bash
source venv/bin/activate
streamlit run app.py
```
Streamlit will launch automatically at `http://localhost:8501`.

---

## 📍 Application Endpoints & Documentation

Once the backend is running, access the following URLs in your browser:
- 🌐 **Web Dashboard SPA**: [http://localhost:8000](http://localhost:8000)
- 📚 **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 📖 **ReDoc OpenAPI Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- 🩺 **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 💡 Example Workflow

1. **Submit a Bug Report**: Enter a title, stack trace, and description via the UI or API (`POST /api/v1/bugs/analyze`).
2. **Review AI Diagnosis**: View the auto-assigned severity, priority, extracted failure module, and RAG-based root cause analysis.
3. **Explore 3-Tier Fixes**: Compare **Hotfix** (fast patch), **Refactor** (clean code solution), and **Architectural Redesign** (long-term prevention).
4. **Run Code Doctor**: Paste code snippets into Code Doctor to perform automated static auditing and obtain health scores.
5. **Chat with AI Mentor**: Ask clarifying technical questions about fix implementations, design patterns, or unit testing strategies.
6. **Generate Auto-Fix & Unit Tests**: Click **Generate Fix** and **Generate Test Suite** to instantly receive patched code and verification test cases.

---

## 🧪 Running Automated Tests

The repository includes 16 comprehensive integration tests covering end-to-end multi-agent pipelines, AI chat, static auditing, fix verification, auto-test generation, and REST endpoints.

To run the test suite:
```bash
source venv/bin/activate
./venv/bin/python -m unittest discover -s backend/tests -v
```

---

## 🔮 Future Improvements

- [ ] **Multi-Model LLM Integration**: Connect cloud LLM providers (OpenAI GPT-4, Claude 3.5, Gemini 1.5) as alternative agent backends.
- [ ] **IDE Extensions**: Build VS Code and IntelliJ plugins for inline bug diagnosis directly inside code editors.
- [ ] **CI/CD Pipeline Integration**: Automatically inspect failing GitHub Actions build logs and suggest pull request fixes.
- [ ] **Custom Vector Stores**: Support external vector databases (Pinecone / Qdrant) for enterprise-scale knowledge bases.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

Copyright (c) 2026 **Sanjay-N797**
