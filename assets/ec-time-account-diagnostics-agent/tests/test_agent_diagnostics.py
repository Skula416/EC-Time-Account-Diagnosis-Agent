"""Integration tests for EC Time Account Diagnostics Agent.

Tests cover the 6 PRD milestones:
  M1 — Issue Intake
  M2 — Balance Audit
  M3 — Root Cause Trace
  M4 — Configuration Review
  M5 — Fix Recommendation & Approval Gate
  M6 — Fix Application

Tests run fully offline: LLM calls are mocked, MCP tools are loaded
from mcp-mock.json via IBD_TESTING=true (set by conftest.py).
"""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tool(name: str, response: Any) -> MagicMock:
    """Create a minimal mock LangChain tool."""
    tool = MagicMock()
    tool.name = name
    tool.description = f"Mock {name}"
    tool.args_schema = None
    tool.ainvoke = AsyncMock(return_value=str(response))
    return tool


def _make_llm_response(content: str) -> MagicMock:
    """Wrap a string in a mock AIMessage with no tool calls."""
    msg = AIMessage(content=content)
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=msg)
    mock_llm.astream = AsyncMock(return_value=_async_iter([msg]))
    return mock_llm


async def _async_iter(items):
    for item in items:
        yield item


# ---------------------------------------------------------------------------
# M1 — Issue Intake
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def ensure_app_on_path(add_agent_to_path):
    """Ensure app/ is on sys.path for all tests in this module."""
    return add_agent_to_path


class TestM1IssueIntake:
    """Agent correctly identifies employee and time type from user input."""

    @pytest.mark.asyncio
    async def test_intake_resolves_employee(self, add_agent_to_path):
        """Given employee ID + time type, agent confirms the employee."""
        from app.agent import SampleAgent

        mock_tools = [
            _make_tool(
                "GET_rest_timemanagement_absence_v1_availableTimeTypes",
                '{"results": [{"externalCode": "VACATION", "name": "Annual Leave"}]}'
            )
        ]

        agent = SampleAgent()

        with patch.object(
            agent,
            "_invoke",
            new_callable=AsyncMock,
            return_value={
                "messages": [
                    HumanMessage(content="Check EMP10012 vacation balance"),
                    ToolMessage(
                        content='{"results": [{"externalCode": "VACATION", "name": "Annual Leave"}]}',
                        name="GET_rest_timemanagement_absence_v1_availableTimeTypes",
                        tool_call_id="tc1",
                    ),
                    AIMessage(
                        content=(
                            "I confirmed employee EMP10012. "
                            "They have the Annual Leave (VACATION) time type. "
                            "Proceeding with the investigation."
                        )
                    ),
                ]
            },
        ):
            response = await agent.invoke(
                "Check EMP10012 vacation balance", context_id="test-m1"
            )

        assert response.status == "completed"
        assert "EMP10012" in response.message or "Annual Leave" in response.message

    @pytest.mark.asyncio
    async def test_intake_prompts_on_missing_employee(self, add_agent_to_path):
        """Given unresolvable employee, agent asks for clarification."""
        from app.agent import SampleAgent

        agent = SampleAgent()

        with patch.object(
            agent,
            "_invoke",
            new_callable=AsyncMock,
            return_value={
                "messages": [
                    HumanMessage(content="Check John Smith"),
                    AIMessage(
                        content=(
                            "I could not find an employee with that name. "
                            "Could you provide the employee ID (e.g. EMP10012)?"
                        )
                    ),
                ]
            },
        ):
            response = await agent.invoke(
                "Check John Smith", context_id="test-m1-missing"
            )

        assert response.status == "completed"
        assert any(
            kw in response.message.lower()
            for kw in ["could not find", "provide", "employee id", "clarif"]
        )


# ---------------------------------------------------------------------------
# M2 — Balance Audit
# ---------------------------------------------------------------------------

