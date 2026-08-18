import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_collector import collect_tweets, load_csv, load_sample_data
from src.performance_analyzer import calculate_engagement_rate, split_performance, get_performance_summary
from src.content_analyzer import analyze_high_performance, format_analysis_report
from src.driver_analysis import analyze_drivers, format_driver_report
from src.template_extractor import extract_templates, format_template_report
from src.content_generator import generate_candidates, format_candidates_report
from src.similarity_checker import full_similarity_check, format_similarity_report
from src.asset_library import add_record, get_all_records, update_candidate_status, update_candidate, update_candidate_performance, delete_record
from src.config import SENSENOVA_API_KEY, ENGAGEMENT_RATE_BENCHMARK

st.set_page_config(page_title="爆款内容拆解 Agent", page_icon="🔥", layout="wide")

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "confirmed" not in st.session_state:
    st.session_state.confirmed = False


def main():
    st.title("🔥 爆款内容拆解与二次创作 Agent")
    st.markdown("输入X账号 → 自动拆解爆款逻辑 → 生成原创候选内容")

    tab1, tab2, tab3 = st.tabs(["📊 内容分析", "📁 资产库", "ℹ️ 说明"])

    with tab1:
        analysis_tab()
    with tab2:
        library_tab()
    with tab3:
        info_tab()


def analysis_tab():
    st.header("第一步：输入X账号")

    data_mode = st.radio(
        "数据采集方式",
        ["自动采集（Apify）", "使用示例数据（Andrew Ng）", "CSV上传（兜底）"],
        horizontal=True,
        help="推荐使用示例数据快速体验完整流程",
    )

    username = None
    uploaded_file = None
    followers = None
    use_sample = False

    if data_mode == "自动采集（Apify）":
        username = st.text_input("X账号用户名（不含@）", placeholder="例如：AndrewYNg")
    elif data_mode == "使用示例数据（Andrew Ng）":
        use_sample = True
        st.info("已预载 Andrew Ng (@AndrewYNg) 的20条推文数据，粉丝数 1,800,674")
    elif data_mode == "CSV上传（兜底）":
        uploaded_file = st.file_uploader("上传CSV文件", type=["csv"])
        if uploaded_file:
            st.info("CSV需包含列：content, published_at, reposts, likes, replies, quotes")
            followers = st.number_input("该账号粉丝数", min_value=1, value=100000, step=10000, key="followers_input", help="在X账号主页可以看到粉丝数")

    if st.button("🚀 开始分析", type="primary"):
        if not SENSENOVA_API_KEY:
            st.error("未检测到API Key，请在.env文件中设置 SENSENOVA_API_KEY")
            return
        if data_mode == "自动采集（Apify）" and not username:
            st.warning("请输入X账号用户名")
            return
        if data_mode == "CSV上传（兜底）" and not uploaded_file:
            st.warning("请上传CSV文件")
            return

        run_analysis(username, uploaded_file, followers, use_sample)

    if st.session_state.analysis_result:
        show_results(st.session_state.analysis_result)


