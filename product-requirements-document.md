# Product Requirements Document (PRD)

**Title:** EC Time Account Diagnostics Agent
**Date:** 2026-11-13
**Owner:** HR Technology / SAP SuccessFactors Team
**Solution Category:** AI Agent

---

## Product Purpose & Value Proposition

**Elevator Pitch:**
HR teams spend 30+ minutes manually tracing time account discrepancies across multiple SuccessFactors screens — and most cases escalate to an HR admin regardless. This agent automates the entire diagnostic flow, identifies root causes in under 5 minutes, and applies approved fixes directly in SAP SuccessFactors Employee Central.

**Business Need:**
Employees and managers frequently raise queries about incorrect vacation balances or missing accrual postings. Today, resolving these requires an HR admin to manually correlate accrual rules, absence bookings, manual adjustments, and EC configuration across multiple screens. There is no single diagnostic flow and no automated way to verify whether a configuration gap is causing the issue. This results in high escalation rates, significant admin time per case, and employee frustration.

**Expected Value:**

- 80% of time account queries resolved without HR admin escalation (from near 0% today)
- Diagnosis time reduced from 30+ minutes to under 5 minutes per case
- HR admin manual effort reduced from full trace per case to review-and-approve only

**Product Objectives (Prioritized):**

1. Automate end-to-end diagnosis of time account issues (balance discrepancies, missed accruals, incorrect absence deductions, manual adjustment errors)
2. Surface configuration gaps in EC time setup and suggest specific, actionable fixes
3. Apply approved corrections directly in SAP SuccessFactors EC with a mandatory human approval gate
4. Instrument all business steps for observability and auditability

---

## Business Metrics

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Time account queries resolved without HR admin escalation | ~0% (most escalate) | 80% | — | Absence quota management / Time account diagnosis | user |
| Time to diagnose a time account issue | ~30+ min per case | <5 min | — | Manage Time & Attendance | user |
| Manual effort for HR admins per time account case | High (full trace required) | Minimal (agent handles diagnosis) | — | HR Administration | agent-derived |

---

## User Profiles & Personas

### Primary Persona: Alex — HR Administrator

Alex is a 35-year-old HR Systems Administrator responsible for configuring and maintaining SAP SuccessFactors Employee Central across a mid-to-large enterprise. Alex manages time types, accrual rules, eligibility groups, and period-end processing configuration. When employees report incorrect balances, Alex is the last line of escalation. Investigating a single case typically requires opening multiple EC admin screens, cross-referencing configuration tables, and checking time account transaction logs — a process that takes 30–60 minutes and pulls Alex away from proactive configuration work. Alex is technically proficient with EC but frustrated by the absence of a single diagnostic view. Success for Alex means resolving employee queries quickly and confidently, with a clear audit trail for every change made.

### Secondary Persona: Jamie — HR Business Partner

Jamie is a 31-year-old HR Business Partner supporting a business unit of 400 employees. Jamie regularly fields time-off balance queries from managers and employees and currently has to either escalate every case to an HR Admin or navigate EC screens they are not fully trained on. Jamie needs a plain-language explanation of why a balance is wrong and what will be done to fix it — without needing deep EC configuration knowledge. Success for Jamie means being able to handle a time account query end-to-end in a single conversation and communicate the outcome clearly to the employee.

### Other User Types

- **Payroll Specialists** — need to verify time account balances before payroll runs and reconcile discrepancies with HR.
- **Employees** — indirectly benefit through faster resolution of their time-off balance queries.

---

## Goals and Non-Goals

### Goals (In Scope)

- Diagnose time account balance discrepancies by tracing accrual postings, absence records, and manual adjustments for a given employee and time type
- Review relevant EC time configuration (accrual rules, time types, eligibility, period-end processing) and identify configuration gaps contributing to the issue
- Present a ranked list of fix recommendations with plain-language explanations
- Apply approved corrections in SAP SuccessFactors EC after explicit human sign-off
- Log all diagnostic steps and applied changes for auditability

