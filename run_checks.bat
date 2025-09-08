@echo off
echo Running UV sync...
uv sync

echo.
echo Running Ruff check with ALL rules...
uv tool run ruff check --select ALL --exclude .venv

echo.
echo Running Ruff check with auto-fix...
uv tool run ruff check --fix --exclude .venv

echo.
echo Running Pylint on Python files...
for /r %%f in (*.py) do (
    echo %%f | findstr /v "\.venv" >nul && (
        echo Checking %%f
        uv tool run pylint 
        "%%f"
    )
)

echo.
echo All checks completed!
exit /b 0