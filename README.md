# DevPilot

> AI-powered developer workspace for understanding, analyzing, reviewing, and improving GitHub repositories.

DevPilot is a full-stack developer tool that connects a GitHub repository to an AI-assisted engineering workspace.

It helps developers explore unfamiliar codebases, understand architecture, chat with their repository, analyze dependencies and security vulnerabilities, review code, generate fixes, and create GitHub commits and pull requests.

---

## ✨ Features

### 📁 Repository Explorer

- Import GitHub repositories
- Browse repository files and folders
- Open source files directly in the code viewer
- View repository statistics

### 🤖 AI Repository Chat

Ask questions about the imported repository and get context-aware answers based on the codebase.

DevPilot uses repository retrieval so conversations can reference relevant source files instead of relying only on the user's prompt.

### 🔍 Code Understanding

- Explain source files and code
- Search repository content
- Retrieve relevant code context
- Navigate directly to referenced source files

### 🧠 Repository Architecture Analysis

Analyze the structure of a repository and identify:

- Entry points
- Major modules
- Detected dependencies
- Architectural observations
- Relationships between files

DevPilot also visualizes detected file dependencies as an interactive graph.

### 📝 AI Repository Review

Run an AI-assisted repository review to identify:

- Bugs
- Security concerns
- Performance issues
- Maintainability concerns

Review results include:

- Severity
- Description
- File location
- Line information
- Finding workflow status
- AI-generated fix actions

### 📦 Dependency Analysis

Analyze dependency manifests across multiple ecosystems.

Currently supported:

- npm
- Python / PyPI
- Maven
- Go
- Rust

DevPilot also reads npm `package-lock.json` files to determine resolved package versions.

### 🔐 Security & Vulnerability Analysis

DevPilot scans repository dependencies against the **OSV vulnerability database**.

The security analysis:

1. Retrieves repository dependencies
2. Resolves exact package versions when available
3. Queries OSV for known vulnerabilities
4. Reports verified vulnerability findings
5. Displays severity and dependency information in the UI

The vulnerability database is used as the authoritative source for vulnerability detection rather than generating vulnerability claims with the AI model.

### 🛠️ AI Code Actions

Generate AI-assisted code modifications for repository findings.

The workflow supports:

- Code modification proposals
- Side-by-side diffs
- Apply / Reject actions
- Repository-aware fixes

### 🌿 GitHub Integration

DevPilot can work with GitHub repositories to support:

- Branch operations
- Commit persistence
- Pull request creation
- Repository file access

### 📊 Review History

Repository reviews can be stored locally and compared over time.

The review dashboard includes:

- Review history
- Finding comparison
- New findings
- Resolved findings
- Persistent findings
- Finding trends
- Markdown export
- Finding workflow status

---

# 🏗️ Architecture

At a high level, DevPilot follows this architecture:

```text
                    GitHub Repository
                           │
                           ▼
                    ┌──────────────┐
                    │   DevPilot   │
                    │   Frontend   │
                    │ React + TS   │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   FastAPI    │
                    │    Backend   │
                    └──────┬───────┘
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
        GitHub API       Gemini        ChromaDB
             │             │             │
             │             │        Repository RAG
             │             │
             │             ▼
             │       AI Analysis
             │
             ▼
      Repository Data
                           │
                           ▼
                    Dependency Analysis
                           │
                           ▼
                         OSV.dev
                           │
                           ▼
                  Security Findings