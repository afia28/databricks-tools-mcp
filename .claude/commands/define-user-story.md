---
description: Generate a comprehensive user story from a feature description
argument-hint: [feature-description]
allowed-tools: Read, Glob, Grep, Write, Task, TodoWrite
---

# Define User Story: $1

You are generating a **comprehensive, implementation-ready user story** from the feature description provided by the user.

## 🎯 MISSION

Transform the user's feature idea into a complete user story document that:
- Follows the exact template format of existing stories
- Includes all 10 required sections with detailed content
- Is immediately actionable by `/implement-user-story`
- Passes all quality validation checkpoints

**Feature Description:** `$1`

## 🔥 CRITICAL: MANDATORY DELEGATION

**You MUST delegate ALL story generation work to the story-architect agent.**

This command is for **coordination only**. Do NOT attempt to generate the story yourself.

```python
# ✅ CORRECT - Delegate to story-architect
Task.invoke(
    subagent_type="story-architect",
    description="Generate user story from feature description",
    prompt=f"""Generate a comprehensive user story for this feature:

Feature Description: {feature_description}

Follow the complete story generation workflow:
1. Parse the feature request and identify key requirements
2. Analyze the existing codebase for context
3. Classify the feature and assign appropriate phase
4. Generate story statement (As a... I want... So that...)
5. Create 7-10 testable acceptance criteria
6. Consult python-architect for architecture design
7. Consult test-strategist for test case scenarios
8. Estimate LOC and identify files to create/modify
9. Validate against 12-point quality checklist
10. Save the complete story to user_stories/

Ensure the generated story is:
- Complete (all 10 sections filled)
- Actionable (ready for implementation)
- Specific (no placeholder text)
- Consistent (matches existing story format)
    """
)

# ❌ WRONG - Never generate story directly
# Do NOT use Write tool or attempt story generation
```

## 📋 PRE-GENERATION SETUP

Before delegating to story-architect, prepare context with TodoWrite:

```python
TodoWrite.invoke({
    "todos": [
        {"content": "Parse feature description and extract requirements", "status": "pending", "activeForm": "Parsing feature description"},
        {"content": "Analyze codebase for relevant context", "status": "pending", "activeForm": "Analyzing codebase context"},
        {"content": "Classify feature type and determine phase", "status": "pending", "activeForm": "Classifying feature type"},
        {"content": "Generate user story statement (As a... I want... So that...)", "status": "pending", "activeForm": "Generating user story statement"},
        {"content": "Create acceptance criteria (7-10 items)", "status": "pending", "activeForm": "Creating acceptance criteria"},
        {"content": "Consult python-architect for architecture design", "status": "pending", "activeForm": "Consulting python-architect"},
        {"content": "Consult test-strategist for test scenarios", "status": "pending", "activeForm": "Consulting test-strategist"},
        {"content": "Generate technical requirements and implementation notes", "status": "pending", "activeForm": "Generating technical requirements"},
        {"content": "Identify files to create/modify", "status": "pending", "activeForm": "Identifying files"},
        {"content": "Validate story against 12-point quality checklist", "status": "pending", "activeForm": "Validating story quality"},
        {"content": "Save story to user_stories/ directory", "status": "pending", "activeForm": "Saving story file"},
        {"content": "Update user_stories/README.md with new story", "status": "pending", "activeForm": "Updating README"}
    ]
})
```

## 🚀 EXECUTION WORKFLOW

### Step 1: Validate Feature Description

Check if the feature description is sufficient:

**Good Examples:**
- ✅ "Add query result caching to improve performance for frequently accessed tables"
- ✅ "Implement connection pooling for database connections with configurable pool size"
- ✅ "Add support for Databricks notebook execution via MCP tools"

**Insufficient Examples:**
- ❌ "Make it faster" (too vague - what specifically?)
- ❌ "Add a service" (what kind of service? what does it do?)
- ❌ "Improve the code" (which code? how?)

