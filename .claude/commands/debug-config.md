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
    prompt="""Debug configuration issues for the databricks-duckdb-replicator project.

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
       ✓ Load configuration through ConfigManager
       ✓ Validate against Pydantic models
       ✓ Check required fields presence
       ✓ Validate field types and constraints
       ✓ Test enum values (optimization_level)

       Use: from databricks_duckdb_replicator.core.config import ConfigManager

    4. ENVIRONMENT VARIABLES:
       ✓ Check DATABRICKS_SERVER_HOSTNAME
       ✓ Check DATABRICKS_HTTP_PATH
       ✓ Check DATABRICKS_ACCESS_TOKEN
       ✓ Verify LOG_LEVEL if set
       ✓ Check for .env file presence

       Provide exact commands to set missing variables

    5. CONNECTIVITY VALIDATION:
       ✓ Test Databricks configuration loading
       ✓ Verify server hostname format
       ✓ Check HTTP path format
       ✓ Validate access token presence
       ✓ Test actual connection if possible

    6. FILE SYSTEM VALIDATION:
       ✓ Check DuckDB path accessibility
       ✓ Verify parent directory exists
       ✓ Check write permissions
       ✓ Handle :memory: special case
       ✓ Suggest path corrections if needed

    7. TABLE CONFIGURATION:
       ✓ Validate each table entry
       ✓ Check catalog.schema.table format
       ✓ Verify optimization levels
       ✓ Check chunk size ranges (1000-10000000)
       ✓ Validate enabled/disabled flags

    8. COMMON ISSUES CHECK:
       ✓ Reserved keywords in table names
       ✓ Special characters in names
       ✓ Duplicate table definitions
       ✓ Circular dependencies
       ✓ Invalid retry configurations

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
       export DATABRICKS_SERVER_HOSTNAME="your-workspace.cloud.databricks.com"
       export DATABRICKS_HTTP_PATH="/sql/1.0/warehouses/your-warehouse-id"
       export DATABRICKS_ACCESS_TOKEN="your-token"
       ```

       For YAML syntax errors:
       ```yaml
       # Correct indentation example
       global:
         duckdb_path: "./data.duckdb"  # 2 spaces indent
         default_optimization_level: "pandas"
       ```

       For permission issues:
       ```bash
       chmod 644 config.yaml
       mkdir -p $(dirname "./replicated_data.duckdb")
       chmod 755 $(dirname "./replicated_data.duckdb")
       ```

    VALIDATION TESTS:
       After fixes, run these tests:
       1. Load configuration successfully
       2. Parse all table definitions
       3. Validate against schema
       4. Test connectivity (if credentials present)

    SAMPLE VALID CONFIGURATION:
       Provide a minimal working example:
       ```yaml
       global:
         duckdb_path: ":memory:"
         default_optimization_level: "pandas"
         default_chunk_size: 100000
         log_level: "INFO"

       tables:
         - name: "sample_table"
           source:
             catalog: "main"
             schema: "default"
             table: "customers"
           enabled: true
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
   - Proceed with replication
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
- Missing Databricks credentials
- Invalid connection strings
- Permission problems
- Path resolution

### Configuration Issues
- Invalid table names
- Wrong optimization levels
- Out-of-range chunk sizes
- Disabled tables

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
- ✅ Databricks connection works
- ✅ Tables properly configured
- ✅ Ready for replication

---
**Remember**: Always delegate to devops-config. Never debug configuration directly in the main conversation.