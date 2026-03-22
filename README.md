<p align="center">
  <a href="https://coff.ee/fjoelnir" target="_blank">
    <img src="https://img.shields.io/badge/Buy%20me%20a%20coffee-Support%20Dev-yellow?style=for-the-badge&logo=buy-me-a-coffee" alt="Buy Me A Coffee">
  </a>
</p>

# SmartHomeCopilot

[![Validate with hassfest](https://img.shields.io/github/actions/workflow/status/Valurii/SmartHomeCopilot/hassfest.yaml?style=for-the-badge)](https://github.com/Valurii/SmartHomeCopilot)
[![HACS Validation](https://img.shields.io/github/actions/workflow/status/Valurii/SmartHomeCopilot/validate.yaml?style=for-the-badge)](https://github.com/Valurii/SmartHomeCopilot)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Valurii/SmartHomeCopilot?style=for-the-badge)](https://github.com/Valurii/SmartHomeCopilot/releases)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/Valurii/SmartHomeCopilot)

`SmartHomeCopilot` is a Home Assistant custom integration that analyzes your current smart-home setup and proposes actionable automation YAML with the help of cloud or local LLM providers.

It is designed as a review-first copilot: suggestions are generated against your real entities, areas, devices, and existing automations, but nothing is applied automatically without your explicit decision.

## What It Does

- snapshots your Home Assistant context
- builds a provider-specific AI prompt from entities, devices, areas, and automations
- returns human-readable suggestions plus ready-to-review YAML
- exposes results through sensors and persistent notifications
- supports accepting suggestions into `automations.yaml`
- supports cloud and local providers including OpenAI, Anthropic, Google, Groq, LocalAI, Ollama, Mistral, Perplexity, and OpenRouter

## Repository Status

- active public integration repository
- default branch: `develop`
- maintained by `@fjoelnr` with `@ha-llm-bot` as contributor/reviewer

Further maintainer context:

- [docs/STATUS.md](docs/STATUS.md)
- [docs/OPERATIONS.md](docs/OPERATIONS.md)
- [AGENTS.md](AGENTS.md)

## How It Works

1. The integration collects a scoped snapshot of your Home Assistant environment.
2. It sends that snapshot to the configured AI provider.
3. The provider response is parsed into human-readable description text and YAML suggestions.
4. Suggestions are surfaced through sensors, notifications, and optional dashboard cards.
5. You review, adjust, and optionally accept the automation.

## Screenshots

<p align="center">
  <img src="images/Screenshot/Screenshot%202025-01-19%20082247-1.png" alt="Notification example" width="700" />
  <br><em>Suggestions delivered directly inside Home Assistant</em>
</p>

<p align="center">
  <img src="images/Screenshot/Screenshot%202025-01-19%20083200.png" alt="Dashboard example" width="700" />
  <br><em>Dashboard surfacing both summary text and YAML suggestion content</em>
</p>

## Installation

### HACS

1. Open HACS.
2. Add or search for `SmartHomeCopilot`.
3. Download the integration.
4. Restart Home Assistant.
5. Add the integration from `Settings -> Devices & Services`.

### Manual

1. Copy `custom_components/smart_home_copilot/` into your Home Assistant `custom_components/` directory.
2. Restart Home Assistant.
3. Add the integration from `Settings -> Devices & Services`.

If you use the dashboard card assets, also deploy the assets from `custom_components/shc_dashboard/` into your Home Assistant frontend path as needed.

## Configuration

The config flow supports provider-specific credentials and settings, including:

- provider selection
- model selection
- API keys or local endpoint URLs
- max token settings
- temperature
- optional custom system prompts

For containerized setups you can inject secrets via environment variables and reference them from Home Assistant configuration.

Example:

```yaml
smart_home_copilot:
  openai_api_key: !env_var OPENAI_API_KEY
  ollama_url: !env_var OLLAMA_URL
```

Alternative secret file flow:

- copy `credentials.yaml.example` to `credentials.yaml`
- keep it out of version control
- mount it into the Home Assistant container if needed

## Service and Output Surface

Main service:

- `smart_home_copilot.generate_suggestions`

Useful request parameters:

- `all_entities`
- `domains`
- `entity_limit`
- `custom_prompt`

Main output surface:

- suggestion sensor with description and YAML attributes
- provider status sensor
- persistent notifications inside Home Assistant

## Development Setup

Use Python 3.11.

```bash
pip install -r requirements.txt
pip install homeassistant pytest-homeassistant-custom-component
pytest -q
```

You can also use the helper script:

```bash
bash scripts/setup_tests.sh
pytest -q
```

## Validation

Repository validation should keep these paths green:

- `hassfest`
- HACS validation
- Python test suite
- repo hygiene checks

## Security Notes

- never commit provider secrets or API keys
- prefer local models if your Home Assistant snapshot data should stay fully local
- review every generated automation before applying it

## License

MIT. See [LICENSE](LICENSE).

## Contributing

Contributions are welcome. If you use an AI agent while contributing, review [AGENTS.md](AGENTS.md) first.

## Disclaimer

This is an independent custom component. It is not affiliated with or endorsed by Home Assistant, Nabu Casa, or any AI provider.
