# Haystack RAG Service Frontend

A React-based frontend for the Haystack RAG service, providing a modern and intuitive interface for document ingestion, management, and querying.

## Features

- Document ingestion with file upload
- Document management and filtering
- Natural language querying with source attribution
- Modern, responsive design
- Dark mode support

## Prerequisites

- Node.js 18+ and npm/yarn
- Backend service running on port 8000

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Build for production:
```bash
npm run build
```

## Testing

Run the test suite:
```bash
npm test
```

Run tests in watch mode:
```bash
npm run test:watch
```

Generate test coverage report:
```bash
npm run test:coverage
```

## Project Structure

```
src/
  ├── components/     # React components
  ├── api/           # API client and types
  ├── styles/        # Global styles and theme
  ├── types/         # TypeScript type definitions
  └── utils/         # Utility functions
```

## API Integration

The frontend communicates with the backend through the following endpoints:

- `POST /api/ingest` - Upload and process documents
- `GET /api/documents` - Retrieve document list
- `POST /api/query` - Submit queries and get responses

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit a pull request

## License

MIT 