"""
skill_db.py - Basis pengetahuan skill (knowledge base). [Tahap 1 - branch keisya-algorithms]

Berisi:
  * SKILL_DB : dictionary (hash table) nama skill -> metadata (kategori, estimasi minggu,
               prasyarat, alias penulisan di lowongan).
  * ROLES    : dictionary posisi pekerjaan -> kata kunci judul + skill inti.
  * ALIAS_MAP: hash table alias -> nama skill kanonik (lookup O(1)).

Relasi prasyarat ("pre") menjadi sisi (edge) pada Directed Graph:
    prasyarat  --->  skill
"""
from __future__ import annotations

# nama: (kategori, estimasi_minggu, [prasyarat], [alias])
_RAW = {
    # --- Fondasi & tools ---
    "Git":              ("Tools", 1, [], ["git", "github", "gitlab", "version control"]),
    "Linux":            ("Tools", 2, [], ["linux", "bash", "shell scripting", "unix"]),
    "Agile":            ("Soft/Process", 1, [], ["agile", "scrum", "kanban", "jira"]),
    "OOP":              ("Fondasi CS", 2, [], ["oop", "object-oriented", "object oriented"]),
    "Data Structures & Algorithms": ("Fondasi CS", 4, ["OOP"],
                         ["data structures", "algorithms", "algorithm", "dsa", "data structure"]),
    "Design Patterns":  ("Fondasi CS", 2, ["OOP"], ["design patterns", "design pattern"]),
    "Testing":          ("Tools", 2, [], ["unit testing", "testing", "pytest", "junit", "jest", "tdd", "qa automation"]),
    # --- Bahasa pemrograman ---
    "Python":           ("Bahasa Pemrograman", 3, [], ["python", "python3", "py"]),
    "JavaScript":       ("Bahasa Pemrograman", 3, [], ["javascript", "js", "ecmascript", "es6"]),
    "TypeScript":       ("Bahasa Pemrograman", 2, ["JavaScript"], ["typescript"]),
    "Java":             ("Bahasa Pemrograman", 4, ["OOP"], ["java"]),
    "Go":               ("Bahasa Pemrograman", 3, [], ["golang"]),
    "Rust":             ("Bahasa Pemrograman", 4, [], ["rust"]),
    "C#":               ("Bahasa Pemrograman", 3, ["OOP"], ["c#", "csharp"]),
    ".NET":             ("Framework Backend", 3, ["C#"], [".net", "dotnet", "asp.net"]),
    "C++":              ("Bahasa Pemrograman", 4, ["OOP"], ["c++"]),
    "PHP":              ("Bahasa Pemrograman", 2, [], ["php"]),
    "Laravel":          ("Framework Backend", 2, ["PHP"], ["laravel"]),
    # --- Database ---
    "SQL":              ("Database", 2, [], ["sql", "mysql", "postgresql", "postgres", "sqlite", "t-sql", "mssql", "sql server"]),
    "NoSQL":            ("Database", 2, ["SQL"], ["nosql", "mongodb", "cassandra", "dynamodb"]),
    "Redis":            ("Database", 1, ["NoSQL"], ["redis"]),
    "Data Warehouse":   ("Data Engineering", 2, ["SQL"], ["data warehouse", "bigquery", "snowflake", "redshift"]),
    # --- Web ---
    "HTML/CSS":         ("Frontend", 2, [], ["html", "css", "html5", "css3", "sass", "tailwind"]),
    "React":            ("Frontend", 3, ["JavaScript", "HTML/CSS"], ["react", "reactjs", "react.js", "next.js", "nextjs"]),
    "Vue.js":           ("Frontend", 2, ["JavaScript", "HTML/CSS"], ["vue", "vue.js", "vuejs", "nuxt"]),
    "Angular":          ("Frontend", 3, ["TypeScript", "HTML/CSS"], ["angular", "angularjs"]),
    "React Native":     ("Mobile", 3, ["React"], ["react native", "react-native"]),
    "Flutter":          ("Mobile", 3, ["OOP"], ["flutter", "dart"]),
    "Node.js":          ("Framework Backend", 3, ["JavaScript"], ["node.js", "nodejs", "express.js", "expressjs"]),
    "REST API":         ("Backend", 2, [], ["restful", "rest api", "rest apis", "api development"]),
    "GraphQL":          ("Backend", 1, ["REST API"], ["graphql"]),
    "Flask":            ("Framework Backend", 2, ["Python", "REST API"], ["flask"]),
    "FastAPI":          ("Framework Backend", 2, ["Python", "REST API"], ["fastapi"]),
    "Django":           ("Framework Backend", 3, ["Python", "SQL"], ["django"]),
    "Spring Boot":      ("Framework Backend", 3, ["Java", "SQL", "REST API"], ["spring boot", "springboot", "spring framework"]),
    "Microservices":    ("Backend", 3, ["REST API", "Docker"], ["microservices", "microservice", "distributed systems"]),
    "System Design":    ("Backend", 3, ["Microservices", "SQL"], ["system design", "scalability", "software architecture"]),
    # --- Data & AI ---
    "Excel":            ("Analitik Data", 1, [], ["excel", "spreadsheet", "google sheets"]),
    "Statistics":       ("Analitik Data", 3, [], ["statistics", "statistical", "statistik", "probability", "a/b testing"]),
    "NumPy":            ("Data Science", 1, ["Python"], ["numpy"]),
    "Pandas":           ("Data Science", 2, ["Python", "NumPy"], ["pandas", "dataframe", "data wrangling"]),
    "Data Visualization": ("Analitik Data", 2, ["Pandas"], ["data visualization", "matplotlib", "seaborn", "plotly", "data viz"]),
    "BI Tools":         ("Analitik Data", 2, ["SQL"], ["tableau", "power bi", "powerbi", "looker", "bi tools", "business intelligence"]),
    "Machine Learning": ("AI/ML", 5, ["Python", "Statistics", "Pandas"],
                         ["machine learning", "ml", "scikit-learn", "sklearn", "xgboost", "predictive modeling", "supervised learning"]),
    "Deep Learning":    ("AI/ML", 4, ["Machine Learning"], ["deep learning", "neural network", "neural networks", "cnn", "rnn", "keras"]),
    "TensorFlow":       ("AI/ML", 2, ["Deep Learning"], ["tensorflow"]),
    "PyTorch":          ("AI/ML", 2, ["Deep Learning"], ["pytorch"]),
    "NLP":              ("AI/ML", 3, ["Machine Learning"], ["nlp", "natural language processing", "text mining", "spacy", "hugging face", "huggingface"]),
    "Computer Vision":  ("AI/ML", 3, ["Deep Learning"], ["computer vision", "opencv", "image processing", "object detection"]),
    "LLM / Generative AI": ("AI/ML", 3, ["NLP", "Deep Learning"],
                         ["llm", "llms", "large language model", "generative ai", "genai", "gen ai", "langchain", "rag", "prompt engineering", "openai", "chatgpt"]),
    "MLOps":            ("AI/ML", 3, ["Machine Learning", "Docker"], ["mlops", "mlflow", "kubeflow", "model deployment", "model serving"]),
    # --- Data engineering ---
    "ETL":              ("Data Engineering", 2, ["SQL", "Python"], ["etl", "elt", "data pipeline", "data pipelines", "data engineering"]),
    "Airflow":          ("Data Engineering", 2, ["ETL"], ["airflow", "dbt"]),
    "Apache Spark":     ("Data Engineering", 3, ["Python", "SQL"], ["spark", "pyspark", "apache spark", "databricks"]),
    # --- DevOps & cloud ---
    "Docker":           ("DevOps", 2, ["Linux"], ["docker", "container", "containers", "containerization"]),
    "Kubernetes":       ("DevOps", 3, ["Docker"], ["kubernetes", "k8s", "helm"]),
    "CI/CD":            ("DevOps", 2, ["Git"], ["ci/cd", "cicd", "jenkins", "github actions", "gitlab ci", "continuous integration"]),
    "Cloud Computing":  ("Cloud", 2, ["Linux"], ["cloud", "cloud computing", "cloud infrastructure"]),
    "AWS":              ("Cloud", 3, ["Cloud Computing"], ["aws", "amazon web services", "ec2"]),
    "Google Cloud":     ("Cloud", 3, ["Cloud Computing"], ["gcp", "google cloud"]),
    "Azure":            ("Cloud", 3, ["Cloud Computing"], ["azure"]),
    "Terraform":        ("DevOps", 2, ["Cloud Computing"], ["terraform", "infrastructure as code", "iac", "ansible"]),
    "Cybersecurity":    ("Keamanan", 3, ["Linux"], ["security", "cybersecurity", "owasp", "penetration testing"]),
}

