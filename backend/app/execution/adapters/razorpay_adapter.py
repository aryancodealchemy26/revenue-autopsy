"""Razorpay Test Mode execution adapter for supported payment recovery operations."""

from datetime import datetime, timezone
import logging
from typing import Optional
from uuid import uuid4
import httpx

from app.application.ports.execution_provider import ExecutionProviderPort
from app.core.config import settings
from app.domain.actions.enums import ActionType
from app.domain.actions.models import ActionPlan
from app.domain.execution.enums import ExecutionStatus
from app.domain.execution.models import ExecutionResult
from app.domain.incidents.models import Incident
from app.domain.merchants.models import Merchant

logger = logging.getLogger(__name__)


class RazorpayTestModeAdapter(ExecutionProviderPort):
    """Execution adapter interacting truthfully with Razorpay REST APIs in Test Mode.

    STRICT SAFETY GUARANTEES:
    - Only operates against Test Mode endpoints (rejects any rzp_live_ keys).
    - Only executes truthfully supported operations (e.g. RETRY_PAYMENT order creation).
    - Never invents undocumented endpoints.
    - Fails closed on network timeout, 4xx/5xx responses, or missing credentials.
    """

    SUPPORTED_ACTION_TYPES = {
        ActionType.RETRY_PAYMENT,
    }

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        base_url: str = "https://api.razorpay.com/v1",
        timeout_seconds: float = 10.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        raw_secret = key_secret
        if not raw_secret and settings.RAZORPAY_KEY_SECRET:
            raw_secret = settings.RAZORPAY_KEY_SECRET.get_secret_value()
        self.key_secret = raw_secret
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._http_client = http_client

    def supports_action_type(self, action_type: ActionType) -> bool:
        """Return True only if the action type has a documented Razorpay write API."""
        return action_type in self.SUPPORTED_ACTION_TYPES

    async def execute(
        self,
        merchant: Merchant,
        incident: Incident,
        action_plan: ActionPlan,
        idempotency_key: str,
        correlation_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute a supported action against Razorpay in Test Mode."""
        now = datetime.now(timezone.utc)

        # 1. Validate capability support
        if not self.supports_action_type(action_plan.action_type):
            return ExecutionResult(
                execution_id=uuid4(),
                merchant_id=merchant.merchant_id,
                incident_id=incident.incident_id,
                action_id=action_plan.action_id,
                provider="razorpay_test_mode",
                action_type=action_plan.action_type,
                status=ExecutionStatus.FAILED,
                is_simulated=False,
                error_message=f"Action type '{action_plan.action_type.value}' is not supported by Razorpay API adapter.",
                idempotency_key=idempotency_key,
                executed_at=now,
                details={"reason": "unsupported_action_type"},
            )

        # 2. Validate Test Mode Credentials (Fail-closed)
        if not self.key_id or not self.key_secret:
            return ExecutionResult(
                execution_id=uuid4(),
                merchant_id=merchant.merchant_id,
                incident_id=incident.incident_id,
                action_id=action_plan.action_id,
                provider="razorpay_test_mode",
                action_type=action_plan.action_type,
                status=ExecutionStatus.FAILED,
                is_simulated=False,
                error_message="Razorpay credentials missing. Cannot execute without valid test mode keys.",
                idempotency_key=idempotency_key,
                executed_at=now,
                details={"reason": "missing_credentials"},
            )

        # 3. Guard against Live Mode keys
        if self.key_id.startswith("rzp_live_"):
            logger.error("Attempted to use live Razorpay key in test mode adapter!")
            return ExecutionResult(
                execution_id=uuid4(),
                merchant_id=merchant.merchant_id,
                incident_id=incident.incident_id,
                action_id=action_plan.action_id,
                provider="razorpay_test_mode",
                action_type=action_plan.action_type,
                status=ExecutionStatus.FAILED,
                is_simulated=False,
                error_message="Live mode keys rejected. Razorpay adapter only permits Test Mode keys (rzp_test_).",
                idempotency_key=idempotency_key,
                executed_at=now,
                details={"reason": "live_key_blocked"},
            )

        # 4. Execute Documented Test Mode API Call (e.g. POST /orders for RETRY_PAYMENT)
        auth = (self.key_id, self.key_secret)
        amount_in_paise = int(action_plan.expected_recovery * 100)
        # Receipt length max 40 chars in Razorpay API
        receipt = idempotency_key[:40] if idempotency_key else str(action_plan.action_id)[:40]

        payload = {
            "amount": amount_in_paise,
            "currency": action_plan.currency,
            "receipt": receipt,
            "notes": {
                "incident_id": str(incident.incident_id),
                "merchant_id": str(merchant.merchant_id),
                "action_id": str(action_plan.action_id),
                "correlation_id": correlation_id or "",
                "purpose": "revenue_recovery_retry",
            },
        }

        client = self._http_client or httpx.AsyncClient(timeout=self.timeout_seconds)
        close_client = self._http_client is None

        try:
            url = f"{self.base_url}/orders"
            response = await client.post(url, json=payload, auth=auth)

            if response.status_code in (200, 201):
                resp_json = response.json()
                order_id = resp_json.get("id")
                return ExecutionResult(
                    execution_id=uuid4(),
                    merchant_id=merchant.merchant_id,
                    incident_id=incident.incident_id,
                    action_id=action_plan.action_id,
                    provider="razorpay_test_mode",
                    action_type=action_plan.action_type,
                    status=ExecutionStatus.SUCCESS,
                    is_simulated=False,
                    provider_reference=order_id,
                    error_message=None,
                    idempotency_key=idempotency_key,
                    executed_at=now,
                    details={
                        "order_id": order_id,
                        "amount": amount_in_paise,
                        "currency": action_plan.currency,
                        "status": resp_json.get("status"),
                        "created_at": resp_json.get("created_at"),
                    },
                )
            else:
                err_body = response.text
                try:
                    err_json = response.json()
                    err_msg = err_json.get("error", {}).get("description", err_body)
                except Exception:
                    err_msg = err_body

                return ExecutionResult(
                    execution_id=uuid4(),
                    merchant_id=merchant.merchant_id,
                    incident_id=incident.incident_id,
                    action_id=action_plan.action_id,
                    provider="razorpay_test_mode",
                    action_type=action_plan.action_type,
                    status=ExecutionStatus.FAILED,
                    is_simulated=False,
                    error_message=f"Razorpay API error ({response.status_code}): {err_msg}",
                    idempotency_key=idempotency_key,
                    executed_at=now,
                    details={"http_status": response.status_code, "response": err_body},
                )

        except httpx.TimeoutException:
            logger.warning("Razorpay API request timed out for action %s", action_plan.action_id)
            return ExecutionResult(
                execution_id=uuid4(),
                merchant_id=merchant.merchant_id,
                incident_id=incident.incident_id,
                action_id=action_plan.action_id,
                provider="razorpay_test_mode",
                action_type=action_plan.action_type,
                status=ExecutionStatus.FAILED,
                is_simulated=False,
                error_message="Razorpay request timed out. Execution failed closed without retrying.",
                idempotency_key=idempotency_key,
                executed_at=now,
                details={"reason": "timeout"},
            )
        except Exception as e:
            logger.exception("Unexpected error calling Razorpay API for action %s", action_plan.action_id)
            return ExecutionResult(
                execution_id=uuid4(),
                merchant_id=merchant.merchant_id,
                incident_id=incident.incident_id,
                action_id=action_plan.action_id,
                provider="razorpay_test_mode",
                action_type=action_plan.action_type,
                status=ExecutionStatus.FAILED,
                is_simulated=False,
                error_message=f"External provider communication failure: {str(e)}",
                idempotency_key=idempotency_key,
                executed_at=now,
                details={"error_type": type(e).__name__},
            )
        finally:
            if close_client:
                await client.aclose()