### Non-Goals (Out of Scope)

- Automatic resolution without human approval — all write operations require explicit confirmation
- Payroll calculation or gross pay adjustments — the agent works at time account level only
- Time sheet management or clock-in/clock-out tracking
- Management of shift schedules or work patterns
- Support for SAP S/4HANA HCM or any non-SuccessFactors time management system
- Bulk reprocessing of accruals across an entire population (single-employee diagnostic scope)

---

## Requirements

### Must-Have Requirements

**R1: Issue Intake & Scope Confirmation**

- **Problem to Solve:** Users need a clear entry point to initiate a diagnostic investigation for a specific employee's time account issue.
- **User Story:** As an HR Admin or HR Business Partner, I need to provide an employee identifier and optionally a time type so that the agent knows what to investigate.
- **Acceptance Criteria:**
  - Given a user provides an employee ID, when the conversation starts, then the agent confirms the employee's name, employment status, and applicable time types before proceeding.
  - Given an ambiguous input, when the agent cannot identify the employee, then it asks a clarifying follow-up question.
- **Maps to Objective:** 1
- **Priority Rank:** 1

**R2: Time Account Balance Audit**

- **Problem to Solve:** Users cannot quickly see whether a balance is actually incorrect or simply misunderstood.
- **User Story:** As an HR Admin, I need the agent to retrieve and display current time account balances so that I can confirm whether a discrepancy exists before deeper investigation.
- **Acceptance Criteria:**
  - Given a valid employee ID and time type, when the agent runs a balance audit, then it displays current balance, accrued to date, taken to date, and any pending requests.
  - Given a balance that matches the expected value, when the agent presents findings, then it explains why no discrepancy exists before closing the case.
- **Maps to Objective:** 1
- **Priority Rank:** 2

**R3: Root Cause Trace**

- **Problem to Solve:** HR admins must manually correlate accrual postings, absence bookings, and manual adjustments across multiple EC screens to find the root cause.
- **User Story:** As an HR Admin, I need the agent to automatically trace all transactions affecting a time account so that I can identify exactly what caused the discrepancy without manual investigation.
- **Acceptance Criteria:**
  - Given a confirmed discrepancy, when the agent runs a root cause trace, then it identifies and summarises all relevant accrual postings, absence deductions, and manual adjustments within the relevant period.
  - Given missing or failed accrual postings, when the agent traces transactions, then it flags the missing postings with the expected dates and amounts.
  - Given incorrect absence deductions, when the agent traces transactions, then it identifies the offending absence request and its booking details.
- **Maps to Objective:** 1
- **Priority Rank:** 3

**R4: Configuration Review**

- **Problem to Solve:** Time account issues are often caused by misconfigured accrual rules, incorrect eligibility, or missing period-end processing — which are invisible without a deliberate config check.
- **User Story:** As an HR Admin, I need the agent to review EC time configuration relevant to the employee's case so that configuration gaps are identified as potential root causes.
- **Acceptance Criteria:**
  - Given a diagnosed discrepancy, when the agent performs a configuration review, then it checks the applicable accrual rule (frequency, amount, eligibility), time type setup, and period-end processing configuration.
  - Given a configuration gap, when the agent identifies it, then it explains the gap in plain language with a reference to the specific configuration object.
- **Maps to Objective:** 2
- **Priority Rank:** 4

**R5: Fix Recommendation with Human Approval Gate**

- **Problem to Solve:** There is no guided, auditable process for an HR admin to review and approve fixes before they are applied to an employee's time account.
- **User Story:** As an HR Admin, I need to review and explicitly approve any proposed fix before it is applied so that I remain in control of all changes to employee data.
- **Acceptance Criteria:**
  - Given a completed root cause trace and configuration review, when the agent proposes fixes, then it presents a ranked list of options with plain-language descriptions, expected outcome, and risk level for each.
  - Given a list of proposed fixes, when the user selects one to approve, then the agent confirms the specific action it will take and asks for final explicit confirmation before executing.
  - Given a user declines all fixes, when the agent acknowledges this, then it summarises the diagnosis and closes the case without making any changes.
