# Example Submissions (detailed)

These show the **level of detail** that lets UCB recreate cases internally (no data required).

---

## Example 1 — Cross‑source churn with stitching & fiscal calendars
**Category:** Cross-Source Federation; Entity Resolution; Temporal/SCD  
**Business question:** Calculate **account churn** for **Q3 FY2024** and list top churn reasons.  
**Time:** Q3 FY2024; **fiscal year starts July**; timezone UTC; late events T+3 days.

**Data sources & backends**
- Salesforce: `Account`, `Opportunity` (≈500k rows), hourly sync
- Snowflake (product): `events`, `sessions` (~10M rows/day)
- Stripe: `subscriptions`, `invoices` via API (daily snapshot)

**Entities & identifiers**
- `account` (Salesforce `account_id`), `user` (product `user_id`), billing `account_uuid`
- Source of truth: billing_status and ARR from Stripe; account hierarchy from Salesforce.

**Join logic & rules**
- Stitch users → accounts via `account_uuid` (prefer Stripe over Salesforce on conflicts)
- Exclude test/internal accounts (`email LIKE '%@yourco.com'` or `account.tier='internal'`)
- Active user = ≥1 **revenue‑generating** event in 30 days (not “last login”)
- Churned = subscription cancelled **or** no revenue‑generating event for 90 consecutive days, as of FY quarter end.

**Expected output shape (no data)**
```

grain: account\_id x fiscal\_quarter
columns:

* account\_id: string (PK)
* fiscal\_quarter: string (e.g., FY2024-Q3)
* churned: boolean
* churn\_reason: enum \[non-payment, voluntary-cancel, downgrade, unknown]
* arr\_usd: number

```

**Tools attempted**
- GPT‑4 SQL agent (Snowflake + Postgres tool), LangChain router, Claude for plan critique.

**Failure mode**
1) Used **calendar** not fiscal quarter  
2) Joined on **company name** → false matches (“Acme”)  
3) Ignored SCD2: used **current** territory instead of **as‑of** boundaries

---

## Example 2 — ARR/MRR with SCD2 + FX at transaction time
**Category:** Temporal/Units/FX; Business Term Disambiguation  
**Business question:** Compute **MRR by region for June 2025** in USD using **txn‑time FX**.  
**Time:** June 1–30, 2025; timezone per transaction; rates from ECB at txn timestamp.

**Data sources & backends**
- Snowflake `billing.transactions` (multi‑currency)
- Snowflake `dim_customer_scd2` (valid_from/valid_to; region assignments)
- FX reference table `fx_rates` (timestamped rates, currency→USD)

**Rules**
- As‑of join from `transactions.timestamp` to `dim_customer_scd2` (SCD2)  
- Convert each txn using **rate at txn timestamp**; aggregate to MRR at month‑end.

**Expected output shape**
```

grain: region x month
columns:

* region: string
* month: date (eom)
* mrr\_usd: number

```

**Failure mode**
- Used **current** region instead of historical SCD2 as‑of  
- Applied **month‑average FX** instead of txn‑time rates  
- Double‑counted upgrades/downgrades within month

---

## Example 3 — Governance: salary metrics with RLS & k‑min
**Category:** Governance & Compliance; Production Control Flow  
**Business question:** Average **salary by department** while enforcing **RLS** and **k ≥ 5**.  
**Data sources:** Snowflake `hr.employees` (PII masked), `policies.sla_v3_2` (doc store)

**Rules**
- Apply row‑level security by requester’s org‑unit  
- Enforce `k >= 5` per department; otherwise return `suppressed = true`

**Expected output shape**
```

grain: department
columns:

* department: string
* avg\_salary\_usd: number | null
* suppressed: boolean
* policy\_citations: array<string>  # e.g., \["SLA v3.2 §4.1", "PII Masking §2.3"]

```

**Failure mode**
- Returned individual salaries for small departments (k‑min ignored)  
- No policy citations; leakage via verbose logs
```

---