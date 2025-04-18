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
│   │   ├── pdf_loader.py
│   │   ├── evaluation.py
│   │   ├── evaluation_pipeline.py
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
- `src/fdds/pdf_loader.py` logic for ingesting PDF files from the list of urls into Qdrant.
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
### 4. Configure settings:
Ensure you created a `.env` file in the project root directory with all needed variables which are listed below:
```
OPEN_API_KEY=<your_api_key>
NEPTUNE_API_KEY=<your_api_key>
QDRANT_API_KEY=<your_api_key>
API_KEY=<your_api_key>
```
Replace the placeholders with your actual credentials and settings, and modify `src/fdds/config.py` to ensure it holds all necessary configurations like paths and connection details.
### 5. Start the system:
Before proceeding, ensure that Docker is running on your machine. Then, start the services using:
```
docker-compose up -d
```
This command will initialize and run three services in detached mode:
- Qdrant: Vector database
- API: Handles model inference and provides the assistant interface
- Jaeger: Monitoring and tracing system
All service ports are configured in `config.py` and `docker-compose.yml`.
-
### 6. Retrieve PDF File Links:
If you don't already have a list of PDF URLs to ingest, you can generate one by running the web scraping script:
```bash
cd scripts/fdds_scrapper
uv run scrapy crawl get_pdf_links
```
This will crawl and extract all PDF file links from the sections specified in the start_urls list, which is defined in: `scripts/fdds_scrapper/fdds_scrapper/spiders/pdf_spider.py`
The collected links will be saved as: `scripts/fdds_scrapper/pdfs.txt`.
> **Note:** To customize which sections are scraped, modify the start_urls list in `pdf_spider.py`.

### 7. Ingest PDF Files into Qdrant:
To load PDF documents into the Qdrant database, prepare a .txt file containing one PDF URL per line (no delimiters or special characters). If you followed the previous step, this file is already generated.
Run the ingestion script with the path to your link file:
```bash
uv run fdds/src/pdf_loader.py --pdf-list <path_to_txt_file>
```
