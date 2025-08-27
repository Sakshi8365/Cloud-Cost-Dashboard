# Proactive Cloud Cost & Performance Monitoring Dashboard

This project is a full-stack monitoring dashboard that ingests, analyzes, and visualizes mock cloud service logs to proactively detect cost anomalies and performance degradation, sending alerts to developers.

## Tech Stack

- Frontend: Next.js (TypeScript) + Recharts
- Backend: FastAPI (Python)
- Data: TimescaleDB (PostgreSQL extension)
- Ingestion: Python script for mock CSV logs
- Orchestration: Docker Compose

## Project Structure

- `frontend/` - Next.js app
- `backend/` - FastAPI app
- `ingestion/` - Data ingestion scripts
- `docker/` - Docker Compose and related files

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js (v18+ recommended) and npm

### 1. Clone the repository
```sh
git clone https://github.com/YOUR_USERNAME/cloud-cost-dashboard.git
cd cloud-cost-dashboard
```

### 2. Start backend and database
```sh
cd docker
docker compose up -d
```
This will start the backend API and TimescaleDB database.

### 3. Start the frontend
Open a new terminal:
```sh
cd ../frontend
npm install
npm run dev
```

### 4. Open the dashboard
Go to [http://localhost:3000](http://localhost:3000) in your browser.

### 5. Features
- Upload CSV files to analyze your own cloud cost data
- Reset to demo/mock data with the circular reset button
- Filter, visualize, and explore cost trends

---

For any issues, see the code comments or open an issue on GitHub.
