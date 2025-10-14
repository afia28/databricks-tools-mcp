# Project Slash Commands

This directory contains custom slash commands for the databricks-duckdb-replicator project. These commands automate common development tasks and provide project-specific functionality.

## 📋 Complete Command Inventory

Total Commands: **8 slash commands** for comprehensive project automation

## Available Commands

### 🎯 /prime
- **File**: `.claude/commands/prime.md`
- **Purpose**: Prime Claude Code with essential project context
- **Usage**: `/prime`
- **What it does**:
  - Lists all tracked files in git repository
  - Reads key project files (README, CLAUDE.md, commands.md, subagents.md)
  - Establishes project context for better assistance
- **When to use**: Start of a new session or when context needs refreshing
- **Example**: `/prime` (no arguments needed)

### 🚀 /implement-user-story
- **File**: `.claude/commands/implement-user-story.md`
- **Purpose**: Complete implementation of a user story with all acceptance criteria
- **Usage**: `/implement-user-story [story-id]`
- **Allowed Tools**: Read, Edit, MultiEdit, Write, Bash, TodoWrite, Task, Grep, Glob
- **What it does**:
  - Creates comprehensive task list with TodoWrite
  - Analyzes acceptance criteria from conversation context
  - Implements all required functionality
  - Generates complete test suite
  - Validates implementation against requirements
  - Updates package exports
  - Engages specialized subagents as needed
- **Example scenarios**:
  ```bash
  /implement-user-story US-2.1        # Implement by story ID
  /implement-user-story US-3.1-Replication-Engine  # Full path
  ```
- **Key features**:
  - Automatic subagent delegation (python-architect, data-engineer)
  - Progress tracking with TodoWrite
  - Comprehensive validation
  - Test generation

### 🧪 /run-tests
- **File**: `.claude/commands/run-tests.md`
- **Purpose**: Execute tests with different scopes and detailed reporting
- **Usage**: `/run-tests [scope]`
- **Allowed Tools**: Bash, Read
- **Available scopes**:
  - `all` (default) - Run entire test suite
  - `unit` - Unit tests only
  - `integration` - Integration tests only
  - `coverage` - Tests with coverage report
  - `failed` - Re-run only previously failed tests
  - `[file-path]` - Specific test file
- **Examples**:
  ```bash
  /run-tests                          # All tests
  /run-tests unit                     # Unit tests only
  /run-tests coverage                 # With coverage report
  /run-tests tests/test_config.py    # Specific file
  /run-tests failed                   # Re-run failures
  ```
- **Output includes**:
  - Test execution summary
  - Failed test details
  - Coverage percentages
  - Performance metrics (slowest tests)

### ✅ /validate-implementation
- **File**: `.claude/commands/validate-implementation.md`
- **Purpose**: Comprehensive validation before committing code
- **Usage**: `/validate-implementation`
- **Allowed Tools**: Bash, Read, Grep
- **What it validates**:
  - All tests pass (`uv run pytest`)
  - Type checking (`uv run mypy src/`)
  - Code formatting (`uv run black --check`)
  - Import sorting (`uv run isort --check`)
  - Linting (`uv run ruff check`)
  - Coverage requirements (>85%)
  - Import verification
- **Example workflow**:
  ```bash
  # After implementing a feature
  /validate-implementation
  # Fix any issues found
  # Commit when all checks pass
  ```
- **Failure handling**: Provides specific commands to fix issues

### 🐛 /debug-config
- **File**: `.claude/commands/debug-config.md`
- **Purpose**: Debug and resolve configuration-related issues
- **Usage**: `/debug-config [config-file-path]`
- **Allowed Tools**: Read, Bash, Grep
- **What it checks**:
  - YAML syntax validation
  - Pydantic model validation
  - Environment variable presence
  - Databricks connectivity
  - DuckDB path accessibility
  - Configuration schema compliance
- **Example scenarios**:
  ```bash
  /debug-config config.yaml          # Debug main config
  /debug-config test-config.yaml     # Debug test config
  /debug-config                      # Default to config.yaml
  ```
- **Diagnostic output**:
  - Configuration structure analysis
  - Missing environment variables
  - Validation errors with line numbers
  - Fix recommendations

### 📊 /analyze-performance
- **File**: `.claude/commands/analyze-performance.md`
- **Purpose**: Analyze performance characteristics and suggest optimizations
- **Usage**: `/analyze-performance [target-module-or-function]`
- **Allowed Tools**: Read, Bash, Grep
- **What it analyzes**:
  - System resources (CPU, memory)
  - Code complexity and patterns
  - Memory usage during imports
  - Database configuration
  - Performance bottlenecks
  - Optimization opportunities
- **Examples**:
  ```bash
  /analyze-performance                # Entire project
  /analyze-performance core/replicator # Specific module
  /analyze-performance replicate_table # Specific function
  ```
- **Recommendations provided**:
  - Chunk size optimization
  - Memory management strategies
  - Database tuning parameters
  - Architecture improvements
  - Profiling setup

### 📝 /update-documentation
- **File**: `.claude/commands/update-documentation.md`
- **Purpose**: Update all project documentation after completing tasks
- **Usage**: `/update-documentation [commit-hash]`
- **Allowed Tools**: Read, Edit, MultiEdit, Bash, Grep
- **What it updates**:
  - README.md with new features
  - CLAUDE.md status and metrics
  - Command documentation
  - API documentation
  - Test coverage reports
  - Performance benchmarks
- **Examples**:
  ```bash
  /update-documentation               # Uses latest commit
  /update-documentation abc123f       # Specific commit
  ```
- **Documentation maintained**:
  - Feature descriptions
  - Configuration examples
  - API references
  - Status tracking
  - Code quality metrics

