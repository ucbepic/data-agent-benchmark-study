# RAG-on-Data Architecture

## Overview

This technique uses Retrieval-Augmented Generation (RAG) to enhance AI's understanding of database schemas, business logic, and data context. By retrieving relevant schema information, documentation, and sample data, the model can generate more accurate and contextually appropriate queries.

## Core Components

```ascii
┌─────────────────────────────────────────────────────────────┐
│                     Benchmark Question                      │
│            "Show me top customers by revenue"               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Query Understanding                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Intent Extraction                     │  │
│  │  - Entity recognition                               │  │
│  │  - Intent classification                            │  │
│  │  - Query decomposition                              │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Knowledge Retrieval                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Schema      │ │ Business    │ │ Sample      │          │
│  │ Vector DB   │ │ Logic       │ │ Data        │          │
│  │             │ │ Vector DB   │ │ Vector DB   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Context Augmentation                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Relevant Information                  │  │
│  │  - Table schemas and relationships                  │  │
│  │  - Business rules and constraints                   │  │
│  │  - Sample queries and patterns                      │  │
│  │  - Data quality notes and caveats                   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Query Generation                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Enhanced LLM                          │  │
│  │  - Schema-aware SQL generation                      │  │
│  │  - Business logic integration                       │  │
│  │  - Best practice application                        │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Result Validation                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Quality Assurance                     │  │
│  │  - Query validation and optimization                │  │
│  │  - Result verification                              │  │
│  │  - Performance analysis                             │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. Knowledge Base Construction
The system builds multiple vector databases from different data sources:

```python
# Schema Knowledge Base
schema_chunks = [
    {
        "content": "customers table: id (PK), name, email, created_at, status",
        "metadata": {
            "table": "customers",
            "type": "schema",
            "columns": ["id", "name", "email", "created_at", "status"]
        }
    },
    {
        "content": "orders table: id (PK), customer_id (FK), amount, order_date, status",
        "metadata": {
            "table": "orders", 
            "type": "schema",
            "columns": ["id", "customer_id", "amount", "order_date", "status"]
        }
    },
    {
        "content": "Relationship: customers.id = orders.customer_id (one-to-many)",
        "metadata": {
            "type": "relationship",
            "from_table": "customers",
            "to_table": "orders",
            "relationship": "one_to_many"
        }
    }
]

# Business Logic Knowledge Base
business_chunks = [
    {
        "content": "Revenue calculation: SUM(orders.amount) WHERE status = 'completed'",
        "metadata": {
            "type": "business_rule",
            "concept": "revenue",
            "tables": ["orders"]
        }
    },
    {
        "content": "Active customers: customers.status = 'active'",
        "metadata": {
            "type": "business_rule", 
            "concept": "active_customer",
            "tables": ["customers"]
        }
    }
]

# Sample Data Knowledge Base
sample_chunks = [
    {
        "content": "Sample customer data: John Doe (id=1) has 3 orders totaling $450",
        "metadata": {
            "type": "sample_data",
            "tables": ["customers", "orders"],
            "customer_id": 1
        }
    }
]
```

### 2. Retrieval Process

```ascii
1. Query Analysis
   "Show me top customers by revenue"
   ↓
   Entities: ["customers", "revenue"]
   Intent: "aggregation_query"
   Tables: ["customers", "orders"]
              ↓
2. Multi-Vector Retrieval
   Schema DB: "customers table schema", "orders table schema", "relationship"
   Business DB: "revenue calculation rule", "active customer definition"
   Sample DB: "customer order examples"
              ↓
3. Context Assembly
   Schema Context:
   - customers(id, name, email, status)
   - orders(id, customer_id, amount, status)
   - customers.id = orders.customer_id
   
   Business Context:
   - Revenue = SUM(amount) WHERE status = 'completed'
   - Active customers have status = 'active'
   
   Sample Context:
   - Example: John Doe has 3 orders totaling $450
              ↓
4. Enhanced Prompt
   "Given this schema: [SCHEMA_CONTEXT]
    And business rules: [BUSINESS_CONTEXT]
    And examples: [SAMPLE_CONTEXT]
    Generate SQL for: [QUESTION]"
              ↓
