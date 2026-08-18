from src.llm_client import chat_json
import json


GENERATE_PROMPT = """你是X平台内容创作专家。请基于以下模板和主题，生成3条差异化的原创推文。

内容模板：
{templates}

高表现内容主题参考：
{topics}

要求：
1. 生成3条英文推文，每条不超过280字符
2. 3条要差异化——不同的Hook方式、不同的角度，但都套用模板的驱动因素
3. 不是简单改写参考内容，是换角度重新创作
4. 每条推文要能独立发布，完整表达一个观点

输出JSON格式：
{{
  "candidates": [
    {{
      "content": "推文英文内容",
      "hook_type": "使用的Hook类型",
      "angle": "切入角度说明",
      "template_used": "套用的模板名称",
      "char_count": "字符数"
    }}
  ]
}}"""


def generate_candidates(templates, high_analyses):
    topics = "\n".join([
        f"- {a.get('topic', '')}"
        for a in high_analyses[:3]
    ])

    template_text = json.dumps(templates, ensure_ascii=False, indent=2)
    prompt = GENERATE_PROMPT.format(templates=template_text, topics=topics)

    return chat_json(prompt, temperature=0.8)


def format_candidates_report(generate_result):
    report = "# 候选内容（待人工审核）\n\n"
    report += "⚠️ 以下内容需人工确认后才会写入资产库\n\n"

    for i, c in enumerate(generate_result.get("candidates", []), 1):
        report += f"## 候选{i}\n\n"
        report += f"**内容**：\n> {c.get('content', '')}\n\n"
        report += f"**Hook类型**：{c.get('hook_type', '')}\n"
        report += f"**切入角度**：{c.get('angle', '')}\n"
        report += f"**套用模板**：{c.get('template_used', '')}\n"
        report += f"**字符数**：{c.get('char_count', '')}/280\n\n"
        report += "---\n\n"

    return report
