# Data Agent Benchmark

**AI fails at enterprise data analysis. We're building a benchmark to help.**

## The Problem

Current AI tools consistently fail on production data analysis tasks:
- Business analysts struggle with AI-generated SQL that misunderstands business logic
- Data teams fight with agents that can't handle multi-database queries  
- Engineers build data agents that work on demos but fail on real datasets
- Organizations waste resources on solutions that don't scale

## Why We Created This Repository

We need your help to build a benchmark that reflects real enterprise data challenges, not toy problems. By submitting the problems you actually face and the techniques you've tried, you're helping create the first crowdsourced benchmark for AI data analysis. Everything will be open source so anyone can run evaluations and see what actually works.

## How to Contribute

**Submit real problems or techniques by creating a GitHub issue.**

### Submit a Problem
Create an issue titled `[PROBLEM] Your description` with:
- What you tried to do
- What tools/approach you used  
- How it failed
- Any context that matters

Example:
```
Title: [PROBLEM] Calculate customer churn from Salesforce + usage data

I tried: Using Claude to write SQL joining CRM and product databases
It failed: Didn't handle different customer ID formats between systems
Context: Salesforce uses account IDs, product DB uses user UUIDs
```

### Submit a Technique
Create an issue titled `[TECHNIQUE] Your approach` with:
- Name of the technique/tool
- Brief description
- Why you think it might work better

Example:
```
Title: [TECHNIQUE] Semantic layer + LLM

Approach: Pre-define business logic in semantic layer, then have LLM query that
Why: Eliminates ambiguity about metrics like "revenue" or "active user"
```

## Example Challenge Categories

We've come up with some challenge areas to get the ball rolling, but this isn't exhaustive - we need your input:

- **Single-Source Structured Analytics** - SQL generation, joins, aggregations
- **Cross-Source Federation** - Combining heterogeneous databases
- **Unstructured Data Integration** - Extracting structure from text/documents
- **Production Control Flow** - Multi-step workflows, error handling
- **Business Term Disambiguation** - Handling ambiguous definitions
- **Temporal & Currency Metrics** - Time-series, FX conversion, SCD
- **Entity Resolution** - De-duplication across systems
- **Time-Series & Cohorts** - Funnels, retention, attribution
- **External API Integration** - Rate limits, pagination, schema drift
- **Governance & Compliance** - Row-level security, PII masking
- **Advanced Analytics** - Statistical tests, graph algorithms
- **Implicit Relationship Discovery** - Fuzzy matching, key derivation

See [CATEGORIES.md](CATEGORIES.md) for detailed descriptions and [EXAMPLES.md](EXAMPLES.md) for real failure cases.

## Sample Dataset

Are you building a data analysis agent and curious about what kinds of queries and data you'll need to handle? One example dataset and set of queries can be found in `src/query_yelp/` - it includes multi-source data, nested JSON, missing values, and entity resolution challenges that mirror real enterprise problems.

## Current Status

We're actively collecting real problems from practitioners, testing initial techniques across the benchmark suite, and building an automated evaluation framework. Watch this repository for regular updates on technique performance and new insights.

---

**Ready to contribute?** [Create an issue](https://github.com/ucbepic/data-agent-benchmark/issues/new/choose) with your problem or technique.