5. Query Generation
   SELECT c.name, SUM(o.amount) as revenue
   FROM customers c
   JOIN orders o ON c.id = o.customer_id
   WHERE o.status = 'completed'
   GROUP BY c.id, c.name
   ORDER BY revenue DESC
   LIMIT 10;
```

### 3. Vector Database Structure

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# Initialize vector stores
embeddings = OpenAIEmbeddings()

# Schema vector store
schema_store = Chroma(
    collection_name="schema_knowledge",
    embedding_function=embeddings,
    persist_directory="./vector_db/schema"
)

# Business logic vector store  
business_store = Chroma(
    collection_name="business_knowledge",
    embedding_function=embeddings,
    persist_directory="./vector_db/business"
)

# Sample data vector store
sample_store = Chroma(
    collection_name="sample_knowledge", 
    embedding_function=embeddings,
    persist_directory="./vector_db/samples"
)

# Add documents to stores
schema_store.add_documents(schema_chunks)
business_store.add_documents(business_chunks)
sample_store.add_documents(sample_chunks)
```

## Key Capabilities

### Multi-Source Knowledge Retrieval
- **Schema Information**: Table structures, relationships, constraints
- **Business Logic**: Calculation rules, definitions, business concepts
- **Sample Data**: Example queries, data patterns, edge cases
- **Documentation**: API docs, data dictionaries, best practices

### Context-Aware Generation
- **Schema Matching**: Maps natural language to actual database elements
- **Business Rule Integration**: Applies domain-specific logic
- **Pattern Recognition**: Uses similar examples for guidance
- **Constraint Awareness**: Respects data types and relationships

### Adaptive Learning
- **Query Feedback**: Learns from successful and failed queries
- **Pattern Updates**: Continuously improves knowledge base
- **Schema Evolution**: Adapts to database changes
- **Performance Optimization**: Learns from query execution patterns

## Strengths

✅ **Rich Context**: Access to comprehensive database knowledge

✅ **Business Logic Integration**: Understands domain-specific rules

✅ **Pattern Learning**: Can learn from successful query patterns

✅ **Schema Evolution**: Adapts to database changes over time

✅ **Multi-Modal Knowledge**: Combines schema, business logic, and examples

✅ **Explainable**: Can explain why certain tables/columns were chosen

✅ **Production Proven**: Used by companies like Databricks and Snowflake

## Limitations

❌ **Knowledge Base Maintenance**: Requires ongoing updates to vector databases

❌ **Retrieval Quality**: Depends on embedding quality and chunking strategy

❌ **Context Window Limits**: May hit token limits with large schemas

❌ **Cold Start**: Needs initial knowledge base construction

❌ **Schema Drift**: May become outdated if database changes frequently

❌ **Complexity Overhead**: Multiple vector stores increase system complexity

## Implementation for Benchmark

### Knowledge Base Setup
```python
class RAGDataSystem:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        self.schema_store = self._build_schema_knowledge()
        self.business_store = self._build_business_knowledge()
        self.sample_store = self._build_sample_knowledge()
    
    def _build_schema_knowledge(self):
        """Extract and vectorize database schema information"""
        schema_chunks = []
        
        # Get all tables
        tables = self.db_connection.execute("""
            SELECT table_name, table_comment 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """).fetchall()
        
        for table in tables:
            # Get columns
            columns = self.db_connection.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s
            """, (table[0],)).fetchall()
            
            # Create schema chunk
            schema_text = f"{table[0]} table: {', '.join([f'{col[0]} ({col[1]})' for col in columns])}"
            schema_chunks.append({
                "content": schema_text,
                "metadata": {
                    "table": table[0],
                    "type": "schema",
                    "columns": [col[0] for col in columns]
                }
            })
        
        return Chroma.from_documents(schema_chunks, OpenAIEmbeddings())
    
    def _build_business_knowledge(self):
        """Extract business logic and rules"""
        business_rules = [
            {
                "content": "Revenue is calculated as SUM(amount) from completed orders",
                "metadata": {"type": "business_rule", "concept": "revenue"}
            },
            {
                "content": "Active customers have status = 'active'",
                "metadata": {"type": "business_rule", "concept": "active_customer"}
            }
        ]
        
        return Chroma.from_documents(business_rules, OpenAIEmbeddings())
```