**If insufficient, ask clarifying questions:**
```
I need more details to create a comprehensive user story. Could you clarify:
1. What specific functionality should be added?
2. Who will use this feature?
3. What problem does it solve?
4. Are there specific requirements or constraints?

For example, instead of "make it faster", consider:
- "Speed up query execution for large tables (>1M rows) using result caching"
- "Reduce workspace connection time from 5s to <1s using connection pooling"
```

### Step 2: Delegate to Story Architect

**Use the Task tool to invoke story-architect agent:**

```python
Task.invoke(
    subagent_type="story-architect",
    description="Generate comprehensive user story",
    prompt=f"""Generate a complete, implementation-ready user story for:

**Feature Description:** $1

**Requirements:**
1. Follow the exact template structure from existing stories
2. Include all 10 sections: Metadata, Overview, User Story, Acceptance Criteria, Technical Requirements, Design Patterns, Implementation Notes, Files, Test Cases, Definition of Done, Expected Outcome
3. Generate 7-10 specific, testable acceptance criteria
4. Consult python-architect for architecture design and patterns
5. Consult test-strategist for comprehensive test scenarios (10-20 tests)
6. Classify feature type and assign appropriate phase (1-6)
7. Auto-generate story ID based on phase and existing stories
8. Estimate LOC based on feature complexity
9. Identify dependencies on existing user stories
10. List specific files to create/modify
11. Validate against 12-point quality checklist
12. Save to user_stories/phase-{{N}}-{{name}}/US-{{phase}}.{{number}}-{{slug}}.md
13. Update user_stories/README.md with new story entry

**Project Context:**
- Study existing stories for format and style
- Use Glob to explore project structure
- Use Grep to find relevant existing code
- Follow Python 3.10+ syntax and typing conventions
- Maintain consistency with existing patterns

**Deliverable:**
Complete user story document saved to user_stories/ directory, ready for implementation via /implement-user-story command.
    """
)
```

The story-architect agent will:
1. ✅ Analyze the feature request
2. ✅ Explore the codebase for context
3. ✅ Classify and assign story ID
4. ✅ Generate complete story with all sections
5. ✅ Consult other agents for expertise
6. ✅ Validate quality
7. ✅ Save story file
8. ✅ Return summary

### Step 3: Review Generated Story

After story-architect completes, review the output:

```python
# The agent will return a summary like:
"""
✅ Story US-2.4 created successfully!

📄 Location: user_stories/phase-2-core/US-2.4-query-caching.md

📊 Story Summary:
- Title: Implement Query Result Caching with TTL
- Phase: Phase 2 - Core Services
- Estimated LOC: ~150 lines
- Dependencies: US-2.3 (Query Executor Service)
- Acceptance Criteria: 8 items
- Test Cases: 15 scenarios

🎯 Quality Validation: ✅ All 12 checkpoints passed

🚀 Ready to implement with:
   /implement-user-story US-2.4
"""
```

### Step 4: Present to User

Show the user what was generated and next steps:

```
✅ **User Story Successfully Generated!**

**Story ID:** US-{phase}.{number}
**Title:** {story-title}
**Location:** `user_stories/phase-{phase}-{name}/US-{phase}.{number}-{slug}.md`

**Summary:**
- **Phase:** Phase {N} - {phase-name}
- **Estimated Complexity:** ~{LOC} lines
- **Acceptance Criteria:** {count} testable requirements
- **Test Cases:** {count} comprehensive scenarios
- **Dependencies:** {list or "None"}

**Quality Validation:** ✅ Passed all 12 checkpoints

**Next Steps:**
1. Review the generated story: `cat {story-path}`
2. Make refinements if needed (you can ask me to modify specific sections)
3. Implement the story: `/implement-user-story {story-id}`

Would you like to:
- 📖 View the complete story
- ✏️ Refine specific sections
- 🚀 Proceed with implementation
```

## 🔍 QUALITY VALIDATION

The story-architect agent will validate against this 12-point checklist:

