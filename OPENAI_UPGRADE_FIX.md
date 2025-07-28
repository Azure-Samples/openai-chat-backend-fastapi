# Fix for OpenAI Dependency Conflict

## Problem
Dependabot PR #73 failed because of a dependency conflict between the OpenAI Python package and httpx. The specific error was:

```
TypeError: AsyncClient.__init__() got an unexpected keyword argument 'proxies'
```

This occurred because:
1. `openai==1.33.0` was written for an older version of httpx that accepted a `proxies` parameter
2. The current dependencies install `httpx==0.28.1` which no longer accepts this parameter
3. This creates an incompatibility when the OpenAI client tries to initialize the AsyncClient

## Solution
Upgraded the OpenAI package from `openai==1.33.0` to `openai>=1.47.0` in `src/requirements.txt`.

This version:
- Is compatible with newer versions of httpx (0.28.x)
- Maintains API compatibility with the existing codebase
- Resolves the AsyncClient initialization issue

## Changes Made
- Updated `src/requirements.txt`: Changed `openai==1.33.0` to `openai>=1.47.0`
- Used `>=` version constraint to allow automatic minor/patch updates within the 1.47+ range

## Verification Steps
To verify this fix works:

1. Create a new virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```

2. Install the updated dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Verify the OpenAI client can be imported and initialized:
   ```python
   import openai
   client = openai.AsyncOpenAI(api_key="test", base_url="http://localhost:8080")
   ```

4. Run the test suite:
   ```bash
   python -m pytest
   ```

## Expected Outcome
- Dependencies install without conflicts
- OpenAI client initializes successfully 
- All existing functionality continues to work
- Tests pass (may need credentials for full Azure OpenAI integration tests)

## Background
This upgrade addresses the same goal as the failed Dependabot PR #73 while resolving the dependency conflict that caused the CI failure. The OpenAI Python SDK has been actively maintained and newer versions (1.47+) properly support the current httpx API.