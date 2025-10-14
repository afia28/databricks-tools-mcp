---
description: Execute tests with different scopes using test-strategist agent
argument-hint: [scope] (all|unit|integration|coverage|specific-file|failed)
allowed-tools: Task, TodoWrite
---

# Running Tests

## 🔥 CRITICAL: MANDATORY DELEGATION

**ALL test execution MUST be delegated to the test-strategist agent.**
- The main conversation is for coordination ONLY
- NO direct test execution with pytest or bash commands
- The test-strategist has specialized expertise for test execution, debugging, and coverage analysis

## Test Scope: $1

### 🎯 Delegation to Test Strategist

I will now delegate test execution to the test-strategist agent who will:
1. Execute the requested test scope
2. Analyze results and failures
3. Debug any issues found
4. Provide coverage analysis
5. Recommend improvements

```python
# Delegating to test-strategist for test execution
Task.invoke(
    subagent_type="test-strategist",
    description="Execute and analyze tests",
    prompt="""Execute tests for the project.

    Test Scope: $1

    Based on the scope, please:

    1. SCOPE INTERPRETATION:
       - 'all' or empty: Run complete test suite (uv run pytest tests/)
       - 'unit': Run unit tests only (exclude integration tests)
       - 'integration': Run integration tests only
       - 'coverage': Run with coverage report (uv run pytest tests/ --cov=src/ --cov-report=term-missing)
       - 'failed': Re-run only previously failed tests (uv run pytest --lf)
       - 'specific [file]': Run specific test file (e.g., tests/test_config.py)

    2. EXECUTION:
       - Use appropriate pytest commands with uv run
       - Capture detailed output including failures
       - Note execution time and test count

    3. ANALYSIS:
       - Identify any test failures and their root causes
       - Debug failing tests if needed
       - Analyze coverage gaps if running with coverage
       - Check for slow tests (>1s execution time)

    4. COVERAGE REPORT (if applicable):
       - Overall coverage percentage
       - Module-by-module breakdown
       - Identify uncovered code paths
       - Recommend specific test additions

    5. RECOMMENDATIONS:
       - Suggest test improvements
       - Identify missing test scenarios
       - Recommend performance optimizations
       - Highlight any test anti-patterns

    6. QUALITY METRICS:
       - Test distribution (unit vs integration)
       - Average test execution time
       - Test maintainability assessment
       - Code coverage trends

    IMPORTANT:
    - Use 'uv run pytest' for all test commands
    - Include -xvs flags for detailed output on failures
    - For coverage, aim for 90%+ on new code
    - Debug any failures before reporting back

    Please provide:
    - Execution summary (passed/failed/skipped)
    - Detailed failure analysis if any
    - Coverage report if requested
    - Actionable recommendations for improvement
    """
)
```

## Expected Outcomes

The test-strategist agent will provide:

### For All Test Scopes
- ✅ Test execution summary
- 📊 Pass/fail statistics
- ⏱️ Execution time metrics
- 🐛 Failure debugging if needed

### For Coverage Scope
- 📈 Overall coverage percentage
- 📋 Module-by-module breakdown
- 🎯 Uncovered code identification
- 💡 Specific test recommendations

### For Failed Tests
- 🔍 Root cause analysis
- 🔧 Debugging steps taken
- ✅ Resolution confirmation
- 📝 Prevention recommendations

## Post-Execution Actions

Based on the test-strategist's findings:

1. **If All Tests Pass**:
   - Report success to user
   - Note coverage metrics
   - Highlight any performance concerns

2. **If Tests Fail**:
   - The test-strategist will debug the failures
   - Provide root cause analysis
   - Suggest or implement fixes
   - Re-run tests to confirm resolution

3. **If Coverage Is Low**:
   - Identify specific untested code paths
   - Recommend test additions
   - Prioritize based on code criticality

## Available Test Commands Reference

The test-strategist will execute the appropriate command:
- `uv run pytest tests/` - All tests
- `uv run pytest tests/ --cov=src/ ` - With coverage
- `uv run pytest tests/ -k "not integration"` - Unit tests only
- `uv run pytest tests/ -k "integration"` - Integration tests only
- `uv run pytest --lf` - Failed tests from last run
- `uv run pytest tests/test_specific.py` - Specific file

## Success Criteria

Test execution is successful when:
- ✅ All requested tests execute
- ✅ Results are clearly reported
- ✅ Failures are debugged and explained
- ✅ Coverage meets project standards (>85%)
- ✅ Recommendations are actionable

---
**Remember**: Always delegate to test-strategist. Never run pytest directly in the main conversation.