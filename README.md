# Personal Log Manager

A standalone desktop application for managing personal logs, tasks, and TODO items with AI-powered analysis capabilities.

## Features

- **Log Management**: Create, edit, and delete log entries with type classification (LOG, TODO, TASK)
- **Task Board**: Kanban-style board for tracking task progress (Pending → Assigned → Ongoing → Completed)
- **Database Export/Import**: Backup and restore your database for portability
- **Excel Import**: Import existing data from Excel files
- **LLM Analysis**: AI-powered weekly summaries, overdue detection, next steps suggestions, and pattern analysis
- **Primary/Fallback LLM**: Configurable API with automatic failover between primary and fallback LLM providers
- **Configurable Port**: Server port can be configured via Settings UI or config.json, with automatic fallback if port is blocked

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + SQLite
- **Frontend**: Vue.js 3 + PrimeVue + Vite
- **Package Manager**: UV (Python) + npm (Node.js)
- **Build**: PyInstaller for standalone executable

## Quick Start

### Prerequisites

- **UV** - Python package manager (auto-installed by batch files)
- **Node.js** - JavaScript runtime (auto-installed by batch files)

### Development Mode

```bash
# Windows
run-dev.bat

# The app will be available at:
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
```

### Build Executable

```bash
# Windows
run-build.bat

# The executable will be created at:
# dist/PersonalLogManager.exe
```

## Project Structure

```
personallog/
├── pyproject.toml              # Python project config
├── uv.lock                     # Lockfile
├── build.py                    # PyInstaller build script
├── config.json                 # App configuration (auto-generated)
│
├── run-dev.bat                 # Development mode launcher
├── run-build.bat               # Build executable
├── run-rebuild-frontend.bat    # Rebuild frontend only
├── check-deps.bat              # Verify dependencies
├── exclude-defender.bat        # Windows Defender exclusion
├── run-prod.bat                # Production mode launcher
│
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── models.py               # Pydantic models
│   ├── database.py             # SQLite schema & connection
│   ├── routers/
│   │   ├── entries.py          # CRUD for log entries
│   │   ├── tags.py             # Tags management
│   │   ├── analysis.py         # LLM analysis endpoints
│   │   ├── import_export.py    # Excel import/export + DB backup/restore
│   │   └── settings.py         # Config management
│   └── services/
│       ├── config.py           # JSON config load/save
│       ├── entries.py          # Entry business logic
│       ├── tags.py             # Tag operations
│       ├── llm_service.py      # LLM API with primary/fallback
│       ├── excel_parser.py     # Excel file handling
│       └── database.py         # DB backup/restore
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── composables/useApi.js
│       ├── components/
│       │   ├── Sidebar.vue
│       │   ├── Dashboard.vue
│       │   ├── LogTimeline.vue
│       │   ├── NewEntry.vue
│       │   ├── TasksBoard.vue
│       │   ├── Analysis.vue
│       │   └── Settings.vue
│       └── styles/main.css
│
└── data/                       # Runtime data (gitignored)
    └── personal_log.db         # SQLite database
```

## Configuration

The app uses a `config.json` file for configuration. It's automatically created on first run with default values.

### Port Configuration

The server port can be configured in two ways:

1. **Settings UI**: Go to Settings → Application → Server Port
2. **config.json**: Edit the `app.port` field

```json
{
  "app": {
    "name": "Personal Log Manager",
    "port": 8000
  }
}
```

If the configured port is unavailable, the app will automatically try alternative ports (8001, 8002, 8003, 5000, 3000, 18080, 28080).

**Note**: Port changes require a restart to take effect.

### LLM Configuration

Configure your LLM API in the Settings tab or edit `config.json`:

```json
{
  "llm": {
    "primary": {
      "base_url": "https://api.openai.com/v1",
      "api_key": "your-api-key",
      "model": "gpt-4"
    },
    "fallback": {
      "base_url": "https://api.anthropic.com/v1",
      "api_key": "your-api-key",
      "model": "claude-3-sonnet"
    }
  }
}
```

### SSL Configuration (Corporate Networks)

If you're behind a corporate firewall with SSL inspection, you may encounter `SSL: CERTIFICATE_VERIFY_FAILED` errors when connecting to LLM APIs.

**Option 1: Disable SSL Verification (Quick Fix)**

1. Go to **Settings** → **LLM Configuration** → **SSL Settings**
2. **Uncheck** "Verify SSL Certificates"
3. Click **Save Settings**

**Option 2: Use Custom CA Bundle (More Secure)**

1. Get the corporate CA certificate file from your IT department
2. Go to **Settings** → **LLM Configuration** → **SSL Settings**
3. Enter the path in "CA Bundle Path" field
4. Keep "Verify SSL Certificates" checked

Or configure in `config.json`:

```json
{
  "llm": {
    "verify_ssl": false,
    "ca_bundle": ""
  }
}
```

## Database Portability

### Edit Entries

Click any entry in the Log Timeline to open the edit modal. You can:

- Modify the activity description
- Change the type (LOG, TODO, TASK)
- Update the status (PENDING, ASSIGNED, ONGOING, COMPLETED)
- Set or change the ETA
- Add follow-up notes
- Delete the entry

**Note**: The entry ID and timestamp are not editable (they are system-assigned).

### Export Database

1. Go to **Settings** tab
2. Click **Backup Database**
3. Save the `.db` file to your desired location

### Import Database

1. Go to **Settings** tab
2. Click **Restore Database**
3. Select your `.db` backup file
4. Confirm the restore operation

### Import from Excel

1. Go to **Settings** tab
2. Click **Import Excel**
3. Select your `.xlsx` file
4. Data will be imported into the database

## Batch Files

| File | Description |
|------|-------------|
| `run-dev.bat` | Start development mode with hot-reload |
| `run-build.bat` | Build standalone executable |
| `run-rebuild-frontend.bat` | Rebuild frontend only |
| `check-deps.bat` | Verify all dependencies are installed |
| `exclude-defender.bat` | Add Windows Defender exclusion (Run as Admin) |
| `run-prod.bat` | Launch built executable |

## Development

### Backend

```bash
# Install dependencies
uv sync

# Run backend server
uv run python -m backend.main
```

### Frontend

```bash
# Install dependencies
cd frontend
npm install

# Run dev server
npm run dev

# Build for production
npm run build
```

## License

MIT
