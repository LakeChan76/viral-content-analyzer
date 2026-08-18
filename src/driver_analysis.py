from src.llm_client import chat_json
import json


DRIVER_PROMPT = """你是资深内容运营专家。请对比以下高表现和低表现推文的拆解结果，找出真正驱动表现的因素。

高表现内容拆解（TOP5）：
{high_analysis}

低表现内容拆解（BOTTOM5）：
{low_analysis}

请对比分析，找出"高表现都有、低表现都缺"的特征，判断真正驱动表现的因素。

输出JSON格式：
{{
  "key_drivers": [
    {{
      "factor": "驱动因素名称（如：数据型Hook）",
      "evidence": "证据（高表现内容中哪些体现了这个因素）",
      "low_evidence": "低表现内容中缺少这个因素的表现",
      "impact": "影响程度（高/中/低）",
      "explanation": "为什么这个因素能驱动表现"
    }}
  ],
  "summary": "整体结论：什么样的内容在这个账号上容易爆"
}}"""


def analyze_drivers(high_analyses, low_analyses):
    high_text = json.dumps(high_analyses, ensure_ascii=False, indent=2)
    low_text = json.dumps(low_analyses, ensure_ascii=False, indent=2)

    prompt = DRIVER_PROMPT.format(high_analysis=high_text, low_analysis=low_text)
    result = chat_json(prompt)
    return result


def format_driver_report(driver_result):
    report = "# 驱动因素分析报告\n\n"
    report += f"**整体结论**：{driver_result.get('summary', '')}\n\n"
    report += "## 关键驱动因素\n\n"

    for i, d in enumerate(driver_result.get("key_drivers", []), 1):
        report += f"### {i}. {d.get('factor', '')}（影响度：{d.get('impact', '')}）\n"
        report += f"- **高表现证据**：{d.get('evidence', '')}\n"
        report += f"- **低表现缺失**：{d.get('low_evidence', '')}\n"
        report += f"- **原因分析**：{d.get('explanation', '')}\n\n"

    return report
