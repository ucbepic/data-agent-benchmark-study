# Tool Calling Architecture

## Overview

This technique uses the Model Context Protocol (MCP), an open standard that enables developers to build secure, two-way connections between their data sources and AI-powered tools. MCP servers expose database operations as callable tools with structured schemas that AI models can understand and invoke.

## Core Components

```ascii
┌─────────────────────────────────────────────────────────────┐
│                     Benchmark Question                      │
│            "Show me top customers by revenue"               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Claude Desktop (Host)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   MCP Client                         │  │
│  │  - Manages connections to MCP servers                │  │
│  │  - Presents available tools to Claude                │  │
│  │  - Routes tool calls to appropriate servers          │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬─────────────┐
        │            │            │             │
        ▼            ▼            ▼             ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│PostgreSQL│ │ MongoDB  │ │  SQLite  │ │ API/SaaS │
│   MCP    │ │   MCP    │ │   MCP    │ │   MCP    │
│  Server  │ │  Server  │ │  Server  │ │  Server  │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │             │
     ▼            ▼            ▼             ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│PostgreSQL│ │ MongoDB  │ │  SQLite  │ │  GitHub  │
│    DB    │ │    DB    │ │    DB    │ │   API    │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

## How It Works

### 1. Server Setup
Each data source gets an MCP server that exposes tools:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["@modelcontextprotocol/postgres-server"],
      "env": {
        "DATABASE_URI": "postgresql://user:pass@localhost/db"
      }
    },
    "mongodb": {
      "command": "npx", 
      "args": ["@sourabhshegane/mongodb-mcp-that-works"],
      "env": {
        "MONGODB_URI": "mongodb://localhost:27017/db"
      }
    }
  }
}
```

### 2. Tool Discovery
MCP servers expose Tools (model-controlled functions that LLMs can call to perform specific actions), each with:
- **Name**: `query_database`, `get_schema`, `list_tables`
- **Description**: What the tool does in natural language
- **Input Schema**: JSON Schema defining parameters
- **Output Schema**: Expected return format

Example tool manifest:
```json
{
  "name": "query_database",
  "description": "Execute a SQL query on PostgreSQL",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "SQL query"},
      "params": {"type": "array", "description": "Query parameters"}
    },
    "required": ["query"]
  }
}
```

### 3. Query Execution Flow

```ascii
1. User asks: "Show revenue by customer"
              ↓
2. Claude sees available tools:
   - postgres.query_database
   - postgres.get_schema
   - mongodb.find_documents
              ↓
3. Claude plans approach:
   a. Call get_schema to understand tables
   b. Generate SQL based on schema
   c. Call query_database with SQL
              ↓
4. Claude invokes tools:
   get_schema({table: "customers"})
   → Returns: columns, types, constraints
              ↓
   query_database({
     query: "SELECT c.name, SUM(o.amount) as revenue 
             FROM customers c JOIN orders o ON c.id = o.customer_id
             GROUP BY c.id, c.name ORDER BY revenue DESC"
   })
   → Returns: query results
              ↓
5. Claude formats and presents results
```

## Key Capabilities

### Database Tools
Common tools exposed by database MCP servers:

| Tool | Purpose | Example |
|------|---------|---------|
| `list_databases` | Show available databases | Returns: `["sales", "inventory"]` |
| `list_tables` | Show tables in database | Returns: `["customers", "orders", "products"]` |
| `get_schema` | Get table structure | Returns columns, types, constraints |
| `query_database` | Execute SELECT queries | Returns result rows |
| `execute_statement` | Run INSERT/UPDATE/DELETE | Returns affected rows |
| `explain_query` | Get query execution plan | Returns optimizer plan |

### Multi-Source Federation
Since its introduction late 2024, MCP has gained rapid adoption across numerous platforms, creating a diverse ecosystem of clients and servers that bridge the gap between LLMs and external tools:

```ascii
Question: "Compare Salesforce pipeline to warehouse revenue"
                    ↓
        ┌───────────┴───────────┐
        ▼                       ▼
  Salesforce MCP           Warehouse MCP
  get_opportunities()       query_database()
        │                       │
        └───────────┬───────────┘
                    ▼
            Claude combines results
```

## Strengths

✅ **Standardized Interface**: Instead of maintaining separate connectors for each data source, developers can now build against a standard protocol

✅ **Tool Transparency**: AI can see exactly what tools are available and their schemas

✅ **Deterministic**: Same tools with same inputs produce same outputs

✅ **Extensible**: Easy to add new data sources by creating MCP servers

✅ **Production-Ready**: Early adopters like Block and Apollo have integrated MCP into their systems

## Limitations

❌ **No Query Optimization**: AI generates queries without understanding performance

❌ **No Business Logic**: Tools expose raw database operations, not business concepts

❌ **Limited Error Recovery**: Failed queries require manual intervention

❌ **No State Management**: Each query is independent, no session context

❌ **Security Concerns**: Direct SQL access requires careful permission management

## Implementation for Benchmark

### Required MCP Servers
- **PostgreSQL**: For transactional data
- **MongoDB**: For document stores  
- **SQLite**: For local databases
- **API Servers**: For external services (GitHub, Salesforce, etc.)

### Evaluation Metrics
- **Correctness**: Does the query return expected results?
- **Tool Selection**: Did AI choose appropriate tools?
- **Query Quality**: Is the generated SQL/query optimal?
- **Error Handling**: How does it recover from failures?
- **Multi-Source**: Can it combine data from different systems?

### Configuration
```yaml
# config.yaml
mcp_servers:
  - name: warehouse
    type: postgresql
    connection: ${PG_CONNECTION_STRING}
    read_only: true
    
  - name: analytics
    type: mongodb
    connection: ${MONGO_URI}
    
  - name: salesforce
    type: api
    base_url: https://api.salesforce.com
    auth: oauth2
```

## Example Test Case

**Problem**: "Find customers with declining orders month-over-month"

**Expected Tool Calls**:
1. `warehouse.get_schema({table: "orders"})`
2. `warehouse.query_database({
     query: "WITH monthly_orders AS (
               SELECT customer_id, 
                      DATE_TRUNC('month', order_date) as month,
                      COUNT(*) as order_count
               FROM orders
               WHERE order_date >= NOW() - INTERVAL '3 months'
               GROUP BY 1, 2
             )
             SELECT ... [month-over-month calculation]"
   })`

**Evaluation**:
- Did it identify the need for window functions?
- Did it handle date truncation correctly?
- Did it return customers with actual declining trends?

## References

- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers)
- [Community MCP Servers](https://www.pulsemcp.com/servers)
