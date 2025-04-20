# Cursor Rules

This directory contains rules for Cursor AI in the MDC format, which allows for more structured and contextual rules handling.

## Available Rules

- **project-context.mdc**: Overall project context and architecture requirements (always applied)
- **file-management.mdc**: Guidelines for file changes and workflow (applied to all files)
- **code-standards.mdc**: Language-specific coding standards for Python, TypeScript, and Docker (applied to relevant file types)
- **quality-assurance.mdc**: Guidelines for error prevention and documentation (manually applied as needed)

## Rule Types

These rules use different application methods:

- **Always Applied**: Rules that provide general project context
- **Auto-attached**: Rules that apply to specific file types based on glob patterns
- **Manually Applied**: Rules that can be referenced by name when needed

## Usage

These rules are automatically applied by Cursor AI based on their metadata. You can also manually reference a rule using the rule name in your prompts.

## Updating Rules

When updating rules:

1. Keep the MDC metadata section at the top of each file
2. Use clear, actionable guidelines
3. Group related concepts together
4. Include examples where helpful
5. Update this README when adding new rule files