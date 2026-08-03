# DESIGN.md — Vue + FastAPI + PyInstaller Standalone App Template

This document is a blueprint for converting any Python CLI tool into a standalone Windows executable with a Vue 3 frontend and FastAPI backend. Feed this to an agent to scaffold or refactor a project following these conventions.

---

## 1. Project Structure

```
project-name/
├── pyproject.toml              # uv project config (Python 3.12+)
├── uv.lock                     # Lockfile
├── .python-version             # Pin Python version
├── .gitignore
├── build.py                    # PyInstaller build script
├── run-dev.bat                 # Windows dev launcher
├── DESIGN.md                   # This file
│
├── backend/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── models.py               # Pydantic models (request/response)
│   ├── routers/
│   │   ├── __init__.py
│   │   └── <feature>.py        # One router per feature endpoint
│   └── services/
│       ├── __init__.py
│       ├── config.py           # JSON config load/save
│       └── <feature>.py        # Business logic (one service per feature)
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── composables/
│       │   └── useApi.js       # All API calls centralized here
│       ├── components/
│       │   ├── Sidebar.vue
│       │   └── <Feature>View.vue
│       └── styles/
│           └── main.css        # Global dark theme styles
│
└── data/                       # Data directory (app-specific)
```

### Rules
- One router file per feature (e.g., `search.py`, `chat.py`).
- One service file per feature containing business logic. Routers are thin wrappers.
- Frontend uses `<script setup>` (Composition API only, no Options API).
- No `vue-router` — use a `ref` in `App.vue` with `v-if` for view switching.
- All API calls go through `useApi.js`. Components never call `axios` directly.
- Single CSS file for global styles. Use CSS variables for theming.

---

## 2. Backend Patterns

### 2.1 FastAPI App (`backend/main.py`)

```python
import sys
import os
import logging

# Determine base directory for the app
if getattr(sys, 'frozen', False):
    APP_BASE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = sys._MEIPASS
else:
    APP_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BUNDLE_DIR = APP_BASE_DIR

# Ensure data directory exists
DATA_DIR = os.path.join(APP_BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Set up logging to file (NOT StreamHandler in frozen mode)
LOG_FILE = os.path.join(APP_BASE_DIR, "app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")]
)
logger = logging.getLogger("app")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Find frontend dist in bundle dir (frozen) or project root (dev)
    frontend_dist = os.path.join(BUNDLE_DIR, "frontend", "dist")
    if not os.path.isdir(frontend_dist):
        frontend_dist = os.path.join(APP_BASE_DIR, "frontend", "dist")
    if os.path.isdir(frontend_dist):
        import webbrowser
        webbrowser.open("http://localhost:8000")
    yield

app = FastAPI(title="AppName", version="1.0.0", lifespan=lifespan)

# ... CORS, routers, etc. ...

# SPA catch-all — find frontend dist correctly
frontend_dist = os.path.join(BUNDLE_DIR, "frontend", "dist")
if not os.path.isdir(frontend_dist):
    frontend_dist = os.path.join(APP_BASE_DIR, "frontend", "dist")

if os.path.isdir(frontend_dist):
    @app("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    # Fix: redirect stdout/stderr for --noconsole exe
    if getattr(sys, 'frozen', False) and sys.stdout is None:
        log_stream = open(LOG_FILE, "a", encoding="utf-8")
        sys.stdout = log_stream
        sys.stderr = log_stream
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

### 2.2 Routers (`backend/routers/<feature>.py`)

```python
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/<feature>", tags=["<feature>"])

class SearchRequest(BaseModel):
    query: str
    limit: int = 20

class SearchResponse(BaseModel):
    results: list[dict]
    total: int

@router.get("/search", response_model=SearchResponse)
async def api_search(q: str = Query(..., description="Search query")):
    from backend.services.<feature> import do_search
    try:
        results = do_search(q)
        return SearchResponse(results=results, total=len(results))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/action")
