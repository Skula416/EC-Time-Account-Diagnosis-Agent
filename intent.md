# EC Time Account Diagnostics Agent

SAP SuccessFactors Employee Central Time Account Issue Diagnosis & Fix Agent

## Business Challenge

Businesses frequently encounter incorrect time account balances in SAP SuccessFactors Employee Central — either vacation balances are wrong or accrual postings have not occurred. Diagnosing these issues currently requires HR admins to manually trace accrual postings, absence bookings, manual adjustments, and configuration settings across multiple screens. This is time-consuming, error-prone, and results in most employee queries being escalated to an HR admin. The goal is an AI agent that can quickly identify the root cause of time account issues, review EC configuration against real-world requirements, and — with human approval — suggest and apply fixes.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Time account queries resolved without HR admin escalation | ~0% (most escalate) | 80% | — | Absence quota management / Time account diagnosis | user |
| Time to diagnose a time account issue | ~30+ min per case | <5 min | — | Manage Time & Attendance | user |
| Manual effort for HR admins per time account case | High (full trace required) | Minimal (agent handles diagnosis) | — | HR Administration | agent-derived |

## Key Milestones

1. **Issue Intake** — Agent receives an employee ID or time type and confirms the scope of the investigation.
2. **Balance Audit** — Agent retrieves current time account balances and compares against expected values.
3. **Root Cause Trace** — Agent traces accrual postings, absence records, and manual adjustments to identify discrepancies.
4. **Configuration Review** — Agent evaluates relevant EC time configuration (accrual rules, time types, eligibility, period-end processing) against the employee's situation.
5. **Fix Recommendation & Approval** — Agent presents a ranked list of fix options; human approves before any changes are applied.
6. **Fix Application** — Agent applies approved corrections (e.g. manual adjustment, accrual repost trigger) and confirms the updated balance.

## Business Architecture (RBA)

### End-to-End Process

Recruit to Retire

### Process Hierarchy

```
Recruit to Retire
└── Manage Workforce (generic)
    └── Manage Time and Attendance (BPS-393)
        └── Manage attendance and absence quotas
        └── Manage work pattern and availability
        └── Record absences
```

### Summary

The challenge maps to the Recruit to Retire E2E, specifically the Manage Workforce / Manage Time and Attendance sub-process (BPS-393), covering absence quota management and absence recording capabilities in SAP SuccessFactors Employee Central.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
|------------------------|------------------------|------------|-------------------|--------------------|--------------------|---------------------|------|---------------------|
| Read time account balances | SAP SuccessFactors EC – Absence Management (SC4500) | `sap.sf:apiResource:Balances:v1` | — | — | — | — | No | REST API available; no MCP server found — translation layer required |
| Retrieve time-off events and accrual postings | SAP SuccessFactors EC – Absence Management | `sap.sf:apiResource:TimeOffEvents:v1` | — | — | — | — | No | REST API available |
| Read absence records and bookings | SAP SuccessFactors EC – Absence Management | `sap.sf:apiResource:ECTimeOff:v1` | — | — | — | — | No | OData API available |
| List available time types for an employee | SAP SuccessFactors EC – Absence Management | `sap.sf:apiResource:AvailableTimeTypes:v1` | — | — | — | — | No | REST API available |
| Review accrual rule and time-type configuration | SAP SuccessFactors EC – Absence Management | `sap.sf:apiResource:ECTimeOff:v1` | — | — | — | — | Maybe | Config entities (accrual rules, period-end processing) may have limited API coverage |
| Apply manual balance adjustments with human approval | SAP SuccessFactors EC – Absence Management | `sap.sf:apiResource:ECTimeOff:v1` | — | — | — | — | Maybe | Write operations need verification; SOAP APIs for adjustments not connected in current landscape |
| Human-in-the-loop approval before applying fixes | Custom agent pattern | — | — | — | — | — | Yes | No standard SAP approval flow available via API — must be built into agent interaction pattern |

### Key Findings

- SAP SuccessFactors Employee Central is the correct product for this challenge; all mandatory capabilities (Absence Management SC4500, Time Sheet Management SC1334) are covered.
- Four relevant REST/OData APIs are available in the connected landscape; two SOAP APIs (Manage Employee Time Accounts Adjustments, Query Time Account Balances) are **not connected** and cannot be used.
- No MCP servers exist for any of the discovered SuccessFactors APIs — MCP translation files will need to be generated for each API used by the agent.
- Configuration review against business rules (accrual eligibility, period-end processing) is a partial gap — API coverage for configuration entities needs verification during specification.
- Human-in-the-loop approval before write operations must be built as a custom agent interaction pattern (A2A protocol).

## Recommendations

### EC Time Account Diagnostics AI Agent

#### Executive Summary

AI agent on SAP BTP that diagnoses EC time issues and applies approved fixes.

#### Recommended Solution

Build a pro-code Python AI agent (A2A protocol) on SAP BTP that connects to SAP SuccessFactors Employee Central via its REST/OData APIs. The agent autonomously traces time account balances, accrual postings, absence records, and configuration settings to identify root causes. It then presents fix recommendations to the user and — upon explicit human approval — applies corrections directly in EC. MCP translation files will be generated for the SuccessFactors APIs to expose them as agent tools.

#### Problem Statement

HR admins, HR Business Partners, and Payroll Specialists spend 30+ minutes manually tracing time account discrepancies across multiple EC screens. Most employee queries escalate to an HR admin due to the complexity of the investigation. There is no automated way to correlate accrual rules, absences, manual adjustments, and configuration in a single diagnostic flow.

#### Affected User Roles

- HR Administrators (EC configuration owners)
- HR Business Partners (handling employee time-off queries)
- Payroll Specialists (reconciling time balances against payroll)
- Employees (indirectly, through faster resolution of their queries)

#### Important Factors

##### Reduces manual effort through automated root-cause tracing
The agent eliminates the need to manually correlate data across multiple EC screens by querying balances, accrual postings, and absence records in a single automated flow.

##### Human approval gate for configuration changes
All write operations (manual adjustments, configuration corrections) require explicit human approval before execution, ensuring compliance and auditability.

##### API coverage partially limits configuration diagnosis
Two SOAP APIs for time account adjustments are not available in the current connected landscape. The agent must rely on REST/OData alternatives or surface these as manual steps for the admin.

#### Potential Risks

##### Limited write API coverage
The SOAP APIs for directly managing time account adjustments are not connected. This may constrain the range of fixes the agent can autonomously apply, potentially requiring manual workarounds for some correction types.

##### Configuration entity API coverage uncertainty
EC configuration entities (accrual rules, period-end processing setups) may have limited or undocumented OData API coverage, which could reduce the depth of the configuration review capability.

#### Recommended Solution Category

AI Agent

#### Intent Fit
88%
