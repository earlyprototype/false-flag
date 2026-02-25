# FALSE FLAG: SITUATION ROOM (Frontend)

This is the Next.js-based persistent dashboard for the "False Flag" wargame.

## Prerequisites

- Node.js 18+
- Python 3.10+ (for the backend API)

## Setup

1. **Install Dependencies:**
   ```bash
   npm install
   ```

2. **Start the Backend API (Headless Engine):**
   Open a separate terminal in the project root (`/wargame`):
   ```bash
   pip install -r api/requirements.txt
   uvicorn api.server:app --reload --port 8000
   ```

3. **Start the Frontend Dev Server:**
   ```bash
   npm run dev
   ```
   
4. **Access the Dashboard:**
   Open [http://localhost:3000](http://localhost:3000) in your browser.

## Architecture

- **`app/page.tsx`**: The main "Situation Room" dashboard. Currently uses mock data but designed to connect to `localhost:8000`.
- **`api/server.py`**: The FastAPI backend that runs the game engine in headless mode.

## Next Steps

- Connect `page.tsx` to the API endpoints (`/game/new`, `/game/action`).
- Implement real-time streaming for Narrator text.
- Add persistent session storage.