async def api_action(req: SearchRequest):
    from backend.services.<feature> import do_action
    try:
        result = do_action(req.query, req.limit)
        return {"status": "ok", "result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Rules
- Use `HTTPException` with proper status codes (400, 404, 500). Never return `{"error": "..."}` with 200 OK.
- Use `response_model=` on router decorators for automatic validation.
- Use `Query(...)` for required query params, `Query(default)` for optional.
- Prefix all endpoints with `/api/<feature>`.
- Routers are thin: load config, call service, return result. No business logic in routers.

### 2.3 Services (`backend/services/<feature>.py`)

```python
import threading

_lock = threading.Lock()
_state = {"progress": 0, "status": "idle"}

def do_something():
    global _state
    with _lock:
        _state["status"] = "running"
    # ... work ...
    with _lock:
        _state["progress"] += 1
        _state["status"] = "done"

def get_status():
    with _lock:
        return dict(_state)  # return copy
```

### Rules
- Use `threading.Lock()` around any mutable global state shared between threads.
- Services return raw data (dicts, lists). Pydantic validation happens in routers.
- Background threads must be `daemon=True` so they die with the main process.

### 2.4 Config (`backend/services/config.py`)

```python
import json
import os
import sys
from pathlib import Path

CONFIG_FILE = "config.json"

DEFAULTS = {
    "setting1": "default_value",
    "setting2": 42,
}

def _get_app_base_dir() -> Path:
    """Get the app base directory (next to executable or project root)."""
    if getattr(sys, 'frozen', False):
        return Path(os.path.dirname(sys.executable))
    else:
        return Path(__file__).parent.parent.parent

def get_config_path() -> Path:
    base_dir = _get_app_base_dir()
    return base_dir / CONFIG_FILE

def load_config() -> dict:
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config = _deep_merge(DEFAULTS, saved)
            return config
        except Exception:
            return DEFAULTS.copy()
    return DEFAULTS.copy()

def save_config(config: dict):
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
```

### 2.5 Pydantic Models (`backend/models.py`)

Define models for ALL request and response bodies. Use them in router `response_model=` and as request body types.

```python
from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str
    limit: int = 20

class SearchResult(BaseModel):
    rank: int
    score: float
    filename: str
    snippet: str

class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int

class ErrorResponse(BaseModel):
    detail: str
```

### Rules
- Every request body and response must have a Pydantic model.
- Models are the source of truth for API contracts.
- Remove unused models. Don't define models "just in case."

---

## 3. Frontend Patterns

### 3.1 Vue App Bootstrap (`frontend/src/main.js`)

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import 'primeicons/primeicons.css'
import './styles/main.css'

createApp(App).mount('#app')
```

No router, no store library. Keep it minimal.

### 3.2 Root Component (`frontend/src/App.vue`)

```vue
<script setup>
import { ref } from 'vue'
import Sidebar from './components/Sidebar.vue'
import FeatureView from './components/FeatureView.vue'
import SettingsPanel from './components/SettingsPanel.vue'

const currentView = ref('feature1')
</script>

<template>
  <div class="app-layout">
    <Sidebar :currentView="currentView" @navigate="currentView = $event" />
    <main class="main-content">
      <SettingsPanel v-if="currentView === 'settings'" />
      <FeatureView v-else-if="currentView === 'feature1'" />
    </main>
  </div>
</template>
```

### 3.3 API Client (`frontend/src/composables/useApi.js`)

```javascript
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// REST calls
export async function searchArticles(query) {
  const { data } = await api.get('/search', { params: { q: query } })
  return data
}

// SSE streaming
export async function* streamChat(messages) {
  const response = await fetch('/api/chat/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  })
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6))
        yield data
      }
    }
  }
}

// Shutdown
export async function shutdownApp() {
  await api.post('/shutdown')
}
```

### Rules
- All HTTP calls go in `useApi.js`. Components import from here.
- Use `axios` for REST, raw `fetch()` for SSE streaming.
- No error handling in `useApi.js` — let components catch and display errors.
- SSE helper is an async generator (`function*`).

### 3.4 Components

```vue
<script setup>
import { ref, onMounted } from 'vue'
import { searchArticles } from '../composables/useApi.js'

const props = defineProps({/* ... */})
const emit = defineEmits(['navigate'])

const query = ref('')
const results = ref([])
const loading = ref(false)
const error = ref(null)

async function doSearch() {
  loading.value = true
  error.value = null
  try {
    results.value = await searchArticles(query.value)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="view-container">
    <div class="view-header">
      <h2>Feature Name</h2>
      <button @click="$emit('navigate', 'settings')">Settings</button>
    </div>
    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loading" class="loading">Loading...</div>
    <!-- results here -->
  </div>
</template>
```

### Rules
- All components use `<script setup>` (Composition API).
- Props via `defineProps`, events via `defineEmits`.
- Error state displayed inline, never `alert()`.
- Loading state shown during async operations.

### 3.5 Dark Theme CSS (`frontend/src/styles/main.css`)

```css
:root {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --bg-card: #1e293b;
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --accent: #3b82f6;
  --accent-hover: #2563eb;
  --border: #334155;
  --success: #22c55e;
  --error: #ef4444;
  --warning: #f59e0b;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Inter', -apple-system, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.app-layout {
  display: flex;
  height: 100vh;
}

/* Sidebar */
.sidebar { width: 240px; background: var(--bg-secondary); /* ... */ }

/* Cards */
.result-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 8px;
}

/* Buttons */
.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
}
.btn-primary:hover { background: var(--accent-hover); }

