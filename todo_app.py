
import streamlit as st
import pandas as pd
import json
from datetime import date, datetime

st.set_page_config(page_title="🗒️ To‑Do List", layout="wide")

# ---------- State ----------
if "tasks" not in st.session_state:
    st.session_state.tasks = []  # list of dicts

def to_df(tasks):
    if not tasks:
        return pd.DataFrame(columns=["title", "notes", "due", "priority", "status", "tag", "created_at", "selected"])
    df = pd.DataFrame(tasks).copy()
    # Ensure columns exist
    for col in ["notes", "due", "priority", "status", "tag", "created_at", "selected"]:
        if col not in df.columns:
            df[col] = "" if col != "selected" else False
    return df

def from_df(df: pd.DataFrame):
    records = df.to_dict(orient="records")
    # Normalize types
    cleaned = []
    for r in records:
        r["title"] = str(r.get("title", "")).strip()
        r["notes"] = str(r.get("notes", "")).strip()
        # Convert due to isoformat string if it's a date
        due_val = r.get("due", "")
        if isinstance(due_val, (pd.Timestamp,)):
            r["due"] = due_val.date().isoformat()
        elif isinstance(due_val, date):
            r["due"] = due_val.isoformat()
        else:
            r["due"] = str(due_val) if due_val not in [None, "NaT", "nan"] else ""
        r["priority"] = r.get("priority", "Medium") or "Medium"
        r["status"] = r.get("status", "Todo") or "Todo"
        r["tag"] = str(r.get("tag", "")).strip()
        r["selected"] = bool(r.get("selected", False))
        r["created_at"] = r.get("created_at") or datetime.now().isoformat(timespec="seconds")
        cleaned.append(r)
    return cleaned

# ---------- Sidebar: Add Task ----------
with st.sidebar:
    st.title("🗒️ To‑Do List")
    st.caption("Streamlit single‑file app")
    st.markdown("---")
    st.subheader("➕ 새 할 일 추가")
    with st.form("add_task_form", clear_on_submit=True):
        title = st.text_input("제목*", placeholder="예: 수학 숙제 3-1 풀기")
        notes = st.text_area("메모", placeholder="세부 내용, 링크 등")
        due = st.date_input("마감일", value=None)
        col1, col2 = st.columns(2)
        with col1:
            priority = st.selectbox("우선순위", ["Low", "Medium", "High"], index=1)
        with col2:
            status = st.selectbox("상태", ["Todo", "Doing", "Done"], index=0)
        tag = st.text_input("태그", placeholder="예: 학교, 프로젝트")
        submitted = st.form_submit_button("추가", use_container_width=True)
        if submitted:
            if not title.strip():
                st.warning("제목은 필수입니다.")
            else:
                st.session_state.tasks.append({
                    "title": title.strip(),
                    "notes": notes.strip(),
                    "due": due.isoformat() if due else "",
                    "priority": priority,
                    "status": status,
                    "tag": tag.strip(),
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                    "selected": False,
                })
                st.success("추가되었습니다!")

    st.markdown("---")
    st.subheader("💾 백업 / 복구")
    # Download JSON
    if st.session_state.tasks:
        json_str = json.dumps(st.session_state.tasks, ensure_ascii=False, indent=2)
        st.download_button(
            "작업 내보내기(JSON)",
            data=json_str.encode("utf-8"),
            file_name="todo_tasks.json",
            mime="application/json",
            use_container_width=True
        )
    # Upload JSON
    uploaded = st.file_uploader("작업 불러오기(JSON)", type=["json"])
    if uploaded is not None:
        try:
            loaded = json.load(uploaded)
            if isinstance(loaded, list):
                st.session_state.tasks = loaded
                st.success("불러오기 완료!")
            else:
                st.error("올바른 형식이 아닙니다. 리스트 형태의 JSON이어야 합니다.")
        except Exception as e:
            st.error(f"불러오기 실패: {e}")

    st.markdown("---")
    st.caption("Tip: 표 안에서 바로 수정 가능해요. ✅로 선택 후 일괄 작업!")

# ---------- Main: Filters & Table ----------
st.header("📋 내 할 일")

