# Haystack RAG Service

A RAG (Retrieval-Augmented Generation) service built with Haystack AI for efficient document processing and question answering.

## Requirements

- Python 3.11 or higher
- pip (Python package installer)

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/haystack-rag-service.git
   cd haystack-rag-service
   ```

2. Run the setup script:
   ```bash
   ./setup.sh
   ```

   This will:
   - Create a virtual environment
   - Install all dependencies
   - Run initial tests

## Development

The project includes several make commands to help with development:

- `make install`: Install all dependencies
- `make test`: Run all tests with coverage report
- `make lint`: Run all linters (flake8, mypy, black, isort)
- `make format`: Format code using black and isort
- `make run`: Start the development server
- `make clean`: Clean up temporary files and caches

## Project Structure

```
haystack-rag-service/
├── app/              # Main application code
├── tests/            # Test files
├── pyproject.toml    # Project configuration and dependencies
├── setup.sh          # Setup script
└── Makefile         # Development commands
```

## License

[Your chosen license]

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request 