def run_analysis(username, uploaded_file, followers_input, use_sample=False):
    progress = st.progress(0)
    status = st.empty()

    # ① 数据采集
    status.write("⏳ 正在采集数据...")
    progress.progress(10)

    if use_sample:
        tweets, followers = load_sample_data()
        if not tweets:
            st.error(f"示例数据加载失败：{followers}")
            return
        username = "AndrewYNg"
    elif uploaded_file:
        tweets, csv_followers = load_csv(uploaded_file)
        if tweets is None:
            st.error(csv_followers)
            return
        followers = csv_followers or followers_input or 100000
    else:
        tweets, result_or_error = collect_tweets(username)
        if not tweets:
            st.error(f"自动采集失败：{result_or_error}")
            st.info("请改用「使用示例数据」或「CSV上传」模式")
            return
        followers = result_or_error if isinstance(result_or_error, int) else (followers_input or 100000)

    progress.progress(25)
    status.write(f"✅ 采集到 {len(tweets)} 条推文，粉丝数：{followers:,}")

    # ② 表现分级
    status.write("⏳ 正在进行表现分级...")
    df = calculate_engagement_rate(tweets, followers)
    high, low = split_performance(df)
    summary = get_performance_summary(df, followers)
    progress.progress(35)

    result = {
        "account": f"@{username}" if username else "上传数据",
        "followers": followers,
        "summary": summary,
        "high_analyses": [],
        "low_analyses": [],
        "driver_result": {},
        "template_result": {},
        "generate_result": {"candidates": []},
        "similarity_results": [],
    }

    # ③ 爆款拆解
    with st.spinner("🔍 正在拆解高表现内容（第1批，调用大模型）..."):
        try:
            high_analyses = analyze_high_performance(high.to_dict("records"))
            result["high_analyses"] = high_analyses
            status.write("✅ 高表现内容拆解完成")
        except Exception as e:
            st.error(f"高表现内容拆解失败：{str(e)}")
            st.info("可点击重新分析重试，或检查API Key是否正确")
            st.session_state.analysis_result = result
            st.session_state.confirmed = False
            return
    progress.progress(42)

    with st.spinner("🔍 正在拆解低表现内容（第2批，调用大模型）..."):
        try:
            low_analyses = analyze_high_performance(low.to_dict("records"))
            result["low_analyses"] = low_analyses
            status.write("✅ 低表现内容拆解完成")
        except Exception as e:
            st.warning(f"低表现内容拆解失败：{str(e)}，跳过此步骤")
            low_analyses = []
    progress.progress(50)

    # ④ 驱动因素分析
    with st.spinner("🎯 正在对比分析驱动因素（调用大模型）..."):
        try:
            driver_result = analyze_drivers(high_analyses, low_analyses)
            result["driver_result"] = driver_result
            status.write("✅ 驱动因素分析完成")
        except Exception as e:
            st.warning(f"驱动因素分析失败：{str(e)}，跳过此步骤")
    progress.progress(65)

    # ⑤ 模板沉淀
    with st.spinner("📝 正在提炼可复用内容模板（调用大模型）..."):
        try:
            template_result = extract_templates(driver_result, high_analyses)
            result["template_result"] = template_result
            status.write("✅ 内容模板提炼完成")
        except Exception as e:
            st.warning(f"模板提炼失败：{str(e)}，跳过此步骤")
    progress.progress(75)

    # ⑥ 候选内容生成
    with st.spinner("✨ 正在生成3条候选内容（调用大模型）..."):
        try:
            generate_result = generate_candidates(template_result, high_analyses)
            result["generate_result"] = generate_result
            status.write("✅ 候选内容生成完成")
        except Exception as e:
            st.warning(f"候选内容生成失败：{str(e)}，跳过此步骤")
    progress.progress(85)

    # ⑦ 相似度检查
    with st.spinner("🔍 正在进行相似度和抄袭风险检查..."):
        try:
            original_contents = [t["content"] for t in tweets]
            similarity_results = full_similarity_check(
                generate_result.get("candidates", []),
                original_contents,
            )
            result["similarity_results"] = similarity_results
        except Exception as e:
            st.warning(f"相似度检查失败：{str(e)}，跳过此步骤")
    progress.progress(95)

    st.session_state.analysis_result = result
    st.session_state.confirmed = False
    progress.progress(100)
    status.write("✅ 分析完成！请查看下方结果")
    st.rerun()


