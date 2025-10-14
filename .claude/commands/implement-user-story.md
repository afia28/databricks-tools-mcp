---
description: Implement a complete user story with all acceptance criteria, tests, and validation
argument-hint: [story-id]
allowed-tools: Read, Edit, MultiEdit, Write, Bash, TodoWrite, Task, Grep, Glob
---

# Implementing User Story: $1

You are implementing user story **$1** for this project. Execute this implementation systematically using the TodoWrite tool to track progress.

## 🚀 EXECUTION WORKFLOW

### 🔥 CRITICAL: MANDATORY DELEGATION STRATEGY
**ALL implementation work MUST be delegated to specialized subagents.**
- The main conversation is for coordination ONLY
- NO direct file editing, test running, or code implementation in main conversation
- Each task type has a designated specialist agent that MUST be used

### Step 1: Initialize and Validate Context
```bash
# First, create a comprehensive task list using TodoWrite tool
```
Use TodoWrite to create tasks for:
- Validate project structure and dependencies
- Analyze user story requirements
- Design implementation approach (DELEGATE to python-architect)
- Implement core functionality (DELEGATE to python-architect or data-engineer)
- Create comprehensive test suite (DELEGATE to test-strategist)
- Validate implementation (DELEGATE to user-story-finalizer)
- Run quality checks (DELEGATE to appropriate specialist)

### Step 2: Project Context Discovery
!`echo "📊 Project Structure:"; find src/ tests/ -type f -name "*.py" | sort`
!`echo "📝 Git Status:"; git status --short`
!`echo "🔍 Dependencies:"; grep -E "^[a-z]" pyproject.toml | head -20`
!`echo "✅ Test Coverage:"; ls tests/test_*.py 2>/dev/null | wc -l`

### Step 3: Requirements Analysis
**CRITICAL**: First locate and analyze the user story definition:
1. Search conversation history for story ID "$1"
2. Extract ALL acceptance criteria (mark as todos)
3. Identify test requirements (mark as todos)
4. Document technical constraints

If user story "$1" is not found in context:
```
❌ ERROR: User story "$1" not found in conversation context.
Please provide the user story definition or use a valid story ID.
Available stories might include: US-2.1, US-2.2, US-3.1, etc.
```

### Step 4: Implementation Strategy

**🔥 MANDATORY: Use specialized subagents for ALL work:**
- **python-architect**: MUST use for class design, Pydantic models, code implementation
- **data-engineer**: MUST use for database optimization, data pipeline performance
- **test-strategist**: MUST use for test design, test execution, debugging
- **devops-config**: MUST use for CLI, configuration, YAML validation
- **user-story-finalizer**: MUST use for final validation and git operations

**Delegation Pattern (REQUIRED):**
```python
# ✅ CORRECT - Always delegate to specialist
Task.invoke(
    subagent_type="python-architect",
    description="Implement user story core functionality",
    prompt="""Implement the core functionality for user story $1:
    - Requirements: [detailed requirements]
    - Files to modify: [list files]
    - Standards: Type hints, docstrings, error handling
    """
)

# ❌ WRONG - Never implement directly in main conversation
# Do NOT use Edit, Write, or Bash tools directly here
```

### Step 5: Core Implementation

**🔥 DELEGATION REQUIRED:**
Do NOT implement directly. Instead:
```python
# Delegate ALL implementation to appropriate specialist
Task.invoke(
    subagent_type="python-architect",  # or "data-engineer" for DB work
    description="Implement core functionality",
    prompt="""[Detailed implementation requirements]"""
)
```

**The subagent will handle:**
1. Using Glob to find related existing files
2. Using Read to understand current implementation
3. Using MultiEdit for batch modifications
4. Using Write only for new files

**B. Code Standards Enforcement:**
- Type hints: REQUIRED for all public methods
- Docstrings: Google style with Args, Returns, Raises, Examples
- Logging: Use `logger = loguru.logger` pattern
- Validation: Pydantic v2 models for all data structures
- Error handling: Specific exceptions with clear messages

**C. Implementation Checklist:**
☐ All acceptance criteria implemented
☐ Proper error handling with custom exceptions
☐ Comprehensive logging at appropriate levels
☐ Type hints on all public APIs
☐ Docstrings with examples
☐ Integration with existing codebase verified

### Step 6: Test Implementation

**🔥 DELEGATION REQUIRED:**
```python
# MUST delegate ALL test work to test-strategist
Task.invoke(
    subagent_type="test-strategist",
    description="Create comprehensive test suite",
    prompt="""Create comprehensive tests for user story $1:
    - Test all acceptance criteria
    - Include happy path, error handling, edge cases
    - Use parametrized tests where appropriate
    - Achieve 90%+ coverage
    """
)
```

