# Agricultural Knowledge Retrieval Agent

Member 3's independent evidence-retrieval service for AgriKetha-AI.

The service retrieves evidence from local agricultural PDFs and text files. It does not generate recommendations.

## Layout

- `app/` - application package
- `knowledge-base/documents/tomato/` - tomato PDF documents
- `knowledge-base/documents/rice/` - rice PDF documents
- `knowledge-base/documents/chilli/` - chilli PDF documents
- `knowledge-base/processed/` - generated chunk metadata
- `vector-store/` - generated FAISS index files
- `tests/` - agent tests

Place source PDFs or text files in the crop folders before ingestion. PDF page numbers are preserved in every result; text files are treated as page 1. No source metadata is invented.

## Local environment

From this directory in PowerShell:

```powershell
py -m venv venv
.\\venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Install dependencies, then ingest documents:

```powershell
python -m app.ingest
```

Start the service on port `8004`:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8004
```

The API provides `GET /agent/health` and `POST /agent/retrieve`. Set `RESEARCH_RELEVANCE_THRESHOLD` to adjust the minimum cosine similarity accepted as evidence.