# Filters
df_all = to_df(st.session_state.tasks)
colf1, colf2, colf3, colf4 = st.columns([2, 1, 1, 1])
with colf1:
    q = st.text_input("검색(제목/메모/태그)", placeholder="키워드 입력")
with colf2:
    f_status = st.multiselect("상태 필터", ["Todo", "Doing", "Done"], default=[])
with colf3:
    f_priority = st.multiselect("우선순위 필터", ["Low", "Medium", "High"], default=[])
with colf4:
    sort_by = st.selectbox("정렬", ["마감일↑", "마감일↓", "우선순위(High→Low)", "생성일 최신", "제목 A→Z"])

# Apply filters
df = df_all.copy()
if q:
    q_lower = q.lower()
    df = df[df.apply(lambda r: any(str(r[c]).lower().find(q_lower) >= 0 for c in ["title", "notes", "tag"]), axis=1)]
if f_status:
    df = df[df["status"].isin(f_status)]
if f_priority:
    df = df[df["priority"].isin(f_priority)]

# Sorting
def prio_rank(p):
    return {"High": 0, "Medium": 1, "Low": 2}.get(p, 3)

if not df.empty:
    if "마감일" in sort_by:
        # Convert 'due' to datetime for sorting
        sdf = df.copy()
        sdf["due_dt"] = pd.to_datetime(sdf["due"], errors="coerce")
        ascending = sort_by.endswith("↑")
        df = sdf.sort_values(by=["due_dt"], ascending=ascending).drop(columns=["due_dt"])
    elif sort_by == "우선순위(High→Low)":
        df = df.sort_values(by="priority", key=lambda s: s.map(prio_rank))
    elif sort_by == "생성일 최신":
        df = df.sort_values(by="created_at", ascending=False)
    elif sort_by == "제목 A→Z":
        df = df.sort_values(by="title", kind="stable")

# Display editable table
st.markdown("### ✍️ 편집 가능한 목록")
help_text = "행을 직접 수정할 수 있어요. 선택(✅) 후 아래 버튼으로 일괄 처리할 수 있습니다."
edited_df = st.data_editor(
    df,
    hide_index=True,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "title": st.column_config.TextColumn("제목", required=True),
        "notes": st.column_config.TextColumn("메모"),
        "due": st.column_config.DateColumn("마감일", format="YYYY-MM-DD"),
        "priority": st.column_config.SelectboxColumn("우선순위", options=["Low", "Medium", "High"], help=help_text),
        "status": st.column_config.SelectboxColumn("상태", options=["Todo", "Doing", "Done"]),
        "tag": st.column_config.TextColumn("태그"),
        "created_at": st.column_config.TextColumn("생성일", disabled=True),
        "selected": st.column_config.CheckboxColumn("✅", help="일괄 작업에 사용"),
    },
    help=help_text,
    key="editor",
)

# Persist edits back to state (on every run)
st.session_state.tasks = from_df(edited_df)

# ---------- Bulk actions ----------
col_a1, col_a2, col_a3 = st.columns([1, 1, 6])
with col_a1:
    if st.button("선택 완료로", use_container_width=True):
        for r in st.session_state.tasks:
            if r.get("selected"):
                r["status"] = "Done"
                r["selected"] = False
        st.success("선택한 작업을 완료 처리했습니다.")
with col_a2:
    if st.button("선택 삭제", use_container_width=True):
        before = len(st.session_state.tasks)
        st.session_state.tasks = [r for r in st.session_state.tasks if not r.get("selected")]
        after = len(st.session_state.tasks)
        st.success(f"{before - after}개 작업을 삭제했습니다.")

# ---------- Stats ----------
st.markdown("---")
st.subheader("📈 진행 상황")
total = len(st.session_state.tasks)
done = sum(1 for r in st.session_state.tasks if r.get("status") == "Done")
doing = sum(1 for r in st.session_state.tasks if r.get("status") == "Doing")
todo = total - done - doing
pct = int((done / total) * 100) if total else 0
st.progress(pct / 100 if total else 0.0, text=f"완료율: {pct}%")
st.caption(f"전체 {total} · 할일 {todo} · 진행중 {doing} · 완료 {done}")

# ---------- Footer ----------
st.markdown("---")
st.caption("만든 이: Streamlit TODO • 단일 파일 앱 • 로컬에서 실행 가능")
