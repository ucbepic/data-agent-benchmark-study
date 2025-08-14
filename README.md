# UCB Query Benchmark

A community-driven benchmark for evaluating **AI Data Analysts**—systems that answer questions in natural language and deterministically plan/execute analysis across enterprise data (SQL/NoSQL, SaaS APIs, documents, the open web).

This project defines **categories of realistic enterprise questions**, along with **specs for reproducible tasks** (schemas, inputs, expected outputs, and scoring) so we can compare AI agents to a strong human analyst baseline. Developed in partnership between UC Berkeley (EPIC Data Lab) and PromptQL, this benchmark aims to understand why current AI/data tools fail in real enterprise scenarios.

> 🧭 Start with [`CATEGORIES.md`](./CATEGORIES.md) to see the taxonomy and propose prompts and tasks.

---

## Goals

- **Realistic**: Mirror messy, multi-source, policy-aware enterprise scenarios.
- **Deterministic**: Require persisted intermediates and reproducible plans.
- **Measurable**: Provide gold outputs, tolerances, and clear scoring rules.
- **Extensible**: Easy to add new categories, tasks, and datasets.

## Benchmark Categories

Our benchmark plans to covere 12 categories of enterprise data analysis challenges so far:

1. **Single-Source Structured Analytics**: Basic to complex SQL queries with joins, window functions, and ranking operations.
2. **Cross-Source Federation & Stitching**: Integrating heterogeneous systems and reconciling schemas across multiple data sources.
3. **Semantic/Unstructured → Structured**: Using LLM/NLP to classify/extract data, then persisting results for SQL analysis.
4. **Orchestrated Pipelines**: Complex workflows with loops, conditionals, and fan-out/fan-in operations at scale.
5. **Business Term Disambiguation**: Applying provided definitions and surfacing assumptions for ambiguous business terms.
6. **Temporal, Unit & Currency-Aware Metrics**: Handling SCD2 queries, foreign exchange, and complex time-based calculations.
7. **Entity Resolution & Source-of-Truth Arbitration**: Deduplication across systems and choosing authoritative sources.
8. **Time-Series, Cohorts & Funnels**: Event sequences, retention analysis, and conversion funnel tracking.
9. **Geospatial & Location-Aware Analysis**: Spatial joins, distance calculations, and location-based insights.
10. **External APIs & SaaS Fusion**: Integrating third-party APIs with rate limits, pagination, and partial data.
11. **Governance, Compliance & Document-Grounded Rules**: Enforcing RLS/PII policies and extracting rules from documents.
12. **Advanced Analytics: Statistical & Graph/Network**: Significance testing, distributions, and graph traversal algorithms.

---

## Repository Structure

```
.
├─ CATEGORIES.md                 # Category descriptions + example prompts
├─ src/                          # Current UCB implementation (in development)
│  ├─ common_scaffold/           # Core framework and utilities
│  ├─ query_*/                   # Individual benchmark datasets
│  └─ requirements.txt           # Python dependencies
```

---

## Contributing

We want to hear from **practitioners building AI/data systems** about their real-world challenges. Have you tried Cursor to write SQL, or Claude with database MCP servers, only to find they don't work reliably in production? We want to understand:

- **What specific problems** are you trying to solve?
- **Where do current tools fail** and why?
- **What would a reliable solution** look like for your use case?

### Share Your Real-World Problems
- **Describe the scenario** you're trying to solve
- **Document the failures** you've encountered
- **Explain your hypothesis** for why current tools don't work
- **Suggest what a better solution** would need to handle

### Improve the Benchmark
- Edit [`CATEGORIES.md`](./CATEGORIES.md) to add new categories or prompts
- Keep it concise: *What it tests*, *Why it's hard*, and **full-sentence prompts** that a business user might actually ask
- Submit a PR with a descriptive title (e.g., `docs: add geo prompts to #9`)

---

## Quality Bar (PR Checklist)

* [ ] **Real-world**: Describe actual problems you've encountered in production.
* [ ] **Specific**: Include concrete examples of where current tools fail.
* [ ] **Hypothesis**: Explain your theory for why the failure occurs.
* [ ] **Actionable**: Suggest what a better solution would need to handle.
* [ ] **Clarity**: Use clear, specific language that other practitioners can understand.

---

## Current Status

The `src/` directory contains the current UCB implementation, which is still under development. The team is working on:

- **Framework improvements** for better agent evaluation
- **Additional datasets** across the 12 categories
- **Understanding real-world failures** of current AI/data tools
- **Building reliable solutions** based on practitioner feedback

**Current Progress:** We have made progress on the first three categories (Single-Source Structured Analytics, Cross-Source Federation & Stitching, and Semantic/Unstructured → Structured) as seen in the query datasets in `src/`. However, we still want your contributions to improve these categories and expand into the remaining nine.

**We're primarily seeking contributions on:**
- **Real-world problems** you've encountered with AI/data tools
- **Failure analysis** of why current solutions don't work
- **Category refinements** and new prompt examples
- **Domain expertise** for realistic enterprise scenarios

---

## License

MIT for code & specs. Data files may carry their own licenses—include notices where applicable.

## Code of Conduct

Be respectful. Assume good faith. Prefer constructive, reproducible critique.
