# UCB Query Benchmark: Real Enterprise Data Problems for AI

A community-driven benchmark to understand **why AI fails on real enterprise data problems** and **which techniques actually work**.

This is a partnership between UC Berkeley (EPIC Data Lab) and PromptQL to create the first benchmark that:
- **Documents real failures** of AI tools in enterprise settings
- **Tests multiple techniques** (RAG, Agents, Text-to-SQL, etc.) against the same problems  
- **Measures what works** with deterministic, reproducible evaluations

> 🎯 **We need your help:** Share the data problems where AI tools failed you, and help us test solutions that might actually work.

---

## The Problem

Every enterprise is trying to use AI for data analysis. They're using Cursor for SQL, Claude with MCP servers, ChatGPT with Code Interpreter, and countless other tools. **And they're all hitting the same walls.**

We've seen the same story repeatedly:
- The demo works perfectly on clean, single-table data
- It breaks immediately on real enterprise data with multiple sources, ambiguous schemas, and business logic
- No one knows which technique (RAG, Agents, Fine-tuning) would actually solve their problem

**This benchmark aims to:**
1. Collect real enterprise data problems where current AI tools fail
2. Test different AI techniques against these problems systematically  
3. Provide clear evidence of what works, what doesn't, and why

---

## How to Contribute

### 1. Share Your Real-World Problems
**We want to hear about your failures.** 

Edit [`EXAMPLES.md`](./EXAMPLES.md) to add:
- **The problem you tried to solve** (be specific about data sources, complexity)
- **What tools/approaches you tried** (Claude, GPT-4, Cursor, custom agents)
- **Exactly how they failed** (wrong results, timeouts, hallucinations)
- **Your hypothesis** for why they failed
- **What a working solution would need** to handle

Example contribution:
```markdown
**Problem:** "Show me customers at risk of churning by combining Salesforce opportunity data with product usage logs"
**What failed:** Claude with database MCP server
**How it failed:** Couldn't handle the date misalignment between systems, generated SQL with wrong join keys
**Why:** No understanding that Salesforce uses fiscal quarters while usage logs use calendar months
**Solution needs:** Temporal alignment logic, business calendar awareness
```

### 2. Propose Techniques to Test
Have an idea for an approach that might work better? Add it to the techniques list:
- Tool Calling with structured schemas
- Multi-agent systems with specialized roles
- Graph RAG over enterprise data
- Semantic layer + LLM
- Your novel approach

### 3. Run Evaluations
Help us test techniques against our problem set:
1. Pick a technique from `techniques/`
2. Run it against problems in `EXAMPLES.md`
3. Report results with full traces
4. Document what worked and what didn't

---

## Techniques Under Test

We're systematically testing these approaches against real enterprise problems:

| Technique | Description | Status |
|-----------|-------------|---------|
| `techniques/tool-calling/` | Function calling with database tools | 🟡 In Progress |
| `techniques/text-to-sql/` | Direct natural language to SQL | 🟡 In Progress |
| `techniques/langgraph-agent/` | Multi-step planning with LangGraph | 🔴 Planned |
| `techniques/rag-on-data/` | RAG over database schemas and docs | 🔴 Planned |
| `techniques/graph-rag/` | Graph-based RAG for relationships | 🔴 Planned |
| `techniques/semantic-layer/` | Business logic layer + LLM | 🔴 Planned |
| `techniques/custom/` | Novel approaches from contributors | 🔵 Open for PRs |

Each technique folder contains:
- `ARCHITECTURE.md` - How the technique works
- `implementation/` - Runnable code
- `results/` - Evaluation results on benchmark problems
- `analysis.md` - What worked, what didn't, and why

---

## Repository Structure

```
.
├── README.md                    # This file
├── EXAMPLES.md                  # Real enterprise problems and failures
├── techniques/                  # Approaches being tested
│   ├── tool-calling/           
│   │   ├── ARCHITECTURE.md     # How tool calling works
│   │   ├── implementation/     # Runnable code
│   │   └── results/            # Evaluation results
│   ├── text-to-sql/
│   ├── langgraph-agent/
│   └── ...
├── src/                         # Evaluation framework (in development)
│   ├── common_scaffold/         # Core utilities
│   ├── query_*/                 # Test datasets
│   └── requirements.txt        
└── evaluations/                 # Results and analysis
    └── comparison.md            # Cross-technique comparison
```

---

## What Makes This Different

**Not another leaderboard.** We're not ranking models on clean datasets. We're:
- Documenting **specific failure modes** in production
- Testing **complete techniques** (not just models)
- Providing **detailed failure analysis** (not just scores)
- Building **reproducible solutions** (not just benchmarks)

**Real problems, not toy examples.** Every problem in this benchmark:
- Comes from an actual enterprise use case
- Has documented failure cases with current tools
- Requires production-grade handling (errors, scale, governance)

**Techniques, not just prompts.** We test:
- Complete architectures (agents, RAG, tools)
- Error handling and recovery strategies
- Performance at scale
- Deterministic, reproducible approaches

---

## Current Status

**✅ Completed:**
- Initial problem collection from enterprise partners
- Basic evaluation framework
- First 5 test datasets (GoogleLocal, BookReview, Yelp, StockIndex, StockMarket)

**🟡 In Progress:**
- Expanding problem documentation with failure analysis
- Implementing technique comparison framework
- Testing initial techniques (tool-calling, text-to-sql)

**🔴 Need Help With:**
- **More real-world failures** - What broke for you?
- **Novel techniques** - What might work better?
- **Evaluation runs** - Help test techniques at scale
- **Failure analysis** - Why exactly do these tools fail?

---

## Getting Started

### For Problem Contributors
1. Read [`EXAMPLES.md`](./EXAMPLES.md) to see existing problems
2. Add your own failures and hypotheses
3. Submit a PR with title like `examples: add Salesforce-MongoDB join failures`

### For Technique Contributors  
1. Check `techniques/` for existing approaches
2. Propose new techniques with an `ARCHITECTURE.md`
3. Implement and test against problems in `EXAMPLES.md`
4. Submit results with full traces

### For Evaluators
1. Set up the environment:
   ```bash
   git clone <repo>
   cd ucb-query-benchmark
   pip install -r src/requirements.txt
   ```
2. Pick a technique and problem set
3. Run evaluations and document results
4. Share findings in `evaluations/`

---

## Quality Bar

**For Problem Contributions:**
- [ ] Based on real enterprise scenario you've encountered
- [ ] Includes specific tools/approaches that failed
- [ ] Documents the exact failure mode
- [ ] Provides hypothesis for root cause
- [ ] Describes what a solution would need

**For Technique Contributions:**
- [ ] Clear architecture documentation
- [ ] Runnable implementation
- [ ] Handles real enterprise complexity
- [ ] Deterministic and reproducible
- [ ] Includes failure recovery strategy

---

## Join the Discussion

- **Discord**: [Join our server](#) for real-time discussion
- **Issues**: Report bugs or propose enhancements
- **Discussions**: Share experiences and hypotheses

---

## License

MIT License for code and specifications. Individual datasets may have their own licenses.

## Acknowledgments

This benchmark is a collaboration between:
- **UC Berkeley EPIC Data Lab** - Academic research on data systems
- **PromptQL** - Enterprise data intelligence platform
- **You** - The practitioners dealing with these problems daily

We especially thank the enterprises who shared their failures and helped us understand why AI tools break in production.
