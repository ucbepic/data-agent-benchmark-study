# Categories & Representative Prompts

This taxonomy groups enterprise analysis challenges into **12 categories**.  
Each section explains **what the category covers**, **why it’s specifically hard for LLM-based agents**, and gives **full-sentence example prompts** you might ask an AI Analyst.

> ✍️ **How to contribute:** Add new prompts under the correct category or propose edits to descriptions. Keep prompts realistic, time-bounded, and self-contained (mention data sources or assumptions in the sentence).

---

## 1) Single-Source Structured Analytics (basic → complex)

**What it covers**  
Natural-language to SQL over a single database: filters, joins within one schema, aggregations, window functions, ranking, and date logic.

**Why it’s hard for LLMs**  
- Infers schema and join keys from names; fragile with cryptic columns.  
- Off-by-one errors in time filters, window frames, or ranking ties.  
- NULL semantics, distinct vs non-distinct, and semi-additive measures frequently misapplied.  
- Tends to generate non-optimal queries (Cartesian joins, unneeded CTEs).

**Representative prompts**  
1. “Within our Postgres warehouse, show me the top ten creators by total watch time for last week, breaking ties with total views.”  
2. “From the `employees_current` table in Snowflake, what is the headcount by department as of yesterday at 23:59 UTC?”  
3. “In our Redshift `sales` schema, rank the five SKUs with the largest week-over-week increase in scrap rate.”  
4. “Using our SaaS billing database, list enterprise-plan customers with more than $10,000 in unpaid invoices over the last 60 days.”

---

## 2) Cross-Source Federation & Stitching

**What it covers**  
Combining heterogeneous sources (e.g., Postgres, MySQL, SQL Server, MongoDB, Salesforce, Zendesk) into one answer; reconciling schemas and types; stitching identities.

**Why it’s hard for LLMs**  
- Different SQL dialects and data models (row vs document) require different query plans.  
- Must minimize data movement and push down filters; naive plans explode costs/latency.  
- Identity stitching requires consistent keys and precedence rules across systems.  
- Eventual consistency: results differ by freshness unless the plan explicitly handles it.

**Representative prompts**  
1. “Using Salesforce opportunities and Snowflake shipped revenue, compare pipeline value to recognized revenue for the last fiscal quarter.”  
2. “Combine sales from our US PostgreSQL database, EU MySQL database, and APAC SQL Server database into a single global daily time series for the past 90 days.”  
3. “Join Zendesk ticket counts with our internal account tiers in Snowflake to report first-response SLA performance by tier for last month.”  
4. “Create a unified customer table by stitching identities across our ecommerce site and retail POS systems.”

---

## 3) Semantic / Unstructured → Structured (deterministic intermediates)

**What it covers**  
Extracting structure from text (or other unstructured inputs) via NLP/LLMs, **persisting** the derived labels/scores, then performing standard SQL analysis.

**Why it’s hard for LLLMs**  
- Stochastic outputs need thresholds and persistence to be reproducible; “memory” is not acceptable.  
- Label drift and ambiguous categories require documented definitions and rerunnable pipelines.  
- Must surface precision/recall trade-offs and error rates in downstream aggregations.

**Representative prompts**  
1. “Identify businesses that are massage therapists from their descriptions and then list those with an average rating of at least 4.0, including the computed averages.”  
2. “Classify support tickets by sentiment and then report the median resolution time for negative-sentiment tickets during the last 30 days.”  
3. “Extract product feature requests from customer emails and summarize the top five requested features by frequency.”  
4. “From marketing landing-page text, tag each page with its primary persona and show the conversion rate by persona for last quarter.”

---

## 4) Orchestrated Pipelines (loops, conditionals, fan-out/fan-in) at scale

**What it covers**  
Multi-step workflows that require iteration, branching, retries, chunking, parallelization, and robust error handling; often across large datasets.

**Why it’s hard for LLMs**  
- Requires **planning + execution** beyond a single query; pure prompting is insufficient.  
- Idempotency, checkpointing, and partial failure recovery must be explicit.  
- Memory and context windows are irrelevant; compute must be pushed to the right engines.

