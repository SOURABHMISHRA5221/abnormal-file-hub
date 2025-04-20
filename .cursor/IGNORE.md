# Cursor Ignore File Documentation

## Overview

The `.cursor/ignore` file specifies patterns for files and directories that should be ignored by the Cursor AI assistant. This helps improve performance, reduce distractions, and prevent the assistant from analyzing unnecessary files.

## Purpose

- **Improve Performance**: Prevents Cursor from analyzing large binary files or generated code that would slow it down
- **Focus Attention**: Helps the assistant focus on relevant code files rather than build artifacts or temporary files
- **Protect Sensitive Information**: Excludes files that might contain sensitive information or credentials
- **Reduce Noise**: Minimizes irrelevant suggestions and recommendations

## File Format

The ignore file uses a pattern format similar to `.gitignore`:

- Blank lines are ignored
- Lines starting with `#` are comments
- Patterns ending with `/` match directories only
- Patterns starting with `/` match from the repository root
- Patterns starting with `!` negate a previous pattern (include a previously excluded file)
- Standard glob patterns work: `*`, `?`, `[abc]`, `[a-z]`

## Default Ignored Patterns

The ignore file includes patterns for:

1. **Build artifacts and compiled code**: `build/`, `dist/`, `__pycache__/`, etc.
2. **Package directories**: `node_modules/`, `venv/`, etc.
3. **Cache and temporary files**: `.cache/`, `.pytest_cache/`, etc.
4. **IDE specific files**: `.idea/`, `.vscode/`, etc.
5. **Large binary files**: `*.zip`, `*.pdf`, media files, etc.
6. **Project specific files**: `media/uploads/`, `*.sqlite3`, etc.
7. **Generated files**: `*.min.js`, `*.bundle.js`, etc.
8. **Sensitive content**: `.env`, `secrets.json`, etc.

## Customizing the Ignore File

When customizing the `.cursor/ignore` file:

1. Add project-specific patterns relevant to your codebase
2. Be specific with patterns to avoid excluding important files
3. Use comments to explain why certain patterns are included
4. Group related patterns together for better organization
5. Test changes to ensure important files aren't accidentally excluded

## Example Usage

```
# Exclude all log files
*.log

# But include important application logs
!app/logs/important.log

# Exclude all files in the temp directory
/temp/*

# Exclude specific large data files
data/large_dataset_*.csv
```

## Integration with Development Workflow

- **Review regularly**: Update the ignore file as your project structure evolves
- **Align with team**: Ensure all team members are aware of ignored files
- **Coordinate with other ignore files**: Consider how it relates to `.gitignore` and other ignore configurations

For more information on Cursor AI configuration, refer to the [Cursor documentation](https://cursor.sh/docs) or the `.cursor/README.md` file. 