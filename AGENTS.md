# AGENTS.md

## Purpose

This file provides essential project-specific instructions for AI agents (e.g., Codex, Claude, Gemini) interacting with the SmartHomeCopilot codebase. It ensures that code suggestions, refactoring, and completions align with the design principles and architectural conventions of the project.

## Project Summary

SmartHomeCopilot is a custom Home Assistant integration that uses large language models (LLMs) to suggest intelligent YAML automations tailored to the user's environment. It analyzes entities, areas, and device states and generates safe, functional automations in YAML format.

## Agent Instructions

- All YAML suggestions **must be syntactically correct** and properly indented.
- Use only **valid Home Assistant entity IDs** where possible.
- Include the following sections in automation YAML (in order):
  1. `alias`
  2. `trigger`
  3. `condition` (optional)
  4. `action`
- Always use `mode: single` or `mode: restart` unless the use case clearly benefits from `queued`.
- Do **not** hardcode credentials or example API keys in YAML examples.
- Avoid entities that begin with `test_` (used for internal testing).
- Use consistent naming for automations: `auto_<area>_<purpose>` (e.g., `auto_kitchen_lights_night`).

## Project Structure

- Custom integration path: `custom_components/smart_home_copilot/`
- YAML prompt context: `data/context/automation.yaml`
- System prompt source (used by backend LLM): `core/prompts/system_prompt.txt`
- Example frontend API: `smart_home_copilot/frontend/` (for UI suggestions)

## Prompting Context (for Agents)

This file may be prepended as part of a system prompt for Codex- or Claude-style tools.
Keep your responses concise, context-aware, and focused on YAML or Home Assistant-specific logic.
When referring to automations, assume the user is not an expert in Home Assistant YAML.

