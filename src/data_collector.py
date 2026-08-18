import requests
import time
import csv
import io
import json
import os
from src.config import APIFY_API_TOKEN, APIFY_ACTOR_ID

SAMPLE_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "andrew_ng_sample.json",
)


def load_sample_data():
    if not os.path.exists(SAMPLE_DATA_PATH):
        return [], "示例数据文件不存在"
    with open(SAMPLE_DATA_PATH, "r", encoding="utf-8") as f:
        results = json.load(f)
    tweets = []
    followers = None
    for item in results:
        if item.get("type") == "profile":
            followers = int(item.get("followersCount", 0) or 0)
            continue
        if item.get("type") != "tweet":
            continue
        tweet = {
            "content": item.get("text", ""),
            "published_at": item.get("createdAt", ""),
            "reposts": int(item.get("retweetCount", 0) or 0),
            "likes": int(item.get("favoriteCount", 0) or 0),
            "replies": int(item.get("replyCount", 0) or 0),
            "quotes": int(item.get("quoteCount", 0) or 0),
        }
        if tweet["content"]:
            tweets.append(tweet)
    if not tweets:
        return [], "示例数据中没有推文"
    return tweets, followers


def collect_tweets(username, limit=30):
    if not APIFY_API_TOKEN:
        return [], "未配置APIFY_API_TOKEN，请使用CSV上传模式"

    try:
        results = _start_apify_run(username)
        if not results:
            return [], "启动Apify采集任务失败（返回为空）"
        if isinstance(results, dict) and results.get("_error"):
            return [], f"Apify API错误: {results['_error']}"

        tweets = []
        followers = None
        for item in results:
            if item.get("type") == "profile":
                followers = int(item.get("followersCount", 0) or 0)
                continue
            if item.get("type") != "tweet":
                continue
            tweet = {
                "content": item.get("text", ""),
                "published_at": item.get("createdAt", ""),
                "reposts": int(item.get("retweetCount", 0) or 0),
                "likes": int(item.get("favoriteCount", 0) or 0),
                "replies": int(item.get("replyCount", 0) or 0),
                "quotes": int(item.get("quoteCount", 0) or 0),
            }
            if tweet["content"]:
                tweets.append(tweet)

        if not tweets:
            return [], "未采集到推文数据（该账号可能没有公开推文）"

        return tweets, followers

    except requests.exceptions.Timeout:
        return [], "采集超时（Apify响应时间过长），请稍后重试或使用CSV上传"
    except Exception as e:
        return [], f"采集异常: {str(e)}"


def _start_apify_run(username):
    url = f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/run-sync-get-dataset-items"
    headers = {"Authorization": f"Bearer {APIFY_API_TOKEN}"}
    payload = {
        "handles": [username],
        "includeProfile": True,
        "includeTweets": True,
        "maxTweets": 50,
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=180)
        if resp.status_code in (200, 201):
            return resp.json()
        return {"_error": f"HTTP {resp.status_code}: {resp.text[:500]}"}
    except requests.exceptions.Timeout:
        return {"_error": "请求超时（180秒）"}
    except Exception as e:
        return {"_error": f"请求异常: {str(e)}"}


COLUMN_MAP = {
    "content": ["content", "text", "tweet", "tweet_text", "full_text", "rawContent", "raw_content", "tweet_content", "body"],
    "published_at": ["published_at", "date", "created_at", "timestamp", "time", "createdAt", "published"],
    "reposts": ["reposts", "retweets", "retweet_count", "repost_count", "retweetCount", "rt"],
    "likes": ["likes", "like_count", "favorite_count", "fav_count", "likeCount", "favorites"],
    "replies": ["replies", "reply_count", "replyCount", "comments"],
    "quotes": ["quotes", "quote_count", "quoteCount", "quote_tweets", "quoted"],
    "followers": ["followers", "followers_count", "follower_count", "followersCount"],
}


def _normalize_header(col):
    col = col.strip().strip('"').strip()
    for target, aliases in COLUMN_MAP.items():
        if col.lower() in [a.lower() for a in aliases]:
            return target
    return col


def load_csv(uploaded_file):
    try:
        content = uploaded_file.read().decode("utf-8-sig")
    except Exception:
        content = uploaded_file.read().decode("utf-8", errors="replace")

    lines = content.strip().split("\n")
    if len(lines) < 2:
        return None, "CSV文件内容太少"

    raw_header = lines[0].split(",")
    header = [_normalize_header(h) for h in raw_header]

    expected = ["content", "published_at", "reposts", "likes", "replies", "quotes"]
    missing = [c for c in expected if c not in header]
    if missing:
        return None, f"CSV缺少必要列: {missing}。检测到的列: {header}"

    followers = None
    if "followers" in header:
        idx = header.index("followers")
        for line in lines[1:]:
            row = next(csv.reader([line], skipinitialspace=True))
            if len(row) > idx:
                try:
                    val = int(str(row[idx]).strip().strip('"'))
                    if val > 0:
                        followers = val
                        break
                except Exception:
                    continue

    tweet_data = []
    for line in lines[1:]:
        if not line.strip():
            continue
        try:
            row = next(csv.reader([line], skipinitialspace=True))
        except Exception:
            continue
        if len(row) < len(header):
            continue

        record = {}
        for i, col in enumerate(header):
            val = row[i] if i < len(row) else ""
            val = val.strip().strip('"')
            if col in ("reposts", "likes", "replies", "quotes", "followers"):
                try:
                    val = int(val)
                except Exception:
                    val = 0
            record[col] = val

        if record.get("content"):
            tweet_data.append(record)

    if not tweet_data:
        return None, "CSV中没有有效的推文数据"
    return tweet_data, followers


def get_followers_count(username):
    return None
