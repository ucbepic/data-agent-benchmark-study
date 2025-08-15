# Text-to-SQL Architecture

## Overview

This technique directly converts natural language questions into SQL queries using large language models. The model is trained or prompted to understand database schemas and generate executable SQL without intermediate tool calls or agent planning.

## Core Components

```ascii
┌─────────────────────────────────────────────────────────────┐
│                     Benchmark Question                      │
│            "Show me top customers by revenue"               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Text-to-SQL Model                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Schema Context                         │  │
│  │  - Table definitions and relationships               │  │
│  │  - Column names, types, and constraints              │  │
│  │  - Sample data for understanding                     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Query Generation                      │  │
│  │  - Natural language → SQL conversion                 │  │
│  │  - Syntax validation and optimization                │  │
│  │  - Error handling and retry logic                    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Database Engine                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Query Execution                       │  │
│  │  - SQL parsing and optimization                      │  │
│  │  - Result set generation                             │  │
│  │  - Error reporting and handling                      │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Results Formatter                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Output Processing                     │  │
│  │  - Data formatting and presentation                  │  │
│  │  - Chart generation and visualization                │  │
│  │  - Natural language explanation                      │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. Schema Understanding
The model receives comprehensive database schema information:

```sql
-- Schema context provided to model
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    amount DECIMAL(10,2) NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending'
);

-- Sample data for context
INSERT INTO customers VALUES (1, 'John Doe', 'john@example.com', '2024-01-01', 'active');
INSERT INTO orders VALUES (1, 1, 150.00, '2024-01-15', 'completed');
```

### 2. Query Generation Process

```ascii
1. User Input: "Show me top customers by revenue"
              ↓
2. Schema Context Injection:
   - Table definitions
   - Column descriptions
   - Sample data
   - Business rules
              ↓
3. Prompt Construction:
   "Given this schema: [SCHEMA]
    Generate SQL for: [QUESTION]
    Requirements: [CONSTRAINTS]"
              ↓
4. Model Generation:
   - Analyzes question intent
   - Maps to schema elements
   - Generates SQL syntax
   - Validates query structure
              ↓
5. SQL Output:
   SELECT c.name, SUM(o.amount) as revenue
   FROM customers c
   JOIN orders o ON c.id = o.customer_id
   WHERE o.status = 'completed'
   GROUP BY c.id, c.name
   ORDER BY revenue DESC
   LIMIT 10;
              ↓
6. Execution & Results
```

### 3. Multi-Database Support

```ascii
┌────────────────────────────────────────────────────────────┐
│                    Text-to-SQL Engine                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ PostgreSQL  │ │   MongoDB   │ │   MySQL     │          │
│  │   Adapter   │ │   Adapter   │ │   Adapter   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└────────────────────┬───────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬─────────────┐
        │            │            │             │
        ▼            ▼            ▼             ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│PostgreSQL│ │ MongoDB  │ │  MySQL   │ │  SQLite  │
│    DB    │ │    DB    │ │    DB    │ │    DB    │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

## Key Capabilities

### Schema-Aware Generation
- **Table Relationships**: Understands foreign keys and joins
- **Data Types**: Generates appropriate type handling
- **Constraints**: Respects NOT NULL, UNIQUE, CHECK constraints
- **Indexes**: Optimizes for indexed columns when possible

### Query Types Supported
| Query Type | Example | Generated SQL |
|------------|---------|---------------|
| **Aggregation** | "Total revenue by month" | `SELECT DATE_TRUNC('month', order_date), SUM(amount) FROM orders GROUP BY 1` |
| **Filtering** | "Active customers only" | `SELECT * FROM customers WHERE status = 'active'` |
| **Joins** | "Customer orders with product details" | `SELECT c.name, o.amount, p.name FROM customers c JOIN orders o ON c.id = o.customer_id JOIN products p ON o.product_id = p.id` |
| **Subqueries** | "Customers who ordered more than average" | `SELECT * FROM customers WHERE id IN (SELECT customer_id FROM orders GROUP BY customer_id HAVING SUM(amount) > (SELECT AVG(total) FROM (SELECT SUM(amount) as total FROM orders GROUP BY customer_id) t))` |
| **Window Functions** | "Revenue ranking by customer" | `SELECT name, revenue, RANK() OVER (ORDER BY revenue DESC) FROM (SELECT c.name, SUM(o.amount) as revenue FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id, c.name) t` |

