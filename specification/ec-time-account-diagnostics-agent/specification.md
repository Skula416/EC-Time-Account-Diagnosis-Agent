# Specification: ec-time-account-diagnostics-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` thoroughly before starting implementation
- [x] Bootstrap agent code in `assets/ec-time-account-diagnostics-agent/` using the `sap-agent-bootstrap` instructions (invoke from inside `assets/ec-time-account-diagnostics-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

The agent requires two runtime skills to keep the system prompt focused and provide structured diagnostic and configuration knowledge:

- [x] Create `assets/ec-time-account-diagnostics-agent/app/skills/diagnostic-workflow/SKILL.md` with:
  - YAML frontmatter: `name: diagnostic-workflow`, `description: Step-by-step instructions for diagnosing a time account issue — intake, balance audit, root cause trace, configuration review`
  - Body: Ordered diagnostic steps with decision criteria (e.g. when to escalate, when to conclude no discrepancy exists, how to handle missing accrual postings vs incorrect absence deductions vs manual adjustment errors)

- [x] Create `assets/ec-time-account-diagnostics-agent/app/skills/fix-recommendation/SKILL.md` with:
  - YAML frontmatter: `name: fix-recommendation`, `description: Rules for generating, ranking and applying fix recommendations for EC time account issues — including the mandatory human approval gate`
  - Body: Fix-ranking criteria, human approval interaction pattern, how to handle failed write operations (surface as manual admin step), and fallback guidance when SOAP adjustment APIs are unavailable

---

## Project-Specific Tasks

### R1 — Issue Intake & Scope Confirmation

- [x] In `assets/ec-time-account-diagnostics-agent/app/agent.py`, add a `@prompt_section` (or equivalent system prompt block) that instructs the agent to:
  - Ask the user for an employee identifier (employee ID or name) and optionally a time type to investigate
  - Confirm the employee's name and employment status using the Available Time Types API before proceeding
  - Confirm which time types are applicable to that employee and ask the user to select one if multiple are returned
  - If the employee cannot be resolved, ask a targeted follow-up question (e.g. check spelling, suggest alternative identifier format)
- [x] Ensure the agent loads the `diagnostic-workflow` runtime skill at the start of any diagnostic conversation

### R2 — Time Account Balance Audit

- [x] Add system prompt instructions for the balance audit step:
  - Retrieve current time account balance for the confirmed employee and time type using the Balances API
  - Display: current balance, accrued-to-date, taken-to-date, any pending/approved requests
  - If the balance matches the user's expected value, explain why no discrepancy exists and offer to close the case
  - If a discrepancy is confirmed, proceed to root cause trace automatically

### R3 — Root Cause Trace

- [x] Add system prompt instructions for the root cause trace step:
  - Retrieve accrual postings and time-off events for the employee and time type within the relevant period using the Time Off Events API
  - Retrieve absence records and booking details using the EC Time Off OData API
  - Correlate the three data sources (accruals, absences, events) and surface:
    - Missing accrual postings (expected date + amount vs actual)
    - Incorrect absence deductions (flag the specific absence request)
    - Erroneous manual adjustments (flag the adjustment record with date and amount)
  - Summarise all findings in plain language before proceeding to configuration review

### R4 — Configuration Review

- [x] Add system prompt instructions for the configuration review step:
  - Retrieve accrual rule configuration for the employee's time type using the EC Time Off OData API
  - Check: accrual frequency, accrual amount, eligibility conditions, period-end processing setup
  - Compare configuration against the employee's actual situation (hire date, employment type, job classification)
  - Identify and explain any configuration gaps in plain language with reference to the specific configuration object name
  - If configuration entities are not accessible via the available OData API surface, clearly state this and recommend a manual admin check with guidance on which EC admin screen to use

### R5 — Fix Recommendation with Human Approval Gate

- [x] Add system prompt instructions for the fix recommendation step:
  - Load the `fix-recommendation` runtime skill to guide the recommendation logic
  - Generate a ranked list of fix options (e.g. manual balance adjustment, absence correction, accrual repost, configuration update)
  - For each option: provide a plain-language description, expected outcome after the fix, and risk level (Low / Medium / High)
  - Present the list to the user and ask them to select one to approve
  - After selection, re-state the exact action the agent will take and ask for **final explicit confirmation** (e.g. "Yes, apply this fix") before executing any write operation
  - If the user declines all fixes: summarise the diagnosis findings and close the case without making any changes
  - Never execute any write operation without receiving the final explicit confirmation in the current session

### R6 — Fix Application & Confirmation

- [x] Add system prompt instructions for the fix application step:
  - After receiving final confirmation, apply the approved correction using the EC Time Off OData API (write operation)
  - Immediately re-retrieve the time account balance after the write operation completes
  - Display: original balance (before fix) vs updated balance (after fix), and confirm the case is resolved
  - If the write operation fails: report the error clearly, do not retry automatically, and surface a step-by-step manual workaround for the admin using the EC admin UI
  - If the required correction type is not available via the OData API (SOAP-only operation), surface this as a documented manual action item before the user approves

### R7 — Multi-Time-Type Diagnostic (High-Want)

- [x] Add system prompt instructions to support multi-time-type sessions:
  - After completing a full diagnostic cycle (intake → balance audit → root cause → config review → fix recommendation → fix application), ask the user: "Would you like to investigate another time type for this employee?"
  - If yes, restart from the balance audit step (employee is already confirmed; skip intake re-confirmation)
  - Track all investigated time types within the session to avoid redundant re-investigation

### R8 — Diagnosis Summary (High-Want)

- [x] Add system prompt instructions to generate a case summary at the end of each session:
  - Include: employee ID, time types investigated, discrepancies found, root causes identified, configuration gaps noted, fixes recommended, fixes applied (with before/after balances), and any items flagged for manual follow-up
  - Present the summary in a structured format the user can copy for their audit records

---

## API Integrations

The following API spec files are available in `specification/ec-time-account-diagnostics-agent/api-specs/` and must be used to generate MCP translation files:

| API Name | ORD ID | Spec File | Type |
|----------|--------|-----------|------|
| Time Off Balances | `sap.sf:apiResource:Balances:v1` | `api-specs/balances.json` | REST (OpenAPI JSON) |
| Time Off Events | `sap.sf:apiResource:TimeOffEvents:v1` | `api-specs/time-off-events.json` | REST (OpenAPI JSON) |
| EC Time Off | `sap.sf:apiResource:ECTimeOff:v1` | `api-specs/ec-time-off.edmx` | OData (EDMX) |
| Available Time Types | `sap.sf:apiResource:AvailableTimeTypes:v1` | `api-specs/available-time-types.json` | REST (OpenAPI JSON) |

**MCP tool scope — Balances API (`sap.sf:apiResource:Balances:v1`)**
```
MCP API: sap.sf:apiResource:Balances:v1
MCP tool scope: read-only
Resources in scope: all
```

**MCP tool scope — Time Off Events API (`sap.sf:apiResource:TimeOffEvents:v1`)**
```
MCP API: sap.sf:apiResource:TimeOffEvents:v1
MCP tool scope: read-only
Resources in scope: all
```

**MCP tool scope — EC Time Off OData API (`sap.sf:apiResource:ECTimeOff:v1`)**
```
MCP API: sap.sf:apiResource:ECTimeOff:v1
MCP tool scope: read-write
Resources in scope: TimeAccountDetail, TimeAccount, TimeAccountSnapshot, TimeAccountPurchasingItem, EmployeeTime, EmployeeTimeCalendar, TimeType, AccrualCalculationBase, TimeManagementTerminationEndHandlingExcludedEventReason
```

**MCP tool scope — Available Time Types API (`sap.sf:apiResource:AvailableTimeTypes:v1`)**
```
MCP API: sap.sf:apiResource:AvailableTimeTypes:v1
MCP tool scope: read-only
Resources in scope: all
```

---

## Business Instrumentation

- [x] Add instrumentation for each of the 6 PRD milestones using `instrumentation.log_milestone` and a named OpenTelemetry span. Log statements must follow the pattern `[MILESTONE_ID].[achieved|missed]: [description]`:

  | Milestone | Span name | Log on achievement | Log on miss |
  |-----------|-----------|-------------------|-------------|
  | M1 — Issue Intake | `m1_issue_intake` | `M1.achieved: issue intake complete — employee {employee_id}, time type {time_type}, period {period}` | `M1.missed: issue intake failed — could not confirm employee or time type from input` |
  | M2 — Balance Audit | `m2_balance_audit` | `M2.achieved: balance audit complete — discrepancy confirmed: {true/false}, balance {current_balance}` | `M2.missed: balance audit failed — API call to Balances endpoint returned no data or an error` |
  | M3 — Root Cause Trace | `m3_root_cause_trace` | `M3.achieved: root cause trace complete — cause identified: {root_cause_summary}` | `M3.missed: root cause trace incomplete — insufficient transaction data or API coverage gap` |
  | M4 — Configuration Review | `m4_configuration_review` | `M4.achieved: configuration review complete — gaps found: {gap_count}` | `M4.missed: configuration review incomplete — configuration entities not accessible via available APIs` |
  | M5 — Fix Recommendation & Approval | `m5_fix_approval` | `M5.achieved: fix approved by user — action: {approved_action}` | `M5.missed: no fix approved — user declined all recommendations or session ended without approval` |
  | M6 — Fix Application | `m6_fix_application` | `M6.achieved: fix applied — updated balance: {new_balance}, case closed` | `M6.missed: fix application failed — write operation returned error: {error_detail}` |

- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

> Read [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) for complete MCP integration patterns.

- [x] Invoke the `mcp-translation-file` skill for each of the four API spec files in `specification/ec-time-account-diagnostics-agent/api-specs/`. Apply the MCP tool scope defined above to prune each translation to only the resources and operations the agent needs.
- [x] After MCP translation files are generated, invoke the `setup-solution` skill to register all MCP server assets in `solution.yaml` and `asset.yaml`
- [x] Verify the `AgentExecutor` in the bootstrapped template loads tools via `mcp_providers.agw.get_mcp_tools()` and passes them to `SampleAgent.stream()`. Do not add a second MCP loader. Do not create direct HTTP clients.
- [x] Add MCP server dependencies to `asset.yaml` under `requires` — one entry per generated MCP server, using exact ORD IDs from the generated MCP assets
- [x] Generate `mcp-mock.json` using the `mcp-mock-config` skill after all MCP translation files are complete (required before tests can run)

---

## Testing

> See [guidelines-agent-python.md](../guidelines-agent-python.md) for Python testing setup and patterns.

- [x] `conftest.py` only sets `IBD_TESTING=true` — this causes the agent to run with mock MCP tool results during tests
- [x] Write one integration test per diagnostic milestone covering:
  - M1: agent correctly identifies employee and time type from user input
  - M2: agent correctly detects a balance discrepancy vs no discrepancy case
  - M3: agent correctly identifies root cause from mocked transaction data
  - M4: agent correctly identifies a configuration gap from mocked config data
  - M5: agent correctly presents fix options and enforces the approval gate (no write without explicit confirmation)
  - M6: agent correctly applies a fix and reports before/after balance
- [x] Write one negative test: agent refuses to apply a write operation when the user has not given explicit confirmation
- [x] Run `pytest` from `assets/ec-time-account-diagnostics-agent/` (no args) — if coverage < 70%, add tests until threshold met
- [x] Run `pytest` again to generate final `test_report.json`
- [x] Verify `test_report.json` exists in `assets/ec-time-account-diagnostics-agent/`
