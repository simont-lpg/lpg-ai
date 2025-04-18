# My RAG App

A RAG (Retrieval-Augmented Generation) microservice using Haystack and Chroma. This project provides a backend service for document retrieval and will be extended with a React frontend in the future.

## Architecture

```
my-rag-app/
├── backend/           # FastAPI + Haystack + Chroma
├── frontend/          # React (stubbed, coming soon)
├── docker-compose.yml # Development environment
├── Makefile          # Common commands
└── .github/          # CI workflows
```

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/my-rag-app.git
   cd my-rag-app
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   python -m pip install -r backend/requirements.txt
   python -m pip install -r backend/requirements-dev.txt
   ```

4. Create a `.env` file in the backend directory (optional):
   ```bash
   CHROMA_PERSIST_DIR=chroma_data
   API_HOST=0.0.0.0
   API_PORT=8000
   DEV_MODE=true
   ```

## Development

### Running Tests

```bash
# Run all tests
make test

# Run unit tests only
make unit

# Run integration tests only
make integration
```

### Code Quality

```bash
# Format code
make format

# Check code style
make lint
```

### Running the Service

```bash
# Start the development server
make run
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### POST /query

Query the RAG pipeline for relevant documents.

Request body:
```json
{
  "query": "your search query"
}
```

Response:
```json
[
  {
    "content": "document content",
    "meta": {
      "source": "document source"
    }
  }
]
```

## CI/CD

The project includes a GitHub Actions workflow that runs on every push and pull request:

1. Checks out the code
2. Sets up Python 3.10
3. Creates and activates virtual environment
4. Installs dependencies using `python -m pip`
5. Runs tests
6. Checks code style

## License

MIT 