**Representative prompts**  
1. “Find the top 100 customers by product usage in the past three months, fetch all of their support tickets, score the ticket sentiment, and return the customers at highest churn risk.”  
2. “Process 90 days of impression logs to compute click-through rate by creative and return the fifty best creatives with the required sample sizes.”  
3. “For SKUs that stocked out last week, call the carrier API to retrieve last-mile delay data and estimate lost revenue by SKU.”  
4. “Iterate through every microservice and compile open GitHub issues joined with each service’s usage and error rate for the past 14 days.”

---

## 5) Business Term Disambiguation (with hints / tribal metadata)

**What it covers**  
Applying canonical business definitions and assumptions to ambiguous terms (e.g., “active user”, “new customer”, “revenue”, “churn”).

**Why it’s hard for LLMs**  
- Multiple defensible interpretations; the model must **select and state** the definition used.  
- Needs to look up or accept provided metadata (metrics dictionary, governance rules).  
- Silent assumption changes across runs break consistency and trust.

**Representative prompts**  
1. “Show me our most active users this month, where ‘active’ is defined as total logged-in minutes.”  
2. “List our new customers from last week, where ‘new’ means the first successful KYC completion date.”  
3. “Identify our most valuable customers this quarter, using ARR rather than product usage as the value metric.”  
4. “Report churned users for June, where churn is defined as ninety consecutive days without a successful login.”

---

## 6) Temporal, Unit & Currency-Aware Business Metrics (incl. SCD)

**What it covers**  
Point-in-time analysis (SCD2), FX conversion at transaction timestamps, mixed units/timezones, and complex KPI calculations across changing dimensions.

**Why it’s hard for LLMs**  
- As-of joins over valid-from/to boundaries are easy to get wrong.  
- FX/units/timezones require correct reference tables and business calendars (e.g., week definitions, fiscal periods).  
- Semi-additive measures (e.g., inventory level) require special aggregation logic.

**Representative prompts**  
1. “Report net sales, profit margin, and average check by store for June 2025 using our Snowflake POS schema.”  
2. “Compute global revenue in USD for the last quarter using the foreign-exchange rate at each transaction timestamp.”  
3. “Show ARR by region as of March 15, 2024 based on historical territory assignments.”  
4. “Normalize temperature readings from Fahrenheit, Celsius, and Kelvin to hourly averages in Celsius for the last seven days.”

---

## 7) Entity Resolution & Source-of-Truth Arbitration

**What it covers**  
De-duplicating entities across systems, defining survivorship rules, and selecting authoritative sources based on freshness and completeness.

**Why it’s hard for LLMs**  
- Fuzzy matching and conflicting attributes require transparent rule-based resolution.  
- Picking the “golden record” demands lineage and justification, not heuristics hidden in a prompt.  
- Freshness vs completeness trade-offs must be explicit and repeatable.

**Representative prompts**  
1. “Provide a unique customer count by segment after merging duplicates across Salesforce and our billing database using email and domain rules.”  
2. “Tell me who our highest-revenue customer is right now, preferring real-time invoice data over delayed Salesforce ARR.”  
3. “Match patient records across two EHR systems using name, date of birth, and partial SSN, and then report the number of merged profiles.”  
4. “Create a unified product catalog by resolving duplicate SKUs between our ERP and ecommerce databases and indicate the chosen source for each item.”

---

## 8) Time-Series, Cohorts & Funnels

**What it covers**  
Event sequences over time: cohorting, retention, conversion funnels, attribution windows, and seasonality.

**Why it’s hard for LLMs**  
- Sessionization rules and attribution windows are subtle and domain-specific.  
- Late-arriving events and timezone boundaries easily corrupt metrics.  
- Requires consistent cohort definitions and reusability across runs.

**Representative prompts**  
1. “Build a signup → activation → paid funnel by acquisition channel for the last 28 days and report conversion rates at each step.”  
2. “Calculate 30/60/90-day retention by the user’s first-purchase cohort.”  
3. “Report cart abandonment rates by weekly cohort with a seven-day attribution window.”  
4. “Compute revenue seasonality by month for the past three years with a moving twelve-month average.”

