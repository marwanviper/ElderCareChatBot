# 🧓 ElderCareChatBot

### AI-Powered Elderly Care & Assistance Platform

ElderCareChatBot is an intelligent care management platform designed to support elderly users through **AI-powered conversations, care management, and personalized assistance**.

The system combines a modern backend with AI capabilities to provide a foundation for managing elderly care data, caregiver interactions, and intelligent conversational experiences.

---

## ✨ Features

> 🚧 Features are being actively developed.

- 🤖 **AI Chatbot** — Intelligent conversational assistance
- 👴 **Elderly Profiles** — Manage user information and care-related data
- 🩺 **Care Reports** — Store and manage care observations and reports
- 👨‍⚕️ **Caregiver Support** — Organize information required by caregivers
- 💬 **Conversation Management** — Maintain and manage user conversations
- 🧠 **AI Memory** — Personalized context and long-term information
- 🔎 **Semantic Retrieval** — Retrieve relevant information using embeddings and vector search
- 🔐 **Authentication** — Secure user authentication and authorization

---

## 🛠️ Tech Stack

| Technology             | Purpose                    |
| ---------------------- | -------------------------- |
| 🐍 **Python**          | Core development language  |
| ⚡ **FastAPI**         | Backend API                |
| 🐘 **PostgreSQL**      | Database                   |
| 🗃️ **SQLAlchemy**      | ORM & database interaction |
| 📋 **Pydantic**        | Data validation & schemas  |
| 🤖 **LLM**             | Conversational AI          |
| 🧠 **Embeddings**      | Semantic representation    |
| 🔎 **Vector Database** | AI-powered retrieval       |
| 🌱 **Git**             | Version control            |

---

## 📁 Project Structure

```text
ElderCareChatBot/
│
├── src/
│   ├── database.py
│   └── models/
│       └── ...
│
├── crud/
│   └── ...
│
├── schemas/
│   └── ...
│
├── utils/
│   └── ...
│
├── README.md
└── ...
```

| Directory  | Description                                       |
| ---------- | ------------------------------------------------- |
| `src/`     | Core application components and SQLAlchemy models |
| `crud/`    | Database CRUD operations                          |
| `schemas/` | Pydantic request and response schemas             |
| `utils/`   | Shared utility functions                          |

---

## 🏗️ Backend

The backend is built around a modular structure that separates:

- Database configuration
- SQLAlchemy models
- CRUD operations
- Pydantic schemas
- API endpoints
- Application services
- AI components

This separation keeps the system maintainable and allows individual components to evolve independently.

---

## 🗄️ Database

PostgreSQL is used as the primary relational database.

SQLAlchemy provides the ORM layer responsible for:

- Database models
- Relationships
- Sessions
- Queries
- CRUD operations

The database layer is designed to support both the care-management system and the AI components that depend on structured user information.

---

## 🤖 AI System

The AI component is intended to provide personalized conversational assistance while maintaining relevant context about the user.

Planned AI capabilities include:

```text
Conversation
     │
     ▼
   LLM
     │
     ├──────────────┐
     ▼              ▼
Context         Retrieval
                    │
                    ▼
              Vector Database
                    │
                    ▼
              Relevant Memory
```

The AI layer will eventually support conversational context, semantic retrieval, and long-term memory.

---

## 🗺️ Roadmap

### Backend

- [x] PostgreSQL setup
- [x] SQLAlchemy configuration
- [x] Database models
- [x] CRUD layer
- [ ] Pydantic schemas
- [ ] FastAPI application
- [ ] API routers
- [ ] Authentication
- [ ] Authorization

### Care Management

- [ ] Elderly profiles
- [ ] Caregiver management
- [ ] Care reports
- [ ] Care history
- [ ] Notifications
- [ ] Care-related records

### AI

- [ ] Chatbot integration
- [ ] Conversation history
- [ ] Context management
- [ ] Long-term memory
- [ ] Embedding pipeline
- [ ] Vector database
- [ ] RAG pipeline
- [ ] Personalized responses

---

## 🚀 Getting Started

### Prerequisites

Make sure you have installed:

- Python 3.11+
- PostgreSQL
- Git

### Clone the repository

```bash
git clone https://github.com/marwanviper/ElderCareChatBot.git
cd ElderCareChatBot
```

### Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file containing the required database and application configuration.

```env
DATABASE_URL=your_database_url
```

Additional environment variables will be added as the application develops.

---

## 📌 Project Status

🚧 **Active Development**

ElderCareChatBot is currently under active development, with the backend infrastructure and database layer being established before expanding into the API and AI components.

---

## 👥 Contributors

Developed by **Marwan Abbas**.

---

## 📄 License

This project is currently under development.
