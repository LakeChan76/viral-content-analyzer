import pandas as pd
from config import TOP_N, ENGAGEMENT_RATE_BENCHMARK


def calculate_engagement_rate(tweets, followers):
    df = pd.DataFrame(tweets)
    df["engagement"] = df["reposts"] + df["likes"] + df["replies"] + df["quotes"]
    df["engagement_rate"] = (df["engagement"] / followers * 100).round(2)
    df["above_benchmark"] = df["engagement_rate"] >= ENGAGEMENT_RATE_BENCHMARK
    return df


def split_performance(df, top_n=TOP_N):
    df_sorted = df.sort_values("engagement_rate", ascending=False).reset_index(drop=True)
    if len(df_sorted) < top_n * 2:
        mid = len(df_sorted) // 2
        high = df_sorted.head(mid)
        low = df_sorted.tail(mid) if mid > 0 else df_sorted.head(0)
    else:
        high = df_sorted.head(top_n)
        low = df_sorted.tail(top_n)
    return high, low


def get_performance_summary(df, followers):
    high, low = split_performance(df)
    return {
        "total_tweets": len(df),
        "followers": followers,
        "avg_engagement_rate": round(df["engagement_rate"].mean(), 2),
        "high_performance": high[["content", "engagement_rate", "reposts", "likes", "replies", "quotes"]].to_dict("records"),
        "low_performance": low[["content", "engagement_rate", "reposts", "likes", "replies", "quotes"]].to_dict("records"),
        "benchmark": ENGAGEMENT_RATE_BENCHMARK,
    }
