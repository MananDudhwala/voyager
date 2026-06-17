# 🌍 Voyager

> **Voyager is a Multi-Agent AI Trip Planner** that uses the Model Context Protocol (MCP) to coordinate specialized AI agents to plan end-to-end trips, including flights, hotels, and daily itineraries.

![Voyager Overview](./frontend/public/icon.png) <!-- Update with actual screenshots if needed -->

## ✨ Features

- **Multi-Agent Orchestration**: A central Orchestrator Agent delegates tasks to specialized sub-agents (Flights, Hotels, Itinerary) using Anthropic's **Model Context Protocol (MCP)**.
- **Real-time Streaming**: Built on FastAPI and Server-Sent Events (SSE), the Next.js frontend dynamically updates in real-time as the agents research and construct your itinerary.
- **Real-World API Integrations**: Agents use SerpAPI to fetch live data from Google Flights, Google Hotels, and Google Local (for Points of Interest and Restaurants).
- **Smart Budget Allocation**: The orchestrator strictly enforces user budgets (e.g., 40% flights, 40% hotels, 20% activities) and automatically replans or shifts budget allocations if a sub-agent fails to find a valid option.
- **Modern, Stunning UI**: A rich, dynamic React 19 interface with glassmorphism, micro-animations, and responsive design.
- **Enterprise-ready CI/CD**: Automated GitHub Actions pipeline that lints, builds multi-stage Docker images, and deploys to Kubernetes via Helm.

## 🛠 Tech Stack

### Frontend
- **Framework**: Next.js 15 (App Router) + React 19
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4 (with custom Base UI and Shadcn components)
- **State Management**: Zustand
- **Forms & Validation**: React Hook Form + Zod
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **LLM Engine**: Anthropic Claude (`claude-opus-4-5`)
- **Agent Communication**: Model Context Protocol (MCP) via stdio
- **Package Manager**: `uv` (Lightning-fast Python dependency management)
- **APIs**: SerpAPI

### DevOps & Deployment
- **Containerization**: Docker (Multi-stage builds)
- **Orchestration**: Kubernetes + Helm Charts
- **CI/CD**: GitHub Actions
- **Linting**: ESLint (Frontend) + Ruff (Backend)

## 🚀 Getting Started

### Prerequisites
- Node.js >= 20.9.0
- Python >= 3.11
- [uv](https://github.com/astral-sh/uv) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Docker (optional, for containerized running)

### Environment Variables
Create a `.env` file in the `backend/` directory:
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key
SERPAPI_KEY=your_serpapi_key
```

### 1. Start the Backend
The backend uses `uv` for fast package management and `uvicorn` for the server.

```bash
cd backend
uv sync
uv run uvicorn api.main:app --port 8000 --reload
```

### 2. Start the Frontend
In a new terminal window:

```bash
cd frontend
npm install
npm run dev
```

The app will be running at `http://localhost:3000`.

## 📦 Deployment

Voyager is fully containerized and ready for Kubernetes deployment.

### Docker
To build the images locally:
```bash
# Frontend
docker build -t voyager-frontend ./frontend

# Backend
docker build -t voyager-backend ./backend
```

### CI/CD Pipeline
The included GitHub Actions pipeline (`.github/workflows/deploy.yml`) automatically lints, builds, and deploys the application.
Ensure you set the following secrets in your GitHub repository:
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `KUBECONFIG`
- `ANTHROPIC_API_KEY`
- `SERPAPI_KEY`

### Kubernetes via Helm
The provided Helm chart deploys both the frontend and backend with integrated Secrets and Services:
```bash
helm upgrade --install voyager-app ./helm/voyager \
  --set secrets.anthropicApiKey=$ANTHROPIC_API_KEY \
  --set secrets.serpapiKey=$SERPAPI_KEY
```

## 🧠 Architecture
- **Orchestrator Agent**: Receives the user request, parses the budget, and sequentially streams prompts to the sub-agents over MCP stdio channels.
- **Flight Agent**: Queries live flight prices and returns the optimal outbound and return flights.
- **Hotel Agent**: Finds accommodations near the destination that fit the remaining budget tier.
- **Itinerary Agent**: Generates a day-by-day travel plan including transit times, restaurants, and landmarks based on the hotel location and flight times.