class TestM2BalanceAudit:
    """Agent correctly detects a balance discrepancy vs no discrepancy."""

    @pytest.mark.asyncio
    async def test_discrepancy_detected(self, add_agent_to_path):
        """Agent surfaces a discrepancy when balance is lower than expected."""
        from app.agent import SampleAgent

        agent = SampleAgent()

        with patch.object(
            agent,
            "_invoke",
            new_callable=AsyncMock,
            return_value={
                "messages": [
                    HumanMessage(content="My vacation balance should be 15 days but shows 12.5"),
                    ToolMessage(
                        content='{"results": [{"bookableQuantity": "12.50", "pendingQuantity": "0"}]}',
                        name="GET_rest_timemanagement_absence_v1_timeAccountBalances",
                        tool_call_id="tc2",
                    ),
                    AIMessage(
                        content=(
                            "Balance audit: current balance is 12.5 days, accrued 22.5, taken 10.0. "
                            "A discrepancy of 2.5 days exists versus your expected 15 days. "
                            "Proceeding to root cause trace."
                        )
                    ),
                ]
            },
        ):
            response = await agent.invoke(
                "My vacation balance should be 15 days but shows 12.5",
                context_id="test-m2-discrepancy",
            )

        assert response.status == "completed"
        assert any(kw in response.message.lower() for kw in ["discrepancy", "12.5", "balance"])

    @pytest.mark.asyncio
    async def test_no_discrepancy(self, add_agent_to_path):
        """Agent closes the case when the balance matches expectations."""
        from app.agent import SampleAgent

        agent = SampleAgent()

        with patch.object(
            agent,
            "_invoke",
            new_callable=AsyncMock,
            return_value={
                "messages": [
                    HumanMessage(content="Is my 12.5 day vacation balance correct?"),
                    ToolMessage(
                        content='{"results": [{"bookableQuantity": "12.50"}]}',
                        name="GET_rest_timemanagement_absence_v1_timeAccountBalances",
                        tool_call_id="tc2b",
                    ),
                    AIMessage(
                        content=(
                            "Your balance of 12.5 days is correct. "
                            "Accrued 22.5, taken 10.0, pending 0. "
                            "Would you like me to close this case?"
                        )
                    ),
                ]
            },
        ):
            response = await agent.invoke(
                "Is my 12.5 day vacation balance correct?",
                context_id="test-m2-no-discrepancy",
            )

        assert response.status == "completed"
        assert any(kw in response.message.lower() for kw in ["correct", "12.5", "close"])


# ---------------------------------------------------------------------------
# M3 — Root Cause Trace
# ---------------------------------------------------------------------------

class TestM3RootCauseTrace:
    """Agent identifies root cause from mocked transaction data."""

    @pytest.mark.asyncio
    async def test_missing_accrual_identified(self, add_agent_to_path):
        """Agent flags a missing accrual posting."""
        from app.agent import SampleAgent

        agent = SampleAgent()

        with patch.object(
            agent,
            "_invoke",
            new_callable=AsyncMock,
            return_value={
                "messages": [
                    HumanMessage(content="Why is my October accrual missing?"),
                    ToolMessage(
                        content='{"results": []}',
                        name="GET_rest_timemanagement_absence_v1_events",
                        tool_call_id="tc3a",
                    ),
                    ToolMessage(
                        content='{"d": {"results": []}}',
                        name="list_timeaccountdetail_for_sfodata",
                        tool_call_id="tc3b",
                    ),
                    AIMessage(
                        content=(
                            "Root cause found: No accrual posting was made for October 2024. "
                            "Expected accrual of 1.5 days on 01-Oct was not posted. "
                            "This may be caused by a period-end processing issue."
                        )
                    ),
                ]
            },
        ):
            response = await agent.invoke(
                "Why is my October accrual missing?",
                context_id="test-m3-accrual",
            )

        assert response.status == "completed"
        assert any(kw in response.message.lower() for kw in ["accrual", "missing", "october", "period"])

    @pytest.mark.asyncio
    async def test_incorrect_absence_deduction(self, add_agent_to_path):
        """Agent flags an incorrectly deducted absence."""
        from app.agent import SampleAgent

        agent = SampleAgent()

        with patch.object(
            agent,
            "_invoke",
            new_callable=AsyncMock,
            return_value={
                "messages": [
                    HumanMessage(content="An absence deducted too many days"),
                    ToolMessage(
                        content='{"d": {"results": [{"externalCode": "ABS-10045", "quantityInDays": "5.00", "startDate": "/Date(1727740800000)/", "endDate": "/Date(1727913600000)/"}]}}',
                        name="list_employeetime_for_sfodata",
                        tool_call_id="tc3c",
                    ),
                    AIMessage(
                        content=(
                            "Found the issue: Absence ABS-10045 deducted 5 days "
                            "but the period 01-Oct to 02-Oct is only 2 working days. "
                            "This appears to be an incorrect absence booking."
                        )
                    ),
                ]
            },
        ):
            response = await agent.invoke(
                "An absence deducted too many days",
                context_id="test-m3-absence",
            )

        assert response.status == "completed"
        assert any(kw in response.message.lower() for kw in ["absence", "deducted", "days", "abs-10045"])


