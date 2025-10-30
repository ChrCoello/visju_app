# Frontend Refactoring: React Migration (Revised)

This document provides a refined approach to migrating from vanilla JS to React.

## Decision Point: Do We Need React?

Before proceeding, consider:
- ✅ Proceed if: Planning significant feature growth, want modern tooling, team prefers React
- ⚠️ Reconsider if: App will stay simple, prefer minimal dependencies, prioritize bundle size

**If proceeding with React:**

## 1. Project Setup

- [ ] **Initialize React Project:**
  ```bash
  npm create vite@latest frontend-react -- --template react-ts
  cd frontend-react
  npm install
  ```

- [ ] **Install Core Dependencies:**
  ```bash
  npm install react-router-dom
  npm install axios
  npm install -D @types/node
  ```

- [ ] **Install Styling Solution (Choose One):**
  - **Recommended:** `npm install -D tailwindcss postcss autoprefixer`
  - **Alternative:** CSS Modules (built into Vite)

- [ ] **Optional but Useful:**
  ```bash
  npm install react-i18next i18next  # For Norwegian/English support
  npm install date-fns               # For Norwegian date formatting
  ```

- [ ] **Project Structure:**
  ```
  frontend-react/
  ├── src/
  │   ├── components/        # Reusable components
  │   │   ├── layout/
  │   │   │   ├── Layout.tsx
  │   │   │   ├── Header.tsx
  │   │   │   └── Navigation.tsx
  │   │   ├── sessions/
  │   │   │   ├── SessionList.tsx
  │   │   │   ├── SessionListItem.tsx
  │   │   │   └── SessionStatus.tsx
  │   │   ├── transcription/
  │   │   │   ├── TranscriptionViewer.tsx
  │   │   │   ├── DialogueTurn.tsx
  │   │   │   ├── SpeakerInfo.tsx
  │   │   │   └── TranscriptionProgress.tsx
  │   │   ├── audio/
  │   │   │   └── AudioPlayer.tsx
  │   │   └── common/
  │   │       ├── LoadingSpinner.tsx
  │   │       ├── ErrorMessage.tsx
  │   │       └── SearchBox.tsx
  │   ├── pages/
  │   │   ├── HomePage.tsx
  │   │   ├── SessionsPage.tsx
  │   │   └── SessionDetailPage.tsx
  │   ├── services/
  │   │   ├── api.ts            # Axios instance and config
  │   │   ├── sessions.ts       # Session-related API calls
  │   │   └── transcription.ts  # Transcription API calls
  │   ├── hooks/
  │   │   ├── useSessions.ts
  │   │   ├── useSessionDetail.ts
  │   │   └── useDebounce.ts
  │   ├── types/
  │   │   └── index.ts          # TypeScript interfaces
  │   ├── utils/
  │   │   ├── formatters.ts     # Date/time formatting
  │   │   └── validation.ts
  │   ├── App.tsx
  │   └── main.tsx
  ├── public/
  └── package.json
  ```

## 2. TypeScript Interfaces (Critical First Step)

- [ ] **Define Core Types:**
  ```typescript
  // src/types/index.ts
  export interface Session {
    id: string;
    filename: string;
    created_at: string;
    processing_status: 'detected' | 'transcribed' | 'error';
    transcript_preview?: string;
    transcript?: Transcript;
  }

  export interface Transcript {
    full_text?: string;
    language?: string;
    model_version?: string;
    processing_duration_ms?: number;
    has_speakers?: boolean;
    speakers_detected?: number;
    segments?: TranscriptSegment[];
    speaker_info?: SpeakerInfo[];
  }

  export interface TranscriptSegment {
    text: string;
    start_time: number;
    end_time: number;
    speaker_id?: string;
  }

  export interface SpeakerInfo {
    speaker_id: string;
    label?: string;
    channel?: string;
    silence_percent: number;
    energy_percent: number;
  }

  export interface DialogueTurn {
    speaker1: string | null;
    speaker2: string | null;
  }
  ```

## 3. API Service Layer

- [ ] **Create Base API Client:**
  ```typescript
  // src/services/api.ts
  import axios from 'axios';

  export const api = axios.create({
    baseURL: '/api/v1',
    headers: { 'Content-Type': 'application/json' },
  });

  api.interceptors.response.use(
    (response) => response,
    (error) => {
      console.error('API Error:', error);
      return Promise.reject(error);
    }
  );
  ```

