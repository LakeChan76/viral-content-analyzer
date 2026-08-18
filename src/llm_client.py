from openai import OpenAI
from src.config import SENSENOVA_API_KEY, SENSENOVA_BASE_URL, LLM_MODEL
import json
import time

client = OpenAI(
    api_key=SENSENOVA_API_KEY,
    base_url=SENSENOVA_BASE_URL,
)


def _call_with_retry(messages, temperature=0.7, json_mode=False, max_retries=5):
    kwargs = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                wait = min(30, 5 * (attempt + 2))
                time.sleep(wait)
                continue
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            raise
    raise Exception("API调用失败，已重试{}次".format(max_retries))


def chat(prompt, system_prompt="你是资深内容运营专家，擅长分析社交媒体爆款内容。", temperature=0.7):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    return _call_with_retry(messages, temperature=temperature)


def chat_json(prompt, system_prompt="你是资深内容运营专家，擅长分析社交媒体爆款内容。请严格按JSON格式输出。", temperature=0.3):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    content = _call_with_retry(messages, temperature=temperature, json_mode=True)
    return json.loads(content)