1. ✅ **Metadata Complete** - All fields (ID, title, phase, LOC, dependencies, status)
2. ✅ **Overview Clear** - 2-3 sentence high-level description
3. ✅ **User Story Format** - Follows "As a... I want... So that..." structure
4. ✅ **Acceptance Criteria** - 7-10 specific, testable requirements
5. ✅ **Technical Requirements** - Concrete implementation details
6. ✅ **Design Patterns** - 2-3 patterns identified with justification
7. ✅ **Implementation Notes** - Best practices, considerations, gotchas
8. ✅ **Files Listed** - Specific paths (not generic placeholders)
9. ✅ **Test Cases** - 10+ detailed test scenarios
10. ✅ **Definition of Done** - Comprehensive checklist (10+ items)
11. ✅ **Expected Outcome** - Usage examples with code
12. ✅ **Dependencies** - Related stories identified

**If any validation fails:**
- Story-architect will attempt to fill gaps automatically
- May ask user for clarification
- Will not save incomplete stories

## 📚 STORY TEMPLATE STRUCTURE

Every generated story includes these 10 sections:

### 1. Metadata
- Story ID (auto-generated)
- Title
- Phase classification
- LOC estimate
- Dependencies
- Status (always "⬜ Not Started")

### 2. Overview
High-level description (2-3 sentences)

### 3. User Story
```markdown
**As a** {role}
**I want** {capability}
**So that** {benefit}
```

### 4. Acceptance Criteria
7-10 specific, testable requirements with ✅ checkboxes

### 5. Technical Requirements
Detailed implementation specifications:
- Classes/functions to create
- Data structures
- Integration approach
- Configuration needs

### 6. Design Patterns Used
2-3 patterns with justification

### 7. Key Implementation Notes
Best practices, security, performance, gotchas

### 8. Files to Create/Modify
Specific file paths organized by create/modify

### 9. Test Cases
10-20 test scenarios with descriptive names

### 10. Definition of Done
Comprehensive checklist (10+ items)

### 11. Expected Outcome
What success looks like with code examples

## 🎯 PHASE CLASSIFICATION

Stories are automatically classified into one of 6 phases:

| Phase | Focus | Examples |
|-------|-------|----------|
| **1: Foundation** | Config, security, RBAC | Pydantic models, workspace config |
| **2: Core** | Infrastructure, DB, utilities | Connection manager, query executor |
| **3: Business** | Domain services, logic | Catalog service, table service |
| **4: Chunking** | Response management | Chunking service, token handling |
| **5: Integration** | MCP tools, refactoring | Tool updates, DI container |
| **6: Quality** | Testing, docs, quality | Test suites, type hints, linting |

## 🔄 REFINEMENT WORKFLOW

If the user wants to refine the generated story:

```
User: "Can you add more detail to the caching strategy section?"

Response:
I'll refine the caching strategy section in US-{phase}.{number}.

[Delegate to story-architect with specific refinement instructions]

Task.invoke(
    subagent_type="story-architect",
    description="Refine caching strategy section",
    prompt="""Refine the user story US-{phase}.{number}:

    Specific refinement: Add more detail to caching strategy

    1. Read current story from user_stories/...
    2. Enhance the caching strategy section with:
       - Different caching strategies (LRU, LFU, TTL-based)
       - Trade-offs for each approach
       - Recommendation with justification
       - Configuration options
    3. Maintain all other sections unchanged
    4. Save updated story
    """
)
```

## ❌ COMMON PITFALLS TO AVOID

### 1. Generating Story Yourself
**❌ DON'T:**
```python
# Attempting to write story content directly
Write.invoke(story_path, story_content)
```

**✅ DO:**
```python
# Delegate to story-architect agent
Task.invoke(subagent_type="story-architect", ...)
```

### 2. Accepting Vague Requests
**❌ DON'T:**
Accept "make it better" without clarification

**✅ DO:**
Ask specific questions about what needs improvement

### 3. Skipping Validation
**❌ DON'T:**
Save story without quality checks

**✅ DO:**
Ensure 12-point validation passes before saving

### 4. Placeholder Content
**❌ DON'T:**
Generate stories with "TODO" or "TBD" sections

**✅ DO:**
Complete all sections with real, actionable content

## 📊 SUCCESS METRICS

The command succeeds when:

