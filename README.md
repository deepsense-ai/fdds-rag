# fdds-rag

### Project Structure
.
├── docker-compose.yml
├── src
│   ├── __init__.py
│   ├── inference.py
│   ├── pdf_loader.py
│   └── config.py
├── data
│   ├── qdrant
│   └── pdfs
├── .env
├── pyproject.toml
├── .pre-commit-config.yaml
├── README.md
└── uv.lock
## Key Components
- `docker-compose.yml` configures the Qdrant service and manages local volumes.
- `src/inference.py` contains methods to process a query and generate responses based on contextual data using RAG.
- `src/pdf_loader.py` loads and processes PDF files from the `data/pdfs` directory into Qdrant.
- `src/config.py` holds configuration settings for the project.
- `data/qdrant`: local volume for Qdrant's data persistence.
- `data/pdfs`: directory for storing your PDF files.
- `pyproject.toml` and `uv.lock`: configuration files for uv and project dependencies.
- `.pre-commit-config.yaml`: configuration for pre-commit hooks to ensure code quality.

## Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Pre-commit
- uv

## Setup and Installation
### 1. Clone the repository:
```bash
git clone git@github.com:deepsense-ai/fdds-rag.git
cd fdds-rag
```
### 2. Install and setup using uv:
```bash
uv python install 3.11
uv sync
```
### 3. Install pre-commit:
```
pre-commit install
```
### 4. Configure settings:
Ensure you created a `.env` file in the project root directory with all needed variables which are listed below:
```
API_KEY=<your_api_key>
```
Replace the placeholders with your actual credentials and settings, and modify src/config.py to ensure it holds all necessary configurations like paths and connection details.
### 5. Start the Qdrant service:
Before using docker-compose ensure that Docker is running.
```
docker-compose up -d
```
### 6. Load PDF files into Qdrant:
Run this step once if there are no changes in the `data/pdfs` directory.
```bash
uv run src/pdf_loader.py
```
### 7. Run a query with the RAG model:
```bash
uv run src/inference.py "<query>"
```
