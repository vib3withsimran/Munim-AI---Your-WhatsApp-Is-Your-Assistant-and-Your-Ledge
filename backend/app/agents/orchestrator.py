import logging
from typing import Dict, Any, Optional

from backend.app.models.schemas import ExtractedMessage
from backend.app.agents.customer_agent import CustomerAgent
from backend.app.agents.order_agent import OrderAgent
from backend.app.agents.finance_agent import FinanceAgent
from backend.app.memory.meko_adapter import get_meko_adapter
from backend.app.ai.response_generator import generate_owner_alert

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    Central router and rule coordinator.
    Receives normalized messages, runs deterministic checks first (privacy switches, owner commands),
    and routes by intent to specialized agents.
    """

    def __init__(self, memory_enabled: bool = True):
        self.meko = get_meko_adapter(enabled=memory_enabled)
        self.customer_agent = CustomerAgent(memory_engine=self.meko)
        self.order_agent = OrderAgent(memory_engine=self.meko)
        self.finance_agent = FinanceAgent()

    async def route_and_execute(
        self,
        message: ExtractedMessage,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if context is None:
            context = {}

        seller_id = context.get("seller_id", "default_seller")
        sender_phone = message.customer_phone
        raw_text = message.raw_text.strip()
        lower_text = raw_text.lower()

        # 1. Deterministic Rule Zero: Privacy Switches (#private / #resume)
        if lower_text.startswith("#private"):
            return {
                "agent_used": "Orchestrator",
                "action": "privacy_activated",
                "reply": "🔒 *Munim AI Paused*: Ledger updates & memory disabled for this chat. Send #resume to reactivate.",
                "escalate": False,
                "data": {"privacy": True}
            }
        elif lower_text.startswith("#resume"):
            return {
                "agent_used": "Orchestrator",
                "action": "privacy_deactivated",
                "reply": "🔓 *Munim AI Active*: Assistant and ledger resumed for this chat.",
                "escalate": False,
                "data": {"privacy": False}
            }

        # 2. Deterministic Rule: Owner Confirmation / Rejection Commands (#confirm / #reject)
        if lower_text.startswith("#confirm"):
            return {
                "agent_used": "Orchestrator",
                "action": "owner_confirmed",
                "reply": "✅ Record confirmed and committed to business ledger.",
                "escalate": False,
                "data": {"confirmed": True}
            }
        elif lower_text.startswith("#reject"):
            return {
                "agent_used": "Orchestrator",
                "action": "owner_rejected",
                "reply": "❌ Record rejected and discarded.",
                "escalate": False,
                "data": {"confirmed": False}
            }

        # 3. Deterministic Rule: Summary & Dues Command
        if lower_text in ["summary", "dues", "pending dues", "hisaab"]:
            summary_txt = await self.finance_agent.get_summary_report(seller_id)
            return {
                "agent_used": "FinanceAgent",
                "action": "summary_delivered",
                "reply": summary_txt,
                "escalate": False,
                "data": {}
            }

        # 4. Route by Intent to Specialized Agents
        intent = message.type
        logger.info(f"Orchestrator routing message '{message.message_id}' (intent={intent}) from {sender_phone}")

        if intent == "order":
            result = await self.order_agent.handle(message, context)
        elif intent in ["payment", "partial_payment"]:
            result = await self.finance_agent.handle(message, context)
        else:
            # catalog_query, delivery_query, question, complaint, unknown
            result = await self.customer_agent.handle(message, context)

        # 5. Build Final Execution Result
        escalate = result.get("escalate", False) or message.escalate_to_owner
        owner_alert = None
        if escalate:
            owner_alert = generate_owner_alert(message)

        return {
            "agent_used": result.get("agent", "UnknownAgent"),
            "action": result.get("action", "processed"),
            "reply": result.get("reply", ""),
            "escalate": escalate,
            "escalation_reason": result.get("escalation_reason") or message.escalation_reason,
            "owner_alert": owner_alert,
            "data": result.get("data", {})
        }

