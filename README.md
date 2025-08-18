# UCB Query Benchmark

**AI fails at enterprise data analysis. We're building a benchmark to fix this.**

A collaboration between [UC Berkeley EPIC Data Lab](https://epic.berkeley.edu) (Prof. Aditya Parameswaran) and [PromptQL](https://promptql.io) to create the first benchmark that measures what actually works for AI-powered data analysis.

## Who This Is For

You, if you've tried using AI for data analysis and hit walls:
- Business analysts struggling with ChatGPT + spreadsheets
- Data analysts fighting with AI-generated SQL
- AI engineers building data agents that don't work
- Anyone who's watched AI tools fail on real data problems

## What You Get

Submit your problems or techniques, and we'll:
1. **Build a comprehensive benchmark** based on real practitioner challenges
2. **Test your techniques** against the full benchmark suite
3. **Share detailed results** showing what works and what doesn't
4. **Open source everything** so you can run it yourself

## How to Contribute

**Just create a GitHub Issue. That's it.**

### Option 1: Submit a Problem
Create an issue titled `[PROBLEM] Your description` with:
- What you tried to do
- What tools/approach you used  
- How it failed
- Any context that matters

Example:
```
Title: [PROBLEM] Calculate customer churn from Salesforce + usage data

I tried: Using Claude to write SQL joining our CRM and product databases
It failed: Didn't handle the different customer ID formats between systems
Context: Salesforce uses account IDs, product DB uses user UUIDs
```

### Option 2: Submit a Technique
Create an issue titled `[TECHNIQUE] Your approach` with:
- Name of the technique/tool
- Brief description
- Why you think it might work better

Example:
```
Title: [TECHNIQUE] Semantic layer + LLM

Approach: Pre-define business logic in a semantic layer, then have LLM query that
Why: Eliminates ambiguity about metrics like "revenue" or "active user"
```

## Current Status

- **Collecting**: Real problems from practitioners (submit yours!)
- **Testing**: Initial techniques (Text-to-SQL, Tool Calling, RAG)
- **Building**: Evaluation framework with deterministic scoring

## The Team

- **UC Berkeley EPIC Data Lab**: Academic rigor in data systems research
- **PromptQL**: Enterprise data intelligence platform
- **You**: The practitioners who know what's actually broken

## Get Results

We'll regularly publish:
- Benchmark updates as new problems are added
- Technique evaluation results
- What's working and what's not

Watch this repo to get notified of updates.

---

**Ready?** [Create an issue](https://github.com/[your-repo]/issues/new) with your problem or technique.
