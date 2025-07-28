# FastAPI 0.114.0 Upgrade Notes

This document explains the changes made to upgrade FastAPI from 0.111.0 to 0.114.0 and fix the compatibility issues that were causing CI failures in Dependabot PR #74.

## Root Cause Analysis

The original Dependabot PR #74 was failing because upgrading FastAPI from 0.111.0 to 0.114.0 brought in a newer version of the `httpx` library that had breaking changes with the older `openai` library (version 1.33.0).

The specific error was:
```
TypeError: AsyncClient.__init__() got an unexpected keyword argument 'proxies'
```

This happened because the older `openai` library was passing a `proxies` parameter to `httpx.AsyncClient`, but newer versions of `httpx` no longer accept this parameter.

## Changes Made

### 1. Dependency Updates (src/requirements.txt)
- **fastapi**: 0.111.0 → 0.114.0 (with [all] extras for full feature support)
- **openai**: 1.33.0 → 1.97.1 (fixes httpx compatibility)
- **uvicorn**: 0.30.1 → 0.35.0
- **gunicorn**: 22.0.0 → 23.0.0
- **azure-identity**: 1.16.1 → 1.23.1
- **environs**: 11.0.0 → 14.2.0
- **aiohttp**: 3.9.5 → 3.12.14

### 2. Configuration Updates (pyproject.toml)
Fixed deprecated Ruff configuration by moving settings to the new structure:
- Moved `select` and `isort` settings under `[tool.ruff.lint]` section

### 3. Development Dependencies (requirements-dev.txt)
- Removed duplicate `fastapi[all]` entry since it's now properly specified in src/requirements.txt

## Installation Command

To install the updated dependencies, use:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

## Verification

After installation, verify the upgrade works by running the CI checks:

```bash
# Lint with ruff
ruff check .

# Check formatting with black
black . --check --verbose

# Run tests with pytest
python -m pytest
```

## Breaking Changes Addressed

1. **OpenAI Library**: Updated to version 1.97.1 which is compatible with the newer httpx versions pulled in by FastAPI 0.114.0
2. **Ruff Configuration**: Updated configuration format to avoid deprecation warnings
3. **Dependency Consistency**: Ensured all dependencies are using compatible versions

## Compatibility Notes

- The OpenAI API usage remains the same (AsyncOpenAI, AsyncAzureOpenAI)
- FastAPI API remains backward compatible
- All existing tests should continue to work without modification
- Configuration file format changes only affect build-time warnings