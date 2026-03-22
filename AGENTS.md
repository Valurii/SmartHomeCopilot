# AGENTS.md

## Purpose

Short reference for AI agents (Codex, Claude, Gemini, etc.) working on this repository.
It ensures suggestions and code changes stay consistent with project rules.

## Project Overview

SmartHomeCopilot is an AI‑driven assistant for Home Assistant.
It is provided as a custom integration that generates YAML automations.

## Important Instructions for AI Agents

- YAML must be valid and correctly indented.
- Use real Home Assistant entity IDs when known.
- Never include credentials or API keys in examples.
- Keep suggestions concise and easy to verify.
- Automation YAML should contain `alias`, `trigger`, `condition`, `action` in that order.

## Project‑Specific Rules

- Ignore automations referencing entities with an `_test` prefix.
- Automation IDs follow `auto_{{area}}_{{description}}`.
- Prefer `mode: single` or `mode: restart`; use `mode: queued` only if necessary.

## Technical Reference

- Integration folder: `custom_components/smart_home_copilot/`
- Dashboard assets: `custom_components/shc_dashboard/`
- Example Home Assistant config: `ha_config/`
- Tests: `tests/`
- Repo status: `docs/STATUS.md`
- Maintainer workflow: `docs/OPERATIONS.md`

## Notes for GPT‑Based Agents

- This file is used as system context when prompting.
- Follow Markdown syntax.
- Maximize information value and minimize tokens.
- Keep README, `manifest.json`, and HACS metadata aligned with the actual repo owner and supported behavior.

