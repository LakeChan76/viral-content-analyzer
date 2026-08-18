import difflib
from src.llm_client import chat_json
import json


def text_similarity(text1, text2):
    return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def check_similarity_batch(candidates, original_contents):
    results = []
    for candidate in candidates:
        cand_text = candidate.get("content", "")
        max_sim = 0
        max_sim_content = ""
        for orig in original_contents:
            sim = text_similarity(cand_text, orig)
            if sim > max_sim:
                max_sim = sim
                max_sim_content = orig

        results.append({
            "candidate": cand_text,
            "max_similarity": round(max_sim, 2),
            "most_similar_original": max_sim_content[:100],
            "risk_level": "high" if max_sim >= 0.7 else "medium" if max_sim >= 0.4 else "low",
        })
    return results


SEMANTIC_CHECK_PROMPT = """你是内容查重专家。请判断以下候选内容是否存在抄袭或过度借鉴原内容的情况。

候选内容：{candidate}
原文内容：{original}

请从以下角度判断：
1. 是否直接复制了原文的句子或段落
2. 是否照搬了原文的独特表达或观点
3. 结构和逻辑是否过度相似

输出JSON：
{{
  "plagiarism_risk": "low/medium/high",
  "reasoning": "判断理由",
  "suggestion": "修改建议（如果risk为medium或high）"
}}"""


def semantic_check(candidate, original):
    prompt = SEMANTIC_CHECK_PROMPT.format(candidate=candidate, original=original)
    return chat_json(prompt)


def full_similarity_check(candidates, original_contents):
    text_results = check_similarity_batch(candidates, original_contents)
    final_results = []
    for i, result in enumerate(text_results):
        if result["max_similarity"] >= 0.4:
            semantic = semantic_check(result["candidate"], result["most_similar_original"])
            result["semantic_check"] = semantic
        else:
            result["semantic_check"] = {"plagiarism_risk": "low", "reasoning": "文本相似度低，无抄袭风险", "suggestion": ""}
        final_results.append(result)
    return final_results


def format_similarity_report(results):
    report = "# 相似度检查报告\n\n"
    for i, r in enumerate(results, 1):
        risk_emoji = {"low": "✅", "medium": "⚠️", "high": "❌"}.get(r["risk_level"], "")
        report += f"## 候选{i} {risk_emoji} 风险等级：{r['risk_level']}\n\n"
        report += f"**文本相似度**：{r['max_similarity']}（阈值0.7）\n"
        report += f"**最相似原文**：{r['most_similar_original']}...\n"
        semantic = r.get("semantic_check", {})
        report += f"**语义查重**：{semantic.get('plagiarism_risk', '')}\n"
        report += f"**判断理由**：{semantic.get('reasoning', '')}\n"
        if semantic.get("suggestion"):
            report += f"**修改建议**：{semantic.get('suggestion', '')}\n"
        report += "\n---\n\n"
    return report
