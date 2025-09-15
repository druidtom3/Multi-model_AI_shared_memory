"""Report extractor utilities for structured work reports.

This module provides a robust parser that attempts to recover structured
information from large-language-model responses.  It follows a progressive
extraction strategy:

1. 主解析器：優先嘗試解析JSON/結構化區塊，若成功則回傳高信心結果。
2. 降級機制：若無法取得結構化資料，改以段落與項目符號的啟發式解析。
3. 最終保護：仍無法解析時，提供 `fallback_extraction` 生成的基礎紀錄，
   確保事件流至少保有摘要與請求內容。

Every returned report contains unified keys and metadata, including a
confidence label describing the reliability of the extraction.
"""

from __future__ import annotations

import ast
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ExtractionMetadata:
    """Metadata describing how a report was extracted."""

    confidence: str
    extraction_method: str
    notes: Optional[str] = None
    raw_structured_data: Optional[Dict[str, Any]] = None
    raw_text_excerpt: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    role: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "confidence": self.confidence,
            "extraction_method": self.extraction_method,
        }
        if self.notes:
            data["notes"] = self.notes
        if self.raw_structured_data is not None:
            data["raw_structured_data"] = self.raw_structured_data
        if self.raw_text_excerpt:
            data["raw_text_excerpt"] = self.raw_text_excerpt
        if self.provider:
            data["provider"] = self.provider
        if self.model:
            data["model"] = self.model
        if self.role:
            data["role"] = self.role
        return data


