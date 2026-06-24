import pandas as pd
import mysql.connector
from mysql.connector import errorcode
import os
from dotenv import load_dotenv

# --- PATHS ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'processed', 'cleaned_skills_data.csv')
OUTPUT_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'processed', 'final_powerbi_data.csv')

# --- LOAD ENVIRONMENT VARIABLES ---
# This looks for the .env file and loads the variables into os.environ
load_dotenv(os.path.join(SCRIPT_DIR, '..', '.env'))

# --- MySQL CONNECTION CONFIG ---
# Safely pull from the .env file, with fallback defaults just in case
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "admin123",        # ← updated
    "database": "skill_salary_db"
}

MIN_POSTINGS = 100

# ── STEP 1: Load cleaned CSV ─────────────────────────────────────────────────
print("🔄 Loading cleaned skills data...")
df = pd.read_csv(INPUT_PATH)
print(f"   ✅ Loaded {len(df):,} rows.")

# ── STEP 2: Pre-compute median salary in pandas (MySQL 8.0+ has PERCENTILE_CONT
#    but it's complex; pandas is simpler and equally accurate here) ───────────
print("🔄 Pre-computing median salary per skill...")
median_df = (
    df.groupby("job_skills")["salary_year_avg"]
    .median()
    .reset_index()
    .rename(columns={"salary_year_avg": "median_salary"})
)
print(f"   ✅ Median computed for {len(median_df):,} unique skills.")

# ── STEP 3: Connect to MySQL and create the database if it doesn't exist ─────
print(f"\n🔄 Connecting to MySQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")

# First connect WITHOUT specifying the database so we can create it
init_config = {k: v for k, v in DB_CONFIG.items() if k != "database"}
conn = mysql.connector.connect(**init_config)
cursor = conn.cursor()

cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}`")
cursor.execute(f"USE `{DB_CONFIG['database']}`")
print(f"   ✅ Database '{DB_CONFIG['database']}' ready.")

# ── STEP 4: Create tables ─────────────────────────────────────────────────────
print("🔄 Creating tables in MySQL...")

cursor.execute("DROP TABLE IF EXISTS skill_medians")
cursor.execute("DROP TABLE IF EXISTS skills_data")

cursor.execute("""
    CREATE TABLE skills_data (
        job_title       VARCHAR(255),
        job_skills      VARCHAR(100),
        salary_year_avg DECIMAL(12, 2)
    )
""")

cursor.execute("""
    CREATE TABLE skill_medians (
        job_skills     VARCHAR(100),
        median_salary  DECIMAL(12, 2)
    )
""")
print("   ✅ Tables 'skills_data' and 'skill_medians' created.")

# ── STEP 5: Bulk-insert data ──────────────────────────────────────────────────
print("🔄 Inserting skills_data rows into MySQL...")
skills_rows = [
    (
        str(row.job_title)      if pd.notna(row.job_title)      else None,
        str(row.job_skills)     if pd.notna(row.job_skills)     else None,
        float(row.salary_year_avg) if pd.notna(row.salary_year_avg) else None
    )
    for row in df.itertuples(index=False)
]
cursor.executemany(
    "INSERT INTO skills_data (job_title, job_skills, salary_year_avg) VALUES (%s, %s, %s)",
    skills_rows
)
print(f"   ✅ Inserted {len(skills_rows):,} rows into skills_data.")

print("🔄 Inserting skill_medians rows into MySQL...")
median_rows = [
    (str(row.job_skills), float(row.median_salary))
    for row in median_df.itertuples(index=False)
]
cursor.executemany(
    "INSERT INTO skill_medians (job_skills, median_salary) VALUES (%s, %s)",
    median_rows
)
conn.commit()
print(f"   ✅ Inserted {len(median_rows):,} rows into skill_medians.")

# ── STEP 6: Run the CTE aggregation query ────────────────────────────────────
SQL_QUERY = """
WITH skill_stats AS (
    SELECT
        s.job_skills                        AS skill,
        COUNT(*)                            AS job_count,
        ROUND(AVG(s.salary_year_avg), 2)    AS avg_salary,
        ROUND(m.median_salary, 2)           AS median_salary
    FROM skills_data s
    JOIN skill_medians m
        ON s.job_skills = m.job_skills
    GROUP BY s.job_skills, m.median_salary
)

SELECT
    skill,
    job_count,
    median_salary,
    avg_salary
FROM skill_stats
WHERE job_count >= %s
ORDER BY median_salary DESC
"""

print(f"\n🔄 Running SQL aggregation (min postings: {MIN_POSTINGS})...")
cursor.execute(SQL_QUERY, (MIN_POSTINGS,))
rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]
result_df = pd.DataFrame(rows, columns=columns)
print(f"   ✅ Query returned {len(result_df):,} qualifying skills.")

# ── STEP 7: Print top 20 to console ──────────────────────────────────────────
print("\n" + "=" * 55)
print("  📊 TOP 20 SKILLS BY MEDIAN SALARY")
print("=" * 55)
print(f"  {'Rank':<5} {'Skill':<20} {'Median $':>10} {'Postings':>10}")
print("-" * 55)
for rank, row in enumerate(result_df.head(20).itertuples(index=False), start=1):
    print(f"  {rank:<5} {row.skill:<20} ${float(row.median_salary):>9,.0f} {int(row.job_count):>10,}")
print("=" * 55)

# ── STEP 8: Save for Power BI ─────────────────────────────────────────────────
cursor.close()
conn.close()

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
result_df.to_csv(OUTPUT_PATH, index=False)
print(f"\n🎉 Power BI data saved to: {OUTPUT_PATH}")
print(f"   Final shape: {len(result_df)} skills × {len(result_df.columns)} columns")
