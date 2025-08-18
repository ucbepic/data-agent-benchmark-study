# Problem Examples

Real data problems where AI tools failed. These help us build better benchmarks.

## How to Read These

Each example shows:
- **Problem**: What someone tried to do
- **Tool**: What they used
- **Failure**: Exactly what went wrong
- **Why**: Root cause (if known)

## Example Problems

### SQL Generation Failures

**Problem**: "Show me top customers by revenue last quarter"  
**Tool**: Claude with database schema  
**Failure**: Used calendar quarter instead of fiscal quarter, ignored currency conversion  
**Why**: No business context about fiscal calendars or multi-currency setup

**Problem**: "Find customers who haven't ordered in 90 days"  
**Tool**: GPT-4 text-to-SQL  
**Failure**: Included test accounts and cancelled orders  
**Why**: No knowledge of data quality rules

### Multi-Database Queries

**Problem**: "Match Salesforce opportunities to Stripe payments"  
**Tool**: LangChain agent with SQL tools  
**Failure**: Pulled entire tables into memory, crashed on 10M rows  
**Why**: No query optimization or pushdown logic

**Problem**: "Compare HR headcount to Finance payroll"  
**Tool**: Custom Python agent  
**Failure**: Different employee ID formats, couldn't match records  
**Why**: No entity resolution strategy

### Business Logic

**Problem**: "Calculate MRR for March 2024"  
**Tool**: ChatGPT Code Interpreter  
**Failure**: Used current subscriptions, not historical state  
**Why**: No understanding of slowly changing dimensions

**Problem**: "Show active users"  
**Tool**: Cursor AI  
**Failure**: Used "last login" instead of "revenue-generating action in 30 days"  
**Why**: No access to business definitions

### Complex Workflows

**Problem**: "For each customer, analyze usage patterns and predict churn"  
**Tool**: AutoGPT-style agent  
**Failure**: Made 800+ API calls, hit rate limits, gave up  
**Why**: No execution planning or state management

**Problem**: "Build weekly executive dashboard"  
**Tool**: GPT-4 with function calling  
**Failure**: Different metrics each run, no consistency  
**Why**: Non-deterministic aggregations

### Data Quality Issues

**Problem**: "Deduplicate customer records"  
**Tool**: Claude with database access  
**Failure**: Merged different people with same name  
**Why**: No fuzzy matching or confidence scoring

**Problem**: "Categorize support tickets"  
**Tool**: GPT-4 API  
**Failure**: Different categories each run  
**Why**: Stochastic classification without consistency

### Compliance Problems

**Problem**: "Average salary by department"  
**Tool**: Text-to-SQL  
**Failure**: Showed individual salaries for small departments  
**Why**: No privacy protection or aggregation rules

**Problem**: "Export customer data for analysis"  
**Tool**: Database chatbot  
**Failure**: Included PII and sensitive fields  
**Why**: No data governance awareness

## Patterns We See

**Common failure modes:**
1. Wrong business logic (fiscal vs calendar, definitions)
2. Scale issues (works on 100 rows, fails on millions)
3. No determinism (different results each run)
4. Missing context (test data, cancelled orders)
5. No state management (can't resume failures)
6. Privacy violations (exposing PII)

## Submit Your Examples

Create a GitHub issue with:
- What you tried
- What failed  
- Any relevant context

We'll add it to our benchmark suite.