/* Markdown content */
.markdown-content h1 { font-size: 1.5em; margin: 16px 0 8px; }
.markdown-content code {
  background: var(--bg-secondary);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
}
.markdown-content pre {
  background: var(--bg-secondary);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
}

/* Error/Loading states */
.error-banner { background: var(--error); color: white; padding: 12px; border-radius: 6px; }
.loading { color: var(--text-secondary); text-align: center; padding: 24px; }
```

### Rules
- Single CSS file. Use CSS custom properties (variables) for all colors.
- All UI text must be readable in dark theme.
- Use semantic class names: `.view-container`, `.view-header`, `.result-card`.
- Never use inline styles.

---

## 4. Build & Deploy

### 4.1 PyInstaller Build Script (`build.py`)

```python
import os
import sys
import shutil
import subprocess

APP_NAME = "AppName"
MAIN_ENTRY = "backend/main.py"
IS_WINDOWS = sys.platform == "win32"

def find_npm():
    """Find npm executable, checking common Windows locations."""
    npm = shutil.which("npm")
    if npm:
        return npm
    for base in [
        os.path.expandvars(r"%ProgramFiles%\nodejs"),
        os.path.expandvars(r"%ProgramFiles(x86)%\nodejs"),
        os.path.expandvars(r"%APPDATA%\npm"),
    ]:
        candidate = os.path.join(base, "npm.cmd")
        if os.path.isfile(candidate):
            return candidate
    return "npm"

def build():
    for d in ["build", "dist"]:
        if os.path.exists(d):
            shutil.rmtree(d)

    npm = find_npm()
    subprocess.run([npm, "install"], cwd="frontend", check=True, shell=IS_WINDOWS)
    subprocess.run([npm, "run", "build"], cwd="frontend", check=True, shell=IS_WINDOWS)

    backend_packages = []
    for item in os.listdir("backend"):
        if os.path.isdir(os.path.join("backend", item)) and not item.startswith("_"):
            backend_packages.append(f"backend.{item}")

    data_args = []
    if os.path.isdir("frontend/dist"):
        data_args += ["--add-data", "frontend/dist;frontend/dist"]

    hidden_imports = [
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "starlette",
        "starlette.routing",
        "starlette.responses",
        "starlette.middleware",
        "starlette.middleware.cors",
        "pydantic",
        "pydantic.fields",
    ]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", APP_NAME,
        *[arg for pkg in backend_packages for arg in ("--hidden-import", pkg)],
        *[arg for hi in hidden_imports for arg in ("--hidden-import", hi)],
        *data_args,
        MAIN_ENTRY,
    ]

    print(f"Building {APP_NAME}.exe ...")
    subprocess.run(cmd, check=True)
    print(f"Done: dist/{APP_NAME}.exe")

if __name__ == "__main__":
    build()
```

### 4.2 Development Launcher (`run-dev.bat`)

```bat
@echo off
echo Installing dependencies...
call uv sync
call cd frontend && npm install && cd ..
echo Starting dev server...
call uv run python -m backend.main
pause
```

### 4.3 `pyproject.toml`

```toml
[project]
name = "project-name"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "pydantic>=2.11.0",
    "requests>=2.32.0",
]

