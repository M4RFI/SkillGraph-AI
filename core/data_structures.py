"""
data_structures.py - Struktur data & algoritma inti SkillGraph AI.   [Tahap 1 - branch keisya-algorithms]

Seluruhnya diimplementasikan sendiri (hanya memakai modul standar Python: heapq, collections, itertools):
  1. SkillGraph          Directed Graph (adjacency list), validasi DAG, backward_bfs,
                         topological_sort_kahn (+ jejak langkah), build_schedule, inspect
  2. Operasi Set         skill_gap, match_percentage
  3. MaxPriorityQueue    max-heap berbasis heapq + skor prioritas + priority inheritance
  4. Sorting/Searching   merge_sort_jobs, linear_search_jobs, binary_search_skill
"""
from __future__ import annotations

import heapq
from collections import deque
from typing import Callable, Iterable

CORE_BONUS = 20.0  # tambahan skor bila skill termasuk skill inti posisi target


# =============================================================================
# 1. DIRECTED GRAPH (ADJACENCY LIST)
# =============================================================================
class SkillGraph:
    """
    Sisi  P -> S  berarti "P adalah prasyarat S".
      adj[P] = [S, ...]   skill yang terbuka setelah P dikuasai (dependen)
      rev[S] = [P, ...]   prasyarat langsung S
    """

    def __init__(self) -> None:
        self.adj: dict[str, list[str]] = {}
        self.rev: dict[str, list[str]] = {}

    # ---- konstruksi -------------------------------------------------------
    @property
    def nodes(self) -> set[str]:
        return set(self.adj)

    def add_node(self, skill: str) -> None:
        self.adj.setdefault(skill, [])
        self.rev.setdefault(skill, [])

    def add_edge(self, prereq: str, skill: str, check_cycle: bool = True) -> None:
        """Tambah sisi prereq -> skill. Menolak sisi yang menciptakan siklus (graph wajib DAG)."""
        if prereq == skill:
            raise ValueError(f"Skill tidak boleh menjadi prasyarat dirinya sendiri: {skill}")
        self.add_node(prereq)
        self.add_node(skill)
        if skill in self.adj[prereq]:
            return                                         # sisi sudah ada
        if check_cycle and self._reachable(skill, prereq):  # skill sudah bisa mencapai prereq -> siklus
            raise ValueError(f"Sisi {prereq} -> {skill} menciptakan siklus")
        self.adj[prereq].append(skill)
        self.rev[skill].append(prereq)

    def _reachable(self, start: str, goal: str) -> bool:
        """BFS maju: apakah goal dapat dicapai dari start? O(V+E)."""
        seen, queue = {start}, deque([start])
        while queue:
            u = queue.popleft()
            if u == goal:
                return True
            for v in self.adj[u]:
                if v not in seen:
                    seen.add(v)
                    queue.append(v)
        return False

    @classmethod
    def from_skill_db(cls, skill_db: dict) -> "SkillGraph":
        g = cls()
        for name, meta in skill_db.items():
            g.add_node(name)
            for p in meta["prereqs"]:
                g.add_edge(p, name)
        return g

    # ---- validasi & inspeksi ---------------------------------------------
    def is_dag(self) -> bool:
        try:
            self.topological_sort_kahn()
            return True
        except ValueError:
            return False

    def validate_dag(self) -> None:
        if not self.is_dag():
            raise ValueError("Graph skill mengandung siklus")

    def edges(self, subset: set[str] | None = None) -> list[tuple[str, str]]:
        sub = self.nodes if subset is None else subset
        return [(u, v) for u in sorted(sub) for v in self.adj[u] if v in sub]

    def in_degree(self, subset: set[str] | None = None) -> dict[str, int]:
        sub = self.nodes if subset is None else set(subset)
        return {n: sum(1 for p in self.rev[n] if p in sub) for n in sub}

    def inspect(self, subset: set[str] | None = None) -> dict:
        """Ringkasan struktur data untuk tab 'Di Balik Layar'."""
        sub = self.nodes if subset is None else set(subset)
        indeg = self.in_degree(sub)
        return {
            "jumlah_node": len(sub),
            "jumlah_sisi": len(self.edges(sub)),
            "adjacency_list": {n: [v for v in self.adj[n] if v in sub] for n in sorted(sub)},
            "prasyarat_langsung": {n: [p for p in self.rev[n] if p in sub] for n in sorted(sub)},
            "in_degree": {n: indeg[n] for n in sorted(sub)},
            "node_akar": sorted(n for n in sub if indeg[n] == 0),
            "node_daun": sorted(n for n in sub if not any(v in sub for v in self.adj[n])),
        }

    # ---- BFS mundur --------------------------------------------------------
    def backward_bfs(self, starts: Iterable[str], stop_at: set[str] | None = None) -> set[str]:
        """
        BFS menelusuri `rev` dari `starts` -> kumpulkan semua prasyarat (langsung & tidak langsung).
        Node di `stop_at` (sudah dikuasai) dicatat tetapi tidak ditelusuri lebih dalam.
        Hasil mencakup `starts`. Kompleksitas O(V+E).
        """
        stop_at = stop_at or set()
        queue = deque(dict.fromkeys(s for s in starts if s in self.adj))
        visited = set(queue)
        while queue:
            cur = queue.popleft()
            if cur in stop_at:
                continue
            for pre in self.rev[cur]:
                if pre not in visited:
                    visited.add(pre)
                    queue.append(pre)
        return visited

    def implied_skills(self, owned: Iterable[str]) -> set[str]:
        """Skill dikuasai + seluruh prasyaratnya (menguasai X dianggap menguasai prasyarat X)."""
        return self.backward_bfs(owned)

    # ---- Topological sort (Kahn) -------------------------------------------
    def topological_sort_kahn(
        self,
        subset: set[str] | None = None,
        priority: dict[str, float] | None = None,
        trace: list | None = None,
    ) -> list[str]:
        """
        Kahn pada sub-graph `subset`. Skill siap (in-degree 0) ditampung di MaxPriorityQueue,
        sehingga yang dipelajari lebih dulu adalah skill ber-skor tertinggi yang prasyaratnya terpenuhi.
        `trace` (list) diisi jejak tiap langkah: antrean siap, skill dipilih, skill yang terbuka.
        Melempar ValueError jika ada siklus. Kompleksitas O((V+E) log V).
        """
        sub = self.nodes if subset is None else set(subset)
        priority = priority or {}
        indeg = self.in_degree(sub)

        pq = MaxPriorityQueue()
        for n in sorted(sub):
            if indeg[n] == 0:
                pq.push(n, priority.get(n, 0.0))

        order: list[str] = []
        while pq:
            step = {"langkah": len(order) + 1,
                    "antrean_siap": [f"{s} ({sc:g})" for s, sc in pq.snapshot()]}
            u, score = pq.pop_with_score()
            order.append(u)
            opened = []
            for v in self.adj[u]:
                if v in sub:
                    indeg[v] -= 1
                    if indeg[v] == 0:
                        pq.push(v, priority.get(v, 0.0))
                        opened.append(v)
            if trace is not None:
                step.update(dipilih=u, skor=score, membuka=opened)
                trace.append(step)

        if len(order) != len(sub):
            raise ValueError("Graph mengandung siklus: topological sort tidak mungkin")
        return order

    def is_valid_order(self, order: list[str]) -> bool:
        """Setiap prasyarat harus muncul SEBELUM skill yang bergantung padanya."""
        pos = {s: i for i, s in enumerate(order)}
        return all(pos[u] < pos[v] for u in order for v in self.adj[u] if v in pos)


