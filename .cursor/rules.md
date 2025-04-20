# Abnormal File Hub Cursor Rules

## Project Context and Architecture
```yaml
SYSTEM_CONTEXT: |
  You are a senior developer working on the Abnormal File Hub project.
  
  Required file reads on startup:
  - docs/architecture.mermaid: System architecture and component relationships
  - docs/technical.md: Technical specifications and patterns
  - tasks/tasks.md: Current development tasks and requirements
  - docs/status.md: Project progress and state

  Before making any changes:
  1. Parse and understand system architecture from docs/architecture.mermaid
  2. Check current task context from tasks/tasks.md
  3. Follow technical specifications from docs/technical.md
  4. Review progress in docs/status.md
```

## Workflow Requirements

### File Management Rules
```yaml
ON_FILE_CHANGE: |
  Required actions after ANY code changes:
  1. READ docs/architecture.mermaid to verify architectural compliance
  2. UPDATE docs/status.md with:
     - Current progress
     - Any new issues encountered
     - Completed items
  3. VALIDATE changes against docs/technical.md specifications
  4. VERIFY task progress against tasks/tasks.md
  5. COMMIT changes with descriptive messages
```

### Task Management
```yaml
TASK_WORKFLOW: |
  Required files:
  - tasks/tasks.md: Source of task definitions
  - docs/status.md: Progress tracking
  - docs/technical.md: Implementation guidelines
  
  Workflow steps:
  1. READ tasks/tasks.md:
     - Parse current task requirements
     - Extract acceptance criteria
     - Identify dependencies
  
  2. VALIDATE against docs/architecture.mermaid:
     - Confirm architectural alignment
     - Check component interactions
  
  3. UPDATE docs/status.md:
     - Mark task as in-progress
     - Track completion of sub-tasks
     - Document any blockers
  
  4. IMPLEMENT following TDD:
     - Create test files first
     - Implement to pass tests
     - Update status on test completion
     
  5. DOCUMENT completed work:
     - Update README.md if needed
     - Update technical documentation
     - Create examples or usage instructions
```

## Code Standards

### Python Guidelines
```yaml
PYTHON_GUIDELINES: |
  - Follow PEP 8 style guide
  - Use proper type hints (Python 3.10+)
  - Write docstrings for all functions and classes
  - Implement proper error handling with try/except
  - Add appropriate logging (DEBUG, INFO, WARNING, ERROR)
  - Use Django's ORM for database operations
  - Follow Django REST Framework patterns
  - Implement transaction handling for data integrity
```

### TypeScript Guidelines
```yaml
TYPESCRIPT_GUIDELINES: |
  - Use strict typing, avoid 'any'
  - Follow SOLID principles
  - Write unit tests for all public methods
  - Document with JSDoc
  - Use React hooks appropriately
  - Implement proper error boundaries
  - Follow ESLint configurations
  - Use TypeScript interfaces for data structures
```

### Docker Guidelines
```yaml
DOCKER_GUIDELINES: |
  - Ensure compatibility with docker-compose
  - Create helper scripts that work with containers
  - Respect environment configurations
  - Ensure volumes are properly configured
  - Test all commands in Docker environment
  - Document Docker-specific instructions
```

## Quality Assurance

### Architecture Understanding
```yaml
READ_ARCHITECTURE: |
  File: docs/architecture.mermaid
  Required parsing:
  1. Load and parse complete Mermaid diagram
  2. Extract and understand:
     - Module boundaries and relationships
     - Data flow patterns
     - System interfaces
     - Component dependencies
  3. Validate any changes against architectural constraints
  4. Ensure new code maintains defined separation of concerns
  
  Error handling:
  1. If file not found: STOP and notify user
  2. If diagram parse fails: REQUEST clarification
  3. If architectural violation detected: WARN user
```

### Error Prevention
```yaml
VALIDATION_RULES: |
  1. Verify type consistency
  2. Check for potential null/undefined
  3. Validate against business rules
  4. Ensure error handling
  5. Implement logging for errors
  6. Add transaction handling for database operations
  7. Test edge cases
  8. Validate user inputs
```

### Documentation Requirements
```yaml
DOCUMENTATION_RULES: |
  1. Update README.md for major feature additions
  2. Maintain comprehensive API documentation
  3. Document all management commands
  4. Create usage examples for new features
  5. Update status.md for completed work
  6. Add technical documentation for architectural changes
  7. Document test procedures
```

## Git Workflow
```yaml
GIT_WORKFLOW: |
  1. Commit changes with descriptive messages
  2. Update documentation before pushing
  3. Verify all tests pass before pushing
  4. Follow conventional commit message format when possible
  5. Push changes only after updating all required documentation
``` 