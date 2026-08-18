from src.llm_client import chat_json
import json
import time


BATCH_ANALYSIS_PROMPT = """你是资深内容运营专家。请从以下6个维度拆解每条推文：
选题、Hook、结构、信息密度、CTA、互动设计

以下是{count}条推文数据：

{tweets_data}

请逐条分析，输出JSON格式：
{{
  "analyses": [
    {{
      "topic": "选题分析",
      "hook": "Hook分析（数据冲击/反常识/提问/故事/争议等）",
      "structure": "结构分析（总分总/递进/对比/清单等）",
      "information_density": "信息密度分析",
      "cta": "CTA分析",
      "interaction_design": "互动设计分析"
    }}
  ]
}}

注意：analyses数组的顺序必须和输入推文顺序一致，共{count}条。"""


def analyze_batch(tweets, batch_label=""):
    tweets_data = ""
    for i, tweet in enumerate(tweets, 1):
        tweets_data += f"\n【推文{i}】\n"
        tweets_data += f"内容：{tweet['content']}\n"
        tweets_data += f"互动 - 转发:{tweet.get('reposts', 0)} 点赞:{tweet.get('likes', 0)} 评论:{tweet.get('replies', 0)} 引用:{tweet.get('quotes', 0)} 互动率:{tweet.get('engagement_rate', 0)}%\n"

    prompt = BATCH_ANALYSIS_PROMPT.format(count=len(tweets), tweets_data=tweets_data)
    result = chat_json(prompt)

    analyses = result.get("analyses", [])
    for i, analysis in enumerate(analyses):
        if i < len(tweets):
            analysis["original_content"] = tweets[i]["content"]
            analysis["engagement_rate"] = tweets[i].get("engagement_rate", 0)

    while len(analyses) < len(tweets):
        analyses.append({
            "topic": "分析失败",
            "hook": "",
            "structure": "",
            "information_density": "",
            "cta": "",
            "interaction_design": "",
            "original_content": tweets[len(analyses)]["content"],
            "engagement_rate": tweets[len(analyses)].get("engagement_rate", 0),
        })

    return analyses


def analyze_high_performance(tweets):
    return analyze_batch(tweets, "高表现")


def format_analysis_report(analyses):
    report = "# 爆款内容拆解报告\n\n"
    for i, a in enumerate(analyses, 1):
        report += f"## 第{i}条 | 互动率 {a.get('engagement_rate', 'N/A')}%\n"
        report += f"> 原文：{a.get('original_content', '')[:100]}...\n\n"
        report += f"**选题**：{a.get('topic', '')}\n\n"
        report += f"**Hook**：{a.get('hook', '')}\n\n"
        report += f"**结构**：{a.get('structure', '')}\n\n"
        report += f"**信息密度**：{a.get('information_density', '')}\n\n"
        report += f"**CTA**：{a.get('cta', '')}\n\n"
        report += f"**互动设计**：{a.get('interaction_design', '')}\n\n"
        report += "---\n\n"
    return report