- [ ] **Create Domain-Specific Services:**
  ```typescript
  // src/services/sessions.ts
  import { api } from './api';
  import type { Session } from '../types';

  export const sessionsService = {
    getAll: async (): Promise<Session[]> => {
      const { data } = await api.get<Session[]>('/sessions/');
      return data;
    },

    getById: async (id: string): Promise<Session> => {
      const { data } = await api.get<Session>(`/sessions/${id}`);
      return data;
    },

    search: async (term: string): Promise<Session[]> => {
      const { data } = await api.get<Session[]>(`/sessions/search/${encodeURIComponent(term)}`);
      return data;
    },
  };

  // src/services/transcription.ts
  export const transcriptionService = {
    basic: async (filename: string) => {
      const { data } = await api.post(`/transcription/transcribe/${filename}`);
      return data;
    },

    speakerAware: async (filename: string) => {
      const { data } = await api.post(`/speaker-aware-transcription/transcribe/${filename}`);
      return data;
    },
  };
  ```

## 4. Custom Hooks (State Management)

- [ ] **Create Data Fetching Hooks:**
  ```typescript
  // src/hooks/useSessions.ts
  import { useState, useEffect } from 'react';
  import { sessionsService } from '../services/sessions';
  import type { Session } from '../types';

  export function useSessions(searchTerm = '') {
    const [sessions, setSessions] = useState<Session[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
      const fetchSessions = async () => {
        setLoading(true);
        setError(null);
        try {
          const data = searchTerm
            ? await sessionsService.search(searchTerm)
            : await sessionsService.getAll();
          setSessions(data);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to load sessions');
        } finally {
          setLoading(false);
        }
      };

      fetchSessions();
    }, [searchTerm]);

    return { sessions, loading, error };
  }

  // src/hooks/useDebounce.ts
  import { useState, useEffect } from 'react';

  export function useDebounce<T>(value: T, delay = 300): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);

    useEffect(() => {
      const handler = setTimeout(() => setDebouncedValue(value), delay);
      return () => clearTimeout(handler);
    }, [value, delay]);

    return debouncedValue;
  }
  ```

## 5. Component Development (Priority Order)

### Phase 1: Layout & Core Components
- [ ] `Layout.tsx` - Main layout wrapper
- [ ] `Header.tsx` - App header with navigation
- [ ] `LoadingSpinner.tsx` - Reusable loading indicator
- [ ] `ErrorMessage.tsx` - Error display component

### Phase 2: Sessions List
- [ ] `SessionsPage.tsx` - Sessions list page
- [ ] `SearchBox.tsx` - Search input with debounce
- [ ] `SessionList.tsx` - List container
- [ ] `SessionListItem.tsx` - Individual session card
- [ ] `SessionStatus.tsx` - Status badge component

### Phase 3: Session Detail
- [ ] `SessionDetailPage.tsx` - Session detail page
- [ ] `TranscriptionViewer.tsx` - Main transcript display
- [ ] `SpeakerInfo.tsx` - Speaker information cards
- [ ] `DialogueTurn.tsx` - Two-column dialogue display
- [ ] `TranscriptionProgress.tsx` - Progress indicator for transcription

### Phase 4: Additional Features
- [ ] `AudioPlayer.tsx` - Audio playback controls
- [ ] `HomePage.tsx` - Landing page

## 6. Routing

- [ ] **Configure Router:**
  ```typescript
  // src/App.tsx
  import { BrowserRouter, Routes, Route } from 'react-router-dom';
  import { Layout } from './components/layout/Layout';
  import { HomePage } from './pages/HomePage';
  import { SessionsPage } from './pages/SessionsPage';
  import { SessionDetailPage } from './pages/SessionDetailPage';

  function App() {
    return (
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/sessions" element={<SessionsPage />} />
            <Route path="/sessions/:id" element={<SessionDetailPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    );
  }

  export default App;
  ```

## 7. Styling with Tailwind CSS (Recommended)

- [ ] **Configure Tailwind:**
  ```bash
  npx tailwindcss init -p
  ```

- [ ] **Update tailwind.config.js:**
  ```javascript
  export default {
    content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
    theme: {
      extend: {
        colors: {
          primary: '#2c3e50',
          secondary: '#3498db',
          success: '#27ae60',
          speaker1: '#e3f2fd',
          speaker2: '#e8f5e9',
        },
      },
    },
    plugins: [],
  };
  ```