def show_results(result):
    st.divider()

    # 表现分级
    st.header("📊 表现分级")
    summary = result["summary"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总推文数", summary["total_tweets"])
    col2.metric("粉丝数", f"{summary['followers']:,}")
    col3.metric("平均互动率", f"{summary['avg_engagement_rate']}%")
    col4.metric("基准线", f"{summary['benchmark']}%")

    st.subheader("高表现 TOP5")
    st.dataframe(pd.DataFrame(summary["high_performance"]))

    st.subheader("低表现 BOTTOM5")
    st.dataframe(pd.DataFrame(summary["low_performance"]))

    # 爆款拆解
    st.header("🔍 爆款拆解报告")
    st.markdown(format_analysis_report(result["high_analyses"]))

    # 驱动因素
    st.header("🎯 驱动因素分析")
    st.markdown(format_driver_report(result["driver_result"]))

    # 内容模板
    st.header("📝 可复用内容模板")
    st.markdown(format_template_report(result["template_result"]))

    # 候选内容 + 相似度检查
    st.header("✨ 候选内容（待人工审核）")
    st.warning("⚠️ 以下内容需人工确认后才会写入资产库，不会自动发布。勾选要保留的候选内容，可编辑后写入。")

    candidates = result["generate_result"].get("candidates", [])
    sim_results = result["similarity_results"]

    selected_candidates = []
    for i, (cand, sim) in enumerate(zip(candidates, sim_results)):
        risk = sim.get("risk_level", "low")
        risk_color = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk, "🟢")
        risk_display = {"low": "低风险", "medium": "中风险", "high": "高风险"}.get(risk, "")

        with st.container(border=True):
            col_check, col_risk = st.columns([5, 2])
            selected = col_check.checkbox(f"保留候选 {i+1}", value=True, key=f"select_{i}")
            col_risk.markdown(f"{risk_color} **{risk_display}** | 相似度 {sim.get('max_similarity', 0)}")

            if sim.get("semantic_check", {}).get("suggestion"):
                st.info(f"💡 修改建议：{sim['semantic_check']['suggestion']}")

            edited = st.text_area(
                f"内容（可编辑）",
                value=cand.get("content", ""),
                height=120,
                key=f"candidate_{i}",
                label_visibility="collapsed",
            )

            if selected:
                selected_candidates.append({
                    **cand,
                    "content": edited,
                })

    # 人工确认
    st.header("✅ 人工确认")
    if not selected_candidates:
        st.warning("请至少勾选一条候选内容")
    else:
        st.write(f"已选择 **{len(selected_candidates)}** 条候选内容，将写入资产库（状态：待审核）")
        confirm = st.checkbox("我已审核以上内容，确认写入资产库")

        if confirm and not st.session_state.confirmed:
            if st.button("确认写入资产库", type="primary"):
                record_id = add_record(
                    account=result["account"],
                    driver_result=result["driver_result"],
                    templates=result["template_result"],
                    candidates=selected_candidates,
                    similarity_results=result["similarity_results"],
                    high_analyses=result["high_analyses"],
                )
                st.session_state.confirmed = True
                st.success(f"✅ 已写入资产库！记录ID：{record_id}，共 {len(selected_candidates)} 条候选内容")
                st.info("可在「资产库」标签页查看和管理")


