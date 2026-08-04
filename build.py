"""
PyInstaller build script for Personal Log Manager.
"""
import os
import sys
import shutil
import subprocess

APP_NAME = "PersonalLogManager"
MAIN_ENTRY = "backend/main.py"

IS_WINDOWS = sys.platform == "win32"


def find_npm():
    """Find npm executable, checking common Windows locations."""
    npm = shutil.which("npm")
    if npm:
        return npm
    # Check common Windows install paths
    for base in [
        os.path.expandvars(r"%ProgramFiles%\nodejs"),
        os.path.expandvars(r"%ProgramFiles(x86)%\nodejs"),
        os.path.expandvars(r"%APPDATA%\npm"),
    ]:
        candidate = os.path.join(base, "npm.cmd")
        if os.path.isfile(candidate):
            return candidate
        candidate = os.path.join(base, "npm.exe")
        if os.path.isfile(candidate):
            return candidate
    return "npm"


def build():
    for d in ["build", "dist"]:
        if os.path.exists(d):
            shutil.rmtree(d)

    npm = find_npm()
    print(f"Using npm: {npm}")

    subprocess.run([npm, "install"], cwd="frontend", check=True, shell=IS_WINDOWS)
    subprocess.run([npm, "run", "build"], cwd="frontend", check=True, shell=IS_WINDOWS)

    backend_packages = []
    for item in os.listdir("backend"):
        if os.path.isdir(os.path.join("backend", item)) and not item.startswith("_"):
            backend_packages.append(f"backend.{item}")

    data_args = []
    if os.path.isdir("frontend/dist"):
        data_args += ["--add-data", "frontend/dist;frontend/dist"]
    if os.path.isfile("config.json"):
        data_args += ["--add-data", "config.json;."]

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
        "aiosqlite",
        "openpyxl",
        "httpx",
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

    if os.path.isfile("config.json"):
        dist_config = os.path.join("dist", "config.json")
        shutil.copy2("config.json", dist_config)
        print(f"Copied config.json to dist/")


if __name__ == "__main__":
    build()
