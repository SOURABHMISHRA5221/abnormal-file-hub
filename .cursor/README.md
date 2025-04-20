# Cursor Configuration

This directory contains configuration files for the Cursor AI assistant, including rules, ignore patterns, and documentation.

## Purpose

This directory centralizes Cursor AI configuration to:

1. Improve the quality of AI assistance with project-specific rules
2. Standardize coding practices and ensure consistency
3. Store documentation for Cursor configurations
4. Optimize AI performance by specifying files to ignore
5. Provide a central place for team members to update and reference cursor configurations

## Files

* **rules.md**: Comprehensive project rules for the Cursor AI assistant
* **ignore**: Directory-specific ignore patterns (similar format to .gitignore)
* **IGNORE.md**: Documentation of the ignore file format and usage

## Ignore Configuration

Cursor uses both `.cursor/ignore` (project-level) and `.cursorignore` (root-level) files to determine which files and patterns to exclude from analysis:

1. `.cursor/ignore`: Project-team shared ignore patterns that should be version controlled
2. `.cursorignore`: Root-level configuration, which can also contain user-specific ignore patterns

Both files use the same pattern format (similar to `.gitignore`).

## Updating Ignore Patterns

When updating ignore patterns:

1. Be specific about what to ignore
2. Add comments to explain why certain patterns are ignored
3. Test carefully to ensure critical files aren't accidentally ignored
4. Group patterns logically by category
5. For user-specific patterns, prefer using the root `.cursorignore` file

## Relationship to Other Files

The configuration in this directory works in conjunction with:
- Tasks in `tasks/tasks.md`
- Status updates in `docs/status.md`
- Technical specifications in `docs/technical.md`
- Architecture diagrams in `docs/architecture.mermaid`

## Updating Rules

When updating the rules, consider the following:

1. **Be explicit** - Clearly define requirements and expectations
2. **Be consistent** - Ensure rules don't contradict each other
3. **Provide context** - Include reasoning for important rules
4. **Be comprehensive** - Cover all aspects of development workflow

After updating rules, commit the changes and ensure all team members pull the latest version. 