---

## 9) Geospatial & Location-Aware Analysis

**What it covers**  
Spatial joins and filters, distance calculations, buffers, intersections, and working with geographic boundaries and projections.

**Why it’s hard for LLMs**  
- Geodesic vs planar distances, CRS conversions, and unit consistency require explicit handling.  
- Large spatial joins need indexing and careful predicate pushdown.  
- Boundary edge cases (on the line/within buffers) must be defined and tested.

**Representative prompts**  
1. “List orders delivered more than ten kilometers from the nearest distribution center and include the delivery times.”  
2. “Identify rides that began within two hundred meters of a rail station during weekday peak hours.”  
3. “Find stores with overlapping five-kilometer trade areas and estimate cannibalization risk by overlap size.”  
4. “Compute average delivery distance by city boundary rather than ZIP code for last month.”

---

## 10) External APIs & SaaS Fusion (with quotas / partial data)

**What it covers**  
Ingesting and joining external API/SaaS data with internal facts while respecting pagination, rate limits, retries, and schema drift.

**Why it’s hard for LLMs**  
- Needs idempotent ingestion, backoff strategies, and checkpointing—not just API calls in prose.  
- Partial/incomplete responses must be detected and reconciled before analysis.  
- Schemas and semantics often drift; the plan must validate and adapt.

**Representative prompts**  
1. “For the top twenty internal services, retrieve open GitHub issues and join them with service usage to rank the most impacted services.”  
2. “Combine Zendesk SLA metrics with our Snowflake account tiers to report median first response time by tier for last quarter.”  
3. “Pull the latest FX rates from the API and recompute today’s multi-currency revenue totals, caching responses to respect rate limits.”  
4. “Fetch marketing campaign stats from the ad platform API and align them with our internal conversions to compute cost per acquisition by campaign.”

---

## 11) Governance, Compliance & Document-Grounded Rules

**What it covers**  
Policy-aware analytics: enforcing row-level security (RLS), masking PII/PHI, extracting rules from policy/contract documents, and **citing** the applied rules.

**Why it’s hard for LLMs**  
- Policies must be executed, not summarized; leakage at row level is unacceptable.  
- Document versions and clause references require deterministic extraction and citation.  
- Minimum-k aggregation thresholds and redaction rules need coded safeguards.

**Representative prompts**  
1. “Compute average salary by organization while respecting row-level security, and ensure that no individual-level data is exposed.”  
2. “Determine breach counts by support tier for last quarter using our SLA v3.2 document and include citations to the relevant clauses.”  
3. “Produce the revenue recognition schedule for Contract A123 according to ASC-606 and output the associated journal entries.”  
4. “Generate a de-identified 30-day hospital readmission rate by facility that complies with our PHI masking policy.”

---

## 12) Advanced Analytics: Statistical & Graph / Network

**What it covers**  
Statistical testing and distribution analysis (A/B tests, confidence intervals, control limits) and graph analytics (paths, centrality, community detection).

**Why it’s hard for LLMs**  
- Must choose appropriate tests, validate assumptions, and report uncertainty (CIs/p-values).  
- Multiple comparisons and guardrails are often ignored without explicit requirements.  
- Graph traversal at scale needs efficient algorithms and cycle handling; naive SQL recursions can be exponential.

**Representative prompts**  
1. “Evaluate our A/B test by calculating lift, confidence intervals, and the p-value for the primary conversion metric.”  
2. “Identify transaction chains that connect flagged accounts within five hops and list the chains with the fewest intermediate accounts.”  
3. “Compute the PageRank of users in our referral network and return the top twenty influencers.”  
4. “Estimate the defect rate control limits for our manufacturing line using three standard deviations from the historical mean.”

---

## Notes for Contributors

- Keep prompts **self-contained**: name data sources (DBs/tables/APIs) or state assumptions in the sentence.  
- Prefer **time-bounded** queries (“last 30 days”, “Q1 2024”) for repeatability.  
- When ambiguity exists, **state the intended definition** (e.g., “active = logged-in minutes”).  
- Avoid toy-only prompts; aim for tasks representative of real enterprise data and policies.

