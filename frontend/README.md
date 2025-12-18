# Phoenix Protocol - Frontend Dashboard

React + TypeScript dashboard for visualizing the Phoenix Protocol agent system.

## Features

- **Graph Viewer**: Interactive Neo4j graph visualization using react-force-graph-2d
- **Agent Brain**: Real-time agent execution state and step tracking
- **Checkpoint Timeline**: Visual timeline of agent checkpoints with restore capability
- **Demo Controls**: Quick actions for demo scenarios (crash, restore, task submission)

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **react-force-graph-2d** for graph visualization
- **Axios** for API communication

## Development

### Prerequisites

- Node.js 20+
- npm or yarn

### Setup

```bash
cd frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

### Environment Variables

Create a `.env` file (optional):

```env
VITE_API_URL=http://localhost:8787
```

If not set, defaults to `http://localhost:8787`

## Docker

The frontend can be run via Docker:

```bash
docker-compose up frontend
```

Or build and run manually:

```bash
docker build -t phoenix-frontend ./frontend
docker run -p 5173:5173 phoenix-frontend
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # React components
│   │   ├── GraphViewer.tsx
│   │   ├── AgentBrain.tsx
│   │   ├── CheckpointTimeline.tsx
│   │   └── DemoControls.tsx
│   ├── services/        # API service layer
│   │   └── api.ts
│   ├── App.tsx          # Main app component
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles
├── public/              # Static assets
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── Dockerfile
```

## API Integration

The frontend communicates with the Phoenix Router API:

- **Graph API**: `/api/graph/*` - Graph visualization and context
- **Agent API**: `/api/agent/*` - Agent task management
- **MemVerge API**: `/api/memverge/*` - Checkpoint and restore operations

See `src/services/api.ts` for all API endpoints and types.