### Query Processing Pipeline
```python
def process_query(self, question: str) -> str:
    """Process natural language query using RAG"""
    
    # 1. Extract entities and intent
    entities = self._extract_entities(question)
    intent = self._classify_intent(question)
    
    # 2. Retrieve relevant knowledge
    schema_context = self._retrieve_schema_context(entities)
    business_context = self._retrieve_business_context(intent)
    sample_context = self._retrieve_sample_context(question)
    
    # 3. Build enhanced prompt
    enhanced_prompt = self._build_enhanced_prompt(
        question, schema_context, business_context, sample_context
    )
    
    # 4. Generate SQL
    sql = self._generate_sql(enhanced_prompt)
    
    # 5. Validate and optimize
    validated_sql = self._validate_sql(sql)
    
    return validated_sql

def _retrieve_schema_context(self, entities: list) -> str:
    """Retrieve relevant schema information"""
    context_parts = []
    
    for entity in entities:
        # Search schema store
        results = self.schema_store.similarity_search(
            entity, k=3
        )
        
        for result in results:
            context_parts.append(result.page_content)
    
    return "\n".join(context_parts)
```

### Evaluation Metrics
- **Retrieval Accuracy**: How relevant is the retrieved context?
- **Context Utilization**: Does the model use the retrieved information?
- **Query Quality**: Are generated queries better with RAG?
- **Knowledge Coverage**: How well does the knowledge base cover the domain?
- **Update Efficiency**: How quickly can the system adapt to schema changes?

### Configuration
```yaml
# config.yaml
rag_on_data:
  vector_stores:
    schema:
      collection_name: "schema_knowledge"
      chunk_size: 1000
      overlap: 200
      
    business:
      collection_name: "business_knowledge" 
      chunk_size: 500
      overlap: 100
      
    samples:
      collection_name: "sample_knowledge"
      chunk_size: 2000
      overlap: 300
  
  retrieval:
    top_k: 5
    similarity_threshold: 0.7
    max_context_length: 4000
    
  generation:
    model: "gpt-4"
    temperature: 0.1
    max_tokens: 2048
```

## Example Test Case

**Problem**: "Find customers with high lifetime value who haven't ordered in the last 30 days"

**Knowledge Retrieval**:
1. **Schema Context**:
   - customers(id, name, email, created_at, status)
   - orders(id, customer_id, amount, order_date, status)
   - customers.id = orders.customer_id (one-to-many)

2. **Business Context**:
   - Lifetime value = SUM(orders.amount) WHERE status = 'completed'
   - High LTV = top 20% of customers by total spend
   - Recent activity = orders in last 30 days

3. **Sample Context**:
   - Example: Customer with LTV $5000, last order 45 days ago

**Generated SQL**:
```sql
WITH customer_ltv AS (
  SELECT 
    c.id,
    c.name,
    c.email,
    SUM(o.amount) as lifetime_value,
    MAX(o.order_date) as last_order_date
  FROM customers c
  JOIN orders o ON c.id = o.customer_id
  WHERE o.status = 'completed'
  GROUP BY c.id, c.name, c.email
),
ltv_percentiles AS (
  SELECT 
    *,
    NTILE(5) OVER (ORDER BY lifetime_value DESC) as ltv_quintile
  FROM customer_ltv
)
SELECT 
  name,
  email,
  lifetime_value,
  last_order_date,
  CURRENT_DATE - last_order_date as days_since_order
FROM ltv_percentiles
WHERE ltv_quintile = 1  -- Top 20% by LTV
  AND last_order_date < CURRENT_DATE - INTERVAL '30 days'
ORDER BY lifetime_value DESC;
```

**Evaluation Criteria**:
- Did it correctly identify the need for LTV calculation?
- Did it use the business rule for "high LTV" (top 20%)?
- Did it properly filter for customers without recent orders?
- Did it include relevant customer information in the output?

## References

- [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)
- [RAG: Retrieval-Augmented Generation](https://ai.meta.com/blog/retrieval-augmented-generation-streamlining-the-creation-of-intelligent-natural-language-processing-models/)
- [Vector Databases for RAG Applications](https://www.pinecone.io/learn/vector-database/)
- [Schema-Aware Text-to-SQL Generation](https://arxiv.org/abs/2109.05153)