**DO NOT run tests directly. The test-strategist will:**
- Design test structure and patterns
- Create test implementations
- Run tests and analyze results
- Debug any failures

### Step 7: Quality Validation

**🔥 DELEGATION REQUIRED:**
```python
# MUST delegate validation to user-story-finalizer
Task.invoke(
    subagent_type="user-story-finalizer",
    description="Validate and finalize implementation",
    prompt="""Validate the implementation of user story $1:
    - Run all quality checks (mypy, black, ruff, pytest)
    - Fix any issues found
    - Ensure all acceptance criteria are met
    - Update documentation as needed
    """
)
```

**DO NOT run validation commands directly. The finalizer will handle all checks.**

### Step 8: Integration Verification

**Verify no regressions:**
!`pytest tests/ --tb=short -q`
!`python -c "import sys; print('✅ Package imports working')"`

## 📋 DELIVERABLES CHECKLIST

Mark each item using TodoWrite as completed:

### Implementation Files
- [ ] Core implementation in `src/` directory
- [ ] Updated `__init__.py` exports if applicable
- [ ] Configuration updates if needed
- [ ] Updated type hints and docstrings

### Test Suite
- [ ] Unit tests in `tests/test_$1.py`
- [ ] Integration tests if applicable
- [ ] Test fixtures in `conftest.py` if needed
- [ ] 90%+ coverage for new code

### Documentation
- [ ] Docstrings for all public APIs
- [ ] Usage examples in docstrings
- [ ] Update CLAUDE.md if patterns changed

### Validation Results
- [ ] All tests passing
- [ ] Type checking clean
- [ ] Linting passed
- [ ] No import errors

### Documentation
- [ ] Docstrings for all public APIs
- [ ] Usage examples in docstrings
- [ ] Update CLAUDE.md if patterns changed

## 🔄 MANDATORY POST-IMPLEMENTATION WORKFLOW

**IMPORTANT**: After completing the core implementation, you MUST execute the following commands in sequence:

### Step 9: Run Comprehensive Tests
**The `/run-tests` command will delegate to test-strategist:**
```bash
/run-tests coverage
```
This command will:
- DELEGATE to test-strategist agent
- Run all unit and integration tests
- Generate coverage report
- Debug any failing tests
- Ensure 90%+ coverage for new code

### Step 10: Validate Implementation
**The `/validate-implementation` command will delegate to user-story-finalizer:**
```bash
/validate-implementation
```
This command will:
- DELEGATE to user-story-finalizer agent
- Run all tests again
- Execute type checking with mypy
- Check code formatting with black
- Run linting with ruff
- Verify import integrity
- Ensure coverage requirements are met

### Step 11: Apply Linting and Formatting
**The `/lint` command will delegate to python-architect:**
```bash
/lint
```
This command will:
- DELEGATE to python-architect agent
- Auto-format code with black
- Sort imports with isort
- Apply flake8 style rules
- Run comprehensive pylint checks
- Ensure code meets all style guidelines

### Step 12: Update Documentation and Complete
**Execute `/update-documentation` command to finalize:**
```bash
/update-documentation
```
This will:
- Update README.md with new features
- Update CLAUDE.md status and metrics
- Check git status for all changes
- Generate detailed commit message
- Commit all changes to git
- Push to remote repository
- Create/update pull request if needed
- Merge with main branch when ready

## 🎯 SUCCESS CRITERIA

The implementation is ONLY complete when:
✅ All acceptance criteria are met
✅ `/run-tests coverage` shows all tests passing with 90%+ coverage
✅ `/validate-implementation` passes all checks
✅ `/lint` shows no issues or auto-fixes applied
✅ `/update-documentation` has committed and pushed all changes
✅ TodoWrite shows all tasks completed
✅ Code is merged to main branch

## 🚨 ERROR RECOVERY

If implementation fails at any step:
1. Mark current task as blocked in TodoWrite
2. Add new task for fixing the issue
3. Use appropriate subagent for expertise
4. Re-run validation after fix
5. Continue with remaining tasks

## 💡 PROACTIVE ENHANCEMENTS

After core implementation, consider:
- Performance optimizations (consult data-engineer subagent)
- Additional error scenarios (consult test-strategist subagent)
- CLI improvements (consult devops-config subagent)
- Architectural improvements (consult python-architect subagent)

---
**Remember**: Use TodoWrite throughout to track progress and ensure nothing is missed!