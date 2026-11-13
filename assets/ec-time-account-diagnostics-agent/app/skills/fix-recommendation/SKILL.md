---
name: fix-recommendation
description: Rules for generating, ranking, and applying fix recommendations for EC time account issues — including the mandatory human approval gate and fallback guidance for unavailable APIs
---

# EC Time Account Fix Recommendation & Application

Use this skill when generating fix recommendations after root cause trace and configuration review are complete.

## Fix Types and Ranking

Rank fixes from lowest risk to highest risk. Always present all applicable fixes and let the user choose.

| Fix Type | Risk Level | API Required | Notes |
|----------|-----------|--------------|-------|
| Re-explanation / no change needed | None | None | Use when user misunderstood the balance |
| Manual balance adjustment (credit) | Low | EC Time Off (OData write) | Adds to balance; use for missed accrual |
| Manual balance adjustment (debit) | Medium | EC Time Off (OData write) | Reduces balance; use for over-accrual |
| Absence correction (amend days) | Medium | EC Time Off (OData write) | Corrects incorrectly deducted absence |
| Configuration update recommendation | Low (action is admin-only) | None (agent surfaces; admin applies) | Always manual; agent cannot apply config changes |
| Accrual repost (trigger rerun) | Medium | EC Time Off (OData write) | Use only if period-end processing was missed |

## Mandatory Human Approval Gate

**NEVER execute any write operation without explicit approval from the user in the current session.**

### Approval Flow

1. Present all applicable fix options as a numbered list. For each:
   - Plain-language description of what will happen
   - Expected balance after the fix (show the calculation)
   - Risk level (Low / Medium / High)
   - Whether an admin must follow up separately (for config changes)

2. Ask the user to select an option by number or name.

3. After selection, re-state EXACTLY:
   > "I will [specific action] on the [time type] account for employee [ID/name]. This will change the balance from [X] to [Y]. Do you confirm? (Yes / No)"

4. Only proceed if the user replies with an unambiguous confirmation: "Yes", "Confirm", "Go ahead", "Apply", or equivalent clear affirmation.

5. If the user replies with anything ambiguous or negative, do NOT proceed. Ask again or close the case.

### Declining All Fixes

If the user declines all options:
- Summarise the diagnosis findings (root causes identified, configuration gaps)
- List any configuration changes recommended that the admin should apply manually
- Close the case without making any changes
- Log: M5.missed — user declined all recommendations

## Applying the Fix

After confirmed approval:

1. Call the EC Time Off tool to apply the write operation.
2. Immediately re-call the Balances tool to retrieve the updated balance.
3. Present: "Fix applied. Balance before: [X]. Balance after: [Y]."
4. Log: M6.achieved — fix applied, new_balance: [Y]

### Write Operation Failure

If the EC Time Off write operation returns an error:
1. Report the error message exactly as received.
2. Do NOT retry automatically.
3. Log: M6.missed — write operation error: [error_detail]
4. Provide step-by-step manual workaround:
   > "To apply this fix manually:
   > 1. Log in to SAP SuccessFactors as an admin.
   > 2. Navigate to Admin Center > Manage Time Off.
   > 3. Search for employee [ID/name].
   > 4. Select the [time type] time account.
   > 5. Click 'Add Adjustment' and enter [amount] days with reason '[reason]'.
   > 6. Save and confirm the updated balance."

## SOAP API Unavailability

If the required correction uses the SOAP Manage Employee Time Account Adjustments API (which is not connected in this environment):
1. Surface this BEFORE presenting the fix for approval:
   > "Note: This type of adjustment requires an API that is not currently connected. If you approve this fix, I will provide step-by-step instructions for applying it manually in the EC admin UI."
2. If the user approves, skip the write operation and provide the manual steps above.
3. Log: M6.missed — SOAP API not available, manual workaround provided

## Configuration Change Recommendations

For configuration gaps, never apply config changes directly. Instead:
1. Describe the specific configuration change required (e.g. "Update the accrual amount on rule 'ANNUAL_LEAVE_MONTHLY' from 1.25 to 1.5 days per month").
2. Provide navigation path in EC admin:
   > "Navigate to: Admin Center > Manage Time Off > Accrual > [Rule Name] > Edit."
3. Note which employees will be affected by the change.
4. Recommend running period-end processing after the change to repost any missed accruals.
