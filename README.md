# 🗺️ Skill-to-Salary Tech Market Map

An end-to-end data analytics ETL pipeline that transforms 61,953 raw Google job postings into a Power BI dashboard revealing which technical skills command the highest salaries in today's tech market.

---

## Dashboard Preview
![Skill to Salary Dashboard](dashboard/dashboard_preview.png)

---

## 🛠️ Tech Stack

| Layer | Tool |
|---|---|
| Data Cleaning | Python · Pandas |
| Aggregation | Python · MySQL |
| Visualization | Power BI · DAX |
| Version Control | Git · GitHub |

---

## 🏗️ Project Architecture

```
Skill-to-Salary-Tech-Market-Map/
│
├── scripts/
│   ├── 01_data_cleaning.py       # Pandas ETL: clean, parse, explode, normalize
│   └── 02_sql_aggregations.py    # MySQL CTE: median salary per skill
│
├── dashboard/
│   └── dashboard_preview.png     # Power BI dashboard screenshot
│
└── README.md
```

**Pipeline Flow:**

```
gsearch_jobs.csv (61,953 raw job postings)
        │
        ▼
01_data_cleaning.py
→ Drop null salaries (retains 10,088 rows)
→ Parse messy skill arrays
→ Explode to one skill per row
→ Normalize to lowercase
        │
        ▼
cleaned_skills_data.csv (28,306 skill-rows)
        │
        ▼
02_sql_aggregations.py
→ Load into MySQL database
→ Pre-compute median salary per skill (Pandas)
→ CTE aggregation: median salary + job count per skill
→ Filter: minimum 50 job postings
        │
        ▼
final_powerbi_data.csv
        │
        ▼
Power BI Dashboard
→ Bar chart: skills ranked by median salary
→ Scatter plot: job count vs median salary
→ Treemap: market size by skill
→ DAX measure: Salary Premium %
```

---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.8+
- MySQL Server running on localhost
- Power BI Desktop (for dashboard)

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/Skill-to-Salary-Tech-Market-Map.git
cd Skill-to-Salary-Tech-Market-Map
```

### 2. Install dependencies
```bash
pip install pandas mysql-connector-python
```

### 3. Add the raw data
Download `gsearch_jobs.csv` from Kaggle and place it at:
```
data/raw/gsearch_jobs.csv
```

### 4. Configure MySQL
Open `scripts/02_sql_aggregations.py` and update these lines with your credentials:
```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "your_password_here",
    "database": "skill_salary_db"
}
```

### 5. Run the pipeline
```bash
python scripts/01_data_cleaning.py
python scripts/02_sql_aggregations.py
```

### 6. Open Power BI
Import `data/processed/final_powerbi_data.csv` into Power BI Desktop.

---

## 📈 Key Business Insights

> *(To be updated after analysis is complete)*

- 🥇 **Highest-paying skill:** `[TBD]` with a median salary of `$[TBD]`
- 📦 **Most in-demand skill:** `[TBD]` with `[TBD]` job postings
- 💡 **Best ROI skill** (high pay + high demand): `[TBD]`
- 📉 **Oversupplied skill** (high demand, below-average pay): `[TBD]`

---

## 📂 Data Source

- **Dataset:** [Google Jobs Search Dataset — Kaggle](https://www.kaggle.com/)
- **Raw rows:** 61,953 job postings
- **After salary filter:** 10,088 rows
- **After skill explode:** 28,306 skill-rows
- **Skills in final output:** 50+ qualifying skills (minimum 50 postings)

---

## 📄 License
[MIT](LICENSE)
