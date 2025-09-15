"""Linus原則合規檢查器。

此模組提供 `check_compliance` 函式，針對 AI 產出的工作報告
進行簡單的規則式分析，評估是否符合 Linus 工程哲學：
- 好品味（Good Taste）：避免特殊案例或骯髒的 quick hack。
- 簡潔性（Simplicity）：避免不必要的複雜度與過度設計。
- 實用主義（Pragmatism）：提供可執行的成果與驗證。
- Never break userspace：維持向後相容與驗證。

規則採保守策略：只在高度可疑時才回報違規，避免誤報。
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

# Linus 工程哲學定義，供檢查時引用
PRINCIPLES = {
    "good_taste": {
        "name": "好品味",
        "description": "讓特殊情況消失並維持一致的設計。",
    },
    "simplicity": {
        "name": "簡潔性",
        "description": "避免過度複雜與不必要的抽象。",
    },
    "pragmatism": {
        "name": "實用主義",
        "description": "交付可落地的成果並處理真實問題。",
    },
    "never_break_userspace": {
        "name": "Never break userspace",
        "description": "維持向後相容並確保測試覆蓋。",
    },
}

# 與程式開發相關的任務型別，用來啟用較嚴格的檢查
CODING_TASK_TYPES = {
    "feature_dev",
    "bug_fix",
    "refactor",
    "system_design",
    "code_review",
    "testing",
    "documentation",
    "performance_optimization",
}

# 與測試相關的關鍵字，用於偵測是否有驗證流程
TEST_KEYWORDS = (
    "test",
    "tests",
    "testing",
    "unit test",
    "integration test",
    "驗證",
    "測試",
    "coverage",
)

# 會造成違規的典型片語
SPECIAL_CASE_PATTERNS = (
    r"special case",
    r"quick hack",
    r"hacky",
    r"temporary fix",
    r"workaround",
    r"monkey patch",
    r"dirty fix",
)

BREAKING_CHANGE_PATTERNS = (
    r"breaking change",
    r"backward incompatible",
    r"incompatible change",
    r"破壞相容",
    r"不相容",
    r"移除舊介面",
)

COMPLEXITY_PATTERNS = (
    r"overly complex",
    r"too complex",
    r"complex workaround",
    r"deeply nested",
    r"過度複雜",
    r"巢狀超過",
)


def _normalize_work_report(work_report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """確保回傳可操作的工作報告資料結構。"""
    if not isinstance(work_report, dict):
        return {}
    return work_report


def _collect_text_fragments(work_report: Dict[str, Any]) -> str:
    """將工作報告內的文字欄位集中為單一字串以供比對。"""
    fragments: List[str] = []
    for key in ("summary", "details", "analysis", "plan", "notes", "raw_response"):
        value = work_report.get(key)
        if isinstance(value, str):
            fragments.append(value)
    # 若提取器有提供步驟或項目列表，也納入分析
    for key in ("steps", "actions", "todos"):
        value = work_report.get(key)
        if isinstance(value, list):
            fragments.extend(str(item) for item in value if item)
    return " \n".join(fragments)


def _add_violation(
    violations: List[Dict[str, Any]],
    principle_key: str,
    description: str,
    suggestion: str,
    severity: str = "medium",
    evidence: Optional[str] = None,
) -> None:
    """建立違規紀錄並加入列表。"""
    principle = PRINCIPLES.get(principle_key, {"name": principle_key})
    violations.append(
        {
            "principle": principle["name"],
            "principle_key": principle_key,
            "description": description,
            "suggestion": suggestion,
            "severity": severity,
            "evidence": evidence,
        }
    )


def _add_good_aspect(
    good_aspects: List[Dict[str, Any]],
    principle_key: str,
    description: str,
    evidence: Optional[str] = None,
) -> None:
    principle = PRINCIPLES.get(principle_key, {"name": principle_key})
    good_aspects.append(
        {
            "principle": principle["name"],
            "principle_key": principle_key,
            "description": description,
            "evidence": evidence,
        }
    )


def check_compliance(work_report: Optional[Dict[str, Any]], ai_role: Optional[str]) -> Dict[str, Any]:
    """根據 Linus 原則檢查工作報告的合規性。

    Args:
        work_report: 由 AI 產出的結構化工作報告。
        ai_role: 目前 AI 的角色名稱，用於調整規則嚴格度。

    Returns:
        Dict[str, Any]: 合規檢查結果，包含違規清單與建議。
    """

    normalized_report = _normalize_work_report(work_report)
    summary: str = str(normalized_report.get("summary", "") or "").strip()
    task_type = normalized_report.get("task_type")
    combined_text = _collect_text_fragments(normalized_report)
    combined_lower = combined_text.lower()

    violations: List[Dict[str, Any]] = []
    good_aspects: List[Dict[str, Any]] = []

    # 規則 1：摘要缺失或過短
    if not summary:
        _add_violation(
            violations,
            "pragmatism",
            "工作報告缺少摘要，難以確認產出的成果。",
            "補充此次工作的關鍵輸出、修改檔案與影響範圍。",
            severity="high",
        )
    elif len(summary) < 30 and (task_type in CODING_TASK_TYPES or ai_role):
        _add_violation(
            violations,
            "pragmatism",
            "摘要過於精簡，可能不足以支援交接或追蹤。",
            "提供更多具體成果與驗證資訊，確保交接順暢。",
            severity="medium",
            evidence=summary,
        )

    # 規則 2：偵測可能破壞相容性的語句
    for pattern in BREAKING_CHANGE_PATTERNS:
        match = re.search(pattern, combined_lower)
        if match:
            _add_violation(
                violations,
                "never_break_userspace",
                "報告提及可能破壞向後相容性的變更。",
                "重新檢視變更對既有使用者的影響，必要時提供遷移方案或退場機制。",
                severity="high",
                evidence=match.group(0),
            )
            break

    # 規則 3：偵測骯髒的 quick hack 或特殊案例處理
    for pattern in SPECIAL_CASE_PATTERNS:
        match = re.search(pattern, combined_lower)
        if match:
            _add_violation(
                violations,
                "good_taste",
                "出現 quick hack 或特殊案例處理，可能破壞一致性。",
                "評估是否可以抽象出通用解法，讓特殊情況消失。",
                severity="medium",
                evidence=match.group(0),
            )
            break

    # 規則 4：過度複雜的描述
    for pattern in COMPLEXITY_PATTERNS:
        match = re.search(pattern, combined_lower)
        if match:
            _add_violation(
                violations,
                "simplicity",
                "報告描述方案可能過度複雜。",
                "重新檢視流程與抽象層級，尋找更簡潔的實作方式。",
                severity="low",
                evidence=match.group(0),
            )
            break

    # 規則 5：缺少測試或驗證（僅對程式相關任務啟用）
    is_coding_task = (task_type in CODING_TASK_TYPES) or (
        ai_role in {
            "system_architect",
            "coder_programmer",
            "coder_reviewer",
            "devops_engineer",
            "qa_engineer",
            "performance_optimizer",
        }
    )

    if is_coding_task:
        if combined_text and any(keyword in combined_lower for keyword in TEST_KEYWORDS):
            # 有提及測試，視為正向指標
            snippet = next(
                (keyword for keyword in TEST_KEYWORDS if keyword in combined_lower),
                None,
            )
            _add_good_aspect(
                good_aspects,
                "never_break_userspace",
                "工作報告提及測試或驗證流程。",
                evidence=snippet,
            )
        else:
            _add_violation(
                violations,
                "never_break_userspace",
                "程式相關任務未提及測試或驗證步驟。",
                "補充單元測試、整合測試或驗證流程，以降低回歸風險。",
                severity="medium",
            )

    # 若報告有提及「重構 / 簡化」，加入正向觀察
    if re.search(r"refactor|重構|simplif", combined_lower):
        _add_good_aspect(
            good_aspects,
            "good_taste",
            "提及重構或簡化設計，有助於維持好品味。",
        )

    # 分數計算：違規扣分，正向加分
    score = max(0, min(100, 100 - len(violations) * 20 + len(good_aspects) * 5))

    compliance_result: Dict[str, Any] = {
        "checked": True,
        "checked_at": datetime.utcnow().isoformat() + "Z",
        "ai_role": ai_role,
        "task_type": task_type,
        "summary": summary,
        "method": "rule_based_v1",
        "score": score,
        "is_compliant": len(violations) == 0,
        "violations": violations,
        "violations_count": len(violations),
        "good_aspects": good_aspects,
    }

    if violations:
        # 根據最嚴重的違規給出簡短描述
        severity_order = {"low": 0, "medium": 1, "high": 2}
        worst = max(violations, key=lambda item: severity_order.get(item["severity"], 0))
        compliance_result["overall_feedback"] = (
            f"發現 {len(violations)} 項可能違反 Linus 原則的情況，"
            f"最嚴重為「{worst['principle']}」。"
        )
    else:
        compliance_result["overall_feedback"] = "未偵測到明顯的 Linus 原則違規。"

    return compliance_result


__all__ = ["check_compliance"]
