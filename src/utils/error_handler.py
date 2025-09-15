"""Unified error handling utilities for the multi-model AI platform."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - runtime optional import
    from core.event_recorder import EventRecorder


class ErrorHandler:
    """Centralised error handling helper.

    The handler is responsible for
    * logging the incident using the provided logger;
    * recording a normalised ``error_occurred`` event when an :class:`EventRecorder`
      is available; and
    * providing small convenience helpers for building graceful fallbacks.
    """

    def __init__(self, event_recorder: Optional["EventRecorder"] = None,
                 logger: Optional[logging.Logger] = None):
        self._event_recorder = event_recorder
        self.logger = logger or logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def bind_event_recorder(self, event_recorder: Optional["EventRecorder"]):
        """Attach an :class:`EventRecorder` instance after initialisation."""
        self._event_recorder = event_recorder

    def handle_api_failure(
        self,
        provider: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        fallback_value: Optional[str] = None,
    ) -> str:
        """Handle API invocation errors and return a graceful fallback string."""
        context_data = {"provider": provider, **(context or {})}
        self.log_error_with_context(error, context_data, severity="error")

        fallback = fallback_value or (
            f"[API_ERROR] {provider} service temporarily unavailable."
        )
        return self.graceful_degradation(
            feature_name=f"{provider}_api_call",
            fallback_value=fallback,
            reason=str(error),
            context=context_data,
            record_event=False,
        )

    def handle_parsing_failure(
        self,
        stage: str,
        error: Exception,
        fallback_value: Any = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Handle downstream parsing/processing errors."""
        context_data = {"stage": stage, **(context or {})}
        self.log_error_with_context(error, context_data, severity="warning")

        return self.graceful_degradation(
            feature_name=f"{stage}_parsing",
            fallback_value=fallback_value,
            reason=str(error),
            context=context_data,
            record_event=False,
        )

    def graceful_degradation(
        self,
        feature_name: str,
        fallback_value: Any,
        reason: str,
        context: Optional[Dict[str, Any]] = None,
        record_event: bool = True,
    ) -> Any:
        """Return a fallback value while logging the degradation."""
        message = (
            f"Graceful degradation engaged for {feature_name}: {reason}"
        )
        self.logger.warning(message)

        if record_event:
            event_payload = {
                "feature": feature_name,
                "reason": reason,
                "context": self._prepare_context(context),
            }
            self._record_error_event(
                category="graceful_degradation",
                severity="warning",
                details=event_payload,
            )

        return fallback_value

    def log_error_with_context(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "error",
    ) -> Dict[str, Any]:
        """Log the provided error and record a normalised error payload."""
        log_message = f"{type(error).__name__}: {error}"
        if severity == "warning":
            self.logger.warning(log_message)
        elif severity == "info":
            self.logger.info(log_message)
        else:
            self.logger.error(log_message)

        error_payload = {
            "error_type": type(error).__name__,
            "message": str(error),
            "context": self._prepare_context(context),
        }
        self._record_error_event(
            category="application_error",
            severity=severity,
            details=error_payload,
        )

        return {
            "success": False,
            "error": str(error),
            "error_type": type(error).__name__,
            "timestamp": datetime.now().isoformat(),
            "context": error_payload["context"],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _record_error_event(
        self,
        category: str,
        severity: str,
        details: Dict[str, Any],
    ) -> None:
        if not self._event_recorder:
            return

        event_data = {
            "category": category,
            "severity": severity,
            "details": details,
        }

        try:
            self._event_recorder.append_system_event(
                "error_occurred", event_data
            )
        except Exception as recorder_error:  # pragma: no cover - logging safeguard
            self.logger.debug(
                "Failed to record error event: %s", recorder_error
            )

    def _prepare_context(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not context:
            return {}

        safe_context: Dict[str, Any] = {}
        for key, value in context.items():
            safe_context[key] = self._safe_value(value)
        return safe_context

    def _safe_value(self, value: Any) -> Any:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, dict):
            return {k: self._safe_value(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._safe_value(v) for v in value]
        return str(value)
