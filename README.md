# LPG AI Service

A modern AI service for document processing and retrieval.

## Installation

```bash
git clone https://github.com/yourusername/lpg-ai-service.git
cd lpg-ai-service
```

## Development

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -e ".[dev]"
```

3. Run the development server:
```bash
uvicorn backend.app.main:app --reload
```

## Testing

Run tests with:
```bash
pytest
```

## Configuration

Environment variables can be set in `.env.development` or `.env.production`:

```bash
LPG_AI_ENVIRONMENT=production
LPG_AI_EMBEDDING_MODEL=sentence-transformers/multi-qa-MiniLM-L6-cos-v1
LPG_AI_GENERATOR_MODEL_NAME=gpt-4
```

## License

MIT 