class ReportExtractor:
    """Work report extractor with progressive degradation."""

    #: Section aliases used by heuristic parser (both English and Chinese).
    SECTION_ALIASES: Dict[str, Tuple[str, ...]] = {
        "summary": (
            "summary",
            "overall summary",
            "overall",
            "overview",
            "result",
            "結果",
            "總結",
            "摘要",
            "概述",
        ),
        "tasks": (
            "tasks",
            "completed tasks",
            "work done",
            "actions",
            "已完成",
            "完成事項",
            "實作",
        ),
        "next_steps": (
            "next steps",
            "todo",
            "upcoming",
            "plan",
            "待辦",
            "下一步",
            "後續工作",
        ),
        "blockers": (
            "blockers",
            "risks",
            "issues",
            "problems",
            "風險",
            "阻礙",
            "問題",
        ),
        "decisions": (
            "decisions",
            "key decisions",
            "choices",
            "決策",
        ),
        "references": (
            "references",
            "links",
            "artifacts",
            "resources",
            "附錄",
            "連結",
        ),
        "notes": (
            "notes",
            "observations",
            "remarks",
            "備註",
        ),
    }

    def extract_work_report(
        self,
        user_message: str,
        ai_response: str,
        ai_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Extract a structured work report with fallback guarantees."""

        if not ai_response:
            logger.warning("AI response is empty, using fallback extraction")
            return self.fallback_extraction(
                user_message,
                ai_response,
                ai_config=ai_config,
                reason="empty_response",
            )

        # Step 1: attempt structured JSON extraction
        try:
            structured_data = self._parse_structured_json(ai_response)
            if structured_data is not None:
                report = self._build_report_from_structured(
                    structured_data,
                    user_message,
                    ai_response,
                    ai_config,
                )
                if report:
                    return report
        except Exception as exc:  # noqa: BLE001 - log unexpected parsing errors
            logger.warning("Structured report parsing failed: %s", exc)

        # Step 2: heuristic extraction based on headings/bullets
        try:
            heuristic_report = self._heuristic_extraction(
                user_message,
                ai_response,
                ai_config,
            )
            if heuristic_report:
                return heuristic_report
        except Exception as exc:  # noqa: BLE001
            logger.warning("Heuristic extraction failed: %s", exc)

        # Step 3: fallback to minimal record
        return self.fallback_extraction(
            user_message,
            ai_response,
            ai_config=ai_config,
            reason="no_structure_detected",
        )

    # ------------------------------------------------------------------
    # Structured JSON extraction
    # ------------------------------------------------------------------
    def _parse_structured_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract the first JSON object embedded in text."""

        for candidate in self._iter_json_candidates(text):
            try:
                loaded = json.loads(candidate)
            except json.JSONDecodeError:
                try:
                    # As a secondary attempt, fall back to literal evaluation.
                    loaded = ast.literal_eval(candidate)
                except (ValueError, SyntaxError):
                    logger.debug("Failed to parse JSON candidate: %s", candidate)
                    continue
            if isinstance(loaded, dict):
                return loaded
            if isinstance(loaded, list):
                # Convert a list into basic tasks list.
                return {"tasks": loaded}
        return None

    def _iter_json_candidates(self, text: str) -> Iterable[str]:
        """Yield JSON candidates discovered in text blocks."""

        fenced_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
        for block in fenced_blocks:
            cleaned = block.strip()
            if cleaned:
                yield cleaned

        stripped = text.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            yield stripped

        # Attempt to capture balanced braces when JSON is embedded inline.
        brace_match = re.search(r"\{[\s\S]*\}", text)
        if brace_match:
            yield brace_match.group(0)

    def _build_report_from_structured(
        self,
        data: Dict[str, Any],
        user_message: str,
        ai_response: str,
        ai_config: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        normalized = self._normalize_report_fields(data, ai_response)

        metadata = ExtractionMetadata(
            confidence="high",
            extraction_method="structured_json",
            notes="Parsed structured JSON block",
            raw_structured_data=data,
            raw_text_excerpt=self._truncate(ai_response, 280),
            provider=(ai_config or {}).get("provider"),
            model=(ai_config or {}).get("model"),
            role=(ai_config or {}).get("role"),
        )

        normalized["metadata"] = metadata.to_dict()
        normalized["task_type"] = (
            data.get("task_type")
            or normalized.get("task_type")
            or self._infer_task_type(ai_response)
        )
        if not normalized.get("summary"):
            normalized["summary"] = self._summarize_text(ai_response)
        normalized.setdefault("source", "structured")
        normalized.setdefault("user_request", self._truncate(user_message, 200))
        return normalized

    def _normalize_report_fields(
        self,
        data: Dict[str, Any],
        ai_response: str,
    ) -> Dict[str, Any]:
        """Normalize various possible field names into unified structure."""

        summary = self._first_non_empty(
            data,
            [
                "summary",
                "overall_summary",
                "overview",
                "result",
                "description",
                "摘要",
                "總結",
                "概述",
            ],
        )
        if isinstance(summary, list):
            summary = " ".join(self._stringify_list(summary))
        elif isinstance(summary, dict):
            summary = json.dumps(summary, ensure_ascii=False)

        report: Dict[str, Any] = {
            "summary": self._clean_sentence(summary) if summary else "",
            "tasks": self._normalize_to_list(
                data,
                [
                    "tasks",
                    "completed_tasks",
                    "work_done",
                    "actions",
                    "實作",
                    "完成事項",
                ],
            ),
            "next_steps": self._normalize_to_list(
                data,
                [
                    "next_steps",
                    "upcoming",
                    "plan",
                    "todo",
                    "待辦",
                    "後續工作",
                ],
            ),
            "blockers": self._normalize_to_list(
                data,
                [
                    "blockers",
                    "risks",
                    "issues",
                    "problems",
                    "風險",
                    "阻礙",
                ],
            ),
            "decisions": self._normalize_to_list(
                data,
                [
                    "decisions",
                    "key_decisions",
                    "choices",
                    "決策",
                ],
            ),
            "references": self._normalize_to_list(
                data,
                [
                    "references",
                    "links",
                    "resources",
                    "artifacts",
                    "附錄",
                ],
            ),
            "notes": self._normalize_to_list(
                data,
                [
                    "notes",
                    "remarks",
                    "observations",
                    "備註",
                ],
            ),
        }

        report["task_type"] = (
            self._first_non_empty(data, ["task_type", "category"])
            or self._infer_task_type(ai_response)
        )

        additional_fields = {
            key: value
            for key, value in data.items()
            if key not in {
                "summary",
                "overall_summary",
                "overview",
                "result",
                "description",
                "tasks",
                "completed_tasks",
                "work_done",
                "actions",
                "實作",
                "完成事項",
                "next_steps",
                "upcoming",
                "plan",
                "todo",
                "待辦",
                "後續工作",
                "blockers",
                "risks",
                "issues",
                "problems",
                "風險",
                "阻礙",
                "decisions",
                "key_decisions",
                "choices",
                "決策",
                "references",
                "links",
                "resources",
                "artifacts",
                "附錄",
                "notes",
                "remarks",
                "observations",
                "備註",
                "task_type",
                "category",
            }
        }
        if additional_fields:
            report["metadata"] = {"additional_fields": additional_fields}

        return report

    # ------------------------------------------------------------------
    # Heuristic extraction
    # ------------------------------------------------------------------
    def _heuristic_extraction(
        self,
        user_message: str,
        ai_response: str,
        ai_config: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        lines = [line.strip() for line in ai_response.splitlines() if line.strip()]
        if not lines:
            return None

        sections = {
            "summary": [],
            "tasks": [],
            "next_steps": [],
            "blockers": [],
            "decisions": [],
            "references": [],
            "notes": [],
        }

        current_section: Optional[str] = None
        orphan_lines: List[str] = []

        for line in lines:
            header, content = self._split_header_content(line)
            section = self._match_section(header)
            cleaned_content = self._clean_sentence(content) if content else ""

            if section:
                current_section = section
                if cleaned_content:
                    self._append_to_section(sections, section, cleaned_content)
                continue

            if self._looks_like_bullet(line):
                bullet_text = self._clean_sentence(self._strip_bullet(line))
                target_section = current_section or "tasks"
                self._append_to_section(sections, target_section, bullet_text)
                continue

            if current_section:
                self._append_to_section(
                    sections,
                    current_section,
                    self._clean_sentence(line),
                )
            else:
                orphan_lines.append(self._clean_sentence(line))

        summary_text = " ".join(sections["summary"]).strip()
        if not summary_text:
            summary_text = " ".join(orphan_lines[:2]).strip()
        if not summary_text:
            summary_text = self._summarize_text(ai_response)

        report = {
            "summary": summary_text,
            "tasks": self._deduplicate(sections["tasks"]),
            "next_steps": self._deduplicate(sections["next_steps"]),
            "blockers": self._deduplicate(sections["blockers"]),
            "decisions": self._deduplicate(sections["decisions"]),
            "references": self._deduplicate(sections["references"]),
            "notes": self._deduplicate(sections["notes"]),
            "task_type": self._infer_task_type(ai_response),
            "user_request": self._truncate(user_message, 200),
            "source": "heuristic",
            "metadata": ExtractionMetadata(
                confidence="medium",
                extraction_method="heuristic",
                notes="Derived from headings/bullet parsing",
                raw_text_excerpt=self._truncate(ai_response, 280),
                provider=(ai_config or {}).get("provider"),
                model=(ai_config or {}).get("model"),
                role=(ai_config or {}).get("role"),
            ).to_dict(),
        }

        return report

    # ------------------------------------------------------------------
    # Fallback extraction
    # ------------------------------------------------------------------
    def fallback_extraction(
        self,
        user_message: str,
        ai_response: str,
        ai_config: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        summary_source = ai_response.strip() or user_message.strip()
        summary = self._truncate(summary_source, 240) if summary_source else ""
        if ai_response.strip() and len(ai_response.strip()) > len(summary):
            summary += "..."

        minimal_tasks = []
        if user_message.strip():
            minimal_tasks.append(
                self._truncate(f"User request: {user_message.strip()}", 200)
            )

        metadata = ExtractionMetadata(
            confidence="low",
            extraction_method="fallback",
            notes=reason or "Unable to parse structured report",
            raw_text_excerpt=self._truncate(ai_response, 180) if ai_response else None,
            provider=(ai_config or {}).get("provider"),
            model=(ai_config or {}).get("model"),
            role=(ai_config or {}).get("role"),
        ).to_dict()

        report = {
            "summary": summary or "AI回應不可用",
            "tasks": minimal_tasks,
            "next_steps": [],
            "blockers": [],
            "decisions": [],
            "references": [],
            "notes": [],
            "task_type": self._infer_task_type(ai_response or user_message),
            "user_request": self._truncate(user_message, 200),
            "source": "fallback",
            "metadata": metadata,
        }

        return report

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _first_non_empty(
        self,
        data: Dict[str, Any],
        keys: List[str],
    ) -> Optional[Any]:
        for key in keys:
            value = data.get(key)
            if value:
                return value
        return None

    def _normalize_to_list(
        self,
        data: Dict[str, Any],
        keys: List[str],
    ) -> List[str]:
        value = self._first_non_empty(data, keys)
        if value is None:
            return []
        return self._stringify_list(value)

    def _stringify_list(self, value: Any) -> List[str]:
        if isinstance(value, list):
            return [self._clean_sentence(self._stringify_item(item)) for item in value if item]
        if isinstance(value, (tuple, set)):
            return [self._clean_sentence(self._stringify_item(item)) for item in value if item]
        return [self._clean_sentence(self._stringify_item(value))]

    def _stringify_item(self, item: Any) -> str:
        if isinstance(item, str):
            return item.strip()
        if isinstance(item, dict):
            return json.dumps(item, ensure_ascii=False)
        return str(item)

    def _split_header_content(self, line: str) -> Tuple[str, str]:
        parts = re.split(r"[:：]", line, maxsplit=1)
        header = parts[0].strip()
        content = parts[1].strip() if len(parts) > 1 else ""
        return header, content

    def _match_section(self, header: str) -> Optional[str]:
        normalized = header.lower()
        for section, aliases in self.SECTION_ALIASES.items():
            if normalized in aliases:
                return section
        return None

    def _append_to_section(self, sections: Dict[str, List[str]], section: str, item: str) -> None:
        if not item:
            return
        if section == "summary":
            sections[section].append(item)
        else:
            sections.setdefault(section, []).append(item)

    def _looks_like_bullet(self, line: str) -> bool:
        return bool(re.match(r"^[\s>*-]*([*\-•]|\d+\.|\d+\))", line))

    def _strip_bullet(self, line: str) -> str:
        return re.sub(r"^[\s>*-]*([*\-•]|\d+\.|\d+\))\s*", "", line).strip()

    def _clean_sentence(self, text: str) -> str:
        if not text:
            return ""
        cleaned = re.sub(r"\s+", " ", text.strip())
        return cleaned

    def _truncate(self, text: str, limit: int) -> str:
        if not text:
            return ""
        truncated = text.strip()
        if len(truncated) <= limit:
            return truncated
        return truncated[: limit - 3].rstrip() + "..."

    def _summarize_text(self, text: str) -> str:
        sentences = re.split(r"(?<=[。.!?])\s+", text.strip()) if text.strip() else []
        if sentences:
            return self._truncate(" ".join(sentences[:2]), 240)
        return self._truncate(text, 240)

    def _deduplicate(self, items: List[str]) -> List[str]:
        seen = set()
        deduped = []
        for item in items:
            key = item.lower()
            if key not in seen and item:
                seen.add(key)
                deduped.append(item)
        return deduped

    def _infer_task_type(self, text: str) -> str:
        if not text:
            return "general"
        lowered = text.lower()
        keyword_map = {
            "system_design": ["architecture", "design", "架構", "設計"],
            "feature_dev": ["implement", "feature", "新增", "開發", "程式碼"],
            "bug_fix": ["bug", "fix", "修復", "修正", "錯誤"],
            "code_review": ["review", "審查", "檢視"],
            "testing": ["test", "testing", "測試"],
            "documentation": ["doc", "document", "documentation", "文檔", "文件"],
            "refactor": ["refactor", "重構"],
            "analysis": ["analysis", "研究", "investigate", "調查"],
        }
        for category, keywords in keyword_map.items():
            if any(keyword in lowered for keyword in keywords):
                return category
        return "general"


__all__ = ["ReportExtractor"]