### Error Handling
- **Syntax Validation**: Checks SQL syntax before execution
- **Schema Validation**: Ensures tables/columns exist
- **Type Checking**: Validates data type compatibility
- **Retry Logic**: Attempts query reformulation on errors

## Strengths

✅ **Direct Translation**: No intermediate steps or tool calls required

✅ **Fast Execution**: Single model inference generates complete query

✅ **Schema Integration**: Deep understanding of database structure

✅ **Complex Queries**: Can handle sophisticated SQL patterns

✅ **Deterministic**: Same input produces same SQL output

✅ **Production Ready**: Proven in enterprise environments (e.g., Databricks, Snowflake)

## Limitations

❌ **Schema Dependency**: Requires complete, accurate schema information

❌ **No Query Optimization**: Generated SQL may not be performance-optimal

❌ **Limited Context**: No understanding of business logic or data quality

❌ **Error Recovery**: Difficult to debug and fix failed queries

❌ **Multi-Source Complexity**: Challenging to handle federated queries across systems

❌ **Security Risks**: Direct SQL generation can lead to injection vulnerabilities

## Implementation for Benchmark

### Model Options
- **Fine-tuned Models**: SQLCoder, SQL-PaLM, CodeLlama-SQL
- **Prompt Engineering**: GPT-4, Claude with SQL prompts
- **Hybrid Approaches**: RAG + LLM for schema understanding

### Schema Representation
```json
{
  "database": "sales",
  "tables": [
    {
      "name": "customers",
      "description": "Customer account information",
      "columns": [
        {
          "name": "id",
          "type": "INTEGER",
          "description": "Unique customer identifier",
          "constraints": ["PRIMARY KEY", "NOT NULL"]
        },
        {
          "name": "name",
          "type": "VARCHAR(255)",
          "description": "Customer full name",
          "constraints": ["NOT NULL"]
        }
      ],
      "relationships": [
        {
          "type": "one_to_many",
          "target_table": "orders",
          "foreign_key": "customer_id"
        }
      ]
    }
  ]
}
```

### Evaluation Metrics
- **Query Correctness**: Does SQL return expected results?
- **Syntax Accuracy**: Is generated SQL valid?
- **Performance**: How efficient is the generated query?
- **Complexity Handling**: Can it handle advanced SQL features?
- **Error Recovery**: How does it handle ambiguous questions?

### Configuration
```yaml
# config.yaml
text_to_sql:
  model: "sqlcoder-7b-2"
  max_tokens: 2048
  temperature: 0.1
  
  schema_representation:
    include_sample_data: true
    include_constraints: true
    include_relationships: true
    
  validation:
    syntax_check: true
    schema_validation: true
    execution_timeout: 30
```

## Example Test Case

**Problem**: "Find customers with declining order volume over the last 3 months"

**Expected SQL**:
```sql
WITH monthly_orders AS (
  SELECT 
    customer_id,
    DATE_TRUNC('month', order_date) as month,
    COUNT(*) as order_count
  FROM orders
  WHERE order_date >= CURRENT_DATE - INTERVAL '3 months'
  GROUP BY customer_id, DATE_TRUNC('month', order_date)
),
monthly_trends AS (
  SELECT 
    customer_id,
    month,
    order_count,
    LAG(order_count) OVER (PARTITION BY customer_id ORDER BY month) as prev_month_count
  FROM monthly_orders
)
SELECT 
  c.name,
  c.email,
  mt.month,
  mt.order_count,
  mt.prev_month_count,
  CASE 
    WHEN mt.prev_month_count IS NULL THEN 'new'
    WHEN mt.order_count < mt.prev_month_count THEN 'declining'
    ELSE 'stable'
  END as trend
FROM monthly_trends mt
JOIN customers c ON mt.customer_id = c.id
WHERE mt.prev_month_count IS NOT NULL 
  AND mt.order_count < mt.prev_month_count
ORDER BY mt.month DESC, mt.order_count;
```

**Evaluation Criteria**:
- Did it use window functions for trend analysis?
- Did it handle the 3-month time window correctly?
- Did it identify declining patterns properly?
- Did it join with customer information for context?

## References

- [SQLCoder: A Large Language Model for SQL Generation](https://github.com/h2oai/sqlcoder)
- [Text-to-SQL Survey](https://arxiv.org/abs/2109.05153)
- [Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task](https://yale-lily.github.io/spider)
- [BIRD: A Large-scale Benchmark for Text-to-SQL Evaluation](https://bird-bench.github.io/)