[tool.uv]
dev-dependencies = [
    "pyinstaller>=6.0",
]
```

### 4.4 `frontend/package.json`

```json
{
  "name": "frontend",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.7.0",
    "primeicons": "^7.0.0",
    "marked": "^15.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.0",
    "vite": "^6.0.0",
    "vue": "^3.5.0"
  }
}
```

### 4.5 `frontend/vite.config.js`

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

### 4.6 `.gitignore`

```
node_modules/
__pycache__/
dist/
build/
*.spec
app_config.json
*.pyc
.opencode/
.venv/
```

---

## 5. Agent Rules

When working on a project following this template, the agent MUST:

### Before Making Changes
1. **Read the existing code first.** Never edit a file without reading it. Understand conventions before modifying.
2. **Check imports.** Before using any library, verify it exists in `pyproject.toml` or `package.json`. Never assume.
3. **Follow existing patterns.** If a project has a certain way of doing things (e.g., error handling, naming), match it.

### After Making Changes
4. **Run lint/typecheck.** After any code change, run the project's lint and typecheck commands. If unknown, ask the user.
5. **Run the build.** After significant changes, run `python build.py` to verify the exe still builds.
6. **Test the endpoint.** After adding/modifying an API endpoint, verify it works with a quick curl or browser check.

### Code Quality
7. **Use proper HTTP status codes.** Return 400/404/500 with `HTTPException`, not 200 with an error key.
8. **Thread safety.** Always use `threading.Lock()` when accessing mutable global state from multiple threads.
9. **No secrets in code.** Never hardcode API keys, passwords, or tokens. Use config files or environment variables.
10. **UTF-8 everywhere.** Use `encoding="utf-8"` for all file I/O. When streaming from external APIs, set `response.encoding = 'utf-8'` before reading.

### File Organization
11. **One concern per file.** One router per feature, one service per feature, one component per view.
12. **No dead code.** If a function/model/router is unused, remove it. Don't leave it "just in case."
13. **Thin routers, fat services.** Routers handle HTTP. Services handle logic. Never put business logic in routers.

### Frontend
14. **No `alert()`.** Display errors inline in the UI. Never use `window.alert()` for error messages.
15. **All API calls in `useApi.js`.** Components never import `axios` directly.
16. **Dark theme first.** All UI must work in dark mode. Use CSS variables from `:root`.

### Build
17. **Always include shutdown endpoint.** Every app must have `POST /api/shutdown` so the user can stop the exe from the UI without killing the process from task manager.
18. **Always include settings endpoint.** Every app must have `GET/POST /api/settings` for persistent configuration.
19. **Test the exe.** After build changes, verify `dist/<AppName>.exe` launches and the frontend loads.

---

## 6. Critical Build Lessons Learned

These are real errors encountered and fixed when building the Personal Log Manager. They apply to ANY PyInstaller + FastAPI + Vue project.

### 6.1 PyInstaller `--noconsole` = stdout is `None`

**Error:**
```
AttributeError: 'NoneType' object has no attribute 'isatty'
ValueError: Unable to configure formatter 'default'
```

**Cause:** `--noconsole` flag sets `sys.stdout = None` and `sys.stderr = None`. Uvicorn's logging formatter calls `sys.stdout.isatty()` which crashes.

**Fix:** Before `uvicorn.run()`, redirect stdout/stderr to a log file:
```python
if getattr(sys, 'frozen', False) and sys.stdout is None:
    log_stream = open(LOG_FILE, "a", encoding="utf-8")
    sys.stdout = log_stream
    sys.stderr = log_stream
```
Also, do NOT add `logging.StreamHandler()` in frozen mode — it writes to `None`.

### 6.2 PyInstaller `--add-data` Paths Are Relative to `_MEIPASS`

**Error:** Frontend not found, no GUI displayed.

**Cause:** `--add-data "frontend/dist;frontend/dist"` bundles files at `frontend/dist` inside the exe. At runtime, they're at `sys._MEIPASS/frontend/dist`, NOT `os.path.dirname(__file__)/frontend/dist`.

**Fix:**
```python
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = sys._MEIPASS        # temp extraction dir (read-only)
    APP_BASE_DIR = os.path.dirname(sys.executable)  # exe location (writable)
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_BASE_DIR = os.path.dirname(BUNDLE_DIR)

# For bundled read-only assets (frontend/dist):
frontend_dist = os.path.join(BUNDLE_DIR, "frontend", "dist")

# For writable data (database, config):
data_dir = os.path.join(APP_BASE_DIR, "data")
```

### 6.3 `__file__` Resolution Differs in Frozen Mode

**Error:** Config and database saved to wrong directory.

**Cause:** In frozen mode, `__file__` points to a temp extraction path that gets deleted. Cannot use it for persistent paths.

**Fix:**
```python
def _get_app_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(os.path.dirname(sys.executable))  # next to .exe
    else:
        return Path(__file__).parent.parent  # project root
```

### 6.4 `subprocess.run("npm")` Fails Through `uv run`

**Error:** `FileNotFoundError: [WinError 2] The system cannot find the file specified`

**Cause:** `uv run python build.py` creates a subprocess that doesn't inherit the system PATH. `npm` can't be found.

**Fix:**
```python
import shutil

