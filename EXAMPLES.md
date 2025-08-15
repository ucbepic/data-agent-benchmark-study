# Real Enterprise Data Problems Where AI Fails

This document collects **actual problems** that practitioners have tried to solve with AI tools, **how those tools failed**, and **what might work better**.

> 📝 **How to contribute:** Add your real-world failures below. Include the specific tools you tried, exactly how they failed, and your hypothesis for why. Keep examples concrete and based on actual experience.

---

## Problem Areas

We've identified 12 common areas where AI consistently fails on enterprise data. For each, we document real failures and patterns.

### 1. Single-Source SQL Generation

**The Promise:** "Just describe what you want in English and AI will write the SQL"

**Reality Check:**
- **Problem tried:** "Show me top 10 customers by revenue last quarter"
- **Tool used:** Claude with database schema  
- **How it failed:** Generated SQL with wrong fiscal quarter calculation, didn't handle partial months correctly
- **Root cause:** No understanding of business calendars, fiscal years vs calendar years
- **Also failed on:** Window functions with complex frames, handling NULLs in aggregations, tie-breaking in rankings

**What practitioners report:**
> "GPT-4 writes syntactically correct SQL that's semantically wrong. It doesn't understand our week starts on Sunday, that 'revenue' means recognized not booked, or that we exclude test accounts."

**Specific failures we've seen:**
```sql
-- What AI generated:
SELECT customer_id, SUM(amount) as revenue
FROM transactions  
WHERE date >= '2024-10-01' AND date <= '2024-12-31'
GROUP BY customer_id
ORDER BY revenue DESC
LIMIT 10

-- What was actually needed:
SELECT c.customer_id, SUM(t.recognized_amount) as revenue
FROM transactions t
JOIN customers c ON t.customer_id = c.id
WHERE t.recognition_date >= fiscal_quarter_start('Q4', 2024)
  AND t.recognition_date < fiscal_quarter_end('Q4', 2024) + INTERVAL '1 day'
  AND c.is_test = false
  AND t.status = 'recognized'
GROUP BY c.customer_id
ORDER BY revenue DESC, c.customer_id -- deterministic tie-breaking
LIMIT 10
```

---

### 2. Multi-Source Data Federation

**The Promise:** "AI can query across all your databases"

**Reality Check:**
- **Problem tried:** "Compare pipeline in Salesforce to recognized revenue in our data warehouse"
- **Tool used:** LangChain agent with SQL tools for both databases
- **How it failed:** 
  - Pulled entire tables into memory causing OOM
  - Didn't handle different definitions of "customer" between systems
  - No awareness that Salesforce opportunities don't map 1:1 to warehouse invoices
- **Root cause:** No query pushdown optimization, no entity resolution strategy, no understanding of business relationships

**What practitioners report:**
> "The agent tried to JOIN a 10M row table from Postgres with Salesforce by pulling both into pandas. After 20 minutes it crashed. Even if it worked, the opportunity stages don't match our revenue recognition stages."

---

### 3. Unstructured Data Extraction

**The Promise:** "AI can structure any text data for analysis"

**Reality Check:**
- **Problem tried:** "Categorize support tickets by issue type and analyze resolution time"
- **Tool used:** GPT-4 API to classify tickets, then SQL for analysis
- **How it failed:**
  - Different categories each run (non-deterministic)
  - No way to update misclassified tickets
  - Couldn't explain why tickets were categorized certain ways
- **Root cause:** Stochastic classification without persistence, no audit trail, no human-in-the-loop correction

**What practitioners report:**
> "We ran the same classification three times and got three different distributions. Customer complaint about 'login issues' was classified as 'authentication', 'user error', and 'technical issue' in different runs."

---

### 4. Complex Multi-Step Workflows

**The Promise:** "Agents can handle complex analytical workflows"

**Reality Check:**
- **Problem tried:** "For each customer, get their usage data, support tickets, and payment history, then identify churn risks"
- **Tool used:** AutoGPT-style agent
- **How it failed:**
  - Timeout after 200+ API calls
  - No progress save/resume
  - Kept re-fetching same data
  - Final result was incomplete with no indication of what was missed
- **Root cause:** No execution plan, no state management, no partial failure handling

**What practitioners report:**
> "The agent made 847 API calls, hit rate limits, waited, tried again, then gave up. We had no idea how far it got or what it was trying to do."

---

### 5. Business Term Ambiguity

**The Promise:** "AI understands business context"

**Reality Check:**
- **Problem tried:** "Show me our active users"
- **Tool used:** Cursor to write SQL
- **How it failed:** Used last login date when we define "active" as "performed revenue-generating action in last 30 days"
- **Root cause:** No access to business glossary, no mechanism to ask for clarification

**What practitioners report:**
> "Every team has different definitions. 'Customer' means account to Sales, user to Product, and billing entity to Finance. The AI just picks one randomly."

---

### 6. Time-Based Business Logic

**The Promise:** "AI handles temporal queries naturally"

