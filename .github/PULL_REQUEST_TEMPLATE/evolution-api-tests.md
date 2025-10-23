Title: test(evolution_api): add comprehensive tests for Evolution API tool (#13)

Summary
-------
This PR adds comprehensive unit tests for the Evolution API MCP tool (automagik_tools/tools/evolution_api). The tests cover all public tool functions, configuration handling, metadata helpers, and error paths. The Evolution API HTTP client is mocked to avoid external calls.

Files changed
-------------
- tests/tools/test_evolution_api.py — new comprehensive tests (fixtures, AsyncMock)
- .github/workflows/ci.yml — CI workflow to run the tests on push/PR
- requirements-dev.txt — dev/test dependencies
- scripts/run_tests_windows.ps1 — Windows helper to create venv and run tests
- TESTING.md — instructions to run tests locally and via CI

What I changed (acceptance checklist)
- [x] Test all public MCP tools: send_text_message, send_media, send_audio, send_reaction, send_location, send_contact, send_presence
- [x] At least one test per tool function
- [x] Configuration tests (EvolutionAPIConfig defaults and env variables)
- [x] Metadata tests (get_metadata, get_config_class) and MCP registration check
- [x] Error handling tests (missing config, client exceptions)
- [x] Mocked EvolutionAPIClient using AsyncMock
- [x] Tests follow pytest patterns and use fixtures/pytest.mark.asyncio

How to run locally (Windows)
----------------------------
From the repo root:

.\scripts\run_tests_windows.ps1

or manually:

# create and activate venv
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .[dev]
python -m pytest tests/tools/test_evolution_api.py -v

CI
--
The PR will run the tests in GitHub Actions (.github/workflows/ci.yml). If tests fail in CI, I'll push fixes to the branch and iterate until green.

Notes
-----
If you want me to run the full test suite (all tests, coverage), I can expand the workflow to run everything and adjust the test selection.
