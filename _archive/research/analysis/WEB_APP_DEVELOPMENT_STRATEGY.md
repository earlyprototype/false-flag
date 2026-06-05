# Web App Development Strategy: False Flag

## Phase 1: Architecture & Core Loop (COMPLETED)
- [x] **Headless Engine**: `GameManager` created to decouple logic from CLI.
- [x] **API Backend**: FastAPI server implemented with endpoints for Game State, Discussion, and Decision.
- [x] **Real-time Streaming**: Server-Sent Events (SSE) implemented for live game event updates.
- [x] **Frontend Scaffold**: Next.js application created and wired to API.
- [x] **Basic Interaction**: Users can start games, receive briefings (via stream), and submit decisions.

## Phase 2: UI Polish & "Situation Room" Aesthetic (IN PROGRESS)
**Goal**: Transform the bare-bones HTML into a high-tension, "Defcon"-style interface.

### 2.1 UI Library Integration (STARTED)
- [x] **Library**: `shadcn/ui` initialized.
- [x] **Components**: Core components installed (Button, Card, Input, ScrollArea, Badge, Skeleton, Alert).
- [ ] **Theme**: Implement "Situation Room" dark theme (black/slate/cyan/red).

### 2.2 Persistent Dashboard Layout
- [ ] **Grid Layout**: Fixed-viewport layout with distinct zones:
    - **Left Panel**: Metrics & Advisor Status (Always visible).
    - **Center Panel**: Main Feed (Transcript/Briefing) & Action Area.
    - **Right Panel**: Resources & Global Map (Future).
- [ ] **Visual Feedback**: Animated status bars for metrics.

### 2.3 Interactive Elements
- [ ] **Briefing Stream**: Display incoming intelligence character-by-character or line-by-line.
- [ ] **Advisor Cards**: Visual representation of advisors with status indicators.
- [ ] **Decision Interface**: clearly delineated choices with risk/reward tooltips.

## Phase 3: Advanced Features
- [ ] **Multi-Session Support**: Persistent storage for games.
- [ ] **Authentication**: Simple user identity.
- [ ] **Global Map Visualization**: Visual representation of unit locations.
