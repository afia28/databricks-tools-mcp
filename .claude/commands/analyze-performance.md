---
description: Analyze performance using data-engineer agent
argument-hint: [target-module-or-function]
allowed-tools: Task, TodoWrite
---

# Performance Analysis

## 🔥 CRITICAL: MANDATORY DELEGATION

**ALL performance analysis MUST be delegated to the data-engineer agent.**
- The main conversation is for coordination ONLY
- NO direct performance analysis or profiling in main conversation
- The data-engineer has expertise in database optimization, ETL patterns, and performance tuning

## Analysis Target: $1

### 🎯 Delegation to Data Engineer

I will now delegate performance analysis to the data-engineer agent who will:
1. Profile code and database operations
2. Identify bottlenecks
3. Analyze memory usage
4. Recommend optimizations
5. Provide tuning strategies

```python
# Delegating to data-engineer for performance analysis
Task.invoke(
    subagent_type="data-engineer",
    description="Analyze and optimize performance",
    prompt="""Perform comprehensive performance analysis for the databricks-duckdb-replicator project.

    Analysis target: ${1:-entire project}

    PERFORMANCE ANALYSIS TASKS:

    1. SYSTEM RESOURCE ANALYSIS:
       ✓ Check CPU cores and memory available
       ✓ Analyze Python version and dependencies
       ✓ Review system configuration
       ✓ Identify resource constraints

       Commands:
       - python -c "import psutil; print(f'CPU: {psutil.cpu_count()}, RAM: {psutil.virtual_memory().total/(1024**3):.1f}GB')"
       - uv pip list | grep -E "(pandas|duckdb|pyarrow|databricks)"

    2. CODE PERFORMANCE PROFILING:
       ✓ Analyze target module/function: ${1:-all modules}
       ✓ Identify performance-critical code paths
       ✓ Check for inefficient patterns
       ✓ Measure function execution times
       ✓ Analyze algorithmic complexity

       Focus areas:
       - Data transfer methods (replicate_table)
       - Optimization strategies (basic, pandas, parquet, streaming)
       - Chunk processing logic
       - Schema conversion operations

    3. MEMORY USAGE ANALYSIS:
       ✓ Profile memory consumption patterns
       ✓ Identify memory leaks or excessive allocation
       ✓ Analyze object creation/destruction
       ✓ Check garbage collection impact
       ✓ Measure peak memory usage

       Use tracemalloc and memory_profiler:
       ```python
       import tracemalloc
       tracemalloc.start()
       # Code to profile
       current, peak = tracemalloc.get_traced_memory()
       ```

    4. DATABASE PERFORMANCE:
       ✓ Analyze Databricks query performance
       ✓ Profile DuckDB operations
       ✓ Check connection pooling efficiency
       ✓ Measure bulk loading speeds
       ✓ Optimize transaction boundaries

       Key metrics:
       - Rows per second throughput
       - Network latency impact
       - Disk I/O patterns
       - Memory usage during transfers

    5. OPTIMIZATION LEVEL ANALYSIS:
       Compare performance across levels:

       BASIC (executemany):
       - Overhead: High
       - Memory: Low
       - Speed: 2-5x baseline
       - Best for: <100K rows

       PANDAS (DataFrame chunks):
       - Overhead: Medium
       - Memory: Medium
       - Speed: 10-50x baseline
       - Best for: 100K-1M rows

       PARQUET (file-based):
       - Overhead: Low
       - Memory: Medium
       - Speed: 50-100x baseline
       - Best for: 1M-10M rows

       STREAMING (memory-efficient):
       - Overhead: Medium
       - Memory: Constant
       - Speed: 50-100x baseline
       - Best for: >10M rows or limited RAM

    6. BOTTLENECK IDENTIFICATION:
       ✓ Network transfer delays
       ✓ Schema conversion overhead
       ✓ Chunk size inefficiencies
       ✓ Connection establishment costs
       ✓ Temporary file I/O
       ✓ Python GIL impact

    7. OPTIMIZATION RECOMMENDATIONS:

       CHUNK SIZE TUNING:
       Based on data characteristics:
       - Small tables (<10MB): 10,000 rows
       - Medium tables (10MB-1GB): 100,000 rows
       - Large tables (>1GB): 500,000-1,000,000 rows

       MEMORY MANAGEMENT:
       - Use generators for large datasets
       - Implement proper cleanup
       - Configure DuckDB memory limits
       - Use connection pooling

       PARALLEL PROCESSING:
       - Consider multiprocessing for multiple tables
       - Async I/O for network operations
       - Batch processing strategies

    8. BENCHMARKING FRAMEWORK:
       Provide specific benchmark code:
       ```python
       from contextlib import contextmanager
       import time
       import psutil

       @contextmanager
       def performance_monitor(operation_name):
           start_time = time.time()
           start_memory = psutil.Process().memory_info().rss
           yield
           duration = time.time() - start_time
           memory_delta = psutil.Process().memory_info().rss - start_memory
           print(f"{operation_name}: {duration:.2f}s, {memory_delta/1024/1024:.1f}MB")
       ```

    PERFORMANCE REPORT FORMAT:

       📊 PERFORMANCE SUMMARY:
       - Target analyzed: ${1:-entire project}
       - Critical paths identified: X
       - Bottlenecks found: Y
       - Optimization opportunities: Z

       🔍 PROFILING RESULTS:
       [For each critical function]
       - Function: name
       - Current time: Xs
       - Memory usage: YMB
       - Calls: Z times
       - Optimization potential: High/Medium/Low

       🎯 BOTTLENECKS:
       1. [Primary bottleneck]
          - Impact: X% of total time
          - Cause: [description]
          - Solution: [specific fix]

       2. [Secondary bottleneck]
          - Impact: Y% of total time
          - Cause: [description]
          - Solution: [specific fix]

       💡 OPTIMIZATION STRATEGY:

       IMMEDIATE FIXES (Quick wins):
       1. [Specific optimization] - Expected improvement: X%
       2. [Specific optimization] - Expected improvement: Y%

       MEDIUM-TERM IMPROVEMENTS:
       1. [Architectural change] - Expected improvement: X%
       2. [Algorithm optimization] - Expected improvement: Y%

       LONG-TERM ENHANCEMENTS:
       1. [Major refactor] - Expected improvement: X%
       2. [Infrastructure change] - Expected improvement: Y%

       📈 RECOMMENDED SETTINGS:
       ```yaml
       global:
         default_optimization_level: [recommended_level]
         default_chunk_size: [optimal_size]

       # For your data profile:
       # - Average table size: XMB
       # - Row count: Y
       # - Network latency: Zms
       ```

       🧪 BENCHMARK SUITE:
       Provide ready-to-run benchmarks:
       1. Configuration loading benchmark
       2. Schema conversion benchmark
       3. Data transfer benchmark
       4. Memory usage benchmark

    IMPORTANT:
       - Use actual profiling tools (cProfile, memory_profiler)
       - Provide quantitative metrics
       - Focus on actionable improvements
       - Consider trade-offs (speed vs memory)
       - Test recommendations before suggesting
    """
)
```

