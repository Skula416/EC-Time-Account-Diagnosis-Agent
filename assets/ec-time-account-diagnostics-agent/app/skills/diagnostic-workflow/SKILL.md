---
name: diagnostic-workflow
description: Step-by-step instructions for diagnosing a SAP SuccessFactors EC time account issue — issue intake, balance audit, root cause trace, and configuration review
---

# EC Time Account Diagnostic Workflow

Use this skill to guide the full diagnostic flow from issue intake through to configuration review.

## When to Use This Skill

Load at the start of any conversation involving a time account discrepancy, incorrect balance, or missed accrual posting.

## Step 1 — Issue Intake

1. Greet the user and ask for:
   - Employee identifier (employee ID or full name)
   - Time type to investigate (e.g. Annual Leave, Sick Leave) — optional; if not provided, list available types and ask the user to choose
   - The period of concern (e.g. "the last 3 months" or a specific date)

2. Call the Available Time Types tool with the employee ID to confirm the employee exists and retrieve applicable time types.

3. Decision:
   | Situation | Action |
   |-----------|--------|
   | Employee not found | Ask user to check ID format or spelling. Try once more, then escalate to manual admin check |
   | Single time type | Proceed with that type automatically |
   | Multiple time types | Present the list and ask the user to select one |
   | No applicable time types | Inform user; recommend checking employment status and time type eligibility in EC admin |

4. Confirm back to the user: "I will investigate the [time type] account for employee [name/ID] for [period]."

## Step 2 — Balance Audit

1. Call the Balances tool to retrieve the current time account balance.
2. Present clearly:
   - Current balance
   - Total accrued to date in the period
   - Total taken (absences deducted) in the period
   - Any pending or approved requests not yet deducted

3. Decision:
   | Situation | Action |
   |-----------|--------|
   | Balance matches user expectation | Explain each component in plain language. Offer to close the case |
   | Discrepancy confirmed | Proceed to Step 3 automatically |
   | API call fails | Report error exactly; recommend manual check in EC Time Account admin |

## Step 3 — Root Cause Trace

1. Call the Time Off Events tool for the employee and time type in the relevant period to retrieve accrual postings and time-off events.
2. Call the EC Time Off tool to retrieve absence requests and any manual adjustment records.
3. Correlate all three data sources:

   **Missing accrual posting checks:**
   - Compare expected accrual dates (based on accrual frequency) against actual postings
   - Flag any expected postings that did not occur with: expected date, expected amount, and whether the period-end processing was run

   **Incorrect absence deduction checks:**
   - Review each absence request: start date, end date, days deducted, approval status
   - Flag any absence that appears to deduct more or fewer days than expected

   **Manual adjustment checks:**
   - List all manual adjustments in the period: date, amount (positive = credit, negative = debit), created-by user
   - Flag adjustments that appear large, duplicate, or applied in error

4. Summarise findings in plain language before proceeding, e.g.:
   - "I found 1 missing accrual posting on 01-Oct (expected 1.5 days)."
   - "Absence request ABS-10045 on 15-Oct deducted 5 days but the period was only 3 working days."
   - "No manual adjustments were found in this period."

## Step 4 — Configuration Review

1. Call the EC Time Off tool to retrieve the accrual rule for the employee's time type.
2. Check each of the following:

   | Config Element | Check |
   |----------------|-------|
   | Accrual frequency | Does it match when the employee expects to accrue? (monthly, yearly, per-pay-period) |
   | Accrual amount | Is the configured amount correct for the employee's entitlement level? |
   | Eligibility | Does the employee meet the eligibility conditions (hire date, employment type, job class)? |
   | Period-end processing | Is period-end processing configured and was it run in the relevant period? |
   | Time type setup | Is the time type active and correctly linked to the accrual rule? |

3. Decision:
   | Situation | Action |
   |-----------|--------|
   | Configuration gap found | Explain in plain language; note the exact EC config object name |
   | Config looks correct | State "Configuration appears correct" and focus root cause on transaction data |
   | Config entity not accessible via API | State: "The [entity] configuration is not accessible via the current API. To verify, navigate to: Admin Center > Manage Time Off > Time Types > [Time Type Name] in EC." |

## Escalation Criteria

Escalate to manual admin review (do not propose an automated fix) if:
- The discrepancy exceeds 5 days of leave entitlement and the root cause is unclear
- Multiple root causes are found simultaneously
- The configuration gap involves a change that would affect more than one employee
- The write operation required is only available via the SOAP adjustment API (not connected)