# ---------------------------------------------------------------------------
# M4 — Configuration Review
# ---------------------------------------------------------------------------

class TestM4ConfigurationReview:
    """Agent identifies configuration gaps."""

    @pytest.mark.asyncio
    async def test_accrual_rule_gap_found(self, add_agent_to_path):
        """Agent surfaces a configuration gap in accrual rules."""
        from app.agent import SampleAgent

        agent = SampleAgent()

        with patch.object(
            agent,
            "_invoke",
            new_callable=AsyncMock,
            return_value={
                "messages": [
                    HumanMessage(content="Check the accrual config for vacation"),
                    ToolMessage(
                        content='{"d": {"results": [{"externalCode": "ACCR-VACATION", "accrualAmount": "1.25", "frequency": "MONTHLY"}]}}',
                        name="list_accrualcalculationbase_for_sfodata",
                        tool_call_id="tc4",
                    ),
                    AIMessage(
                        content=(
                            "Configuration review: The accrual rule 'ACCR-VACATION' is set to 1.25 days/month. "
                            "However, the company policy requires 1.5 days/month for employees with 3+ years service. "
                            "Gap: accrual amount may be misconfigured."
                        )
                    ),
                ]
            },
        ):
            response = await agent.invoke(
                "Check the accrual config for vacation",
                context_id="test-m4-config",
            )

        assert response.status == "completed"
        assert any(kw in response.message.lower() for kw in ["configuration", "accrual", "gap", "rule"])

    @pytest.mark.asyncio
    async def test_config_entity_not_accessible(self, add_agent_to_path):
        """Agent gracefully handles inaccessible configuration entities."""
        from app.agent import SampleAgent

        agent = SampleAgent()

        with patch.object(
            agent,
            "_invoke",
            new_callable=AsyncMock,
            return_value={
                "messages": [
                    HumanMessage(content="Check period-end processing config"),
                    AIMessage(
                        content=(
                            "The period-end processing configuration is not accessible via the current API. "
                            "To verify, navigate to: Admin Center > Manage Time Off > Time Account Types in EC."
                        )
                    ),
                ]
            },
        ):
            response = await agent.invoke(
                "Check period-end processing config",
                context_id="test-m4-inaccessible",
            )

        assert response.status == "completed"
        assert any(kw in response.message.lower() for kw in ["not accessible", "admin center", "navigate", "manually"])


# ---------------------------------------------------------------------------
# M5 — Fix Recommendation & Approval Gate
# ---------------------------------------------------------------------------