**Reality Check:**
- **Problem tried:** "Calculate MRR as of March 15, 2024"
- **Tool used:** Claude with SQL access
- **How it failed:** 
  - Used current subscription states, not historical
  - Didn't handle mid-month upgrades/downgrades
  - Wrong currency conversion rates (used today's rates)
- **Root cause:** No SCD2 awareness, no point-in-time joins, no temporal business logic

**Specific example that failed:**
```python
# What AI tried:
mrr = subscriptions.query("status == 'active'").monthly_amount.sum()

# What was needed:
mrr = calculate_mrr_as_of(
    date='2024-03-15',
    include_trials=False,
    fx_rates=historical_fx_rates('2024-03-15'),
    proration_method='daily',
    recognition_rules=revenue_recognition_policy_v2
)
```

---

### 7. Entity Resolution

**The Promise:** "AI can match records across systems"

**Reality Check:**
- **Problem tried:** "Deduplicate customer records between CRM and billing system"
- **Tool used:** GPT-4 with database access
- **How it failed:**
  - Matched "John Smith" records that were different people
  - Didn't match "IBM" with "International Business Machines"
  - No confidence scores or explanation for matches
- **Root cause:** No fuzzy matching strategy, no domain-specific rules, no human review process

---

### 8. Event Sequences and Funnels

**The Promise:** "Describe your funnel and AI will calculate it"

**Reality Check:**
- **Problem tried:** "Calculate our signup to paid conversion funnel with 7-day attribution window"
- **Tool used:** ChatGPT to generate SQL
- **How it failed:**
  - Wrong attribution (last-touch vs first-touch)
  - Didn't handle users who entered funnel multiple times
  - Timezone issues corrupted day boundaries
- **Root cause:** No sessionization logic, no attribution model selection, no timezone handling

---

### 9. External API Integration

**The Promise:** "AI agents can gather data from any API"

**Reality Check:**
- **Problem tried:** "Get GitHub issues for our repos and match with deployment incidents"
- **Tool used:** LangChain agent with API tools
- **How it failed:**
  - No pagination handling (only got first 100 issues)
  - No rate limit respect (got blocked)
  - No caching (repeated same calls)
  - Couldn't match issues to incidents (different ID formats)
- **Root cause:** No API state management, no retry logic, no data reconciliation strategy

---

### 10. Compliance and Governance

**The Promise:** "AI respects data governance rules"

**Reality Check:**
- **Problem tried:** "Average salary by department"
- **Tool used:** Text-to-SQL with GPT-4
- **How it failed:** 
  - Returned individual salaries for departments with <5 people
  - Included terminated employees who should be excluded
  - No audit log of who accessed what data
- **Root cause:** No row-level security enforcement, no PII detection, no audit trail

**What practitioners report:**
> "It happily returned SSNs when asked for 'employee identifiers'. We had to shut it down immediately."

---

### 11. Statistical Analysis

**The Promise:** "AI can run statistical tests"

**Reality Check:**
- **Problem tried:** "Is our A/B test significant?"
- **Tool used:** Code Interpreter
- **How it failed:**
  - Used t-test on non-normal data
  - No multiple comparison correction
  - Ignored clustering in the data
  - Reported p-value without confidence intervals
- **Root cause:** No assumption checking, no guardrail metrics, wrong test selection

---

### 12. Discovering Hidden Relationships

**The Promise:** "AI finds insights in your data"

**Reality Check:**
- **Problem tried:** "Find which support tickets relate to the same issue"
- **Tool used:** Claude with database access
- **How it failed:**
  - Only found exact title matches
  - Couldn't identify issues described differently
  - No confidence scoring for relationships
  - No way to validate or correct discoveries
- **Root cause:** No semantic similarity, no clustering strategy, no human-in-the-loop validation

---

## Contributing Your Failures

**Template for new contributions:**

```markdown
### [Problem Category]

**Problem I tried to solve:**
[Specific description of what you needed]

**What I tried:**
- Tool: [Specific AI tool/framework]
- Approach: [How you tried to use it]

**How it failed:**
- [Specific failure mode 1]
- [Specific failure mode 2]

**Example:**
[Show actual vs expected output if possible]

**My hypothesis for why it failed:**
[Your analysis of root cause]

**What a working solution would need:**
- [Requirement 1]
- [Requirement 2]
```

---

## Patterns We're Seeing

After collecting hundreds of failures, patterns emerge:

**AI tools consistently fail when:**
1. **Business logic matters** - "Revenue" never means just SUM(amount)
2. **Multiple systems interact** - Different schemas, different definitions, different update cycles
3. **Determinism is required** - Same query must give same results
4. **Scale matters** - Works on 100 rows, fails on 100M rows
5. **Errors cascade** - One wrong assumption corrupts everything downstream
6. **Audit matters** - Need to explain and verify every decision
7. **State matters** - Can't just retry from scratch when things fail

**What might actually work:**
- Semantic layers that encode business logic
- Deterministic planning before execution
- Pushdown optimization to avoid data movement
- Explicit state management and checkpointing
- Human-in-the-loop for ambiguity resolution
- Audit trails for every decision

---

## Join the Investigation

We're building this benchmark to find what actually works. If you've:
- **Hit these walls** - Share your specific failures
- **Found workarounds** - Document what worked
- **Have hypotheses** - Propose techniques to test

Every contribution helps us understand why AI fails on real enterprise data and how to fix it.