# Penyeragaman kategori ke 8 kelompok yang dipakai UI & treemap
CATEGORY_MAP = {
    "Bahasa Pemrograman": "Bahasa", "Database": "Database", "AI/ML": "AI/ML",
    "DevOps": "DevOps & Cloud", "Cloud": "DevOps & Cloud", "Keamanan": "DevOps & Cloud",
    "Frontend": "Web/Backend", "Backend": "Web/Backend", "Framework Backend": "Web/Backend", "Mobile": "Web/Backend",
    "Data Engineering": "Data Engineering", "Analitik Data": "Analitik Data", "Data Science": "Analitik Data",
    "Fondasi CS": "Fundamental", "Tools": "Fundamental", "Soft/Process": "Fundamental",
}

SKILL_DB: dict[str, dict] = {
    name: {"category": CATEGORY_MAP[cat], "weeks": wk, "prereqs": list(pre), "aliases": list(al)}
    for name, (cat, wk, pre, al) in _RAW.items()
}

# Hash table alias -> skill kanonik. Nama skill sendiri (lowercase) juga menjadi alias.
ALIAS_MAP: dict[str, str] = {}
for _name, _meta in SKILL_DB.items():
    ALIAS_MAP[_name.lower()] = _name
    for _a in _meta["aliases"]:
        ALIAS_MAP[_a.lower()] = _name

