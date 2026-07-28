#!/bin/bash
python -m uvicorn api.main_unified_chromadb:app --host 0.0.0.0 --port 8000