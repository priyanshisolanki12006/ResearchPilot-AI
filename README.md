# 📚 ResearchPilot AI

> **A Production-Ready Multi-Agent AI Research Assistant built with Google ADK, MCP, FastAPI, React, and Retrieval-Augmented Generation (RAG).**

ResearchPilot AI is a full-stack AI-powered research assistant that simplifies academic research by automating paper analysis, semantic search, literature review generation, citation management, research gap identification, and paper comparison through intelligent collaboration between multiple specialized AI agents.

---

## 🚀 Features

- 📄 Upload and analyze research papers (PDF)
- 🤖 Multi-Agent AI orchestration
- 🔍 Semantic search using vector embeddings
- 📝 AI-powered paper summarization
- 📚 Automatic literature review generation
- 📊 Side-by-side paper comparison
- 🎯 Research gap identification
- 📖 Citation generation (APA, IEEE, MLA, BibTeX, Chicago)
- 💻 Code implementation suggestions
- 📽 Presentation & slide generation
- 📤 Export reports as PDF, DOCX, and Markdown
- 🔒 Secure sandbox execution
- 🌐 Local deployment with React + FastAPI

---

# 🧠 Multi-Agent Architecture

ResearchPilot AI consists of **10 specialized AI agents** coordinated by a central Planner Agent.

| Agent | Responsibility |
|--------|---------------|
| 🧭 Planner Agent | Coordinates the complete workflow |
| 🔎 Research Retrieval Agent | Retrieves papers from local storage and research databases |
| 📑 Paper Analysis Agent | Extracts methodology, datasets, architecture and results |
| ✍️ Summarization Agent | Generates concise research summaries |
| ⚖️ Comparison Agent | Compares multiple research papers |
| 📚 Citation Agent | Generates citations in multiple formats |
| 📖 Literature Review Agent | Creates structured literature reviews |
| 🎯 Research Gap Agent | Identifies limitations and future research directions |
| 💻 Code Generation Agent | Suggests implementation code and repositories |
| 🎤 Presentation Agent | Generates presentation slides and speaker notes |

---

# 🏗️ System Architecture

```
                        User
                          │
                          ▼
                Planner Agent (Master)
                          │
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
 Research          Analysis Agent      Literature Agent
 Retrieval               │                  │
        ▼                 ▼                  ▼
 Vector Database     Comparison       Research Gap
        │                 │                  │
        └────────────┬────┴──────────────┬───┘
                     ▼                   ▼
               Citation Agent     Code Generator
                     │
                     ▼
             Presentation Agent
                     │
                     ▼
                 Final Response
```

---

# 📂 Project Structure

```
Capstone Project
│
├── backend
│   ├── app
│   │   ├── agents
│   │   ├── config
│   │   ├── db
│   │   ├── mcp
│   │   ├── schemas
│   │   ├── services
│   │   └── main.py
│   │
│   ├── tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
│
├── frontend
│   ├── src
│   ├── public
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
│
├── data
│
├── docker-compose.yml
└── README.md
```

---

# ⚙️ Tech Stack

### Frontend

- React.js
- Vite
- CSS
- Axios

### Backend

- FastAPI
- Python
- SQLAlchemy
- Pydantic
- Uvicorn

### AI & RAG

- Google Gemini
- Google ADK
- MCP
- PyMuPDF
- ChromaDB / In-Memory Vector Store
- Semantic Search

### Database

- SQLite
- ChromaDB

### DevOps

- Docker
- Docker Compose

---

# 🔒 Security Features

- Secure file upload validation
- Sandboxed file access
- Input sanitization
- Safe MCP tool execution
- Local simulation mode
- API key fallback
- Secure path validation

---

# 🚀 Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/yourusername/ResearchPilot-AI.git

cd ResearchPilot-AI
```

---

## 2️⃣ Backend Setup

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt

python -m uvicorn app.main:app --reload --port 8000
```

Backend will start at

```
http://localhost:8000
```

Swagger Documentation

```
http://localhost:8000/docs
```

---

## 3️⃣ Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend will start at

```
http://localhost:3000
```

---

# 🐳 Docker Deployment

```bash
docker-compose up --build
```

| Service | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

# 🧪 Running Tests

```bash
cd backend

python tests/run_tests.py
```

or

```bash
pytest tests/
```

---

# 📊 Core Functionalities

- PDF Upload
- Semantic Search
- Multi-Agent Collaboration
- Research Paper Summarization
- Literature Review Generation
- Citation Management
- Paper Comparison
- Research Gap Analysis
- Export Reports
- AI Chat Workspace

---

# 📸 Application Preview

Add screenshots here.

### Dashboard

```
assets/dashboard.png
```

### Agent Workspace

```
assets/chat.png
```

### Literature Review

```
assets/literature.png
```

### Paper Comparison

```
assets/comparison.png
```

---
<img width="1920" height="1080" alt="Screenshot 2026-07-03 205452" src="https://github.com/user-attachments/assets/18799ff2-6bda-4ce0-b19a-4bda40bffef6" />

# 🔮 Future Enhancements

- Multi-user authentication
- Cloud deployment
- Real-time collaboration
- Voice-enabled research assistant
- OCR support for scanned papers
- Research graph visualization
- AI-powered presentation generation
- Mobile responsive application
- Live arXiv integration
- Citation network visualization

---

# 👨‍💻 Author

**Priyanshi Solanki**

B.Tech CSE (Software Engineering)

VIT Bhopal University

---

# ⭐ Support

If you found this project helpful, consider giving it a ⭐ on GitHub.

---

# 📄 License

This project is developed for educational and portfolio purposes under the MIT License.
