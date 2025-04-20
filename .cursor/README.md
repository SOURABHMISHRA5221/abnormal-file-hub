# Cursor Rules Directory

This directory contains configuration and rules for the Cursor AI coding assistant used in the Abnormal File Hub project.

## Contents

- **rules.md** - The main rules file that defines:
  - Project context and architecture requirements
  - Workflow requirements for file changes
  - Code standards for Python, TypeScript, and Docker
  - Quality assurance procedures
  - Documentation requirements
  - Git workflow guidelines

- **ignore** - File patterns to be ignored by Cursor AI:
  - Build artifacts and compiled code
  - Large binary files and media
  - Sensitive configuration files
  - Temporary and cache files
  
- **IGNORE.md** - Documentation for the ignore file format and usage

## Purpose

These rules ensure that all changes made with Cursor AI assistance follow the project's standards and maintain consistent quality. The rules direct the assistant to:

1. Read and understand project architecture before making changes
2. Follow established code patterns and styles
3. Update documentation appropriately
4. Maintain test coverage
5. Follow proper Git workflow

The ignore patterns help improve performance by excluding large files, build artifacts, and sensitive content from analysis.

## Usage

The rules and configuration in this directory are automatically loaded by Cursor AI when working in this repository. No additional configuration is needed.

## Updating Rules

When updating the rules, consider the following:

1. **Be explicit** - Clearly define requirements and expectations
2. **Be consistent** - Ensure rules don't contradict each other
3. **Provide context** - Include reasoning for important rules
4. **Be comprehensive** - Cover all aspects of development workflow

After updating rules, commit the changes and ensure all team members pull the latest version.

## Updating Ignore Patterns

When updating the ignore patterns:

1. **Be specific** - Use precise patterns to avoid excluding important files
2. **Add comments** - Document why certain patterns are included
3. **Test carefully** - Ensure critical files aren't accidentally excluded
4. **Group logically** - Organize patterns by type or purpose

See `IGNORE.md` for detailed documentation on the ignore file format and usage. 