# fdds-rag

# How to run the app:

## 1. Set up the environment:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
## 2.  Start Qdrant with Docker:
```bash
docker-compose up -d
```
## 3. Load PDFs and build the vector store:
```bash
python src/pdf_loader.py
python src/vector_store.py
```
## 4. Run the RAG pipeline and query interface:
```bash
python src/rag_pipeline.py
python src/query_interface.py
```