- **Maps to Objective:** 3
- **Priority Rank:** 5

**R6: Fix Application & Confirmation**

- **Problem to Solve:** After approval, fixes must be applied accurately and the outcome confirmed so the user knows the issue is resolved.
- **User Story:** As an HR Admin, I need the agent to apply the approved fix in EC and confirm the updated balance so that I can verify the issue is resolved without navigating EC myself.
- **Acceptance Criteria:**
  - Given an approved fix, when the agent applies it, then the updated time account balance is retrieved and displayed alongside the original balance.
  - Given a failed write operation, when the agent encounters an error, then it reports the failure clearly and suggests a manual workaround.
- **Maps to Objective:** 3
- **Priority Rank:** 6

### High-Want Requirements

**R7: Multi-Time-Type Diagnostic**

- **Problem to Solve:** Some employees have discrepancies across more than one time type (e.g. annual leave and sick leave), requiring separate investigations.
- **User Story:** As an HR Admin, I need to diagnose multiple time types in a single session so that I do not have to restart the agent for each time type.
- **Priority Rank:** 1

**R8: Diagnosis Summary Report**

- **Problem to Solve:** HR admins need a record of the investigation and any changes made for audit and future reference.
- **User Story:** As an HR Admin, I need a written summary of the diagnosis, findings, and any corrections applied so that I have an audit trail for each case.
- **Priority Rank:** 2

### Nice-to-Have Requirements

**R9: Suggested Proactive Configuration Improvements**

- **Problem to Solve:** Beyond fixing a specific issue, there may be broader configuration improvements that would reduce future incidents.
- **User Story:** As an HR Admin, I need the agent to flag best-practice configuration improvements so that I can proactively reduce the volume of time account queries.
- **Priority Rank:** 1

---

## Non-Functional Requirements

### Performance

- **Latency:** Diagnosis complete (root cause trace + config review) within 30 seconds for a standard case.
- **Throughput:** Designed to support concurrent sessions from multiple HR users without degradation.

### Reliability

- **Availability:** Follows SAP BTP service availability standards.
- **Fallback:** If a SuccessFactors API call fails, the agent reports the failure clearly and advises the user to perform that specific check manually.

### Explainability

- **Traceability:** Every finding must be traceable to the specific API call and data record that produced it.
- **Decision Logging:** All agent actions, recommendations, approvals, and write operations are logged with timestamps and user identity.
- **Uncertainty Communication:** When API coverage is insufficient to fully diagnose an issue, the agent explicitly states this and recommends a manual follow-up step.

---

## Solution Architecture

**Architecture Overview:**
A pro-code Python AI agent built to the A2A (Agent-to-Agent) protocol, deployed on SAP BTP. The agent connects to SAP SuccessFactors Employee Central via REST and OData APIs, exposed as MCP tools through generated translation files. The agent converses with HR users through a chat interface and enforces a mandatory human approval gate before executing any write operations.

**Key Components:**

- **Python AI Agent (A2A protocol):** Core reasoning engine that orchestrates the diagnostic flow, interprets API responses, and manages the multi-turn conversation.
- **MCP Translation Layer:** Auto-generated MCP translation files for each SuccessFactors API (Balances, Time Off Events, EC Time Off, Available Time Types), exposing them as callable tools.
- **SAP SuccessFactors Employee Central:** Source of truth for time account balances, transactions, absence records, and configuration.
- **Human Approval Gate:** Built into the agent's conversational flow — no write operation executes without explicit user confirmation in the same session.

**Integration Points:**

- `sap.sf:apiResource:Balances:v1` — read time account balances (REST, read-only)
- `sap.sf:apiResource:TimeOffEvents:v1` — retrieve accrual postings and time-off events (REST, read-only)
- `sap.sf:apiResource:ECTimeOff:v1` — read absence records and time configuration; apply corrections (OData, read + write)
- `sap.sf:apiResource:AvailableTimeTypes:v1` — list time types available to an employee (REST, read-only)

