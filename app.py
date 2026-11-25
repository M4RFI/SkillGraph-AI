from __future__ import annotations

import pandas as pd
import streamlit as st

from core.data_structures import (SkillGraph, binary_search_skill, build_schedule, compute_priority_scores,
                                  inherit_priority, skill_gap, sorted_skill_names, top_n_by_priority)
from core.skill_db import ROLES, SKILL_DB, validate_kb

st.set_page_config(page_title="SkillGraph AI", page_icon="🕸️", layout="wide")
validate_kb()


@st.cache_resource
def get_graph() -> SkillGraph:
    return SkillGraph.from_skill_db(SKILL_DB)


GRAPH = get_graph()
ALL_SKILLS = sorted_skill_names(SKILL_DB)
TABS = ["Ringkasan", "Peta Skill", "Kurikulum", "Di Balik Layar"]


def demo_demand(role: str) -> dict[str, float]:
    """DATA DEMO Tahap 1: skill inti menurun 90%, 83%, 76%, ...; skill tetangga prasyarat 15%."""
    core = ROLES[role]["core"]
    demand = {s: max(90.0 - 7 * i, 30.0) for i, s in enumerate(core)}
    for s in GRAPH.backward_bfs(core):
        demand.setdefault(s, 15.0)
    return demand


def analyze(role: str, owned_declared: set[str], weeks_budget: int, assume_implied: bool) -> dict:
    core = set(ROLES[role]["core"])
    owned = GRAPH.implied_skills(owned_declared) if assume_implied else set(owned_declared)
    demand = demo_demand(role)

    target = core | {s for s, _ in top_n_by_priority(demand, 12)}            # priority queue: Top-K pasar
    have, missing = skill_gap(target, owned)                                  # set: irisan & selisih
    base = compute_priority_scores(demand, core)                              # skor + bonus skill inti
    to_learn = GRAPH.backward_bfs(missing, stop_at=owned) - owned             # BFS mundur
    eff = inherit_priority(GRAPH, to_learn, base)                             # priority inheritance
    trace: list = []
    order = GRAPH.topological_sort_kahn(to_learn, eff, trace)                 # Kahn + heap
    schedule = build_schedule(order, {s: SKILL_DB[s]["weeks"] for s in order}, weeks_budget)

    weight = {s: max(base.get(s, 1.0), 1.0) for s in target}
    readiness = 100 * sum(weight[s] for s in have) / sum(weight.values())
    return {"role": role, "weeks_budget": weeks_budget, "core": core, "owned": owned, "demand": demand,
            "target": target, "have": have, "missing": missing, "base": base, "to_learn": to_learn,
            "eff": eff, "order": order, "trace": trace, "schedule": schedule,
            "total_weeks": schedule[-1]["end_week"] if schedule else 0,
            "priority_missing": top_n_by_priority({s: base.get(s, 0.0) for s in missing}, len(missing)),
            "readiness": round(readiness, 1)}


def explorer(key: str) -> None:
    """Penjelajah skill: binary search pada daftar nama skill terurut."""
    st.subheader("Penjelajah skill (binary search)")
    q = st.text_input("Nama skill", value="Pandas", key=key)
    idx = binary_search_skill(ALL_SKILLS, q)
    if idx >= 0:
        name = ALL_SKILLS[idx]; meta = SKILL_DB[name]
        st.success(f"Ditemukan di indeks {idx} dari {len(ALL_SKILLS)}")
        st.write(f"**{name}** · {meta['category']} · estimasi {meta['weeks']} minggu")
        st.write("Prasyarat langsung:", ", ".join(GRAPH.rev[name]) or "-")
        st.write("Membuka skill:", ", ".join(GRAPH.adj[name]) or "-")
        st.write("Semua prasyarat (BFS mundur):", ", ".join(sorted(GRAPH.backward_bfs([name]) - {name})) or "-")
    elif q:
        st.error("Skill tidak ada di basis pengetahuan.")


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.title("🕸️ SkillGraph AI")
    st.caption("Peta jalan belajar berdasarkan prasyarat skill")

    st.subheader("Target karier")
    role = st.selectbox("Posisi target", list(ROLES))
    weeks = st.slider("Target waktu belajar (minggu)", 4, 52, 12)

    st.subheader("Skill yang dikuasai")
    owned_input = st.multiselect("Pilih dari 63 skill", ALL_SKILLS, default=["Python", "Git"])
    assume_implied = st.checkbox("Prasyarat skill yang dikuasai dianggap sudah dikuasai", value=True)

    run = st.button("🚀 Analisis Sekarang", type="primary", width="stretch")

if run:
    st.session_state["res"] = analyze(role, set(owned_input), weeks, assume_implied)
res = st.session_state.get("res")

# =============================================================================
# HALAMAN UTAMA
# =============================================================================
st.title("SkillGraph AI")
st.caption("Pemeta Peta Jalan Karier & Radar Lowongan Kerja Real-Time")
tabs = st.tabs(TABS)

