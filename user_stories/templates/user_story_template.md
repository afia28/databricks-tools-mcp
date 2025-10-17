# US-{PHASE}.{NUMBER}: {TITLE}

## Metadata
- **Story ID**: US-{PHASE}.{NUMBER}
- **Title**: {Descriptive Title}
- **Phase**: Phase {PHASE} - {PHASE_NAME}
- **Estimated LOC**: ~{ESTIMATE} lines
- **Dependencies**: {DEPENDENT_STORIES or "None"}
- **Status**: ⬜ Not Started

## Overview
{2-3 sentence high-level description of what this story delivers. Should be understandable by both technical and non-technical stakeholders.}

## User Story
**As a** {role: developer | analyst | system admin | user}
**I want** {specific capability or feature}
**So that** {concrete benefit or value delivered}

## Acceptance Criteria
1. ✅ {Specific, measurable, testable criterion 1}
2. ✅ {Specific, measurable, testable criterion 2}
3. ✅ {Specific, measurable, testable criterion 3}
4. ✅ {Specific, measurable, testable criterion 4}
5. ✅ {Specific, measurable, testable criterion 5}
6. ✅ {Specific, measurable, testable criterion 6}
7. ✅ {Specific, measurable, testable criterion 7}
8. ✅ {Optional: Additional criteria as needed - aim for 7-10 total}

## Technical Requirements

### {Component/Module 1}
{Detailed specifications including:}
- Classes/functions to create
- Method signatures and return types
- Data structures and types
- Key algorithms or logic
- Integration points

### {Component/Module 2}
{Additional technical details as needed}

### Configuration
{Any configuration requirements:}
- Environment variables
- Settings/options
- Default values
- Validation rules

### Integration Points
{How this integrates with existing code:}
- Which services/modules it depends on
- Which services/modules will use it
- API contracts or interfaces

## Design Patterns Used
- **{Pattern 1}**: {Justification for using this pattern}
- **{Pattern 2}**: {Justification for using this pattern}
- **{Pattern 3}**: {Optional: Additional patterns as needed}

{Common patterns in this project:}
- Repository Pattern - Data access abstraction
- Strategy Pattern - Interchangeable algorithms
- Factory Pattern - Object creation
- Dependency Injection - Loose coupling
- Service Layer - Business logic organization
- Context Manager Protocol - Resource management

## Key Implementation Notes

### Best Practices
- {Practice 1: e.g., Use type hints with Python 3.10+ syntax}
- {Practice 2: e.g., Add comprehensive docstrings with examples}
- {Practice 3: e.g., Follow existing error handling patterns}

### Security Considerations
- {Security note 1: e.g., Never log sensitive credentials}
- {Security note 2: e.g., Validate all inputs}

### Performance Considerations
- {Performance note 1: e.g., Use caching where appropriate}
- {Performance note 2: e.g., Consider batch operations}

### Potential Gotchas
- {Gotcha 1: e.g., Watch out for connection timeouts}
- {Gotcha 2: e.g., Handle edge case where X is empty}

## Files to Create/Modify

### Create
- `{path/to/new/file1.py}` - {Brief description of purpose}
- `{path/to/new/file2.py}` - {Brief description of purpose}
- `{path/to/test/file1.py}` - {Test file for file1}
- `{path/to/test/file2.py}` - {Test file for file2}

### Modify
- `{path/to/existing/file1.py}` - {What changes to make}
- `{path/to/existing/file2.py}` - {What changes to make}
- `{path/to/__init__.py}` - {Update exports}

## Test Cases

### Happy Path Tests
1. **test_{scenario_1}**
   - Input: {Description of input}
   - Expected: {Expected outcome}
   - Assertions: {What to verify}

2. **test_{scenario_2}**
   - Input: {Description of input}
   - Expected: {Expected outcome}
   - Assertions: {What to verify}

### Error Handling Tests
3. **test_{error_scenario_1}**
   - Input: {Description of invalid input}
   - Expected: {Expected exception or error}
   - Assertions: {What to verify}

4. **test_{error_scenario_2}**
   - Input: {Description of invalid input}
   - Expected: {Expected exception or error}
   - Assertions: {What to verify}

### Edge Case Tests
5. **test_{edge_case_1}**
   - Input: {Description of edge case}
   - Expected: {Expected behavior}
   - Assertions: {What to verify}

6. **test_{edge_case_2}**
   - Input: {Description of edge case}
   - Expected: {Expected behavior}
   - Assertions: {What to verify}

### Integration Tests
7. **test_{integration_scenario_1}**
   - Setup: {What needs to be set up}
   - Action: {What operation to perform}
   - Expected: {Expected end-to-end result}
   - Assertions: {What to verify}

8. **test_{integration_scenario_2}**
   - Setup: {What needs to be set up}
   - Action: {What operation to perform}
   - Expected: {Expected end-to-end result}
   - Assertions: {What to verify}

{Continue with additional test cases - aim for 10-20 total covering all acceptance criteria}

## Definition of Done

- [ ] All classes/functions implemented with type hints
- [ ] All methods have comprehensive docstrings (Google style)
- [ ] All acceptance criteria met and verified
- [ ] All test cases passing (10+ tests minimum)
- [ ] Test coverage ≥90% for new code
- [ ] Code passes `ruff check` linting
- [ ] Code formatted with `ruff format`
- [ ] Type checking passes with `mypy --strict`
- [ ] No breaking changes to existing functionality
- [ ] Integration with existing services verified
- [ ] Error handling comprehensive and tested
- [ ] Logging added at appropriate levels
- [ ] Package exports updated (`__init__.py` files)
- [ ] Documentation updated (docstrings, examples)
- [ ] No TODO or placeholder comments remaining
- [ ] Code reviewed and approved
- [ ] All pre-commit hooks passing

## Expected Outcome

### What Success Looks Like
{Description of the end state after this story is complete. Include:}
- What new capabilities are available
- How the system behaves differently
- What users can now do
- Performance improvements (if applicable)

### Usage Example
```python
# Example of how the new feature will be used
from {module} import {Class or Function}

# Setup
{setup_code}

# Usage
result = {usage_example}

# Expected result
assert result == {expected_value}
```

### Example Scenario
```python
# Realistic scenario demonstrating the feature
{scenario_code_showing_practical_usage}
```

## Related User Stories
- **Depends on**: {List of stories that must be completed first}
- **Blocks**: {List of stories that depend on this one}
- **Related to**: {List of related but not dependent stories}

## Notes
{Any additional context, decisions made, alternatives considered, or future enhancements to consider}

---

**Template Version**: 1.0
**Last Updated**: 2025-10-16
**Template maintained by**: story-architect agent