def library_tab():
    st.header("📁 内容资产库")

    records = get_all_records()
    if not records:
        st.info("暂无记录。完成分析并确认后，内容将保存到这里。")
        return

    cand_status_map = {
        "pending_review": "⏳ 待审核",
        "published": "📤 已发布",
        "validated": "✅ 已验证",
        "archived": "📦 已归档",
    }

    st.write(f"共 **{len(records)}** 条记录")

    for record in reversed(records):
        cands = record.get("candidates", [])
        statuses = [c.get("status", "pending_review") for c in cands]
        status_summary = ", ".join(f"{cand_status_map.get(s, s)}" for s in statuses)

        with st.expander(f"{record['account']} | {record['created_at'][:10]} | {status_summary}", expanded=False):
            st.write(f"**记录ID**：`{record['id']}`")

            st.subheader("候选内容")
            for i, cand in enumerate(record.get("candidates", [])):
                with st.container(border=True):
                    cand_status = cand.get("status", "pending_review")
                    status_label = cand_status_map.get(cand_status, cand_status)

                    col_num, col_status = st.columns([4, 2])
                    col_num.write(f"**候选 {i+1}**")
                    col_status.markdown(f"**{status_label}**")

                    st.write(cand.get("content", ""))

                    perf = cand.get("performance")
                    if perf:
                        st.caption(f"📊 实际表现：点赞 {perf.get('likes', '—')} | 转发 {perf.get('reposts', '—')} | 回复 {perf.get('replies', '—')}")

                    with st.popover("📝 记录后续表现"):
                        st.write(f"为候选 {i+1} 记录发布后的实际表现数据")
                        p_likes = st.number_input("点赞数", min_value=0, value=0, key=f"likes_{record['id']}_{i}")
                        p_reposts = st.number_input("转发数", min_value=0, value=0, key=f"reposts_{record['id']}_{i}")
                        p_replies = st.number_input("回复数", min_value=0, value=0, key=f"replies_{record['id']}_{i}")
                        if st.button("保存表现数据", key=f"save_perf_{record['id']}_{i}", type="primary"):
                            update_candidate_performance(record["id"], i, {
                                "likes": p_likes,
                                "reposts": p_reposts,
                                "replies": p_replies,
                            })
                            st.toast("表现数据已保存", icon="📝")
                            st.rerun()

                    st.caption("---")
                    st.write("**此条状态管理**")

                    if cand_status == "pending_review":
                        if st.button("📤 标记为已发布", key=f"pub_{record['id']}_{i}", type="primary"):
                            update_candidate_status(record["id"], i, "published")
                            st.toast(f"候选 {i+1} 已标记为已发布", icon="📤")
                            st.rerun()
                    elif cand_status == "published":
                        if st.button("✅ 标记为已验证（录入表现数据后）", key=f"val_{record['id']}_{i}", type="primary"):
                            update_candidate_status(record["id"], i, "validated")
                            st.toast(f"候选 {i+1} 已标记为已验证", icon="✅")
                            st.rerun()

                    col1, col2 = st.columns(2)
                    if col1.button("🔄 重置待审核", key=f"reset_{record['id']}_{i}"):
                        update_candidate_status(record["id"], i, "pending_review")
                        st.toast(f"候选 {i+1} 已重置为待审核", icon="🔄")
                        st.rerun()
                    if col2.button("📦 归档", key=f"arc_{record['id']}_{i}"):
                        update_candidate_status(record["id"], i, "archived")
                        st.toast(f"候选 {i+1} 已归档", icon="📦")
                        st.rerun()

            st.subheader("驱动因素")
            drivers = record.get("driver_result", {}).get("key_drivers", [])
            if drivers:
                for d in drivers:
                    impact = d.get("impact", "")
                    factor = d.get("factor", "")
                    st.markdown(f"- **{factor}** — {impact}")
            else:
                st.caption("无")

            st.subheader("可复用模板")
            templates = record.get("templates", {})
            if templates:
                st.markdown(format_template_report(templates))
            else:
                st.caption("无")


def info_tab():
    st.header("ℹ️ 产品说明")

    st.subheader("产品逻辑")
    st.write('帮内容运营拆解"爆款为什么爆"，找出可复用规律，基于规律自动生成新的候选内容。')

    st.subheader("工作流")
    st.markdown("""
    1. **数据采集**：Apify自动抓取X账号推文+互动数据（无需登录，基于公开数据源）
    2. **表现分级**：按粉丝数算互动率，分TOP5/BOTTOM5
    3. **爆款拆解**：大模型从6维度拆解高表现内容
    4. **驱动因素分析**：对比高低表现组，找出驱动因素
    5. **模板沉淀**：提炼可复用内容结构模板
    6. **候选内容生成**：生成3条差异化原创内容
    7. **相似度检查**：检查抄袭风险
    8. **人工确认**：审核后写入资产库
    """)

    st.subheader("LLM选型")
    st.write("DeepSeek V4 Flash（通过商汤日日新API调用），兼容OpenAI格式，256K上下文")

    st.subheader("人工确认点")
    st.warning("候选内容必须经过人工审核确认后才会写入资产库，系统不会自动发布任何内容")

    st.subheader("当前局限")
    st.markdown("""
    - 数据采集依赖Apify第三方服务，大规模使用需付费
    - 互动率按粉丝数计算，未考虑曝光量
    - 驱动因素基于有限样本（TOP5 vs BOTTOM5）
    - 反馈闭环需手动录入发布后表现数据
    """)

    st.subheader("优化方向")
    st.markdown("""
    - 接入X官方API，提升数据采集稳定性
    - 扩大样本量到TOP20/BOTTOM20
    - 支持多账号横向对比
    - 自动追踪发布后表现，验证拆解结论
    - 多模态分析（图片、视频内容）
    """)


if __name__ == "__main__":
    main()