if not res:
    with tabs[0]:
        st.info("Atur posisi, skill, dan target waktu di sidebar, lalu klik **Analisis Sekarang**.")
    for i in (2, 3):
        with tabs[i]:
            st.caption("Klik Analisis Sekarang terlebih dahulu.")
    with tabs[1]:
        explorer("explorer_q0")
    st.stop()

# ---- Ringkasan --------------------------------------------------------------------
with tabs[0]:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Skor kesiapan", f"{res['readiness']}%")
    m2.metric("Skill target", len(res["target"]))
    m3.metric("Sudah dikuasai", len(res["have"]))
    m4.metric("Skill kurang", len(res["missing"]))
    st.progress(min(res["readiness"], 100) / 100, text="Skor kesiapan")
    if res["total_weeks"] <= res["weeks_budget"]:
        st.success(f"Kurikulum {res['total_weeks']} minggu muat dalam target {res['weeks_budget']} minggu.")
    else:
        fit = sum(1 for r in res["schedule"] if r["within_budget"])
        st.warning(f"Kurikulum butuh {res['total_weeks']} minggu; dalam {res['weeks_budget']} minggu "
                   f"baru {fit} dari {len(res['schedule'])} skill tercapai.")
    st.markdown("**Skill kurang berdasarkan prioritas (priority queue)**")
    st.dataframe(pd.DataFrame([{"Prioritas": i + 1, "Skill": s, "Skor": round(sc, 1),
                                "Permintaan demo (%)": round(res["demand"].get(s, 0), 1)}
                               for i, (s, sc) in enumerate(res["priority_missing"])]),
                 hide_index=True, width="stretch")
    st.markdown("**Sudah dikuasai (irisan):** " + (", ".join(sorted(res["have"])) or "-"))
    st.caption("Data permintaan pasar pada Tahap 1 masih DEMO.")

# ---- Peta Skill -------------------------------------------------------------------
with tabs[1]:
    explorer("explorer_q1")
    st.divider()
    st.markdown("**Sisi graph kurikulum (prasyarat → skill):**")
    st.dataframe(pd.DataFrame(GRAPH.edges(res["to_learn"]), columns=["Prasyarat", "Skill"]),
                 hide_index=True, width="stretch")

# ---- Kurikulum ----------------------------------------------------------------------
with tabs[2]:
    if not res["schedule"]:
        st.success("Seluruh skill target sudah dikuasai.")
    else:
        st.dataframe(pd.DataFrame([{
            "Urutan": i + 1, "Skill": r["skill"], "Kategori": SKILL_DB[r["skill"]]["category"],
            "Minggu": f"{r['start_week']}-{r['end_week']}",
            "Jenis": "target pasar" if r["skill"] in res["missing"] else "prasyarat",
            "Dalam target waktu": "Ya" if r["within_budget"] else "Tidak"}
            for i, r in enumerate(res["schedule"])]), hide_index=True, width="stretch")
        st.caption("Urutan dari topological sort (Kahn) + priority queue: tidak ada skill sebelum prasyaratnya. "
                   "")

# ---- Di Balik Layar -----------------------------------------------------------------------
with tabs[3]:
    st.caption("Isi struktur data nyata dari analisis di atas - bahan demo untuk dosen.")
    with st.expander("1. Directed graph - adjacency list (skill yang perlu dipelajari)", expanded=True):
        info = GRAPH.inspect(res["to_learn"])
        st.write(f"{info['jumlah_node']} node, {info['jumlah_sisi']} sisi · akar: {', '.join(info['node_akar']) or '-'}")
        st.json(info["adjacency_list"])
    with st.expander("2. Set - irisan dan selisih"):
        st.write("Target:", sorted(res["target"]))
        st.write("Dikuasai:", sorted(res["owned"]))
        st.write("Irisan (target & dikuasai):", sorted(res["have"]))
        st.write("Selisih (target - dikuasai):", sorted(res["missing"]))
    with st.expander("3. Priority queue (max-heap) - urutan pop"):
        st.write([f"{s} ({sc:g})" for s, sc in res["priority_missing"]])
        st.caption("Skor = % permintaan + 20 bila skill inti posisi.")
    with st.expander("4. BFS mundur - closure prasyarat"):
        st.write("Dimulai dari skill kurang:", sorted(res["missing"]))
        st.write("Prasyarat tambahan yang belum dikuasai:", sorted(res["to_learn"] - res["missing"]))
    with st.expander("5. Priority inheritance"):
        st.dataframe(pd.DataFrame([{"Skill": s, "Skor sendiri": res["base"].get(s, 0), "Skor efektif": res["eff"][s]}
                                   for s in res["order"]]), hide_index=True, width="stretch")
    with st.expander("6. Jejak topological sort (Kahn)", expanded=True):
        st.dataframe(pd.DataFrame([{"Langkah": t["langkah"], "Antrean siap (skor)": ", ".join(t["antrean_siap"]),
                                    "Dipilih": t["dipilih"], "Membuka": ", ".join(t["membuka"]) or "-"}
                                   for t in res["trace"]]), hide_index=True, width="stretch")
        st.write("Urutan valid (prasyarat selalu sebelum skill):", GRAPH.is_valid_order(res["order"]))