def find_npm():
    npm = shutil.which("npm")
    if npm:
        return npm
    for base in [
        os.path.expandvars(r"%ProgramFiles%\nodejs"),
        os.path.expandvars(r"%APPDATA%\npm"),
    ]:
        candidate = os.path.join(base, "npm.cmd")
        if os.path.isfile(candidate):
            return candidate
    return "npm"

# Use shell=True on Windows:
subprocess.run([npm, "install"], cwd="frontend", check=True, shell=True)
```

### 6.5 Vue Template Optional Chaining in `v-model`

**Error:** `The left-hand side of an assignment expression must be a variable or a property access`

**Cause:** Vue 3's template compiler doesn't support `?.` in `v-model` assignments:
```html
<!-- BROKEN — compiles to invalid JS assignment -->
<input v-model="settings.llm?.primary?.base_url" />
```

**Fix:** Ensure the object structure is fully initialized before render:
```javascript
settings.value = {
  ...DEFAULT_SETTINGS,
  ...data,
  llm: {
    ...DEFAULT_SETTINGS.llm,
    ...(data.llm || {}),
    primary: { ...DEFAULT_SETTINGS.llm.primary, ...(data.llm?.primary || {}) }
  }
}
```
Then use plain property access in template:
```html
<input v-model="settings.llm.primary.base_url" />
```

### 6.6 Data Directory Must Be Created Proactively

**Error:** Database creation fails silently.

**Fix:** Create `data/` in both `main.py` lifespan and `database.py`:
```python
DATA_DIR = os.path.join(APP_BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
```

### 6.7 UV `.python-version` Auto-Installs Python

Adding `.python-version` with `3.12` in the repo root makes UV automatically download Python 3.12 on machines without it. Combined with `requires-python = ">=3.12"` in `pyproject.toml`, this ensures consistent Python versions across environments.

### 6.8 Shutdown: Return Response Before `os._exit(0)`

**Error:** Browser tab stays open, or "Failed to fetch" error.

**Cause:** Calling `os._exit(0)` directly in the async handler kills the process before the response reaches the client. The frontend never receives the `{"status": "shutting down"}` response.

**Fix:** Return the response FIRST, then kill the process in a background thread:
```python
import threading
import time

@app.post("/api/shutdown")
async def shutdown():
    threading.Thread(target=lambda: (time.sleep(1) or os._exit(0)), daemon=True).start()
    return {"status": "shutting down"}
```
The 1-second delay ensures the response is fully sent before the process dies. Use `daemon=True` so the thread doesn't prevent shutdown.

### 6.9 PyInstaller Build Checklist

1. `npm install` + `npm run build` in `frontend/`
2. `uv sync` to install Python deps
3. `uv run python build.py` — cleans build/dist, runs PyInstaller
4. Verify `dist/<AppName>.exe` exists
5. Test by copying exe to empty folder — `data/` and `config.json` should be created automatically
6. Check `personallog.log` for startup errors if GUI doesn't appear

---

## 7. Feature Checklist

When creating a new project from this template, ensure these are present:

- [ ] `backend/main.py` with FastAPI app, CORS, lifespan, shutdown endpoint, settings endpoint, SPA catch-all
- [ ] `backend/main.py` handles frozen mode: stdout redirect, `_MEIPASS` vs `sys.executable` paths
- [ ] `backend/models.py` with Pydantic models for all request/response bodies
- [ ] `backend/services/config.py` with `load_config()` / `save_config()` using `_get_app_base_dir()`
- [ ] `backend/database.py` (if using SQLite) with `_get_app_base_dir()` for data path
- [ ] `backend/routers/` — one file per feature endpoint
- [ ] `backend/services/` — one file per feature with business logic
- [ ] `frontend/src/composables/useApi.js` with all API calls
- [ ] `frontend/src/components/Sidebar.vue` with navigation
- [ ] `frontend/src/components/SettingsPanel.vue` with config editor + shutdown button
- [ ] `frontend/src/styles/main.css` with dark theme CSS variables
- [ ] `build.py` with PyInstaller build script + `find_npm()` + `shell=True`
- [ ] `run-dev.bat` for development mode
- [ ] `pyproject.toml` with all dependencies + `requires-python = ">=3.12"`
- [ ] `.python-version` file with `3.12`
- [ ] `frontend/package.json` with all dependencies
- [ ] `.gitignore` with all generated files
- [ ] `data/` directory created automatically at startup
- [ ] Logging to file (not stdout) for frozen mode debugging
