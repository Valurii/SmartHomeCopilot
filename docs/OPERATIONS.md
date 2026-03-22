# Operations

## Repository Role

This repository owns the Home Assistant custom integration, dashboard assets, example Home Assistant config, and the test suite.

The main integration lives in:

- `custom_components/smart_home_copilot/`

Related assets live in:

- `custom_components/shc_dashboard/`
- `ha_config/`
- `tests/`

## Local Development

Use Python 3.11 for local development and tests.

```bash
pip install -r requirements.txt
pip install homeassistant pytest-homeassistant-custom-component
pytest -q
```

## Validation

Repository-level validation should cover:

1. Home Assistant metadata validation (`hassfest`)
2. HACS validation
3. Python test suite
4. required public repo files (`README.md`, `AGENTS.md`, `docs/STATUS.md`, `.github/CODEOWNERS`)

## Configuration Rules

- never commit API keys or provider secrets
- keep example credentials in tracked `*.example` files only
- keep provider-specific docs aligned with the actual supported provider list in `manifest.json` and runtime code

## Branch Flow

Use `feature -> develop -> main`.

`develop` is the working integration branch. Public documentation and CI should validate `develop`, not only `main`.
