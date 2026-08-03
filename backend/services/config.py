"""
Configuration management service.
"""
import json
import os
from pathlib import Path

CONFIG_FILE = "config.json"

DEFAULTS = {
    "app": {
        "name": "Personal Log Manager",
        "version": "1.0.0",
        "data_dir": "./data",
        "db_path": "./data/personal_log.db",
        "log_level": "INFO"
    },
    "llm": {
        "primary": {
            "enabled": True,
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "model": "gpt-4",
            "timeout": 60,
            "max_tokens": 4096
        },
        "fallback": {
            "enabled": True,
            "base_url": "https://api.anthropic.com/v1",
            "api_key": "",
            "model": "claude-3-sonnet",
            "timeout": 60,
            "max_tokens": 4096
        },
        "analysis": {
            "weekly_report_day": "friday",
            "auto_analyze": False,
            "include_completed_tasks": True,
            "summary_style": "concise"
        }
    },
    "ui": {
        "theme": "dark",
        "sidebar_collapsed": False,
        "date_format": "YYYY-MM-DD HH:mm",
        "items_per_page": 25
    },
    "import": {
        "excel_path": "",
        "last_import_date": None,
        "auto_import_on_start": False
    }
}


def get_config_path() -> Path:
    base_dir = Path(__file__).parent.parent.parent
    return base_dir / CONFIG_FILE


def load_config() -> dict:
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        config = _deep_merge(DEFAULTS, saved)
        return config
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
