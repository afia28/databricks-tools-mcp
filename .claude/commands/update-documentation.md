---
description: Update all project documentation, commit changes, and push to complete user story
argument-hint: "[commit-hash]"
allowed-tools: Bash, Read, Edit, MultiEdit, Glob, Grep
---

# Complete User Story: Update Documentation, Commit, and Push

This command is the **final step** in implementing a user story. It updates all project documentation, commits all changes with a detailed message, pushes to the remote repository, and optionally creates a pull request for merging to main.

## What This Command Does

1. **Analyzes All Changes**: Reviews git status and diff to understand what was implemented
2. **Updates Documentation**:
   - README.md with new features and usage examples
   - CLAUDE.md with status updates and metrics
   - Command and subagent documentation
3. **Commits Changes**: Creates detailed commit messages following conventional commits
4. **Pushes to Remote**: Pushes all commits to the remote repository
5. **Creates PR if Needed**: Optionally creates a pull request for review
6. **Merges to Main**: Completes the user story by merging approved changes

## Usage

```bash
# Update documentation after latest changes
/update-documentation

# Update documentation for a specific commit
/update-documentation abc123f
```

## Execution Flow

### Step 1: Analyze Recent Changes
```bash
# Get the latest commit or specified commit
! git log -1 --stat $(if [ -n "$1" ]; then echo $1; else echo HEAD; fi)

# Get detailed diff of changes
! git diff $(if [ -n "$1" ]; then echo "$1^..$1"; else echo "HEAD^..HEAD"; fi) --name-status

# Check for new test files
! find tests/ -name "*.py" -type f | wc -l
```

### Step 2: Review Current Documentation
Read and analyze current state of:
- README.md
- CLAUDE.md
- .claude/commands.md
- .claude/subagents.md

### Step 3: Update README.md
Update sections based on changes:
- Features list if new capabilities were added
- Python Library Usage if new functions were exported
- Project Structure if new files were added
- Running Tests section if test files were added

### Step 4: Update CLAUDE.md
Update key sections:
- Current Status (mark completed tasks)
- Project Structure diagram
- Recent Accomplishments (add new completed features)
- Code Quality Metrics (update test counts and coverage)
- Next Steps (remove completed items, add new ones)

### Step 5: Update Command Documentation
If new commands were added, update:
- .claude/commands.md with new command description
- CLAUDE.md command list section

### Step 6: Verify Documentation Consistency
Check that all documentation is consistent:
- File paths are correct
- Test counts match actual tests
- Feature descriptions align
- No outdated information remains

## 🚀 GIT WORKFLOW - COMMIT AND PUSH

### Step 7: Check Git Status and Stage Changes
```bash
# Check all modified and new files
! git status

# Review all changes to be committed
! git diff --staged

# Stage all changes if not already staged
! git add -A

# Show final status before commit
! git status --short
```

### Step 8: Generate Detailed Commit Message
Create a comprehensive commit message following conventional commits format:

```bash
# Analyze changes to generate commit message
! git diff --staged --stat

# Generate commit message based on:
# - User story ID (if from /implement-user-story)
# - Type of change (feat/fix/docs/test/refactor)
# - Scope of change (core/utils/tests/config)
# - Description of what was done
# - Breaking changes if any
# - Related issues or user stories
```

Example commit message format:
```
feat(core): implement comprehensive table utilities (US-2.3)

- Added 7 table utility functions for validation and transformation
- Implemented TableReference class with full Databricks/DuckDB conversion
- Added comprehensive test suite with 98% coverage
- Updated documentation and exports

Tests: 173 tests passing
Coverage: 89% overall
Breaking: None
```

### Step 9: Commit All Changes
```bash
# Commit with detailed message
! git commit -m "feat: [description based on implementation]

[Detailed bullet points of what was changed]

Tests: [test count and status]
Coverage: [coverage percentage]
User Story: [story ID if applicable]"

# Verify commit was successful
! git log -1 --oneline
```

### Step 10: Push to Remote Repository
```bash
# Get current branch name
! git branch --show-current

# Push to remote (with upstream if new branch)
! git push origin $(git branch --show-current) || git push -u origin $(git branch --show-current)

# Show push result
! git log origin/$(git branch --show-current)..HEAD --oneline
```

### Step 11: Create Pull Request (if on feature branch)
If not on main branch, create a pull request:

```bash
# Check if we're on a feature branch
! if [ "$(git branch --show-current)" != "main" ]; then
    echo "📝 Creating pull request..."
    # Using GitHub CLI if available
    gh pr create --title "feat: [User Story Title]" \
                 --body "## Summary

                 Implements [user story/feature description]

                 ## Changes
                 - [List key changes]

                 ## Testing
                 - All tests passing
                 - Coverage: X%

                 ## Documentation
                 - README updated
                 - CLAUDE.md updated" \
                 --base main || echo "Please create PR manually on GitHub"
else
    echo "✅ Already on main branch"
fi
```

### Step 12: Merge to Main (if applicable)
If PR is approved or working directly on main:

```bash
# If on feature branch and ready to merge
! if [ "$(git branch --show-current)" != "main" ]; then
    echo "🔀 Ready to merge to main"
    echo "Options:"
    echo "1. Merge via GitHub PR interface (recommended)"
    echo "2. Local merge: git checkout main && git merge $(git branch --show-current)"
    echo "3. Fast-forward: git checkout main && git merge --ff-only $(git branch --show-current)"
else
    echo "✅ Changes committed to main branch"
fi

# Final status
! git status
! echo "✅ User story implementation complete!"
```

## Integration with implement-user-story

This command is **automatically called** at the end of `/implement-user-story` to:
1. Update all documentation
2. Commit all changes with detailed message
3. Push to remote repository
4. Create PR if needed
5. Complete the user story workflow

## Complete Workflow Example

```
📚 Documentation Update and Git Workflow
=========================================

Step 1: Analyzing changes...
✅ Found 15 modified files
✅ Found 5 new test files

Step 2: Updating documentation...
✅ Updated README.md:
   - Added table utility functions to features
   - Updated usage examples
   - Updated project structure

✅ Updated CLAUDE.md:
   - Marked Task 2.3 as complete
   - Updated test count: 173 tests
   - Updated coverage: 89%

Step 3: Preparing commit...
✅ Staged 20 files for commit

Step 4: Committing changes...
✅ Created commit: feat(utils): implement table utilities (US-2.3)

Step 5: Pushing to remote...
✅ Pushed to origin/main

Step 6: User Story Complete!
✅ All documentation updated
✅ All changes committed
✅ Code pushed to repository
✅ Ready for next user story

🎉 User Story US-2.3 Successfully Completed!
```

## Error Handling

The command handles various scenarios:
- **Uncommitted changes**: Stages and includes them
- **Merge conflicts**: Provides resolution guidance
- **Push failures**: Offers troubleshooting steps
- **PR creation issues**: Falls back to manual instructions

## Best Practices

1. **Always run after /implement-user-story** to complete the workflow
2. **Review changes** before the commit is created
3. **Ensure tests pass** before running this command
4. **Write meaningful commit messages** that reference the user story
5. **Create PRs for review** when working in teams
6. **Keep documentation synchronized** with code changes

## Command Integration

This command integrates with the full workflow:

```mermaid
graph LR
    A[/implement-user-story] --> B[/run-tests]
    B --> C[/validate-implementation]
    C --> D[/lint]
    D --> E[/update-documentation]
    E --> F[Complete!]
```

The `/update-documentation` command is the **final step** that:
- Ensures all documentation is current
- Commits all work with proper attribution
- Pushes changes to the repository
- Completes the user story lifecycle