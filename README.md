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

Our benchmark covers 12 categories of enterprise data analysis challenges:

1. **Single-Source Structured Analytics**: Natural-language to SQL over a single database with filters, joins, aggregations, window functions, ranking, and date logic.
2. **Cross-Source Federation & Stitching**: Combining heterogeneous sources (Postgres, MySQL, SQL Server, MongoDB, Salesforce, Zendesk) into one answer while reconciling schemas and types.
3. **Integrating Unstructured Data**: Extracting structure from text via NLP/LLMs, persisting derived labels/scores, then performing standard SQL analysis.
4. **Production-Grade Control Flow**: Multi-step workflows requiring iteration, branching, retries, chunking, parallelization, checkpointing, and robust error handling.
5. **Business Term Disambiguation**: Applying canonical business definitions and assumptions to ambiguous terms (e.g., "active user", "new customer", "revenue", "churn").
6. **Temporal, Unit & Currency-Aware Business Metrics**: Point-in-time analysis (SCD2), FX conversion at transaction timestamps, mixed units/timezones, and complex KPI calculations.
7. **Entity Resolution & Source-of-Truth Arbitration**: De-duplicating entities across systems, defining survivorship rules, and selecting authoritative sources.
8. **Time-Series, Cohorts & Funnels**: Event sequences over time including cohorting, retention, conversion funnels, attribution windows, and seasonality.
9. **External APIs, SaaS, and Open-Web Fusion**: Ingesting and joining external API/SaaS data and open-web content with internal facts while respecting pagination, rate limits, and caching.
10. **Governance, Compliance & Document-Grounded Rules**: Policy-aware analytics enforcing row-level security, masking PII/PHI, and extracting rules from policy documents.
11. **Advanced Analytics: Statistical and Graph/Network**: Statistical testing, distribution analysis, and graph analytics including paths, centrality, and community detection.
12. **Implicit Relationship Discovery**: Inferring and validating relationships when explicit keys or well-defined join paths don't exist, including fuzzy matching and data-driven path discovery.

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

**Current Progress:** We have made progress on several categories as seen in the query datasets in `src/`. However, we still want your contributions to improve these categories and expand into the remaining ones.

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