- [ ] **Add to src/index.css:**
  ```css
  @tailwind base;
  @tailwind components;
  @tailwind utilities;

  /* Custom component classes */
  @layer components {
    .dialogue-left {
      @apply p-6 bg-speaker1 rounded-xl border-l-4 border-secondary;
    }

    .dialogue-right {
      @apply p-6 bg-speaker2 rounded-xl border-l-4 border-success;
    }
  }
  ```

## 8. Norwegian Language Support

- [ ] **Setup i18next (Optional but Recommended):**
  ```bash
  npm install react-i18next i18next
  ```

- [ ] **Configure date-fns for Norwegian locale:**
  ```typescript
  // src/utils/formatters.ts
  import { format } from 'date-fns';
  import { nb } from 'date-fns/locale';

  export function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return format(date, 'PPpp', { locale: nb }); // Norwegian format
  }

  export function formatTime(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }
  ```

## 9. Testing Strategy

- [ ] **Setup Testing Tools:**
  ```bash
  npm install -D vitest @testing-library/react @testing-library/jest-dom
  npm install -D @testing-library/user-event
  npm install -D @playwright/test  # For E2E
  ```

- [ ] **Write Tests:**
  - [ ] Component tests for SessionList, TranscriptionViewer
  - [ ] Hook tests for useSessions, useDebounce
  - [ ] E2E tests for critical user flows

## 10. Build and Backend Integration

- [ ] **Update vite.config.ts for Development Proxy:**
  ```typescript
  import { defineConfig } from 'vite';
  import react from '@vitejs/plugin-react';

  export default defineConfig({
    plugins: [react()],
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  });
  ```

- [ ] **Build for Production:**
  ```bash
  npm run build  # Creates dist/ folder
  ```

- [ ] **Update FastAPI to Serve React App:**
  ```python
  # backend/main.py
  from fastapi.staticfiles import StaticFiles
  from fastapi.responses import FileResponse
  import os

  # Mount static assets
  app.mount("/assets", StaticFiles(directory="frontend-react/dist/assets"), name="assets")

  # Serve index.html for all non-API routes (SPA fallback)
  @app.get("/{full_path:path}")
  async def serve_react_app(full_path: str):
      file_path = f"frontend-react/dist/{full_path}"
      if os.path.exists(file_path) and os.path.isfile(file_path):
          return FileResponse(file_path)
      return FileResponse("frontend-react/dist/index.html")
  ```

## 11. Migration Strategy (Incremental)

Rather than a big-bang rewrite, migrate incrementally:

- [ ] **Phase 1:** Setup React app, create Layout + HomePage (coexist with old frontend)
- [ ] **Phase 2:** Migrate SessionsPage only
- [ ] **Phase 3:** Migrate SessionDetailPage
- [ ] **Phase 4:** Remove old `frontend/` directory
- [ ] **Phase 5:** Add new features (e.g., real-time updates, advanced search)

**Coexistence Strategy:**
```python
# Serve React for specific routes, old frontend for others
@app.get("/")
async def home():
    return FileResponse("frontend-react/dist/index.html")

@app.get("/sessions-old")
async def old_sessions():
    return templates.TemplateResponse("sessions.html", {"request": request})
```

## 12. Documentation Updates

- [ ] **Update README.md:**
  - Development setup instructions
  - Build and deployment process
  - Environment variables for frontend

- [ ] **Create FRONTEND_ARCHITECTURE.md:**
  - Component hierarchy
  - State management approach
  - API integration patterns

## 13. Cleanup

- [ ] **After Full Migration:**
  - [ ] Remove `frontend/templates/` directory
  - [ ] Remove `frontend/static/` directory
  - [ ] Remove Jinja2 template rendering from FastAPI
  - [ ] Update CORS settings if deploying frontend separately

---

## Alternative: Lighter Alternatives to Consider

If React seems too heavy, consider:

1. **Alpine.js + htmx** - Stay server-side with sprinkles of interactivity
2. **Preact** - React-compatible but 3KB instead of 40KB
3. **SolidJS** - Better performance, similar API to React
4. **Vanilla JS refactor** - Reorganize current code into ES6 modules

---

## Decision Checklist

Before starting, answer these:

- [ ] Why are we migrating? (Feature growth, team preference, modern tooling?)
- [ ] Do we need TypeScript? (Recommended: Yes)
- [ ] Which styling approach? (Recommended: Tailwind CSS)
- [ ] Do we need a UI library? (Recommended: No, start without)
- [ ] State management? (Recommended: Start with hooks, add Zustand only if needed)
- [ ] Migration strategy? (Recommended: Incremental)
- [ ] Testing priority? (Recommended: Component tests + E2E for critical flows)
