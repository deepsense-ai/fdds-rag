# fdds-rag

### Project Structure
```
.
├── docker-compose.yml
├── Dockerfile
├── .env
├── pyproject.toml
├── uv.lock
├── .pre-commit-config.yaml
├── README.md

├── data/
│   └── qdrant/

├── src/
│   ├── fdds/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── handlers.py
│   │   ├── inference.py
│   │   ├── evaluation.py
│   │   ├── evaluation_pipeline.py
│   │   ├── manage_pdfs.py
│   │   └── reranker.py
│   ├── ui-build/
│   └── chat.py
```
## Key Components
- `docker-compose.yml` Defines and manages services like Qdrant (vector DB), the API backend, and Jaeger (for monitoring and tracing).
- `Dockerfile`: Builds the backend API service that serves the RAG-based chatbot.
- `pyproject.toml` and `uv.lock`: Configuration files for uv and project dependencies.
- `.pre-commit-config.yaml`: Configuration for pre-commit hooks to ensure code quality.
- `data/qdrant`: Persistent volume for Qdrant's vector data storage.
- `src/fdds/inference.py` contains methods to process a query and generate responses based on contextual data using RAG.
- `src/fdds/manage_pdfs.py` script to ingest and delete PDF files from the list of URLs in Qdrant.
- `src/fdds/evaluation.py` Evaluates RAG using a defined pipeline in the `src/fdds/evaluation_pipeline.py` file (requires NEPTUNE_API_KEY).
- `src/fdds/config.py` holds configuration settings for the project.
- `src/ui-build`: Precompiled frontend UI assets for the chatbot interface.
- `src/chat.py`: Contains the core `MyChat` class responsible for managing conversation flow.

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
### 4. Start the system:
Use the automated startup script to launch the system. The script will handle environment configuration and service startup:

```bash
./start.sh
```

#### Startup Script Options:
- `--help` - Show all available options
- `--with-ingest` - Include ingestion service to process PDFs
- `--with-ingest-file FILE` - Use custom PDF file list for ingestion
- `--detached` - Run services in background mode
- `--jaeger` - Enable Jaeger tracing
- `--port PORT` - Set API port (default: 8000)
- `--host HOST` - Set API host (default: 0.0.0.0)
- `--data-path PATH` - Set data mount path (default: ./app-data)
- `--env-file FILE` - Load environment variables from file
- `--env KEY=VALUE` - Set individual environment variables

#### Examples:
```bash
# Basic startup with ingestion
./start.sh --with-ingest

# Custom port and detached mode
./start.sh --with-ingest --port 9000 --detached

# Use custom PDF list
./start.sh --with-ingest-file my-pdfs.txt

# Load environment from file
./start.sh --env-file .env.prod --with-ingest
```

The script will:
- Prompt for OpenAI API key if not found in environment
- Generate secure API keys for internal services
- Create the data directory and environment configuration
- Start Docker services (Qdrant, API, and optionally Jaeger/Ingestion)

**Note:** Ensure Docker is running before executing the script.

### 5. Retrieve PDF File Links (Optional):
If you don't already have a list of PDF URLs to ingest, you can generate one by running the web scraping script:
```bash
cd scripts/fdds_scrapper
uv run scrapy crawl get_pdf_links
```
This will crawl and extract all PDF file links from the sections specified in the start_urls list, which is defined in: `scripts/fdds_scrapper/fdds_scrapper/spiders/pdf_spider.py`
The collected links will be saved as: `scripts/fdds_scrapper/pdfs.txt`.
> **Note:** To customize which sections are scraped, modify the start_urls list in `pdf_spider.py`.

### 6. Manage PDF Files in Qdrant (Optional):
To load PDF documents into the Qdrant database, prepare a .txt file containing one PDF URL per line (no delimiters or special characters). If you followed the previous step, this file is already generated.
To ingest the documents, run:
```bash
uv run src/fdds/manage_pdfs.py --ingest <path_to_txt_file>
```
To delete the corresponding documents from Qdrant, use:
```bash
uv run src/fdds/manage_pdfs.py --delete <path_to_txt_file>
```
