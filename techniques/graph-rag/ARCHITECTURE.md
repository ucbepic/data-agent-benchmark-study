# Graph RAG Architecture

## Overview

This technique uses graph databases to model complex relationships between data entities, business concepts, and query patterns. By representing knowledge as a graph structure, the system can traverse relationships to find relevant context and generate more accurate queries that understand data dependencies and business logic.

## Core Components

```ascii
┌─────────────────────────────────────────────────────────────┐
│                     Benchmark Question                      │
│            "Show me top customers by revenue"               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Graph Query Engine                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Entity Extraction                     │  │
│  │  - Named entity recognition                         │  │
│  │  - Relationship identification                      │  │
│  │  - Intent mapping                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Knowledge Graph                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Schema      │ │ Business    │ │ Query       │          │
│  │ Graph       │ │ Logic       │ │ Pattern     │          │
│  │             │ │ Graph       │ │ Graph       │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Graph Traversal                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Path Finding                          │  │
│  │  - Multi-hop relationship traversal                 │  │
│  │  - Context aggregation                              │  │
│  │  - Relevance scoring                                │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Context Assembly                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Graph-Based Context                   │  │
│  │  - Related entities and relationships               │  │
│  │  - Business logic chains                            │  │
│  │  - Query pattern matching                           │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Query Generation                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Graph-Aware LLM                       │  │
│  │  - Relationship-aware SQL generation                │  │
│  │  - Business logic integration                       │  │
│  │  - Pattern-based optimization                       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. Knowledge Graph Construction
The system builds multiple interconnected graphs representing different aspects of the data domain:

```python
# Schema Graph
schema_graph = {
    "nodes": [
        {"id": "customers", "type": "table", "properties": {"name": "customers"}},
        {"id": "orders", "type": "table", "properties": {"name": "orders"}},
        {"id": "customer_id", "type": "column", "properties": {"name": "customer_id", "table": "orders"}},
        {"id": "id", "type": "column", "properties": {"name": "id", "table": "customers"}},
        {"id": "amount", "type": "column", "properties": {"name": "amount", "table": "orders"}}
    ],
    "relationships": [
        {"source": "orders", "target": "customers", "type": "REFERENCES", "properties": {"via": "customer_id"}},
        {"source": "customer_id", "target": "id", "type": "FOREIGN_KEY", "properties": {"constraint": "fk_orders_customers"}},
        {"source": "orders", "target": "amount", "type": "HAS_COLUMN", "properties": {"data_type": "DECIMAL"}}
    ]
}

# Business Logic Graph
business_graph = {
    "nodes": [
        {"id": "revenue", "type": "concept", "properties": {"name": "revenue", "definition": "Total sales amount"}},
        {"id": "customer", "type": "concept", "properties": {"name": "customer", "definition": "Business customer"}},
        {"id": "order", "type": "concept", "properties": {"name": "order", "definition": "Customer purchase"}},
        {"id": "completed", "type": "status", "properties": {"name": "completed", "meaning": "Order fulfilled"}}
    ],
    "relationships": [
        {"source": "revenue", "target": "order", "type": "CALCULATED_FROM", "properties": {"formula": "SUM(amount)"}},
        {"source": "order", "target": "customer", "type": "BELONGS_TO", "properties": {"cardinality": "many_to_one"}},
        {"source": "order", "target": "completed", "type": "HAS_STATUS", "properties": {"filter": "status = 'completed'"}}
    ]
}

# Query Pattern Graph
pattern_graph = {
    "nodes": [
        {"id": "top_customers", "type": "pattern", "properties": {"name": "top_customers", "description": "Rank customers by metric"}},
        {"id": "revenue_aggregation", "type": "pattern", "properties": {"name": "revenue_aggregation", "description": "Sum order amounts"}},
        {"id": "customer_ranking", "type": "pattern", "properties": {"name": "customer_ranking", "description": "ORDER BY with LIMIT"}}
    ],
    "relationships": [
        {"source": "top_customers", "target": "revenue_aggregation", "type": "REQUIRES", "properties": {"dependency": "required"}},
        {"source": "top_customers", "target": "customer_ranking", "type": "REQUIRES", "properties": {"dependency": "required"}},
        {"source": "revenue_aggregation", "target": "customer_ranking", "type": "FEEDS_INTO", "properties": {"flow": "aggregation_to_ranking"}}
    ]
}
```

### 2. Graph Traversal Process

```ascii
1. Entity Extraction
   "Show me top customers by revenue"
   ↓
   Entities: ["customers", "revenue"]
   Intent: "ranking_query"
              ↓