def build_schedule(order: list[str], weeks: dict[str, int], weeks_budget: int) -> list[dict]:
    """Petakan urutan topologis ke minggu mulai/selesai kumulatif dan tandai yang muat dalam target waktu."""
    schedule, cursor = [], 0
    for s in order:
        start, end = cursor + 1, cursor + weeks[s]
        schedule.append({"skill": s, "weeks": weeks[s], "start_week": start, "end_week": end,
                         "within_budget": end <= weeks_budget})
        cursor = end
    return schedule


# =============================================================================
# 2. OPERASI SET - ANALISIS SKILL GAP
# =============================================================================
def skill_gap(target: set[str], owned: set[str]) -> tuple[set[str], set[str]]:
    """have = target & owned (irisan);  missing = target - owned (selisih)."""
    return target & owned, target - owned


def match_percentage(job_skills: set[str], owned: set[str]) -> float:
    """Persentase kecocokan lowongan = 100 * |job_skills & owned| / |job_skills|."""
    if not job_skills:
        return 0.0
    return round(100 * len(job_skills & owned) / len(job_skills), 1)


# =============================================================================
# 3. PRIORITY QUEUE (MAX-HEAP) + SKOR PRIORITAS
# =============================================================================
class MaxPriorityQueue:
    """
    heapq adalah min-heap -> skor disimpan negatif. Entri (-skor, nama): bila skor sama,
    nama (alfabet) menjadi tie-breaker sehingga hasil deterministik. push/pop O(log n), peek O(1).
    """

    def __init__(self) -> None:
        self._heap: list[tuple[float, str]] = []

    def push(self, item: str, score: float) -> None:
        heapq.heappush(self._heap, (-score, item))

    def pop(self) -> str:
        return heapq.heappop(self._heap)[1]

    def pop_with_score(self) -> tuple[str, float]:
        neg, item = heapq.heappop(self._heap)
        return item, -neg

    def peek(self) -> tuple[str, float]:
        neg, item = self._heap[0]
        return item, -neg

    def snapshot(self) -> list[tuple[str, float]]:
        """Isi heap urut prioritas tertinggi (tidak mengubah heap) - untuk tampilan/inspeksi."""
        return [(item, -neg) for neg, item in sorted(self._heap)]

    def __len__(self) -> int:
        return len(self._heap)

    def __bool__(self) -> bool:
        return bool(self._heap)


