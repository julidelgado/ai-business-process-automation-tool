from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings
from app.schemas.planner import PlannerResponse, WorkflowSpec


@dataclass
class PlannerResult:
    spec: WorkflowSpec
    confidence: float
    warnings: list[str]
    provider: str


class PlannerService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def generate(self, prompt: str) -> PlannerResponse:
        if self.settings.ai_provider.lower() == "ollama":
            result = self._try_ollama(prompt)
            if result is not None:
                return PlannerResponse(
                    spec=result.spec,
                    confidence=result.confidence,
                    warnings=result.warnings,
                    provider=result.provider,
                )

        fallback = self._fallback(prompt)
        return PlannerResponse(
            spec=fallback.spec,
            confidence=fallback.confidence,
            warnings=fallback.warnings,
            provider=fallback.provider,
        )

    def _try_ollama(self, prompt: str) -> PlannerResult | None:
        instructions = (
            "Return JSON only with keys: name, version, trigger, steps, warnings. "
            "trigger.type one of webhook/manual/schedule. "
            "steps[].type one of crm.create_contact,email.send,http.request. "
            "steps[].depends_on must reference existing step ids."
        )
        full_prompt = f"{instructions}\n\nUser intent:\n{prompt}"
        configured_model = self.settings.ollama_model

        try:
            spec = self._generate_with_model(configured_model, full_prompt)
            return PlannerResult(
                spec=spec,
                confidence=0.86,
                warnings=spec.warnings,
                provider=f"ollama:{configured_model}",
            )
        except httpx.HTTPStatusError as exc:
            message = self._extract_ollama_error(exc.response)
            if exc.response.status_code == 404 and "model" in message.lower() and "not found" in message.lower():
                detected_model = self._find_first_available_model()
                if detected_model and detected_model != configured_model:
                    try:
                        spec = self._generate_with_model(detected_model, full_prompt)
                        warnings = list(spec.warnings)
                        warnings.append(
                            f"Configured model '{configured_model}' was not found. Used installed model '{detected_model}'."
                        )
                        return PlannerResult(
                            spec=spec,
                            confidence=0.82,
                            warnings=warnings,
                            provider=f"ollama:{detected_model}",
                        )
                    except Exception as retry_exc:  # noqa: BLE001
                        return PlannerResult(
                            spec=self._fallback(prompt).spec,
                            confidence=0.62,
                            warnings=[
                                "Ollama model mismatch and retry failed, fallback used: "
                                f"{retry_exc!s}"
                            ],
                            provider="fallback",
                        )
            return PlannerResult(
                spec=self._fallback(prompt).spec,
                confidence=0.62,
                warnings=["Ollama request failed. A deterministic fallback planner generated the workflow spec."],
                provider="fallback",
            )
        except Exception:  # noqa: BLE001
            return PlannerResult(
                spec=self._fallback(prompt).spec,
                confidence=0.62,
                warnings=["Ollama response could not be validated. A deterministic fallback spec was generated."],
                provider="fallback",
            )

    def _generate_with_model(self, model: str, prompt: str) -> WorkflowSpec:
        response = httpx.post(
            f"{self.settings.ollama_base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        model_output = response.json().get("response", "")
        parsed = json.loads(model_output)
        normalized = self._normalize_ollama_payload(parsed)
        return WorkflowSpec.model_validate(normalized)

    def _find_first_available_model(self) -> str | None:
        try:
            response = httpx.get(
                f"{self.settings.ollama_base_url}/api/tags",
                timeout=self.settings.request_timeout_seconds,
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            models = payload.get("models", [])
            if not models:
                return None
            first = models[0]
            if isinstance(first, dict):
                name = first.get("name")
                if isinstance(name, str) and name:
                    return name
            return None
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _extract_ollama_error(response: httpx.Response) -> str:
        try:
            data = response.json()
            if isinstance(data, dict) and isinstance(data.get("error"), str):
                return data["error"]
            return response.text
        except Exception:  # noqa: BLE001
            return response.text

    @staticmethod
    def _normalize_ollama_payload(raw: Any) -> dict[str, Any]:
        if not isinstance(raw, dict):
            return {
                "name": "generated-workflow",
                "version": 1,
                "trigger": {"type": "manual"},
                "steps": [
                    {
                        "id": "call_external_api",
                        "type": "http.request",
                        "input": {"method": "POST", "url": "https://example.com/webhook"},
                    }
                ],
                "warnings": ["Ollama output was not a JSON object; normalized to generic workflow."],
            }

        payload = dict(raw)
        payload.setdefault("name", "generated-workflow")
        payload["version"] = PlannerService._coerce_version(payload.get("version"))
        payload.setdefault("warnings", [])

        trigger = payload.get("trigger")
        if isinstance(trigger, str):
            trigger = {"type": trigger}
        if not isinstance(trigger, dict):
            trigger = {"type": "manual"}
        trigger_type_raw = str(trigger.get("type", "manual")).lower()
        trigger_type = PlannerService._normalize_trigger_type(trigger_type_raw)
        trigger["type"] = trigger_type
        if trigger_type == "webhook" and not trigger.get("event"):
            trigger["event"] = "client.created"
        if trigger_type == "schedule" and not trigger.get("cron"):
            trigger["cron"] = "0 9 * * *"
        payload["trigger"] = trigger

        steps_raw = payload.get("steps")
        if not isinstance(steps_raw, list) or not steps_raw:
            steps_raw = [{"type": "http.request", "input": {"method": "POST", "url": "https://example.com/webhook"}}]

        normalized_steps: list[dict[str, Any]] = []
        generated_ids: list[str] = []
        for idx, step in enumerate(steps_raw, start=1):
            if not isinstance(step, dict):
                continue
            step_copy = dict(step)
            step_type = PlannerService._normalize_step_type(str(step_copy.get("type", "http.request")))
            step_copy["type"] = step_type
            step_id = step_copy.get("id")
            if not isinstance(step_id, str) or not step_id.strip():
                if step_type == "crm.create_contact":
                    step_id = "create_crm_contact"
                elif step_type == "email.send":
                    step_id = "send_welcome_email"
                elif step_type == "http.request":
                    step_id = "call_external_api"
                else:
                    step_id = f"step_{idx}"
            step_copy["id"] = step_id

            depends_on = step_copy.get("depends_on", [])
            if not isinstance(depends_on, list):
                depends_on = []
            normalized_id_lookup = {
                re.sub(r"[^a-z0-9]+", "", item.lower()): item for item in generated_ids
            }
            fixed_depends: list[str] = []
            for dep in depends_on:
                if not isinstance(dep, str) or not dep.strip():
                    continue
                dep_clean = dep.strip()
                if dep_clean.startswith("<existing_step_id") and generated_ids:
                    fixed_depends.append(generated_ids[0])
                    continue
                if dep_clean in generated_ids:
                    fixed_depends.append(dep_clean)
                    continue
                dep_key = re.sub(r"[^a-z0-9]+", "", dep_clean.lower())
                mapped = normalized_id_lookup.get(dep_key)
                if mapped:
                    fixed_depends.append(mapped)
                    continue
                if "crm" in dep_key and generated_ids:
                    crm_step = next((item for item in generated_ids if "crm" in item), generated_ids[0])
                    fixed_depends.append(crm_step)
            step_copy["depends_on"] = fixed_depends

            input_payload = step_copy.get("input")
            if not isinstance(input_payload, dict):
                config_payload = step_copy.get("config")
                if isinstance(config_payload, dict):
                    input_payload = config_payload
                else:
                    input_payload = {}
            step_copy["input"] = input_payload

            normalized_steps.append(step_copy)
            generated_ids.append(step_id)

        payload["steps"] = normalized_steps or [
            {"id": "call_external_api", "type": "http.request", "input": {"method": "POST", "url": "https://example.com/webhook"}}
        ]
        return payload

    @staticmethod
    def _normalize_trigger_type(raw_type: str) -> str:
        mapping = {
            "schedule": "schedule",
            "scheduled": "schedule",
            "cron": "schedule",
            "webhook": "webhook",
            "manual": "manual",
        }
        return mapping.get(raw_type, "manual")

    @staticmethod
    def _normalize_step_type(raw_type: str) -> str:
        normalized = raw_type.strip().lower()
        mapping = {
            "crm.create_contact": "crm.create_contact",
            "crm.create_entry": "crm.create_contact",
            "crm.create_record": "crm.create_contact",
            "email.send": "email.send",
            "email.send_email": "email.send",
            "smtp.send": "email.send",
            "http.request": "http.request",
            "http.call": "http.request",
        }
        return mapping.get(normalized, "http.request")

    @staticmethod
    def _coerce_version(raw_version: Any) -> int:
        if isinstance(raw_version, int):
            return max(raw_version, 1)
        if isinstance(raw_version, float):
            return max(int(raw_version), 1)
        if isinstance(raw_version, str):
            text = raw_version.strip()
            if text.isdigit():
                return max(int(text), 1)
            try:
                return max(int(float(text)), 1)
            except ValueError:
                return 1
        return 1

    def _fallback(self, prompt: str) -> PlannerResult:
        prompt_l = prompt.lower()
        warnings: list[str] = []
        steps: list[dict] = []

        trigger: dict = {"type": "manual"}
        cron = self._infer_schedule_cron(prompt_l)
        if cron is not None:
            trigger = {"type": "schedule", "cron": cron}
        if "when" in prompt_l and any(token in prompt_l for token in ["sign up", "signup", "new client", "client signs"]):
            trigger = {"type": "webhook", "event": "client.created"}

        to_email = self._extract_first_email(prompt)
        default_to = to_email if to_email else "{{trigger.payload.email}}"

        if "crm" in prompt_l or "client" in prompt_l or "contact" in prompt_l:
            steps.append(
                {
                    "id": "create_crm_contact",
                    "type": "crm.create_contact",
                    "input": {
                        "email": "{{trigger.payload.email}}",
                        "first_name": "{{trigger.payload.first_name}}",
                        "last_name": "{{trigger.payload.last_name}}",
                    },
                    "retry": {"max_attempts": 3, "backoff_seconds": 10},
                }
            )

        wants_email = "email" in prompt_l and any(
            token in prompt_l for token in ["send", "welcome", "notify", "summary", "report"]
        )
        if wants_email:
            depends = ["create_crm_contact"] if any(step["id"] == "create_crm_contact" for step in steps) else []
            subject = "Welcome to our service"
            if "summary" in prompt_l:
                subject = "Daily Summary"
            elif "report" in prompt_l:
                subject = "Automated Report"
            steps.append(
                {
                    "id": "send_welcome_email",
                    "type": "email.send",
                    "depends_on": depends,
                    "input": {
                        "to": default_to,
                        "subject": subject,
                        "template_id": "welcome_v1",
                        "variables": {"first_name": "{{trigger.payload.first_name}}"},
                    },
                    "retry": {"max_attempts": 3, "backoff_seconds": 10},
                }
            )

        if not steps:
            warnings.append("Could not confidently infer actions; generated a generic HTTP step.")
            steps.append(
                {
                    "id": "call_external_api",
                    "type": "http.request",
                    "input": {
                        "method": "POST",
                        "url": "https://example.com/webhook",
                        "json": {"payload": "{{trigger.payload}}"},
                    },
                    "retry": {"max_attempts": 2, "backoff_seconds": 10},
                }
            )

        slug = re.sub(r"[^a-z0-9]+", "-", prompt_l).strip("-")[:50] or "generated-workflow"
        spec = WorkflowSpec.model_validate(
            {
                "name": slug,
                "version": 1,
                "trigger": trigger,
                "steps": steps,
                "warnings": warnings,
            }
        )
        return PlannerResult(
            spec=spec,
            confidence=0.68 if not warnings else 0.52,
            warnings=warnings,
            provider="fallback",
        )

    @staticmethod
    def _extract_first_email(prompt: str) -> str | None:
        match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", prompt)
        return match.group(0) if match else None

    @staticmethod
    def _infer_schedule_cron(prompt_l: str) -> str | None:
        schedule_tokens = [
            "every day",
            "daily",
            "every weekday",
            "weekdays",
            "every monday",
            "every tuesday",
            "every wednesday",
            "every thursday",
            "every friday",
            "every saturday",
            "every sunday",
        ]
        has_schedule_intent = any(token in prompt_l for token in schedule_tokens)
        has_time = " at " in f" {prompt_l} " or re.search(r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b", prompt_l) is not None
        if not has_schedule_intent and not has_time:
            return None

        minute = 0
        hour = 9
        time_match = re.search(r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", prompt_l)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            meridian = time_match.group(3)
            if meridian == "pm" and hour != 12:
                hour += 12
            if meridian == "am" and hour == 12:
                hour = 0

        dow = "*"
        days_map = {
            "monday": "1",
            "tuesday": "2",
            "wednesday": "3",
            "thursday": "4",
            "friday": "5",
            "saturday": "6",
            "sunday": "0",
        }
        for day_name, day_val in days_map.items():
            if f"every {day_name}" in prompt_l:
                dow = day_val
                break
        if "weekday" in prompt_l:
            dow = "1-5"

        return f"{minute} {hour} * * {dow}"