### 🔧 /lint
- **File**: `.claude/commands/lint.md`
- **Purpose**: Run Python code linting and formatting tools
- **Usage**: `/lint`
- **What it runs**:
  - **Black**: Code formatting
  - **isort**: Import sorting
  - **flake8**: Style guide enforcement
  - **pylint**: Comprehensive linting
  - **mypy**: Type checking (if configured)
- **Example workflow**:
  ```bash
  /lint                               # Run all linters
  # Review output
  # Fix issues or accept auto-fixes
  ```
- **Configuration files**:
  - `.flake8` for style rules
  - `pyproject.toml` for Black/isort
  - `.pylintrc` for pylint rules

## Command Features

### Frontmatter Configuration
Each command includes YAML frontmatter with:
- `description`: Brief description shown in `/help`
- `argument-hint`: Shows expected arguments in autocomplete
- `allowed-tools`: Specific tools the command can use (Bash, Read, Edit, Grep, TodoWrite, Task, etc.)
- `model`: Optional model preference for command execution

### Dynamic Command Execution
Commands support:
- **Bash execution** (`!` prefix): Execute shell commands and capture output
- **File references** (`@` syntax): Include file contents directly
- **Variable substitution** (`$1`, `$2`, etc.): Pass arguments to commands
- **Conditional logic**: Different paths based on results

### Error Handling
All commands include:
- Graceful failure handling
- Clear, actionable error messages
- Fallback behavior for missing dependencies
- Validation of prerequisites

## 🔄 Workflow Patterns

### Standard Development Flow
```bash
# 1. Start session with context
/prime

# 2. Implement new feature
/implement-user-story US-3.4

# 3. Validate and test
/run-tests coverage
/validate-implementation

# 4. Fix any issues
/lint
/debug-config

# 5. Update documentation
/update-documentation
```

### Quick Fix Workflow
```bash
# 1. Run tests to identify issues
/run-tests failed

# 2. Debug specific problems
/debug-config
/analyze-performance problematic-module

# 3. Apply fixes and validate
/lint
/validate-implementation
```

### Performance Optimization Workflow
```bash
# 1. Baseline analysis
/analyze-performance

# 2. Target specific modules
/analyze-performance core/replicator
/analyze-performance utils/table_reference

# 3. Implement optimizations
# ... make changes ...

# 4. Validate improvements
/run-tests performance
/validate-implementation
```

## 🎭 Command Composition

Commands can be used together for comprehensive workflows:

### Feature Development Pipeline
```mermaid
graph LR
    A[/prime] --> B[/implement-user-story]
    B --> C[/run-tests]
    C --> D[/lint]
    D --> E[/validate-implementation]
    E --> F[/update-documentation]
```

### Debugging Pipeline
```mermaid
graph LR
    A[/debug-config] --> B[/analyze-performance]
    B --> C[/run-tests specific]
    C --> D[Fix Issues]
    D --> E[/validate-implementation]
```

## 📊 Command Categories

### 🚀 Development Commands
- `/prime` - Initialize context
- `/implement-user-story` - Feature implementation
- `/lint` - Code quality

### 🧪 Testing Commands
- `/run-tests` - Test execution
- `/validate-implementation` - Pre-commit validation

### 🔍 Diagnostic Commands
- `/debug-config` - Configuration debugging
- `/analyze-performance` - Performance analysis

### 📝 Documentation Commands
- `/update-documentation` - Doc maintenance

## 💡 Best Practices

### Command Usage Guidelines

1. **Start New Sessions**: Always run `/prime` at the beginning
2. **Feature Development**: Use `/implement-user-story` for structured implementation
3. **Regular Validation**: Run `/validate-implementation` before commits
4. **Performance Monitoring**: Periodically run `/analyze-performance`
5. **Documentation Updates**: Use `/update-documentation` after major changes

### Command Development Guidelines

When creating new commands:
1. **Clear Purpose**: Each command should have a single, clear purpose
2. **Comprehensive Output**: Provide detailed, actionable output
3. **Error Handling**: Include robust error handling and recovery
4. **Tool Selection**: Choose appropriate allowed-tools for the task
5. **Documentation**: Include usage examples and expected outcomes

### Integration with Subagents

Commands can leverage subagents:
- `/implement-user-story` → Uses python-architect, data-engineer
- `/run-tests` → Can invoke test-strategist for analysis
- `/debug-config` → May use devops-config for recommendations

## 🔒 Command Security

### Safe Practices
- Commands never modify critical system files
- All destructive operations require confirmation
- Environment variables are never exposed in output
- Sensitive data is masked in logs

### Tool Restrictions
Each command specifies allowed tools to:
- Limit scope of operations
- Prevent unintended modifications
- Ensure predictable behavior

## 📈 Command Performance

### Optimization Tips
- Commands cache results when appropriate
- Parallel execution for independent tasks
- Lazy loading of large files
- Incremental processing for large datasets

### Resource Management
- Memory-efficient for large codebases
- Timeout protection for long-running operations
- Progress indicators for lengthy tasks

## 🔮 Future Enhancements

Planned improvements:
- Command chaining and pipelines
- Custom command templates
- Command history and replay
- Interactive mode for complex operations
- Integration with CI/CD pipelines

## Management

### Command Discovery
```bash
# List all available commands
/help

# Get details about specific command
/help implement-user-story
```

### Creating Custom Commands
1. Create `.md` file in `.claude/commands/`
2. Add YAML frontmatter with metadata
3. Include command logic and bash scripts
4. Test thoroughly before use

### Command Maintenance
- Regular review of command effectiveness
- Update based on project evolution
- Remove deprecated commands
- Document breaking changes

These commands form a comprehensive toolkit for efficient development of the databricks-duckdb-replicator project, ensuring quality, consistency, and productivity.