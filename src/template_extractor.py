from src.llm_client import chat_json
import json


TEMPLATE_PROMPT = """你是资深内容运营专家。基于以下驱动因素分析，提炼出可复用的内容结构模板。

驱动因素分析：
{driver_analysis}

高表现内容示例：
{high_examples}

请输出1-2个可复用的内容结构模板，JSON格式：
{{
  "templates": [
    {{
      "name": "模板名称（如：数据冲击型）",
      "formula": "内容公式（如：数据开头 + 3点递进分析 + 反问式收尾）",
      "opening": "开头写法（具体说明怎么开头）",
      "body": "主体结构（怎么组织内容）",
      "ending": "结尾写法（怎么收尾，CTA怎么设计）",
      "applicable_topics": "适合什么类型的话题",
      "example": "用这个模板写一个简短示例"
    }}
  ]
}}"""


def extract_templates(driver_result, high_analyses):
    high_examples = "\n".join([
        f"- {a.get('original_content', '')[:150]}"
        for a in high_analyses[:3]
    ])

    prompt = TEMPLATE_PROMPT.format(
        driver_analysis=json.dumps(driver_result, ensure_ascii=False),
        high_examples=high_examples,
    )
    return chat_json(prompt)


def format_template_report(template_result):
    report = "# 可复用内容模板\n\n"
    for i, t in enumerate(template_result.get("templates", []), 1):
        report += f"## 模板{i}：{t.get('name', '')}\n\n"
        report += f"**内容公式**：{t.get('formula', '')}\n\n"
        report += f"**开头写法**：{t.get('opening', '')}\n\n"
        report += f"**主体结构**：{t.get('body', '')}\n\n"
        report += f"**结尾写法**：{t.get('ending', '')}\n\n"
        report += f"**适合话题**：{t.get('applicable_topics', '')}\n\n"
        report += f"**示例**：{t.get('example', '')}\n\n"
        report += "---\n\n"
    return report
