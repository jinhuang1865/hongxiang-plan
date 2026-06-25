"""
鸿享计划 - 2026年教育BG课程资源
Streamlit 版本，带浏览量统计（服务端 JSON 文件存储）
同时作为 GitHub Pages 前端的浏览量 API 后端
"""
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from collections import Counter

# ── 浏览量存储（服务端 JSON） ──────────────────────────
VIEWS_FILE = "streamlit_views.json"

def load_views():
    if os.path.exists(VIEWS_FILE):
        with open(VIEWS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_views(views):
    with open(VIEWS_FILE, "w") as f:
        json.dump(views, f)

def increment_view(course_id):
    views = load_views()
    views[course_id] = views.get(course_id, 0) + 1
    save_views(views)

# ── API 模式：供 GitHub Pages 前端调用 ──────────────────
params = st.query_params
api_action = params.get("api", "")

if api_action == "views":
    st.text(json.dumps(load_views(), ensure_ascii=False))
    st.stop()

if api_action == "add":
    cid = params.get("id", "")
    if cid:
        increment_view(cid)
        st.text(json.dumps({"success": True, "id": cid, "count": load_views().get(cid, 0)}, ensure_ascii=False))
    else:
        st.text(json.dumps({"error": "Missing id"}))
    st.stop()

# ── 页面配置 ──────────────────────────────────────────
st.set_page_config(
    page_title="鸿享计划 · 教育BG课程资源",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 自定义样式 ──────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stMetric { background: #f8fafb; border: 1px solid #e5e8eb; border-radius: 8px; padding: 12px 16px; }
    .stMetric label { font-size: 13px; color: #6b7280; }
    .stMetric [data-testid="stMetricValue"] { font-size: 28px; color: #1a6b63; font-weight: 800; }
    .view-badge { display: inline-flex; align-items: center; gap: 4px; padding: 2px 10px;
                  background: #e8f5f3; border-radius: 12px; font-size: 13px; font-weight: 600; color: #1a6b63; }
    .featured-tag { display: inline-block; padding: 2px 8px; background: #fef3c7; color: #92400e;
                    border-radius: 4px; font-size: 12px; font-weight: 700; margin-left: 6px; }
    div[data-testid="stCaptionContainer"] { margin-top: 6px; }
    hr { margin: 0.5rem 0; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── 数据加载 ────────────────────────────────────────────
@st.cache_data
def load_courses():
    df = pd.read_csv("courses.csv", encoding="utf-8-sig")
    df["授课日期"] = pd.to_datetime(df["授课日期"], errors="coerce")
    df["课程属性"] = df["课程属性"].fillna("")
    df["course_id"] = [f"course-{i}" for i in range(len(df))]
    return df

courses = load_courses()

# ── 数据预处理 ──────────────────────────────────────────
courses["年份月份"] = courses["授课日期"].dt.strftime("%Y-%m")
courses["年份"] = courses["授课日期"].dt.year

# 精品课程标记
courses["is_featured"] = courses["课程属性"].str.contains("精品课程", na=False)

# ── 核心指标 ────────────────────────────────────────────
total = len(courses)
dept_count = courses["二级部门"].nunique()
type_count = courses["课程类型"].nunique()
latest_month = courses["授课日期"].max()
featured_count = courses["is_featured"].sum()

# ── 标题 ────────────────────────────────────────────────
st.markdown("### 📚 鸿享计划 · 2026年教育BG课程资源")
st.caption("把各部门课程材料，沉淀成可检索、可追踪、可复用的资源地图。")

# 指标卡片
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("有效课程", total)
col2.metric("覆盖部门", dept_count)
col3.metric("课程类型", type_count)
col4.metric("精品课程", featured_count)
col5.metric("最新月份", f"{latest_month:%Y-%m}" if pd.notna(latest_month) else "--")

st.divider()

# ── 筛选区 ──────────────────────────────────────────────
col_kw, col_type, col_dept, col_month, col_feat, col_sort = st.columns([2, 1.2, 1.2, 1.2, 1, 1])

keyword = col_kw.text_input("🔍 关键词搜索", placeholder="课程名称或介绍...")

all_types = ["全部"] + sorted(courses["课程类型"].dropna().unique().tolist())
selected_type = col_type.selectbox("课程类型", all_types)

all_depts = ["全部"] + sorted(courses["二级部门"].dropna().unique().tolist())
selected_dept = col_dept.selectbox("二级部门", all_depts)

all_months = ["全部"] + sorted(courses["年份月份"].dropna().unique().tolist(), reverse=True)
selected_month = col_month.selectbox("月份", all_months)

featured_only = col_feat.checkbox("只看精品", value=False)

sort_options = {"最新优先": "date-desc", "最早优先": "date-asc", "名称 A-Z": "name-asc"}
sort_label = col_sort.selectbox("排序", list(sort_options.keys()))
sort_key = sort_options[sort_label]

# ── 筛选逻辑 ────────────────────────────────────────────
filtered = courses.copy()

if keyword:
    mask = filtered["课程名称"].str.contains(keyword, case=False, na=False) | \
           filtered["课程介绍"].str.contains(keyword, case=False, na=False)
    filtered = filtered[mask]

if selected_type != "全部":
    filtered = filtered[filtered["课程类型"] == selected_type]

if selected_dept != "全部":
    filtered = filtered[filtered["二级部门"] == selected_dept]

if selected_month != "全部":
    filtered = filtered[filtered["年份月份"] == selected_month]

if featured_only:
    filtered = filtered[filtered["is_featured"]]

if sort_key == "date-desc":
    filtered = filtered.sort_values("授课日期", ascending=False)
elif sort_key == "date-asc":
    filtered = filtered.sort_values("授课日期", ascending=True)
elif sort_key == "name-asc":
    filtered = filtered.sort_values("课程名称", ascending=True)

# ── 分页 ────────────────────────────────────────────────
PAGE_SIZE = 20
total_filtered = len(filtered)
total_pages = max(1, (total_filtered + PAGE_SIZE - 1) // PAGE_SIZE)

if "page" not in st.session_state:
    st.session_state.page = 1

# 筛选变化时重置页码
st.session_state.page = min(st.session_state.page, total_pages)

start_idx = (st.session_state.page - 1) * PAGE_SIZE
page_items = filtered.iloc[start_idx:start_idx + PAGE_SIZE]

# ── 已选课程（用于生成推荐） ────────────────────────────
if "selected_courses" not in st.session_state:
    st.session_state.selected_courses = set()

# ── 结果展示 ────────────────────────────────────────────
st.caption(f"共 {total_filtered} 门课程")

if total_filtered == 0:
    st.info("没有找到匹配课程，请调整筛选条件。")
    if st.button("🔄 清空所有筛选"):
        st.session_state.page = 1
        st.rerun()
else:
    # 课程表格
    cols = st.columns([0.5, 3.5, 1, 1, 1, 0.8, 1.2])
    headers = ["选择", "课程信息", "类型", "部门", "日期", "浏览", "操作"]
    for i, h in enumerate(headers):
        cols[i].markdown(f"**{h}**")

    st.divider()

    for _, row in page_items.iterrows():
        cid = row["course_id"]
        c1, c2, c3, c4, c5, c6, c7 = st.columns([0.5, 3.5, 1, 1, 1, 0.8, 1.2])

        # 选择框
        checked = cid in st.session_state.selected_courses
        if c1.checkbox("", value=checked, key=f"sel_{cid}", label_visibility="collapsed"):
            st.session_state.selected_courses.add(cid)
        else:
            st.session_state.selected_courses.discard(cid)

        # 课程信息
        title = row["课程名称"]
        desc = str(row["课程介绍"])[:120] + ("..." if len(str(row["课程介绍"])) > 120 else "")
        featured = row["is_featured"]
        c2.markdown(f"[{title}]({row['课程链接']}){' <span class=\"featured-tag\">精品</span>' if featured else ''}<br><small style=\"color:#6b7280\">{desc}</small>", unsafe_allow_html=True)

        # 类型
        c3.markdown(f"<small>{row['课程类型'] or '未标注'}</small>", unsafe_allow_html=True)

        # 部门
        c4.markdown(f"<small>{row['二级部门'] or '未标注'}</small>", unsafe_allow_html=True)

        # 日期
        d = row["授课日期"]
        date_str = d.strftime("%Y-%m-%d") if pd.notna(d) else "--"
        c5.markdown(f"<small>{date_str}</small>", unsafe_allow_html=True)

        # 浏览量
        vc = get_view_count(cid)
        c6.markdown(f"<span class='view-badge'>👁 {vc}</span>", unsafe_allow_html=True)

        # 操作
        # 点击"查看"时触发浏览计数
        if c7.button("查看", key=f"view_{cid}"):
            increment_view(cid)
        c7.markdown(f"<a href='{row['课程链接']}' target='_blank' style='font-size:13px;color:#1a6b63;text-decoration:none;'>🔗 打开</a>", unsafe_allow_html=True)

    st.divider()

    # 分页控件
    if total_pages > 1:
        pc1, pc2, pc3 = st.columns([1, 2, 1])
        if pc1.button("◀ 上一页", disabled=st.session_state.page <= 1):
            st.session_state.page -= 1
            st.rerun()
        pc2.markdown(f"<div style='text-align:center;color:#6b7280;padding-top:6px'>第 {st.session_state.page} / {total_pages} 页</div>", unsafe_allow_html=True)
        if pc3.button("下一页 ▶", disabled=st.session_state.page >= total_pages):
            st.session_state.page += 1
            st.rerun()

# ── 已选课程推荐生成 ────────────────────────────────────
st.divider()
st.markdown("### 📋 学习推荐生成器")

selected_list = courses[courses["course_id"].isin(st.session_state.selected_courses)]

if len(selected_list) == 0:
    st.caption("勾选课程后，可一键生成适合转发的学习推荐。")
else:
    st.caption(f"已选 {len(selected_list)} 门课程")

    # 生成转发文案
    lines = ["推荐学习以下课程：", ""]
    for i, (_, row) in enumerate(selected_list.iterrows()):
        lines.append(f"{i+1}. 《{row['课程名称']}》")
        lines.append(f"   推荐理由：{row['课程介绍']}")
        lines.append(f"   链接：{row['课程链接']}")
    lines.append("")
    lines.append("欢迎按需学习，也欢迎继续贡献优秀课程与经验材料。")
    share_text = "\n".join(lines)

    st.text_area("转发文案（可直接复制）", share_text, height=200)

    c1, c2 = st.columns(2)
    if c1.button("📋 复制文案"):
        st.toast("已复制到剪贴板")
    if c2.button("🗑 清空已选"):
        st.session_state.selected_courses.clear()
        st.rerun()

# ── 数据可视化 ──────────────────────────────────────────
st.divider()
st.markdown("### 📊 课程分布")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**按课程类型**")
    type_counts = courses["课程类型"].value_counts()
    st.bar_chart(type_counts, horizontal=True)

with chart_col2:
    st.markdown("**按二级部门（Top 10）**")
    dept_counts = courses["二级部门"].value_counts().head(10)
    st.bar_chart(dept_counts, horizontal=True)

# ── 贡献榜 ──────────────────────────────────────────────
st.divider()
st.markdown("### 🏆 感谢致敬")
st.caption("按当前课程库中各二级部门贡献课程数量统计。")

# 月度贡献榜
latest_month_str = courses["年份月份"].max()
if pd.notna(latest_month_str):
    monthly = courses[courses["年份月份"] == latest_month_str]
    monthly_dept = monthly["二级部门"].value_counts().head(5)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"**月度贡献榜** （{latest_month_str}）")
        if len(monthly_dept) == 0:
            st.caption("暂无数据")
        else:
            for rank, (dept, count) in enumerate(monthly_dept.items(), 1):
                emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][rank - 1]
                st.markdown(f"{emoji} **{dept}** — {count} 门")

    # 年度贡献榜
    yearly_dept = courses["二级部门"].value_counts().head(5)
    with col_b:
        st.markdown("**年度贡献榜**")
        for rank, (dept, count) in enumerate(yearly_dept.items(), 1):
            emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][rank - 1]
            st.markdown(f"{emoji} **{dept}** — {count} 门")

# ── 本月新增 ────────────────────────────────────────────
st.divider()
st.markdown("### 🆕 本月新增课程")
latest = courses[courses["年份月份"] == latest_month_str]
st.caption(f"共 {len(latest)} 门")
for _, row in latest.iterrows():
    d = row["授课日期"]
    date_str = d.strftime("%m-%d") if pd.notna(d) else ""
    ft = " 🏷️精品" if row["is_featured"] else ""
    st.markdown(f"- [{row['课程名称']}]({row['课程链接']}) — {row['课程类型']} · {row['二级部门']} · {date_str}{ft}")

# ── 页脚 ────────────────────────────────────────────────
st.divider()
st.caption("Made with ❤️ by 鸿享计划 · 教育BG")
