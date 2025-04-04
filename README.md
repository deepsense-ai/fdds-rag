# fdds-rag

### Project Structure
```
.
├── docker-compose.yml
├── Dockerfile
├── src/fdds
│   ├── __init__.py
│   ├── app.py
│   ├── inference.py
│   ├── pdf_loader.py
│   ├── handlers.py
│   ├── evaluation.py
│   ├── evaluation_pipeline.py
│   └── config.py
├── data
│   ├── qdrant
│   └── pdfs
├── .env
├── pyproject.toml
├── .pre-commit-config.yaml
├── README.md
└── uv.lock
```
## Key Components
- `data/pdfs`: directory for storing your PDF files.
- `data/qdrant`: local volume for Qdrant's data persistence.
- `docker-compose.yml` configures the Qdrant service and API (for the API see also `Dockerfile`).
- `src/fdds/inference.py` contains methods to process a query and generate responses based on contextual data using RAG.
- `src/fdds/pdf_loader.py` loads and processes PDF files from the `data/pdfs` directory into Qdrant.
- `src/fdds/evaluation.py` Evaluates RAG using a defined pipeline in the `src/fdds/evaluation_pipeline.py` file.
- `src/fdds/config.py` holds configuration settings for the project.
- `pyproject.toml` and `uv.lock`: configuration files for uv and project dependencies.
- `.pre-commit-config.yaml`: configuration for pre-commit hooks to ensure code quality.

## Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Pre-commit
- uv (https://docs.astral.sh/uv/)

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
OPEN_API_KEY=<your_api_key>
NEPTUNE_API_KEY=<your_api_key>
QDRANT_API_KEY=<your_api_key>
API_KEY=<your_api_key>
```
Replace the placeholders with your actual credentials and settings, and modify `src/fdds/config.py` to ensure it holds all necessary configurations like paths and connection details.
### 5. Start the Qdrant service:
Before using docker-compose ensure that Docker is running.
```
docker-compose up -d
```
### 6. Get links of PDF files:
Run this step only if you don't have a ready list of links to pdf files you want to use
```bash
cd scripts/fdds_scrapper
uv run scrapy crawl get_pdf_links
```
Links are saved in `scripts/fdds_scrapper/pdfs.txt`.
After properly checking the obtained links, place the text file in `data/pdfs`

### 7. Load PDF files into Qdrant:
Run this step once if there are no changes in the `data/pdfs` directory.
```bash
uv run src/pdf_loader.py
```
### 8. Run a query with the RAG model:
```bash
uv run src/inference.py "<Your query here>"
```