2. Graph Traversal
   Schema Graph:
   customers → orders (via customer_id)
   orders → amount (HAS_COLUMN)
   
   Business Graph:
   revenue → order (CALCULATED_FROM)
   order → customer (BELONGS_TO)
   order → completed (HAS_STATUS)
   
   Pattern Graph:
   top_customers → revenue_aggregation (REQUIRES)
   top_customers → customer_ranking (REQUIRES)
              ↓
3. Context Assembly
   Schema Context:
   - customers table with id, name, email
   - orders table with customer_id, amount, status
   - Relationship: orders.customer_id = customers.id
   
   Business Context:
   - Revenue = SUM(orders.amount) WHERE status = 'completed'
   - Customers have multiple orders (one-to-many)
   
   Pattern Context:
   - Use GROUP BY customer_id for aggregation
   - Use ORDER BY revenue DESC for ranking
   - Use LIMIT for top N results
              ↓
4. Query Generation
   SELECT c.name, SUM(o.amount) as revenue
   FROM customers c
   JOIN orders o ON c.id = o.customer_id
   WHERE o.status = 'completed'
   GROUP BY c.id, c.name
   ORDER BY revenue DESC
   LIMIT 10;
```

### 3. Graph Database Implementation

```python
from neo4j import GraphDatabase
import networkx as nx

class GraphRAGSystem:
    def __init__(self, neo4j_uri, username, password):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
        self.graph = nx.MultiDiGraph()
    
    def build_knowledge_graph(self):
        """Construct the knowledge graph from database schema and business rules"""
        
        # Schema graph construction
        with self.driver.session() as session:
            # Create table nodes
            session.run("""
                CREATE (c:Table {name: 'customers', type: 'table'})
                CREATE (o:Table {name: 'orders', type: 'table'})
                CREATE (p:Table {name: 'products', type: 'table'})
            """)
            
            # Create column nodes
            session.run("""
                CREATE (cid:Column {name: 'customer_id', table: 'orders', type: 'INTEGER'})
                CREATE (id:Column {name: 'id', table: 'customers', type: 'INTEGER'})
                CREATE (amount:Column {name: 'amount', table: 'orders', type: 'DECIMAL'})
                CREATE (status:Column {name: 'status', table: 'orders', type: 'VARCHAR'})
            """)
            
            # Create relationships
            session.run("""
                MATCH (o:Table {name: 'orders'})
                MATCH (c:Table {name: 'customers'})
                MATCH (cid:Column {name: 'customer_id'})
                MATCH (id:Column {name: 'id'})
                CREATE (o)-[:REFERENCES]->(c)
                CREATE (cid)-[:FOREIGN_KEY]->(id)
                CREATE (o)-[:HAS_COLUMN]->(amount)
                CREATE (o)-[:HAS_COLUMN]->(status)
            """)
    
    def traverse_graph(self, entities: list, max_hops: int = 3):
        """Traverse the graph to find relevant context"""
        
        with self.driver.session() as session:
            # Find paths from entities to related concepts
            query = """
            MATCH path = (start)-[*1..%d]-(related)
            WHERE start.name IN $entities
            RETURN path, related
            ORDER BY length(path)
            LIMIT 20
            """ % max_hops
            
            result = session.run(query, entities=entities)
            
            context = {
                "schema_info": [],
                "business_logic": [],
                "query_patterns": []
            }
            
            for record in result:
                path = record["path"]
                related = record["related"]
                
                # Categorize based on node type
                if related.get("type") == "table":
                    context["schema_info"].append(related)
                elif related.get("type") == "concept":
                    context["business_logic"].append(related)
                elif related.get("type") == "pattern":
                    context["query_patterns"].append(related)
            
            return context