**Deployment:** SAP BTP Cloud Foundry

---

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
The agent is designed with clear tool boundaries so that new SuccessFactors APIs or third-party time management tools can be added as additional MCP tools without changing core agent logic. The system prompt and tool descriptions are maintained separately from the reasoning engine to support prompt-level extensibility.

Extension points:
- Additional MCP tools for new SuccessFactors APIs (e.g. time sheet management, payroll time sheets)
- Custom configuration review rules per organisation or country-specific legal requirements
- Integration with third-party time management systems (e.g. SAP Time and Attendance Management by WorkForce Software)

**Business Step Instrumentation:**
All six business milestones are instrumented with structured log statements following the pattern `[MILESTONE_ID].[achieved|missed]: [description]`. This enables production monitoring of agent behaviour and case completion rates.

---

### Automation & Agent Behaviour

**Automation Level:** Autonomous agent with mandatory human approval gate for write operations

**Actions the system performs without human approval:**
- Retrieve time account balances for a given employee and time type
- Fetch accrual postings and time-off events within a specified period
- Read absence records and booking details
- List available time types for an employee
- Read EC time configuration (accrual rules, time types, eligibility)
- Identify and explain root causes and configuration gaps

**Actions that require human review or approval:**
- Apply a manual balance adjustment to an employee's time account
- Trigger a correction to an absence record
- Initiate a configuration change recommendation for admin follow-up

**Model or engine used:** Large language model via SAP Generative AI Hub

**Knowledge & data sources accessed:**

- SAP SuccessFactors Employee Central: time account balances, accrual transactions, absence records, time type configuration, accrual rule definitions, eligibility groups, period-end processing setup

**Tools or connectors invoked:**

- `Balances API` (read-only): retrieve current time account balance and balance components for a given employee and time type
- `TimeOffEvents API` (read-only): retrieve accrual postings, time-off events and their status within a date range
- `ECTimeOff OData API` (read + write): read absence requests, time account transactions, accrual rule configuration; write approved balance corrections
- `AvailableTimeTypes API` (read-only): list time types applicable to an employee based on their eligibility profile

**Guardrails & fail-safes:**

- Never apply any write operation to SuccessFactors without receiving explicit user confirmation in the current conversation session
- Never expose employee personal data beyond what is necessary to diagnose the specific issue raised
- If a SuccessFactors API call fails or returns unexpected data, halt the affected diagnostic step, report the error clearly, and advise manual verification
- Confidence below a defined threshold routes the recommendation to the HR admin for manual review rather than auto-suggesting a fix
- If the SOAP adjustment APIs are required for a fix but unavailable, surface this as a manual action item with step-by-step guidance

---

## Milestones

### M1: Issue Intake

- **Description:** The agent has received a valid employee identifier and confirmed the scope of the investigation (time type and period).
- **Achieved when:** Employee is confirmed in SuccessFactors and at least one applicable time type is identified.
- **Log on achievement:** `M1.achieved: issue intake complete — employee {employee_id}, time type {time_type}, period {period}`
- **Log on miss:** `M1.missed: issue intake failed — could not confirm employee or time type from input`

### M2: Balance Audit

- **Description:** The agent has retrieved and presented the current time account balances, confirming whether a discrepancy exists.
- **Achieved when:** Balance data is successfully retrieved and a discrepancy is confirmed or ruled out.
- **Log on achievement:** `M2.achieved: balance audit complete — discrepancy confirmed: {true|false}, balance {current_balance}`
- **Log on miss:** `M2.missed: balance audit failed — API call to Balances endpoint returned no data or an error`

### M3: Root Cause Trace

- **Description:** The agent has traced all accrual postings, absence deductions, and manual adjustments in the relevant period and identified the root cause of the discrepancy.
- **Achieved when:** At least one root cause (missing accrual, incorrect absence deduction, or erroneous manual adjustment) is identified and explained.
- **Log on achievement:** `M3.achieved: root cause trace complete — cause identified: {root_cause_summary}`
- **Log on miss:** `M3.missed: root cause trace incomplete — insufficient transaction data or API coverage gap`

