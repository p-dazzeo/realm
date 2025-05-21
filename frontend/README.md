# REALM Frontend

A React-based frontend for the REALM (Reverse Engineering Assistant) project. This application provides a user interface for interacting with the REALM backend services: GenDoc (documentation generation) and RAG (retrieval-augmented generation).

## Features

- Upload code projects (ZIP files) for analysis
- Generate documentation for projects (overview, architecture, etc.)
- Ask questions about your codebase with AI assistance
- View history of generated documentation and queries
- Simple, responsive UI

## Technologies

- React 18
- React Router for navigation
- Axios for API requests
- Vite for build tooling

## Getting Started

### Prerequisites

- Node.js (LTS version recommended)
- npm, yarn or pnpm

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   npm install
   ```

### Development Server

Start the development server:

```
npm run dev
```

By default, the server runs on http://localhost:3000 and proxies API requests to the backend services.

### Configuration

The application proxies requests to the backend services:

- `/gendoc` → `http://localhost:8000` (GenDoc service)
- `/rag` → `http://localhost:8001` (RAG service)

You can customize these endpoints by setting environment variables:

- `GENDOC_URL`: URL for the GenDoc service
- `RAG_URL`: URL for the RAG service

### Build for Production

Create a production build:

```
npm run build
```

The build artifacts will be available in the `dist` directory.

### Preview Production Build

To preview the production build locally:

```
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── assets/          # Static assets
│   ├── components/      # Reusable UI components
│   ├── context/         # React context providers
│   ├── pages/           # Page-level components
│   ├── services/        # API service clients
│   ├── styles/          # CSS files
│   ├── utils/           # Utility functions
│   ├── App.jsx          # Main app component
│   └── main.jsx         # Application entry point
├── index.html           # HTML entry point
├── vite.config.js       # Vite configuration
└── package.json         # Project dependencies and scripts
```

## Backend Services

The frontend interacts with two backend services:

1. **GenDoc Service**: Generates documentation for code projects
2. **RAG Service**: Answers questions about code using retrieval-augmented generation

Both services should be running for full functionality. 