```

## Key Capabilities

### Multi-Hop Relationship Traversal
- **Schema Relationships**: Follow foreign keys, constraints, and dependencies
- **Business Logic Chains**: Trace calculation rules and business concepts
- **Query Pattern Matching**: Identify similar query structures and approaches
- **Context Aggregation**: Combine information from multiple related entities

### Graph-Based Context Understanding
- **Entity Resolution**: Map natural language to graph nodes
- **Relationship Inference**: Understand implicit connections
- **Path Optimization**: Find shortest/most relevant paths between concepts
- **Relevance Scoring**: Rank context based on graph distance and importance

### Dynamic Graph Updates
- **Schema Evolution**: Update graph when database structure changes
- **Pattern Learning**: Add new query patterns as they're discovered
- **Business Rule Updates**: Modify business logic graph as rules change
- **Performance Optimization**: Cache frequently traversed paths

## Strengths

✅ **Relationship Awareness**: Understands complex data dependencies

✅ **Multi-Hop Reasoning**: Can traverse multiple relationships to find context

✅ **Pattern Recognition**: Identifies and reuses successful query patterns

✅ **Business Logic Integration**: Captures domain-specific rules and concepts

✅ **Scalable**: Graph databases handle large, complex knowledge structures

✅ **Explainable**: Can trace reasoning paths through the graph

✅ **Adaptive**: Can learn and update patterns over time

## Limitations

❌ **Graph Complexity**: Complex graphs can be difficult to maintain and debug

❌ **Traversal Overhead**: Multi-hop traversals can be computationally expensive

❌ **Knowledge Engineering**: Requires significant effort to build comprehensive graphs

❌ **Cold Start**: Needs substantial initial graph construction

❌ **Graph Consistency**: Maintaining consistency across multiple graph types is challenging

❌ **Query Performance**: Complex graph queries may be slow on large graphs

## Implementation for Benchmark

### Graph Schema Design
```cypher
// Schema Graph
CREATE CONSTRAINT table_name IF NOT EXISTS FOR (t:Table) REQUIRE t.name IS UNIQUE;
CREATE CONSTRAINT column_name IF NOT EXISTS FOR (c:Column) REQUIRE c.name IS UNIQUE;

// Business Logic Graph
CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT rule_name IF NOT EXISTS FOR (r:Rule) REQUIRE r.name IS UNIQUE;

// Query Pattern Graph
CREATE CONSTRAINT pattern_name IF NOT EXISTS FOR (p:Pattern) REQUIRE p.name IS UNIQUE;
```

### Graph Construction Pipeline
```python
def build_comprehensive_graph(self):
    """Build a comprehensive knowledge graph"""
    
    # 1. Extract schema information
    schema_graph = self._extract_schema_graph()
    
    # 2. Build business logic graph
    business_graph = self._build_business_logic_graph()
    
    # 3. Create query pattern graph
    pattern_graph = self._create_pattern_graph()
    
    # 4. Connect graphs with cross-references
    self._connect_graphs(schema_graph, business_graph, pattern_graph)
    
    return self._merge_graphs([schema_graph, business_graph, pattern_graph])

def _extract_schema_graph(self):
    """Extract database schema into graph structure"""
    with self.driver.session() as session:
        # Get all tables
        tables = session.run("""
            SELECT table_name, table_comment 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        for table in tables:
            # Create table node
            session.run("""
                CREATE (t:Table {name: $name, comment: $comment})
            """, name=table["table_name"], comment=table["table_comment"])
            
            # Get columns for this table
            columns = session.run("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = $table_name
            """, table_name=table["table_name"])
            
            for column in columns:
                # Create column node
                session.run("""
                    MATCH (t:Table {name: $table_name})
                    CREATE (c:Column {name: $col_name, type: $data_type, nullable: $nullable})
                    CREATE (t)-[:HAS_COLUMN]->(c)
                """, table_name=table["table_name"], 
                     col_name=column["column_name"],
                     data_type=column["data_type"],
                     nullable=column["is_nullable"])
```

### Query Processing with Graph Context
```python
def process_query_with_graph(self, question: str) -> str:
    """Process query using graph-based context retrieval"""
    
    # 1. Extract entities and intent
    entities = self._extract_entities(question)
    intent = self._classify_intent(question)
    
    # 2. Traverse graph for context
    graph_context = self._traverse_graph(entities, max_hops=3)
    
    # 3. Find relevant patterns
    patterns = self._find_matching_patterns(intent, entities)
    
    # 4. Build enhanced context
    enhanced_context = self._build_graph_context(graph_context, patterns)
    
    # 5. Generate SQL with graph awareness
    sql = self._generate_graph_aware_sql(question, enhanced_context)
    
    return sql