# Posisi pekerjaan: kata kunci judul (untuk searching) + skill inti
ROLES: dict[str, dict] = {
    "Data Scientist": {
        "keywords": ["data scientist", "data science", "machine learning", "ml engineer"],
        "core": ["Python", "SQL", "Statistics", "Pandas", "Machine Learning", "Data Visualization", "Deep Learning"]},
    "Data Analyst": {
        "keywords": ["data analyst", "analytics", "business intelligence", "bi analyst", "data analysis"],
        "core": ["SQL", "Excel", "BI Tools", "Data Visualization", "Statistics", "Python", "Pandas"]},
    "Data Engineer": {
        "keywords": ["data engineer", "etl", "data platform", "analytics engineer"],
        "core": ["Python", "SQL", "ETL", "Apache Spark", "Airflow", "Data Warehouse", "Docker", "Cloud Computing"]},
    "Machine Learning Engineer": {
        "keywords": ["machine learning engineer", "ml engineer", "mlops", "machine learning"],
        "core": ["Python", "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "MLOps", "Docker", "Git"]},
    "AI Engineer": {
        "keywords": ["ai engineer", "machine learning engineer", "ml engineer", "llm", "generative ai",
                     "artificial intelligence", "applied scientist", "ai/ml", "nlp"],
        "core": ["Python", "Machine Learning", "Deep Learning", "PyTorch", "NLP", "LLM / Generative AI", "MLOps", "Docker"]},
    "Backend Developer": {
        "keywords": ["backend", "back-end", "back end", "server-side", "api developer", "software engineer"],
        "core": ["Python", "SQL", "REST API", "Git", "Docker", "Testing", "Microservices"]},
    "Frontend Developer": {
        "keywords": ["frontend", "front-end", "front end", "ui developer", "web developer"],
        "core": ["JavaScript", "HTML/CSS", "TypeScript", "React", "Git", "Testing"]},
    "Full Stack Developer": {
        "keywords": ["full stack", "fullstack", "full-stack"],
        "core": ["JavaScript", "HTML/CSS", "React", "Node.js", "SQL", "Git", "REST API"]},
    "DevOps Engineer": {
        "keywords": ["devops", "site reliability", "sre", "platform engineer", "cloud engineer", "infrastructure"],
        "core": ["Linux", "Git", "Docker", "Kubernetes", "CI/CD", "Cloud Computing", "Terraform", "AWS"]},
}


def validate_kb() -> None:
    """Pastikan semua prasyarat terdaftar sebagai skill (integritas data)."""
    for name, meta in SKILL_DB.items():
        for p in meta["prereqs"]:
            assert p in SKILL_DB, f"Prasyarat '{p}' pada '{name}' tidak terdaftar"
    for role, meta in ROLES.items():
        for s in meta["core"]:
            assert s in SKILL_DB, f"Skill inti '{s}' pada '{role}' tidak terdaftar"


def normalize_skill(text: str) -> str | None:
    """Normalisasi satu penulisan skill ke nama baku lewat hash table ALIAS_MAP, O(1). None jika tidak dikenal."""
    return ALIAS_MAP.get(text.strip().lower())


def normalize_skills(texts) -> set[str]:
    """Normalisasi banyak penulisan sekaligus; hasil berupa SET (tanpa duplikat, yang tidak dikenal dibuang)."""
    return {n for t in texts if (n := normalize_skill(t))}


if __name__ == "__main__":
    validate_kb()
    print(f"{len(SKILL_DB)} skill, {len(ALIAS_MAP)} alias, {len(ROLES)} posisi - OK")
