---
description: Debug configuration issues using devops-config agent
argument-hint: [config-file-path]
allowed-tools: Task, TodoWrite
---

# Configuration Debugging

## 🔥 CRITICAL: MANDATORY DELEGATION

**ALL configuration debugging MUST be delegated to the devops-config agent.**
- The main conversation is for coordination ONLY
- NO direct configuration validation or debugging in main conversation
- The devops-config agent has expertise in YAML, environment setup, and configuration management

## Configuration File: $1

### 🎯 Delegation to DevOps Config Agent

I will now delegate configuration debugging to the devops-config agent who will:
1. Validate YAML syntax and structure
2. Check environment variables
3. Test connectivity
4. Diagnose issues
5. Provide fixes and recommendations

```python
# Delegating to devops-config for configuration debugging
Task.invoke(
    subagent_type="devops-config",
    description="Debug and fix configuration issues",
    prompt="""Debug configuration issues for this project.

    Configuration file to debug: ${1:-config.yaml}

    DEBUGGING TASKS:

    1. FILE VALIDATION:
       ✓ Check if configuration file exists
       ✓ Verify file permissions (readable)
       ✓ Check file format and extension
       ✓ Validate file encoding (UTF-8)

    2. YAML SYNTAX VALIDATION:
       ✓ Parse YAML for syntax errors
       ✓ Check indentation (spaces vs tabs)
       ✓ Validate structure (lists, dicts, scalars)
       ✓ Identify line numbers for any errors

       Use: python -c "import yaml; yaml.safe_load(open('${1:-config.yaml}'))"

    3. PYDANTIC MODEL VALIDATION:
       ✓ Load configuration through appropriate config manager
       ✓ Validate against Pydantic models
       ✓ Check required fields presence
       ✓ Validate field types and constraints
       ✓ Test enum values if applicable

       Use: from [project_module].config import ConfigManager (adjust based on project structure)

    4. ENVIRONMENT VARIABLES:
       ✓ Check required environment variables
       ✓ Verify LOG_LEVEL if set
       ✓ Check for .env file presence
       ✓ Validate environment variable formats

       Provide exact commands to set missing variables

    5. CONNECTIVITY VALIDATION:
       ✓ Test configuration loading
       ✓ Verify connection string formats
       ✓ Validate credentials presence
       ✓ Test actual connection to external services if possible

    6. FILE SYSTEM VALIDATION:
       ✓ Check file path accessibility
       ✓ Verify parent directory exists
       ✓ Check write permissions
       ✓ Handle special cases (e.g., :memory:)
       ✓ Suggest path corrections if needed

    7. APPLICATION CONFIGURATION:
       ✓ Validate each configuration entry
       ✓ Check naming conventions
       ✓ Verify configuration values
       ✓ Check value ranges if applicable
       ✓ Validate feature flags and settings

    8. COMMON ISSUES CHECK:
       ✓ Reserved keywords in identifiers
       ✓ Special characters in names
       ✓ Duplicate definitions
       ✓ Circular dependencies
       ✓ Invalid retry/timeout configurations

    DIAGNOSTIC OUTPUT FORMAT:

       🔍 CONFIGURATION ANALYSIS:
       File: ${1:-config.yaml}
       Status: Valid/Invalid
       Issues Found: X

       ✅ PASSED CHECKS:
       - [List all successful validations]

       ❌ FAILED CHECKS:
       [For each failure]
       - Issue: Description
       - Location: Line X, Column Y (if applicable)
       - Error: Exact error message
       - Fix: Specific solution

       ⚠️ WARNINGS:
       - [Non-critical issues]
       - [Optimization suggestions]
       - [Best practice violations]

       🔧 AUTOMATIC FIXES APPLIED:
       - [List any fixes made]

       📋 MANUAL FIXES REQUIRED:
       [For each manual fix]
       - Step 1: [Specific action]
       - Step 2: [Specific command or edit]
       - Verification: [How to verify fix worked]

       💡 RECOMMENDATIONS:
       1. [Priority improvement 1]
       2. [Priority improvement 2]
       3. [Priority improvement 3]

    EXAMPLE FIXES TO PROVIDE:

       For missing environment variables:
       ```bash
       export REQUIRED_ENV_VAR="your-value-here"
       export OPTIONAL_ENV_VAR="optional-value"
       # Add application-specific environment variables as needed
       ```

       For YAML syntax errors:
       ```yaml
       # Correct indentation example
       global:
         setting_one: "value1"  # 2 spaces indent
         setting_two: "value2"
       ```

       For permission issues:
       ```bash
       chmod 644 config.yaml
       mkdir -p $(dirname "./data/output.db")
       chmod 755 $(dirname "./data/output.db")
       ```

    VALIDATION TESTS:
       After fixes, run these tests:
       1. Load configuration successfully
       2. Parse all configuration entries
       3. Validate against schema
       4. Test connectivity to external services (if credentials present)

    SAMPLE VALID CONFIGURATION:
       Provide a minimal working example:
       ```yaml
       global:
         log_level: "INFO"
         setting_one: "value1"
         setting_two: 100000

       items:
         - name: "sample_item"
           enabled: true
           # Add application-specific fields
       ```

    IMPORTANT:
       - Fix auto-fixable issues immediately
       - Provide exact commands for manual fixes
       - Test fixes before reporting success
       - Focus on getting configuration working
       - Be specific about error locations
    """
)
```

## Expected Outcomes

The devops-config agent will provide:

### Diagnostic Results
- 🔍 Complete configuration analysis
- ✅ List of passed validations
- ❌ Detailed error descriptions
- ⚠️ Warnings and recommendations

### Automatic Fixes
- 🔧 YAML formatting corrections
- 📝 Missing field additions
- 🔄 Type conversions
- ✏️ Simple syntax fixes

### Manual Fix Instructions
- 📋 Step-by-step solutions
- 💻 Exact commands to run
- 📁 File edits required
- ✓ Verification steps

### Environment Setup
- 🔑 Environment variable commands
- 📄 .env file template
- 🔗 Connection string formats
- 🛡️ Security best practices

## Post-Debugging Actions

Based on the devops-config agent's findings:

1. **If Configuration Is Valid**:
   - Proceed with application execution
   - Note any warnings for future improvement
   - Document configuration for team

2. **If Auto-Fixes Applied**:
   - Review the changes
   - Test configuration loading
   - Verify connectivity
   - Run dry-run to confirm

3. **If Manual Fixes Required**:
   - Follow step-by-step instructions
   - Set environment variables as directed
   - Edit configuration file as specified
   - Re-run debugging to verify

## Common Issues Reference

The devops-config agent will handle:

### YAML Issues
- Indentation errors
- Invalid syntax
- Type mismatches
- Missing required fields

### Environment Issues
- Missing service credentials
- Invalid connection strings
- Permission problems
- Path resolution

### Configuration Issues
- Invalid configuration entries
- Wrong optimization levels
- Out-of-range parameter values
- Disabled features

### Connectivity Issues
- Network problems
- Authentication failures
- Firewall blocks
- SSL/TLS errors

## Success Criteria

Configuration debugging is successful when:
- ✅ YAML parses without errors
- ✅ Pydantic validation passes
- ✅ All environment variables set
- ✅ File paths accessible
- ✅ External service connections work
- ✅ Configuration entries properly validated
- ✅ Ready for application execution

---
**Remember**: Always delegate to devops-config. Never debug configuration directly in the main conversation.