def _find_matching_patterns(self, intent: str, entities: list) -> list:
    """Find query patterns that match the intent and entities"""
    
    with self.driver.session() as session:
        query = """
        MATCH (p:Pattern)-[:MATCHES]->(i:Intent {name: $intent})
        MATCH (p)-[:USES]->(e:Entity)
        WHERE e.name IN $entities
        RETURN p, e
        ORDER BY p.frequency DESC
        LIMIT 5
        """
        
        result = session.run(query, intent=intent, entities=entities)
        return [record["p"] for record in result]
```

### Evaluation Metrics
- **Graph Coverage**: How well does the graph cover the domain?
- **Traversal Efficiency**: How quickly can relevant context be found?
- **Pattern Matching**: How accurately does it identify relevant patterns?
- **Relationship Accuracy**: Are the graph relationships correct?
- **Context Relevance**: Is the retrieved context actually useful?

### Configuration
```yaml
# config.yaml
graph_rag:
  database:
    type: "neo4j"
    uri: "bolt://localhost:7687"
    database: "knowledge_graph"
    
  traversal:
    max_hops: 3
    max_results: 20
    similarity_threshold: 0.7
    
  graphs:
    schema:
      enabled: true
      update_frequency: "daily"
      
    business_logic:
      enabled: true
      rules_file: "business_rules.yaml"
      
    patterns:
      enabled: true
      learning_rate: 0.1
      
  generation:
    model: "gpt-4"
    temperature: 0.1
    max_tokens: 2048
```

## Example Test Case

**Problem**: "Find customers who have purchased products from multiple categories and show their total spend by category"

**Graph Traversal**:
1. **Entity Extraction**: ["customers", "products", "categories", "purchase", "spend"]
2. **Schema Graph Traversal**:
   - customers → orders (via customer_id)
   - orders → order_items (via order_id)
   - order_items → products (via product_id)
   - products → categories (via category_id)

3. **Business Logic Graph Traversal**:
   - purchase → order (IS_A)
   - spend → amount (CALCULATED_FROM)
   - category → product (HAS_CATEGORY)

4. **Pattern Graph Traversal**:
   - multi_category_customers → category_aggregation (REQUIRES)
   - category_aggregation → group_by_category (REQUIRES)

**Generated SQL**:
```sql
WITH customer_categories AS (
  SELECT 
    c.id as customer_id,
    c.name as customer_name,
    cat.name as category_name,
    SUM(oi.quantity * p.price) as category_spend
  FROM customers c
  JOIN orders o ON c.id = o.customer_id
  JOIN order_items oi ON o.id = oi.order_id
  JOIN products p ON oi.product_id = p.id
  JOIN categories cat ON p.category_id = cat.id
  WHERE o.status = 'completed'
  GROUP BY c.id, c.name, cat.id, cat.name
),
category_counts AS (
  SELECT 
    customer_id,
    COUNT(DISTINCT category_name) as category_count
  FROM customer_categories
  GROUP BY customer_id
)
SELECT 
  cc.customer_name,
  cc.category_name,
  cc.category_spend,
  ccat.category_count
FROM customer_categories cc
JOIN category_counts ccat ON cc.customer_id = ccat.customer_id
WHERE ccat.category_count > 1
ORDER BY cc.customer_name, cc.category_spend DESC;
```

**Evaluation Criteria**:
- Did it correctly identify the need for multi-category filtering?
- Did it use the proper join path through the schema graph?
- Did it apply the business logic for spend calculation?
- Did it follow the pattern for category aggregation?

## References

- [Neo4j Graph Database](https://neo4j.com/)
- [Graph Neural Networks for Text-to-SQL](https://arxiv.org/abs/2109.05153)
- [Knowledge Graph Construction and Applications](https://arxiv.org/abs/2003.02320)
- [Graph-Based RAG Systems](https://arxiv.org/abs/2401.00051)
