# Documentation Guidelines for databricks-tools

This document provides comprehensive guidelines for creating, organizing, and maintaining documentation in the databricks-tools project.

## Table of Contents
- [Directory Structure](#directory-structure)
- [File Placement Rules](#file-placement-rules)
- [Naming Conventions](#naming-conventions)
- [Content Guidelines](#content-guidelines)
- [Markdown Style Guide](#markdown-style-guide)
- [When to Update Which Files](#when-to-update-which-files)

## Directory Structure

```
databricks-tools-clean/
├── README.md                     # Primary documentation (root only)
├── CHANGELOG.md                  # Version history (root only)
├── CLAUDE.md                     # Claude Code instructions (root only)
│
├── docs/                         # All other documentation goes here
│   ├── guides/                   # User-facing guides
│   │   ├── INSTALLATION.md      # End-user installation guide
│   │   ├── PROJECT_SETUP.md     # Developer setup guide
│   │   └── *.md                 # Future guides
│   │
│   ├── architecture/             # Technical design docs
│   │   ├── ARCHITECTURE.md      # System architecture
│   │   └── *.md                 # Future architecture docs
│   │
│   └── development/              # Internal dev docs
│       ├── USER_STORY_FRAMEWORK.md
│       ├── USER_STORY_AUTOMATION_WALKTHROUGH.md
│       ├── ROLES.md
│       ├── IMPLEMENTATION_SUMMARY.md
│       └── *.md                 # Future dev docs
│
├── examples/                     # Executable code examples
│   ├── basic_usage.py
│   ├── advanced_queries.py
│   ├── custom_service.py
│   └── testing_example.py
│
└── .claude/                      # Claude Code configuration
    ├── commands/                 # Slash command definitions
    ├── agents/                   # Subagent definitions
    ├── commands.md               # Commands documentation
    ├── subagents.md              # Subagents documentation
    └── DOCUMENTATION_GUIDELINES.md  # This file
```

## File Placement Rules

### Root Directory Files (ONLY These Three)
**Keep the root directory clean with only essential project-level files:**

1. **README.md**
   - Primary entry point for the project
   - Quick start guide and overview
   - Links to detailed documentation
   - Installation instructions summary
   - Key features and capabilities

2. **CHANGELOG.md**
   - Version history
   - Release notes
   - Breaking changes
   - Migration guides

3. **CLAUDE.md**
   - Claude Code instructions
   - Project structure overview
   - Quick commands reference
   - Development workflow
   - User story tracking

### docs/ Directory Rules

#### docs/guides/ - User-Facing Documentation
**Purpose:** Help users and developers get started and accomplish tasks

**Place here:**
- Installation guides
- Getting started tutorials
- How-to guides
- Troubleshooting guides
- Best practices guides
- API usage guides
- Configuration guides

**Examples:**
- `INSTALLATION.md` - End-user installation steps
- `PROJECT_SETUP.md` - Developer environment setup
- `QUICK_START.md` - Fast path to first success
- `TROUBLESHOOTING.md` - Common problems and solutions
- `CONFIGURATION.md` - Configuration options

#### docs/architecture/ - Technical Design Documentation
**Purpose:** Explain system design, architecture, and technical decisions

**Place here:**
- System architecture documents
- Design pattern explanations
- Component diagrams
- Data flow diagrams
- API design documents
- Database schemas
- Performance considerations
- Security architecture

**Examples:**
- `ARCHITECTURE.md` - Overall system design
- `DATABASE_DESIGN.md` - Schema and data models
- `API_DESIGN.md` - API structure and patterns
- `SECURITY.md` - Security architecture and practices
- `PERFORMANCE.md` - Performance optimization strategies

#### docs/development/ - Internal Development Documentation
**Purpose:** Guide development team processes and workflows

**Place here:**
- User story frameworks
- Development workflows
- Coding standards
- Testing strategies
- Review processes
- Implementation summaries
- Team roles and responsibilities
- Onboarding guides

**Examples:**
- `USER_STORY_FRAMEWORK.md` - Story creation process
- `USER_STORY_AUTOMATION_WALKTHROUGH.md` - Automation guide
- `ROLES.md` - Team member responsibilities
- `IMPLEMENTATION_SUMMARY.md` - Feature implementation summaries
- `CODING_STANDARDS.md` - Code style and conventions
- `TESTING_GUIDE.md` - Testing approaches

### examples/ Directory Rules
**Purpose:** Provide executable code demonstrating project usage

**Place here:**
- Working Python scripts
- Usage demonstrations
- Integration examples
- Testing examples
- Pattern examples

**Requirements:**
- All code must be executable
- Include docstrings and comments
- Show realistic use cases
- Follow project coding standards

**Examples:**
- `basic_usage.py` - Simple operations
- `advanced_queries.py` - Complex scenarios
- `custom_service.py` - Extension patterns
- `testing_example.py` - Testing approaches

### .claude/ Directory Rules
**Purpose:** Claude Code configuration and instructions

**Place here:**
- Slash command definitions (`.claude/commands/`)
- Subagent definitions (`.claude/agents/`)
- Commands documentation (`commands.md`)
- Subagents documentation (`subagents.md`)
- Documentation rules (this file)
- Settings and preferences

**Do NOT place here:**
- User-facing documentation
- Architecture documents
- Code examples
- Development guides

## Naming Conventions

### File Names
- Use **SCREAMING_SNAKE_CASE** for `.md` files (e.g., `USER_STORY_FRAMEWORK.md`)
- Use **snake_case** for `.py` files (e.g., `basic_usage.py`)
- Be descriptive and specific
- Avoid abbreviations unless widely understood

### Good Examples
- `INSTALLATION.md` - Clear purpose
- `USER_STORY_FRAMEWORK.md` - Specific and descriptive
- `advanced_queries.py` - Clear what it demonstrates

### Bad Examples
- `doc.md` - Too vague
- `guide1.md` - Non-descriptive
- `tmp.py` - Temporary, unclear purpose
- `USF.md` - Unclear abbreviation

## Content Guidelines

### Markdown Structure
Every `.md` file should include:

1. **Title** (H1)
   ```markdown
   # Document Title
   ```

2. **Table of Contents** (for files >200 lines)
   ```markdown
   ## Table of Contents
   - [Section 1](#section-1)
   - [Section 2](#section-2)
   ```

3. **Introduction**
   - Purpose of the document
   - Target audience
   - Prerequisites (if any)

4. **Main Content**
   - Organized with clear headings
   - Use examples liberally
   - Include code blocks with syntax highlighting

5. **References/Links** (if applicable)
   - Related documentation
   - External resources

### Code Blocks
Always specify the language for syntax highlighting:

```markdown
```python
def example():
    return "Use syntax highlighting"
\```
```

```markdown
```bash
uv run pytest tests/
\```
```

### Links
- Use relative links for internal documentation
- Use absolute URLs for external resources
- Verify all links work

**Examples:**
```markdown
See [Architecture](../architecture/ARCHITECTURE.md) for details.
Visit [Python Docs](https://docs.python.org/3/) for more info.
```

## Markdown Style Guide

### Headers
- Use ATX-style headers (`#` not `===`)
- One blank line before and after headers
- No trailing punctuation in headers

```markdown
## Good Header

Content here.

### Subsection

More content.
```

### Lists
- Use `-` for unordered lists
- Use `1.` for ordered lists
- Indent nested lists by 2 spaces

```markdown
- Item 1
  - Nested item
- Item 2

1. First step
2. Second step
   - Additional detail
```

### Code Formatting
- Use backticks for inline code: `variable_name`
- Use triple backticks for code blocks
- Always specify language for code blocks

### Emphasis
- Use `**bold**` for strong emphasis
- Use `*italic*` for mild emphasis
- Use `**_bold italic_**` for both

### Tables
- Use proper alignment
- Include header separator

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
```

## When to Update Which Files

### When to Update README.md
- Adding new major features
- Changing installation process
- Updating quick start guide
- Adding/removing key dependencies
- Changing project description

### When to Update CHANGELOG.md
- Every version release
- Adding new features (Added)
- Fixing bugs (Fixed)
- Breaking changes (Changed)
- Removing features (Removed)

### When to Update CLAUDE.md
- Adding new source files
- Adding new tests
- Completing user stories
- Changing project structure
- Updating development workflow
- Adding new commands or tools

### When to Create New Documentation
Create documentation in `docs/` when:
- Implementing a new major feature (→ `docs/guides/`)
- Making architectural changes (→ `docs/architecture/`)
- Establishing new processes (→ `docs/development/`)
- Creating reusable examples (→ `examples/`)

## Best Practices

### DO
✅ Keep root directory clean (only 3 `.md` files)
✅ Use descriptive file names
✅ Include table of contents for long docs
✅ Use code examples liberally
✅ Keep documentation in sync with code
✅ Use relative links for internal docs
✅ Verify all links work
✅ Include prerequisites
✅ Specify target audience

### DON'T
❌ Put documentation in root directory
❌ Use vague file names
❌ Write documentation without code examples
❌ Let documentation go stale
❌ Use absolute paths for internal links
❌ Assume reader knowledge
❌ Skip table of contents for long docs
❌ Forget syntax highlighting on code blocks

## Migration Checklist

When reorganizing documentation:

- [ ] Move files to appropriate directories
- [ ] Update all internal links
- [ ] Update CLAUDE.md with new paths
- [ ] Update README.md with new paths
- [ ] Verify all links work
- [ ] Update CHANGELOG.md with reorganization
- [ ] Test examples still work
- [ ] Update pyproject.toml (exclude docs/)
- [ ] Commit with clear message

## Questions?

When unsure where to place documentation:

1. **Is it for end users?** → `docs/guides/`
2. **Is it about system design?** → `docs/architecture/`
3. **Is it for developers/team?** → `docs/development/`
4. **Is it executable code?** → `examples/`
5. **Is it project-wide?** → Update root files (README, CHANGELOG, CLAUDE)
6. **Is it Claude-specific?** → `.claude/`

Still unsure? Ask the team or refer to existing similar documentation.

## Summary

The key principle is: **Keep the root directory clean**. Only README.md, CHANGELOG.md, and CLAUDE.md belong in the root. Everything else goes into organized subdirectories based on purpose and audience.

This structure ensures:
- Easy navigation
- Clear organization
- Professional appearance
- Scalable documentation
- Maintainable structure
