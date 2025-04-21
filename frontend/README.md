# RAG Frontend

A React-based frontend for a RAG (Retrieval-Augmented Generation) application.

## Features

- File management (upload, delete, select)
- Chat interface for RAG queries
- Source document display
- Responsive two-column layout

## Prerequisites

- Node.js (v16 or higher)
- npm (v7 or higher)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

## Development

To start the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

## Testing

To run the test suite:

```bash
npm test
```

## Project Structure

- `src/components/` - React components
  - `FileManager.tsx` - File management interface
  - `Chat.tsx` - Chat interface for RAG queries
- `src/api.ts` - API client for backend communication
- `src/components/__tests__/` - Component tests

## API Endpoints

The frontend expects the following backend API endpoints:

- `GET /files` - List uploaded files
- `POST /upload` - Upload new files
- `DELETE /documents` - Delete a document
- `POST /query` - Query the RAG system

## Technologies Used

- React
- TypeScript
- Chakra UI
- Jest
- React Testing Library
