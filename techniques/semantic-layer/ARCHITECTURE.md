# Semantic Layer Architecture

## Overview

This technique implements a semantic layer that abstracts complex database schemas into business-friendly concepts and metrics. By providing a unified, business-oriented interface, the semantic layer enables natural language queries to be translated into optimized SQL through predefined business logic and data models.

## Core Components

```ascii
┌─────────────────────────────────────────────────────────────┐
│                     Benchmark Question                      │
│            "Show me top customers by revenue"               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Semantic Layer                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Business Concepts                     │  │
│  │  - Customer, Revenue, Order, Product                │  │
│  │  - Business metrics and KPIs                        │  │
│  │  - Hierarchical dimensions                          │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Query Translation                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Concept     │ │ Metric      │ │ Dimension   │          │
│  │ Mapping     │ │ Calculation │ │ Hierarchy   │          │
│  │             │ │ Engine      │ │ Engine      │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Data Model Engine                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Logical Model                         │  │
│  │  - Entity relationships and joins                   │  │
│  │  - Data transformations and filters                 │  │
│  │  - Business rules and constraints                   │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    SQL Generation                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Optimized SQL                         │  │
│  │  - Generated from semantic model                    │  │
│  │  - Performance optimized                            │  │
│  │  - Business logic enforced                          │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    Database Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ PostgreSQL  │ │ MongoDB     │ │ Data        │          │
│  │ Warehouse   │ │ Document    │ │ Lake        │          │
│  │             │ │ Store       │ │             │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. Semantic Model Definition
The semantic layer defines business concepts and their relationships:

```yaml
# semantic_model.yaml
concepts:
  customer:
    description: "Business customer who makes purchases"
    entity: "customers"
    attributes:
      - name: "customer_id"
        source: "customers.id"
        type: "identifier"
      - name: "customer_name"
        source: "customers.name"
        type: "string"
      - name: "customer_email"
        source: "customers.email"
        type: "string"
      - name: "customer_status"
        source: "customers.status"
        type: "enum"
        values: ["active", "inactive", "suspended"]
    
  order:
    description: "Customer purchase transaction"
    entity: "orders"
    attributes:
      - name: "order_id"
        source: "orders.id"
        type: "identifier"
      - name: "order_date"
        source: "orders.order_date"
        type: "date"
      - name: "order_status"
        source: "orders.status"
        type: "enum"
        values: ["pending", "completed", "cancelled"]
      - name: "order_amount"
        source: "orders.amount"
        type: "decimal"

  revenue:
    description: "Total sales amount from completed orders"
    type: "metric"
    calculation: "SUM(orders.amount)"
    filters:
      - condition: "orders.status = 'completed'"
    dimensions:
      - customer
      - order_date
      - product_category

relationships:
  - from: "order"
    to: "customer"
    type: "many_to_one"
    join: "orders.customer_id = customers.id"
    description: "Each order belongs to one customer"

dimensions:
  time:
    hierarchy:
      - level: "year"
        source: "YEAR(orders.order_date)"
      - level: "quarter"
        source: "QUARTER(orders.order_date)"
      - level: "month"
        source: "MONTH(orders.order_date)"
      - level: "day"
        source: "DATE(orders.order_date)"
  
  geography:
    hierarchy:
      - level: "country"
        source: "customers.country"
      - level: "state"
        source: "customers.state"
      - level: "city"
        source: "customers.city"
```

### 2. Query Translation Process

```ascii
1. Natural Language Parsing
   "Show me top customers by revenue"
   ↓
   Intent: "ranking_query"
   Concepts: ["customer", "revenue"]
   Dimensions: []
   Filters: []
              ↓
2. Concept Resolution
   customer → customers table with attributes
   revenue → SUM(orders.amount) WHERE status = 'completed'
              ↓
3. Relationship Mapping
   customer ← order (via customer_id)
   order → revenue (via amount aggregation)
              ↓
4. SQL Generation
   SELECT 
     c.name as customer_name,
     SUM(o.amount) as revenue
   FROM customers c
   JOIN orders o ON c.id = o.customer_id
   WHERE o.status = 'completed'
   GROUP BY c.id, c.name
   ORDER BY revenue DESC
   LIMIT 10;