1. ✅ Complete story file created in user_stories/
2. ✅ All 10 sections have detailed content
3. ✅ 12-point validation passes
4. ✅ Story is implementation-ready
5. ✅ user_stories/README.md updated
6. ✅ User receives clear summary and next steps

## 🎓 EXAMPLES

### Example 1: Simple Feature

**Command:**
```bash
/define-user-story "Add CLI flag to enable debug logging"
```

**Process:**
1. Delegate to story-architect
2. Agent classifies: Phase 6 (Quality - logging enhancement)
3. Generates: US-6.5-debug-logging.md
4. Returns summary

**Output:**
```
✅ Story US-6.5 created!
📄 user_stories/phase-6-quality/US-6.5-debug-logging.md
🚀 Implement with: /implement-user-story US-6.5
```

### Example 2: Complex Feature

**Command:**
```bash
/define-user-story "Add support for Delta Lake table operations including time travel and table optimization"
```

**Process:**
1. Delegate to story-architect
2. Agent classifies: Phase 3 (Business Services)
3. Consults python-architect for API design
4. Consults test-strategist for comprehensive tests
5. Generates: US-3.5-delta-lake-operations.md
6. Returns detailed summary

### Example 3: Ambiguous Request

**Command:**
```bash
/define-user-story "Make queries faster"
```

**Response:**
```
I need more specifics to create a comprehensive user story. Could you clarify:

1. **What aspect should be faster?**
   - Query execution time?
   - Connection establishment?
   - Result retrieval?

2. **What's the current performance?**
   - e.g., "Queries take 5 seconds"

3. **What's the target performance?**
   - e.g., "Under 1 second"

4. **What causes the slowness?**
   - Large result sets?
   - Repeated queries?
   - Network latency?

**Example specific requests:**
- "Add query result caching to reduce execution time for frequently-run queries"
- "Implement connection pooling to reduce connection overhead"
- "Add pagination for large result sets to improve initial load time"

Please provide more details, and I'll generate a comprehensive story!
```

## 🚀 POST-GENERATION WORKFLOW

After story generation completes:

```mermaid
graph LR
    GEN[Story Generated] --> REVIEW{User Review}
    REVIEW -->|Approve| IMPL[/implement-user-story]
    REVIEW -->|Refine| MOD[Modify Story]
    MOD --> GEN
    IMPL --> EXEC[Execution Framework]
    EXEC --> PROD[Production Ready]

    style GEN fill:#4CAF50,color:#fff
    style IMPL fill:#2196F3,color:#fff
    style PROD fill:#4CAF50,color:#fff
```

**Workflow:**
1. **Story Generated** → User reviews output
2. **User Approves** → Run `/implement-user-story US-X.X`
3. **User Refines** → Modify sections and regenerate
4. **Implementation** → Existing automation takes over
5. **Production** → Feature deployed

## 💡 TIPS FOR BEST RESULTS

### For Users

**Provide clear, specific descriptions:**
- ✅ "Add query result caching with configurable TTL and LRU eviction"
- ❌ "Make queries better"

**Include context when helpful:**
- Mention existing components if relevant
- Note performance requirements
- Specify any constraints

**Review generated stories:**
- Check that acceptance criteria match expectations
- Verify technical approach makes sense
- Confirm test scenarios are comprehensive

### For Story Generation

**The story-architect will:**
- Study existing stories for patterns
- Analyze codebase for context
- Consult expert agents
- Validate quality rigorously
- Provide detailed justifications

**You (coordinator) should:**
- Delegate completely to story-architect
- Validate feature description first
- Present results clearly to user
- Handle refinement requests
- Track progress with TodoWrite

## 🎯 FINAL REMINDERS

1. **ALWAYS delegate to story-architect** - Never generate stories yourself
2. **Validate input** - Ensure feature description is sufficient before proceeding
3. **Track progress** - Use TodoWrite for visibility
4. **Present clearly** - Give user actionable summary
5. **Support refinement** - Make it easy to improve generated stories
6. **Maintain quality** - Never compromise on the 12-point validation

**Goal:** Every generated story should be indistinguishable from manually-crafted stories in quality, completeness, and implementability.

---

**Ready to generate implementation-ready user stories! 📝**
