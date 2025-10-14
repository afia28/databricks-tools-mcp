# US-6.2: Enhance Pre-commit Hooks

## Metadata
- **Story ID**: US-6.2
- **Title**: Enhance Pre-commit Hooks
- **Phase**: Phase 6 - Testing & Quality
- **Estimated LOC**: ~30 lines of config
- **Dependencies**: US-6.1 (Integration Tests)
- **Status**: ⬜ Not Started

## Overview
Add mypy, pytest, and coverage checks to pre-commit hooks to ensure code quality before commits.

## User Story
**As a** developer
**I want** automated quality checks on commit
**So that** code quality is consistently high

## Acceptance Criteria
1. ✅ mypy added to pre-commit
2. ✅ pytest added to pre-commit
3. ✅ coverage threshold check added
4. ✅ All hooks configured correctly
5. ✅ Hooks run successfully

## Files to Update

### .pre-commit-config.yaml
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict, --ignore-missing-imports]

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest
        language: system
        pass_filenames: false
        always_run: true

      - id: pytest-cov
        name: pytest-coverage
        entry: uv run pytest --cov=src/databricks_tools --cov-report=term --cov-fail-under=85
        language: system
        pass_filenames: false
        always_run: true
```

### mypy.ini (create)
```ini
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
strict_equality = True

[mypy-databricks.*]
ignore_missing_imports = True

[mypy-tiktoken.*]
ignore_missing_imports = True

[mypy-mcp.*]
ignore_missing_imports = True
```

## Test Cases
1. test_precommit_hooks_installed
2. test_mypy_passes
3. test_pytest_passes
4. test_coverage_threshold
5. test_ruff_passes

## Files
- **Modify**: `.pre-commit-config.yaml`
- **Create**: `mypy.ini`

## Commands to Run
```bash
# Install/update hooks
uv run pre-commit install
uv run pre-commit autoupdate

# Test hooks
uv run pre-commit run --all-files
```

## Related Stories
- **Depends on**: US-6.1
- **Blocks**: US-6.3