### M4: Configuration Review

- **Description:** The agent has reviewed the relevant EC time configuration and identified any configuration gaps contributing to the issue.
- **Achieved when:** Accrual rule, time type, eligibility, and period-end processing configuration have been checked against the employee's situation.
- **Log on achievement:** `M4.achieved: configuration review complete — gaps found: {gap_count}`
- **Log on miss:** `M4.missed: configuration review incomplete — configuration entities not accessible via available APIs`

### M5: Fix Recommendation & Approval

- **Description:** The agent has presented ranked fix options and received explicit human approval for one or more actions.
- **Achieved when:** The user selects and confirms a fix from the agent's recommendation list.
- **Log on achievement:** `M5.achieved: fix approved by user — action: {approved_action}`
- **Log on miss:** `M5.missed: no fix approved — user declined all recommendations or session ended without approval`

### M6: Fix Application

- **Description:** The agent has applied the approved correction in SAP SuccessFactors EC and confirmed the updated balance.
- **Achieved when:** The write operation completes successfully and the updated balance is retrieved and displayed.
- **Log on achievement:** `M6.achieved: fix applied — updated balance: {new_balance}, case closed`
- **Log on miss:** `M6.missed: fix application failed — write operation returned error: {error_detail}`

---

## Risks, Assumptions, and Dependencies

### Risks

- **Limited write API coverage:** The SOAP APIs for directly managing time account adjustments (`Manage Employee Time Accounts Adjustments`, `Query Time Account Balances`) are not connected in the current landscape. Certain correction types may need to be surfaced as manual admin tasks rather than automated fixes.
- **Configuration entity API coverage uncertainty:** EC accrual rule and period-end processing configuration entities may have limited OData coverage. The depth of automated configuration review will be validated during the specification phase.
- **LLM reasoning accuracy:** Incorrect root cause identification could lead to wrong fix recommendations. The mandatory human approval gate mitigates this risk but does not eliminate it.

### Assumptions

- SAP SuccessFactors Employee Central is the active time management system in use.
- The four REST/OData APIs identified (`Balances:v1`, `TimeOffEvents:v1`, `ECTimeOff:v1`, `AvailableTimeTypes:v1`) are accessible from SAP BTP via the Agent Gateway.
- Users interacting with the agent have sufficient EC permissions to view employee time data and approve adjustments.
- No direct connection to SAP S/4HANA or other payroll systems is required in scope.

### Dependencies

- SAP SuccessFactors Employee Central REST/OData API connectivity from SAP BTP
- SAP Generative AI Hub access for the LLM runtime
- MCP translation files generated for all four SuccessFactors APIs
- Agent Gateway routing configured for SuccessFactors API calls

---

## Appendix

### Glossary

- **Time Account:** A container in SuccessFactors EC that tracks an employee's balance for a specific time type (e.g. annual leave, sick leave).
- **Accrual Rule:** An EC configuration object that defines how and when time is credited to a time account (frequency, amount, eligibility conditions).
- **Period-End Processing:** An EC automated process that calculates and posts accruals at the end of a defined period.
- **Time Type:** A category of time off (e.g. vacation, sick leave, compensatory time) with associated rules and accounts.
- **Manual Adjustment:** A direct correction to a time account balance made by an HR admin outside the normal accrual/absence flow.
- **A2A Protocol:** Agent-to-Agent protocol used by SAP Joule Studio runtime for deploying pro-code Python agents on SAP BTP.
- **MCP Translation File:** A generated configuration artifact that exposes a REST or OData API as a set of callable tools for an AI agent.

### References

- SAP SuccessFactors Employee Central Time Off API documentation
- SAP Build (Joule Studio) Agent development guidelines
- SAP Business Accelerator Hub — SuccessFactors Time APIs