```

### 3. Semantic Layer Implementation

```python
class SemanticLayer:
    def __init__(self, model_config: str):
        self.model = self._load_semantic_model(model_config)
        self.concept_mapper = ConceptMapper(self.model)
        self.metric_calculator = MetricCalculator(self.model)
        self.dimension_engine = DimensionEngine(self.model)
    
    def _load_semantic_model(self, config_path: str) -> dict:
        """Load semantic model from YAML configuration"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def translate_query(self, natural_query: str) -> str:
        """Translate natural language to SQL using semantic layer"""
        
        # 1. Parse natural language
        parsed = self._parse_natural_language(natural_query)
        
        # 2. Resolve concepts
        resolved_concepts = self.concept_mapper.resolve_concepts(parsed.concepts)
        
        # 3. Calculate metrics
        metric_sql = self.metric_calculator.calculate_metrics(parsed.metrics)
        
        # 4. Apply dimensions
        dimension_sql = self.dimension_engine.apply_dimensions(parsed.dimensions)
        
        # 5. Generate final SQL
        sql = self._generate_sql(resolved_concepts, metric_sql, dimension_sql, parsed.filters)
        
        return sql
    
    def _parse_natural_language(self, query: str) -> ParsedQuery:
        """Parse natural language into structured components"""
        # Use LLM to extract intent, concepts, metrics, dimensions, filters
        prompt = f"""
        Parse this query: "{query}"
        
        Extract:
        - Intent (ranking, filtering, aggregation, etc.)
        - Concepts (customer, order, product, etc.)
        - Metrics (revenue, count, average, etc.)
        - Dimensions (time, geography, category, etc.)
        - Filters (conditions, date ranges, etc.)
        """
        
        response = self.llm.generate(prompt)
        return self._parse_llm_response(response)
    
    def _generate_sql(self, concepts: dict, metrics: dict, dimensions: dict, filters: list) -> str:
        """Generate SQL from semantic components"""
        
        # Build FROM clause
        from_clause = self._build_from_clause(concepts)
        
        # Build SELECT clause
        select_clause = self._build_select_clause(concepts, metrics, dimensions)
        
        # Build WHERE clause
        where_clause = self._build_where_clause(filters)
        
        # Build GROUP BY clause
        group_by_clause = self._build_group_by_clause(dimensions)
        
        # Build ORDER BY clause
        order_by_clause = self._build_order_by_clause(metrics)
        
        # Combine into final SQL
        sql = f"""
        SELECT {select_clause}
        FROM {from_clause}
        {where_clause}
        {group_by_clause}
        {order_by_clause}
        """
        
        return sql.strip()
```

## Key Capabilities

### Business Concept Abstraction
- **Entity Mapping**: Maps business concepts to database tables
- **Attribute Resolution**: Translates business terms to database columns
- **Relationship Modeling**: Defines business relationships between entities
- **Hierarchy Support**: Supports dimensional hierarchies (time, geography, etc.)

### Metric Calculation Engine
- **Predefined Metrics**: Business KPIs and calculations
- **Dynamic Aggregation**: SUM, COUNT, AVG, MIN, MAX operations
- **Filter Integration**: Business rules and constraints
- **Time Intelligence**: Period-over-period calculations

### Dimension Management
- **Hierarchical Dimensions**: Time, geography, product hierarchies
- **Drill-Down Support**: Navigate from summary to detail
- **Cross-Dimensional Analysis**: Multiple dimension combinations
- **Dynamic Filtering**: Dimension-based filtering

### Query Optimization
- **Semantic Optimization**: Optimize based on business context
- **Join Optimization**: Efficient table joins based on relationships
- **Index Utilization**: Leverage database indexes for performance
- **Caching Strategy**: Cache frequently used semantic queries

## Strengths

✅ **Business-Friendly**: Natural language maps to business concepts

✅ **Consistent Logic**: Centralized business rules and calculations

✅ **Performance Optimized**: Pre-optimized queries and data models

✅ **Scalable**: Handles complex enterprise data architectures

✅ **Governance**: Centralized data definitions and access control

✅ **Self-Service**: Enables business users to query data directly

✅ **Production Proven**: Used by companies like Looker, Tableau, Power BI

## Limitations

❌ **Model Complexity**: Requires significant upfront modeling effort

❌ **Schema Coupling**: Tightly coupled to specific database schemas

❌ **Maintenance Overhead**: Requires ongoing model maintenance

❌ **Learning Curve**: Complex semantic models can be difficult to understand

❌ **Flexibility Trade-offs**: Less flexible than direct SQL generation

❌ **Vendor Lock-in**: Often tied to specific BI platform implementations

## Implementation for Benchmark

### Semantic Model Configuration
```yaml
# config/semantic_model.yaml
version: "1.0"
name: "E-commerce Semantic Model"

data_sources:
  - name: "warehouse"
    type: "postgresql"
    connection: "${WAREHOUSE_CONNECTION_STRING}"
    
  - name: "operational"
    type: "mysql"
    connection: "${OPERATIONAL_CONNECTION_STRING}"

concepts:
  customer:
    description: "Business customer"
    entity: "customers"
    source: "warehouse"
    attributes:
      - name: "customer_id"
        source: "customers.id"
        type: "identifier"
        primary_key: true
      - name: "customer_name"
        source: "customers.name"
        type: "string"
        business_name: "Customer Name"
      - name: "customer_email"
        source: "customers.email"
        type: "string"
        business_name: "Email Address"
      - name: "customer_status"
        source: "customers.status"
        type: "enum"
        business_name: "Customer Status"
        values: ["active", "inactive", "suspended"]

  order:
    description: "Customer purchase"
    entity: "orders"
    source: "warehouse"
    attributes:
      - name: "order_id"
        source: "orders.id"
        type: "identifier"
        primary_key: true
      - name: "order_date"
        source: "orders.order_date"
        type: "date"
        business_name: "Order Date"
      - name: "order_status"
        source: "orders.status"
        type: "enum"
        business_name: "Order Status"
        values: ["pending", "completed", "cancelled", "refunded"]
      - name: "order_amount"
        source: "orders.amount"
        type: "decimal"
        business_name: "Order Amount"

metrics:
  revenue:
    description: "Total sales revenue"
    type: "sum"
    source: "order.order_amount"
    filters:
      - condition: "order.order_status = 'completed'"
    business_name: "Revenue"
    
  order_count:
    description: "Number of orders"
    type: "count"
    source: "order.order_id"
    filters:
      - condition: "order.order_status = 'completed'"
    business_name: "Order Count"
    
  average_order_value:
    description: "Average order value"
    type: "average"
    source: "order.order_amount"
    filters:
      - condition: "order.order_status = 'completed'"
    business_name: "Average Order Value"

dimensions:
  time:
    description: "Time dimension"
    hierarchy:
      - level: "year"
        source: "YEAR(order.order_date)"
        business_name: "Year"
      - level: "quarter"
        source: "QUARTER(order.order_date)"
        business_name: "Quarter"
      - level: "month"
        source: "MONTH(order.order_date)"
        business_name: "Month"
      - level: "day"
        source: "DATE(order.order_date)"
        business_name: "Day"

relationships:
  - from: "order"
    to: "customer"
    type: "many_to_one"
    join: "orders.customer_id = customers.id"
    description: "Order belongs to customer"
```

### Query Translation Engine
```python
class SemanticQueryEngine:
    def __init__(self, model_path: str):
        self.semantic_layer = SemanticLayer(model_path)
        self.llm = OpenAI(model="gpt-4")
    
    def process_query(self, question: str) -> str:
        """Process natural language query through semantic layer"""
        
        # 1. Parse and understand the question
        parsed = self._parse_question(question)
        
        # 2. Map to semantic concepts
        semantic_query = self._map_to_semantic_concepts(parsed)
        
        # 3. Generate SQL through semantic layer
        sql = self.semantic_layer.translate_query(semantic_query)
        
        return sql
    
    def _parse_question(self, question: str) -> dict:
        """Parse natural language question into structured format"""
        prompt = f"""
        Parse this business question: "{question}"
        
        Identify:
        1. Main entities (customer, order, product, etc.)
        2. Metrics to calculate (revenue, count, average, etc.)
        3. Dimensions to group by (time, geography, category, etc.)
        4. Filters to apply (date ranges, status, etc.)
        5. Sorting requirements (top N, order by, etc.)
        
        Return as JSON structure.
        """
        
        response = self.llm.generate(prompt)
        return json.loads(response)
    
    def _map_to_semantic_concepts(self, parsed: dict) -> str:
        """Map parsed question to semantic layer concepts"""
        
        # Build semantic query string
        semantic_parts = []
        
        # Add entities
        if parsed.get("entities"):
            semantic_parts.append(f"Entities: {', '.join(parsed['entities'])}")
        
        # Add metrics
        if parsed.get("metrics"):
            semantic_parts.append(f"Metrics: {', '.join(parsed['metrics'])}")
        
        # Add dimensions
        if parsed.get("dimensions"):
            semantic_parts.append(f"Group by: {', '.join(parsed['dimensions'])}")
        
        # Add filters
        if parsed.get("filters"):
            semantic_parts.append(f"Filters: {', '.join(parsed['filters'])}")
        
        # Add sorting
        if parsed.get("sorting"):
            semantic_parts.append(f"Sort by: {parsed['sorting']}")
        
        return " | ".join(semantic_parts)
```

### Evaluation Metrics
- **Concept Accuracy**: How well does it map business concepts?
- **Query Translation**: Does it generate correct SQL from semantic queries?
- **Performance**: How does semantic layer overhead affect query speed?
- **Business Logic**: Are business rules correctly applied?
- **Flexibility**: Can it handle complex business scenarios?

### Configuration
```yaml
# config.yaml
semantic_layer:
  model:
    path: "config/semantic_model.yaml"
    version: "1.0"
    
  translation:
    engine: "llm"
    model: "gpt-4"
    temperature: 0.1
    max_tokens: 2048
    
  optimization:
    enable_caching: true
    cache_ttl: 3600
    enable_optimization: true
    
  governance:
    enable_audit: true
    log_queries: true
    access_control: true
```

## Example Test Case

**Problem**: "Show me revenue by customer segment for the last quarter, comparing to the previous quarter"

**Semantic Translation**:
1. **Entity Resolution**: customer, revenue, customer_segment
2. **Metric Calculation**: revenue (SUM of completed orders)
3. **Dimension Application**: customer_segment, quarter
4. **Time Intelligence**: current quarter vs previous quarter
5. **Business Logic**: Only completed orders count toward revenue

**Generated SQL**:
```sql
WITH current_quarter_revenue AS (
  SELECT 
    c.segment as customer_segment,
    SUM(o.amount) as revenue
  FROM customers c
  JOIN orders o ON c.id = o.customer_id
  WHERE o.status = 'completed'
    AND o.order_date >= DATE_TRUNC('quarter', CURRENT_DATE)
    AND o.order_date < DATE_TRUNC('quarter', CURRENT_DATE) + INTERVAL '3 months'
  GROUP BY c.segment
),
previous_quarter_revenue AS (
  SELECT 
    c.segment as customer_segment,
    SUM(o.amount) as revenue
  FROM customers c
  JOIN orders o ON c.id = o.customer_id
  WHERE o.status = 'completed'
    AND o.order_date >= DATE_TRUNC('quarter', CURRENT_DATE) - INTERVAL '3 months'
    AND o.order_date < DATE_TRUNC('quarter', CURRENT_DATE)
  GROUP BY c.segment
)
SELECT 
  COALESCE(cq.customer_segment, pq.customer_segment) as customer_segment,
  cq.revenue as current_quarter_revenue,
  pq.revenue as previous_quarter_revenue,
  cq.revenue - pq.revenue as revenue_change,
  CASE 
    WHEN pq.revenue = 0 THEN NULL
    ELSE ((cq.revenue - pq.revenue) / pq.revenue) * 100
  END as revenue_growth_percent
FROM current_quarter_revenue cq
FULL OUTER JOIN previous_quarter_revenue pq ON cq.customer_segment = pq.customer_segment
ORDER BY cq.revenue DESC;
```

**Evaluation Criteria**:
- Did it correctly identify the need for time intelligence?
- Did it apply the business rule for completed orders only?
- Did it handle the quarter-over-quarter comparison properly?
- Did it calculate growth percentages correctly?
- Did it use the customer segment dimension appropriately?

## References

- [Looker Semantic Layer](https://looker.com/platform/semantic-layer)
- [Tableau Data Model](https://help.tableau.com/current/pro/desktop/en-us/datasource_datamodel.htm)
- [Power BI Semantic Models](https://learn.microsoft.com/en-us/power-bi/enterprise/service-premium-architecture)
- [Semantic Layer Architecture Patterns](https://www.databricks.com/blog/2020/02/19/semantic-layers-for-data-lakes.html)
