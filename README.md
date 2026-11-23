# SkillGraph AI

Pemeta Peta Jalan Karier & Radar Lowongan Kerja Real-Time (Project Besar Praktikum Struktur Data).

## Menjalankan
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Gemini API key: isi di sidebar, atau salin `.streamlit/secrets.toml.example` menjadi `.streamlit/secrets.toml`.
Jika API lowongan tidak dapat diakses, centang **Data demo offline** di sidebar.

## Struktur
| Berkas | Isi |
|---|---|
| `app.py` | Antarmuka Streamlit (sidebar, 8 tab) |
| `core/data_structures.py` | SkillGraph (adjacency list, BFS, Kahn), MaxPriorityQueue (heapq), merge sort, binary & linear search |
| `core/analyzer.py` | Counter, operasi set, prioritas + inheritance, kurikulum, skor kesiapan |
| `core/skill_db.py` | 63 skill, relasi prasyarat, alias (hash table), 8 posisi |
| `core/job_api.py` | Remotive & Arbeitnow + cache hash table (TTL 6 jam) |
| `core/extractor.py` | Ekstraksi skill (regex alias) + pembaca PDF/TXT/CSV |
| `core/visuals.py` | Network graph, bar chart, treemap, gauge, timeline |
| `core/ai_engine.py` | Prompt & pemanggilan Gemini (`google-genai`) |
| `core/exporters.py` | Laporan PDF (fpdf2) dan Excel (openpyxl) |
| `tests/test_core.py` | Uji logika inti: `python tests/test_core.py` |