def top_n_by_priority(scores: dict[str, float], n: int) -> list[tuple[str, float]]:
    pq = MaxPriorityQueue()
    for s, sc in scores.items():
        pq.push(s, sc)
    return [pq.pop_with_score() for _ in range(min(n, len(pq)))]


def compute_priority_scores(demand_pct: dict[str, float], core_skills: set[str],
                            core_bonus: float = CORE_BONUS) -> dict[str, float]:
    """Skor = % lowongan yang meminta skill + core_bonus bila skill inti posisi target."""
    return {s: demand_pct.get(s, 0.0) + (core_bonus if s in core_skills else 0.0)
            for s in set(demand_pct) | set(core_skills)}


def inherit_priority(graph: SkillGraph, nodes: set[str], base: dict[str, float]) -> dict[str, float]:
    """
    Priority inheritance: skor efektif sebuah skill = max(skor sendiri, skor efektif semua dependennya
    di dalam `nodes`). Prasyarat jarang disebut di lowongan, tetapi harus dipelajari lebih awal
    bila membuka skill yang sangat dicari. Memoisasi -> O(V+E).
    """
    memo: dict[str, float] = {}

    def eff(n: str) -> float:
        if n not in memo:
            memo[n] = max([base.get(n, 0.0)] + [eff(d) for d in graph.adj[n] if d in nodes])
        return memo[n]

    return {n: eff(n) for n in nodes}


# =============================================================================
# 4. SORTING & SEARCHING
# =============================================================================
def merge_sort(items: list, key: Callable = lambda x: x, reverse: bool = False) -> list:
    """Merge sort stabil O(n log n); mengembalikan list baru."""
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    left, right = merge_sort(items[:mid], key, reverse), merge_sort(items[mid:], key, reverse)
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        a, b = key(left[i]), key(right[j])
        if (a >= b) if reverse else (a <= b):     # tanda '=' menjaga kestabilan
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    out.extend(left[i:]); out.extend(right[j:])
    return out


def merge_sort_jobs(jobs: list[dict]) -> list[dict]:
    """Urutkan lowongan dari (match_pct, jumlah skill) tertinggi. Lowongan butuh kunci 'match_pct' & 'skills'."""
    return merge_sort(jobs, key=lambda j: (j["match_pct"], len(j.get("skills", ()))), reverse=True)


def linear_search_jobs(jobs: list[dict], keywords: list[str]) -> list[dict]:
    """Filter lowongan yang judulnya memuat salah satu kata kunci. O(n*k)."""
    kws = [k.lower().strip() for k in keywords if k.strip()]
    return [j for j in jobs if any(k in j["title"].lower() for k in kws)]


def binary_search_skill(sorted_names: list[str], target: str) -> int:
    """Binary search O(log n) pada list nama skill TERURUT (case-insensitive). Indeks, atau -1 bila tidak ada."""
    lo, hi, t = 0, len(sorted_names) - 1, target.strip().lower()
    while lo <= hi:
        mid = (lo + hi) // 2
        cur = sorted_names[mid].lower()
        if cur == t:
            return mid
        lo, hi = (mid + 1, hi) if cur < t else (lo, mid - 1)
    return -1


def sorted_skill_names(skill_db: dict) -> list[str]:
    """Daftar nama skill terurut (case-insensitive) sebagai masukan binary_search_skill."""
    return sorted(skill_db, key=str.lower)
