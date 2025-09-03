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

---

## What to contribute

You can submit two kinds of issues:

1) **Problem** — A real enterprise analysis task where AI failed  
2) **Technique** — An approach you believe works better (semantic layers, RAG, agents, tool calling, etc.)

> 🔒 **Privacy & scope**  
> Do **not** share production data, credentials, or PII/PHI. We only need enough **business context and shape** for UCB to synthesize a representative case internally. See [SANITIZATION.md](SANITIZATION.md).

---

## What “enough detail” means (for UCB to reproduce)

When you submit a **Problem**, please give:

- **Business question** — the exact ask (e.g., “Calculate churn from Salesforce + product usage for Q3 FY2024”)
- **Time window & calendars** — e.g., “Q3 FY2024 (FY starts July), timezone UTC; late data up to T+3 days”
- **Data sources & backends** — named systems/tables or objects (no data), scale (“~10M rows”), freshness
- **Entities & identifiers** — `account_id`, `user_id`, email domain, etc., plus which system is source of truth
- **Join logic & rules** — how tables/systems should be stitched; known exclusions (test users, cancelled orders)
- **Expected output *shape*** — columns & types, grain, and an example row *format* (values optional)
- **Failure mode** — what the AI did wrong (e.g., wrong fiscal calendar; joined on company name; ignored SCD)
- **Tools tried** — which LLMs/agents/semantic layers, and any relevant settings

For **Techniques**, include: **where it applies**, **input/output contract**, **requirements** (e.g., semantic layer), and any **observed results** or known **limits**.

---

## How to contribute

- 👉 **Open an issue**: [Create an issue](https://github.com/ucbepic/data-agent-benchmark-study/issues/new/choose)
  - Choose **Problem** or **Technique**
  - Fill the form (no uploads of proprietary data, please)

- Browse **categories** we track in [CATEGORIES.md](CATEGORIES.md)  
- See detailed **example submissions** in [EXAMPLES.md](EXAMPLES.md)

---

## What happens next (triage → recreate → evaluate)

We label and triage incoming issues:

- `type: problem` / `type: technique`  
- `category: …` (from our taxonomy)  
- `status: needs info → accepted → in synthesis → evaluated → published`  

Once we have essence‑level detail, the UCB team will:
1) Recreate the case internally (private benchmark repo)  
2) Run techniques over the recreated case  
3) Share results and lessons learned publicly

See [docs/TRIAGE.md](docs/TRIAGE.md) for label definitions and status meanings.

---

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

**Ready to contribute?** [Submit a Problem](https://github.com/ucbepic/data-agent-benchmark-study/issues/new?template=problem_report.yml) or [Submit a Technique](https://github.com/ucbepic/data-agent-benchmark-study/issues/new?template=technique_submission.yml).