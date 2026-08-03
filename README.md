# Personal Log Manager

A standalone desktop application for managing personal logs, tasks, and TODO items with AI-powered analysis capabilities.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)


<img src="https://github.com/fabiomatricardi/personalLOGsystem/raw/main/assets/personalLOG_001.png" width=900>
## Features

- **Log Management**: Create, edit, and delete log entries with type classification (LOG, TODO, TASK)
- **Task Board**: Kanban-style board for tracking task progress (Pending → Assigned → Ongoing → Completed)
- **Database Export/Import**: Backup and restore your database for portability
- **Excel Import**: Import existing data from Excel files
- **LLM Analysis**: AI-powered weekly summaries, overdue detection, next steps suggestions, and pattern analysis
- **Primary/Fallback LLM**: Configurable API with automatic failover between primary and fallback LLM providers
- **Report Export**: Download generated reports as Markdown files

## Screenshots

<img src="https://github.com/fabiomatricardi/personalLOGsystem/raw/main/assets/personalLOG_002.png" width=900>
<img src="https://github.com/fabiomatricardi/personalLOGsystem/raw/main/assets/personalLOG_003.png" width=900>
<img src="https://github.com/fabiomatricardi/personalLOGsystem/raw/main/assets/personalLOG_004.png" width=900>
## Quick Start

### Prerequisites

- **UV** - Python package manager (auto-installed by batch files)
- **Node.js** - JavaScript runtime (auto-installed by batch files)

### First Run

1. Run `run-dev.bat` (or `run-build.bat` to build standalone executable)
2. The app will automatically install all dependencies
3. Browser opens to `http://localhost:5173`
4. **Import sample data:** Go to Settings → Import Excel → select `data/personal_log_sample.xlsx`

### Importing Your Data

The app includes a sample Excel file at `data/personal_log_sample.xlsx`. To import it:

1. Open the app
2. Go to **Settings** tab
3. Click **Import Excel** button
4. Select `data/personal_log_sample.xlsx`
5. Your data will appear in the Dashboard and Log Timeline

### Development Mode

```bash
# Clone the repository
git clone https://github.com/fabio-matricardi/personallog.git
cd personallog

# Windows - Run development mode
run-dev.bat

# The app will be available at:
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
```

### Build Executable

```bash
# Windows - Build standalone executable
run-build.bat

# The executable will be created at:
# dist/PersonalLogManager.exe
```

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + SQLite
- **Frontend**: Vue.js 3 + PrimeVue + Vite
- **Package Manager**: UV (Python) + npm (Node.js)
- **Build**: PyInstaller for standalone executable

## Project Structure

```
personallog/
├── pyproject.toml              # Python project config (requires Python 3.12+)
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



<img src="https://github.com/fabiomatricardi/personalLOGsystem/raw/main/assets/personalLOG_005.png" width=900>

<img src="https://github.com/fabiomatricardi/personalLOGsystem/raw/main/assets/personalLOG_006.png" width=900>

## Configuration

The app uses a `config.json` file for configuration. It's automatically created on first run with default values.

### LLM Configuration

Configure your LLM API in the Settings tab:

```json
{
  "llm": {
    "primary": {
      "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
      "api_key": "your-api-key",
      "model": "gemini-2.0-flash"
    },
    "fallback": {
      "base_url": "https://api.anthropic.com/v1",
      "api_key": "your-api-key",
      "model": "claude-3-sonnet"
    }
  }
}
```

### Supported LLM Providers

- **Google Gemini** (via OpenAI-compatible endpoint)
- **OpenAI** (GPT-4, GPT-3.5)
- **Anthropic** (Claude)
- Any OpenAI-compatible API

## Database Portability

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

## Report Types

- **Weekly Summary**: AI-generated summary for a specific week
- **Comprehensive Report**: Full report with statistics and insights
- **Overdue Tasks**: Analysis of items past their due date
- **Next Steps**: AI-suggested priorities based on recent activity
- **Pattern Analysis**: Work pattern insights and trends

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Fabio Matricardi**
- Email: fabio.matricardi@gmail.com
- GitHub: [fabio-matricardi](https://github.com/fabio-matricardi)

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [Vue.js](https://vuejs.org/) and [PrimeVue](https://primevue.org/)
- Package management by [UV](https://github.com/astral-sh/uv)