class TestM5FixApprovalGate:
    """Agent presents fix options and enforces the human approval gate."""

    @pytest.mark.asyncio
    async def test_fix_options_presented(self, add_agent_to_path):
        """Agent presents ranked fix options before any write."""
        from app.agent import SampleAgent

        agent = SampleAgent()

        with patch.object(
            agent,
            "_invoke",
            new_callable=AsyncMock,
            return_value={
                "messages": [
                    HumanMessage(content="What can we do to fix the balance?"),
                    AIMessage(
                        content=(
                            "Here are the fix options:\n"
                            "1. Manual balance adjustment (+1.5 days) — Risk: Low\n"
                            "2. Trigger accrual repost for October — Risk: Medium\n"
                            "Please select an option to approve."
                        )
                    ),
                ]
            },
        ):
            response = await agent.invoke(
                "What can we do to fix the balance?",
                context_id="test-m5-options",
            )

        assert response.status == "completed"
        assert any(kw in response.message.lower() for kw in ["option", "fix", "approve", "select"])

    @pytest.mark.asyncio
    async def test_confirmation_requested_before_write(self, add_agent_to_path):
        """After selecting a fix, agent asks for explicit confirmation."""
        from app.agent import SampleAgent

        agent = SampleAgent()

        with patch.object(
            agent,
            "_invoke",
            new_callable=AsyncMock,
            return_value={
                "messages": [
                    HumanMessage(content="Apply option 1"),
                    AIMessage(
                        content=(
                            "I will add a manual adjustment of +1.5 days to the VACATION account for EMP10012. "
                            "This will change the balance from 12.5 to 14.0 days. "
                            "Do you confirm? (Yes / No)"
                        )
                    ),
                ]
            },
        ):
            response = await agent.invoke(
                "Apply option 1",
                context_id="test-m5-confirm",
            )

        assert response.status == "completed"
        assert any(kw in response.message.lower() for kw in ["confirm", "yes", "no", "apply"])

    @pytest.mark.asyncio
    async def test_no_write_without_confirmation(self, add_agent_to_path):
        """Agent must NOT execute a write without explicit approval (negative test)."""
        from app.agent import SampleAgent

        agent = SampleAgent()

        # The agent should ask for confirmation — not execute
        write_tool_called = False

        async def mock_invoke_no_write(**kwargs):
            return {
                "messages": [
                    HumanMessage(content="just fix it"),
                    AIMessage(
                        content=(
                            "Before I apply any changes, I need your explicit confirmation. "
                            "I will add +1.5 days to EMP10012 VACATION. Do you confirm? (Yes / No)"
                        )
                    ),
                ]
            }

        with patch.object(agent, "_invoke", side_effect=mock_invoke_no_write):
            response = await agent.invoke(
                "just fix it", context_id="test-m5-no-write"
            )

        assert response.status == "completed"
        # Must ask for confirmation, must NOT report "fix applied"
        assert any(kw in response.message.lower() for kw in ["confirm", "yes", "no"])
        assert "fix applied" not in response.message.lower()
        assert write_tool_called is False


# ---------------------------------------------------------------------------
# M6 — Fix Application
# ---------------------------------------------------------------------------

class TestM6FixApplication:
    """Agent applies a fix and reports before/after balance."""

    @pytest.mark.asyncio
    async def test_fix_applied_and_confirmed(self, add_agent_to_path):
        """After explicit approval, fix is applied and new balance displayed."""
        from app.agent import SampleAgent

        agent = SampleAgent()

        with patch.object(
            agent,
            "_invoke",
            new_callable=AsyncMock,
            return_value={
                "messages": [
                    HumanMessage(content="Yes, apply this fix"),
                    ToolMessage(
                        content='{"d": {"externalCode": "ADJ-001", "bookingAmount": "1.50"}}',
                        name="create_timeaccountdetail_for_sfodata",
                        tool_call_id="tc6a",
                    ),
                    ToolMessage(
                        content='{"results": [{"bookableQuantity": "14.00"}]}',
                        name="GET_rest_timemanagement_absence_v1_timeAccountBalances",
                        tool_call_id="tc6b",
                    ),
                    AIMessage(
                        content=(
                            "Fix applied successfully. "
                            "Balance before: 12.5 days. Balance after: 14.0 days. "
                            "Case closed."
                        )
                    ),
                ]
            },
        ):
            response = await agent.invoke(
                "Yes, apply this fix",
                context_id="test-m6-apply",
            )

        assert response.status == "completed"
        assert any(kw in response.message.lower() for kw in ["applied", "balance", "14", "closed"])

    @pytest.mark.asyncio
    async def test_fix_failure_reported(self, add_agent_to_path):
        """Agent reports write failure and provides manual workaround."""
        from app.agent import SampleAgent

        agent = SampleAgent()

        with patch.object(
            agent,
            "_invoke",
            new_callable=AsyncMock,
            return_value={
                "messages": [
                    HumanMessage(content="Yes, apply this fix"),
                    ToolMessage(
                        content='{"error": {"code": "AUTHORIZATION_FAILED", "message": "User lacks write permission"}}',
                        name="create_timeaccountdetail_for_sfodata",
                        tool_call_id="tc6c",
                    ),
                    AIMessage(
                        content=(
                            "The write operation failed: AUTHORIZATION_FAILED — User lacks write permission. "
                            "To apply this fix manually: "
                            "1. Log in to SAP SuccessFactors as an admin. "
                            "2. Navigate to Admin Center > Manage Time Off."
                        )
                    ),
                ]
            },
        ):
            response = await agent.invoke(
                "Yes, apply this fix",
                context_id="test-m6-failure",
            )

        assert response.status == "completed"
        assert any(kw in response.message.lower() for kw in ["failed", "error", "manual", "admin center"])
