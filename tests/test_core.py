"""
Unit test logika inti Tahap 1.
Jalankan:  pytest -v      atau      python tests/test_core.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from core.data_structures import (MaxPriorityQueue, SkillGraph, binary_search_skill,  # noqa: E402
                                  build_schedule, compute_priority_scores, inherit_priority,
                                  linear_search_jobs, match_percentage, merge_sort,
                                  merge_sort_jobs, skill_gap, sorted_skill_names, top_n_by_priority)
from core.skill_db import ALIAS_MAP, ROLES, SKILL_DB, normalize_skill, normalize_skills, validate_kb  # noqa: E402


def mini_graph() -> SkillGraph:
    g = SkillGraph()
    for p, s in [("Python", "NumPy"), ("NumPy", "Pandas"), ("Python", "Pandas"), ("Pandas", "Machine Learning"),
                 ("Statistics", "Machine Learning"), ("Linux", "Docker")]:
        g.add_edge(p, s)
    return g


# ---- basis pengetahuan -------------------------------------------------------
def test_knowledge_base_size_and_integrity():
    validate_kb()
    assert len(SKILL_DB) == 63 and len(ALIAS_MAP) >= 200
    for role in ["Data Scientist", "Machine Learning Engineer", "Backend Developer",
                 "Data Analyst", "DevOps Engineer", "Full Stack Developer"]:
        assert role in ROLES


def test_alias_normalization_hash_table():
    assert normalize_skill("JS") == "JavaScript" and normalize_skill(" ecmascript ") == "JavaScript"
    assert normalize_skill("py") == "Python" and normalize_skill("ML") == "Machine Learning"
    assert normalize_skill("tidak ada") is None
    assert normalize_skills(["js", "JavaScript", "py", "???"]) == {"JavaScript", "Python"}


# ---- DAG ---------------------------------------------------------------------
def test_full_knowledge_base_is_dag():
    g = SkillGraph.from_skill_db(SKILL_DB)
    assert g.is_dag()
    g.validate_dag()


def test_add_edge_rejects_cycle_and_self_loop():
    g = mini_graph()
    with pytest.raises(ValueError):
        g.add_edge("Machine Learning", "Python")       # Python -> ... -> ML -> Python = siklus
    with pytest.raises(ValueError):
        g.add_edge("Python", "Python")


def test_adjacency_and_reverse_lists():
    g = mini_graph()
    assert set(g.adj["Python"]) == {"NumPy", "Pandas"}
    assert set(g.rev["Machine Learning"]) == {"Pandas", "Statistics"}
    info = g.inspect()
    assert info["jumlah_node"] == 7 and info["jumlah_sisi"] == 6
    assert "Python" in info["node_akar"] and "Machine Learning" in info["node_daun"]


# ---- operasi set ---------------------------------------------------------------
def test_set_operations_and_match_percentage():
    have, missing = skill_gap({"Python", "SQL", "Docker", "Git"}, {"Python", "Git", "Rust"})
    assert have == {"Python", "Git"} and missing == {"SQL", "Docker"}
    assert match_percentage({"Python", "SQL", "Docker", "Git"}, {"Python", "Git"}) == 50.0
    assert match_percentage(set(), {"Python"}) == 0.0


# ---- priority queue ----------------------------------------------------------------
def test_max_priority_queue_order_and_deterministic_tiebreak():
    pq = MaxPriorityQueue()
    for item, sc in [("b", 5), ("a", 5), ("c", 9), ("d", 1)]:
        pq.push(item, sc)
    assert pq.peek() == ("c", 9)
    assert [pq.pop() for _ in range(4)] == ["c", "a", "b", "d"]   # skor sama -> alfabet
    assert not pq


def test_priority_scores_with_core_bonus_and_top_n():
    sc = compute_priority_scores({"Python": 60, "Docker": 40}, {"Python", "Git"})
    assert sc == {"Python": 80, "Docker": 40, "Git": 20}
    assert top_n_by_priority(sc, 2) == [("Python", 80), ("Docker", 40)]


def test_priority_inheritance():
    g = mini_graph()
    sub = {"NumPy", "Pandas", "Statistics", "Machine Learning", "Docker"}
    eff = inherit_priority(g, sub, {"Machine Learning": 75, "Pandas": 30, "NumPy": 5, "Statistics": 40, "Docker": 50})
    assert eff["NumPy"] == eff["Pandas"] == eff["Statistics"] == 75 and eff["Docker"] == 50


# ---- BFS mundur ------------------------------------------------------------------------
def test_backward_bfs_collects_all_prerequisites():
    g = mini_graph()
    assert g.backward_bfs(["Machine Learning"]) == {"Machine Learning", "Pandas", "NumPy", "Python", "Statistics"}


def test_backward_bfs_stops_at_owned_skills():
    g = mini_graph()
    res = g.backward_bfs(["Machine Learning"], stop_at={"Python"})
    assert "Python" in res and res == {"Machine Learning", "Pandas", "NumPy", "Python", "Statistics"}
    res2 = g.backward_bfs(["Machine Learning"], stop_at={"NumPy", "Pandas"})
    assert "Python" not in res2                            # tidak menelusuri lewat skill yang dikuasai


def test_implied_skills():
    assert mini_graph().implied_skills(["Pandas"]) == {"Pandas", "NumPy", "Python"}


# ---- topological sort Kahn --------------------------------------------------------------
def test_kahn_prerequisites_always_before_dependents_on_full_db():
    g = SkillGraph.from_skill_db(SKILL_DB)
    order = g.topological_sort_kahn()
    assert len(order) == 63 and g.is_valid_order(order)
    pos = {s: i for i, s in enumerate(order)}
    for skill, meta in SKILL_DB.items():
        for p in meta["prereqs"]:
            assert pos[p] < pos[skill]


def test_kahn_example_from_proposal_with_trace():
    g = mini_graph()
    owned = {"Python", "Linux"}
    sub = g.backward_bfs({"Pandas", "Statistics", "Machine Learning", "Docker"}, stop_at=owned) - owned
    prio = {"NumPy": 75, "Pandas": 75, "Statistics": 75, "Machine Learning": 75, "Docker": 50}
    trace: list = []
    order = g.topological_sort_kahn(sub, prio, trace)
    assert order == ["NumPy", "Pandas", "Statistics", "Machine Learning", "Docker"]
    assert [t["dipilih"] for t in trace] == order
    assert trace[0]["antrean_siap"] == ["NumPy (75)", "Statistics (75)", "Docker (50)"]
    assert trace[0]["membuka"] == ["Pandas"]


def test_kahn_priority_changes_order_but_stays_valid():
    g = mini_graph()
    sub = {"NumPy", "Pandas", "Statistics", "Machine Learning", "Docker"}
    order = g.topological_sort_kahn(sub, {"Docker": 99, "Statistics": 90})
    assert order[0] == "Docker" and order[1] == "Statistics" and g.is_valid_order(order)


def test_kahn_detects_cycle():
    g = SkillGraph()
    g.add_edge("A", "B"); g.add_edge("B", "C")
    g.add_edge("C", "A", check_cycle=False)                # sengaja merusak DAG
    with pytest.raises(ValueError):
        g.topological_sort_kahn()
    assert not g.is_dag()


def test_is_valid_order_detects_violation():
    assert not mini_graph().is_valid_order(["Pandas", "NumPy"])


def test_build_schedule_and_budget():
    sch = build_schedule(["NumPy", "Pandas", "Machine Learning"], {"NumPy": 1, "Pandas": 2, "Machine Learning": 5}, 4)
    assert [(s["start_week"], s["end_week"]) for s in sch] == [(1, 1), (2, 3), (4, 8)]
    assert [s["within_budget"] for s in sch] == [True, True, False]


# ---- sorting & searching -------------------------------------------------------------------
def test_merge_sort_is_stable_and_correct():
    data = [("a", 3), ("b", 1), ("c", 3), ("d", 2)]
    assert merge_sort(data, key=lambda x: x[1], reverse=True) == [("a", 3), ("c", 3), ("d", 2), ("b", 1)]
    assert merge_sort([5, 2, 9, 1, 5, 6]) == [1, 2, 5, 5, 6, 9]
    assert merge_sort([]) == []


def test_merge_sort_jobs_by_match_then_skill_count():
    jobs = [{"title": "A", "match_pct": 50, "skills": {1, 2}}, {"title": "B", "match_pct": 80, "skills": {1}},
            {"title": "C", "match_pct": 50, "skills": {1, 2, 3}}, {"title": "D", "match_pct": 50, "skills": {1, 2}}]
    assert [j["title"] for j in merge_sort_jobs(jobs)] == ["B", "C", "A", "D"]   # A sebelum D (stabil)


def test_linear_search_jobs():
    jobs = [{"title": "Senior Data Scientist"}, {"title": "Backend Developer"}, {"title": "ML Engineer"}]
    assert [j["title"] for j in linear_search_jobs(jobs, ["data scientist", "ml engineer"])] == ["Senior Data Scientist", "ML Engineer"]
    assert linear_search_jobs(jobs, ["  "]) == []


def test_binary_search_skill():
    names = sorted_skill_names(SKILL_DB)
    for s in SKILL_DB:
        assert names[binary_search_skill(names, s)] == s
    assert binary_search_skill(names, "pandas") != -1 and binary_search_skill(names, "Cobol") == -1
    assert binary_search_skill([], "x") == -1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