## Expected Outcomes

The data-engineer will provide:

### Performance Metrics
- 📊 Execution time analysis
- 💾 Memory usage patterns
- 🔄 Throughput measurements
- ⚡ Bottleneck identification

### Optimization Recommendations
- 🎯 Quick wins (immediate fixes)
- 📈 Medium-term improvements
- 🏗️ Long-term architecture changes
- ⚙️ Configuration tuning

### Benchmark Results
- ⏱️ Before/after comparisons
- 📉 Performance graphs
- 🧪 Test scenarios
- 📋 Reproducible benchmarks

### Database Tuning
- 🗄️ Databricks optimizations
- 🦆 DuckDB configurations
- 🔗 Connection pooling
- 📦 Bulk loading strategies

## Post-Analysis Actions

Based on the data-engineer's findings:

1. **If Quick Wins Available**:
   - Implement immediate optimizations
   - Measure performance improvement
   - Document changes
   - Update configuration

2. **If Architectural Issues Found**:
   - Plan refactoring approach
   - Create implementation tasks
   - Estimate improvement potential
   - Schedule changes

3. **If Configuration Tuning Needed**:
   - Update chunk sizes
   - Adjust optimization levels
   - Modify retry settings
   - Test new configuration

## Performance Categories

The data-engineer will analyze:

### Code Performance
- Function execution times
- Algorithm complexity
- Memory allocation patterns
- Python-specific optimizations

### Database Performance
- Query optimization
- Bulk loading efficiency
- Transaction management
- Connection overhead

### Network Performance
- Transfer rates
- Latency impact
- Retry overhead
- Compression benefits

### Memory Performance
- Peak usage
- Allocation patterns
- Garbage collection
- Memory leaks

## Success Criteria

Performance analysis is complete when:
- ✅ All bottlenecks identified
- ✅ Metrics quantified
- ✅ Optimizations prioritized
- ✅ Benchmarks provided
- ✅ Configuration tuned
- ✅ Trade-offs documented
- ✅ Implementation plan ready

## Optimization Levels Reference

The data-engineer will recommend:

| Level | Use Case | Performance | Memory |
|-------|----------|------------|--------|
| basic | <100K rows | 2-5x | Low |
| pandas | 100K-1M rows | 10-50x | Medium |
| parquet | 1M-10M rows | 50-100x | Medium |
| streaming | >10M rows | 50-100x | Constant |

---
**Remember**: Always delegate to data-engineer. Never perform analysis directly in the main conversation.