import pandas as pd
import ast
import os

# --- PATHS ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'raw', 'gsearch_jobs.csv')
PROCESSED_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'processed', 'cleaned_skills_data.csv')

print(f"🔄 Loading raw data from: {RAW_PATH}")
df = pd.read_csv(RAW_PATH)
print(f"   ✅ Loaded {len(df):,} rows.")

# --- STEP 1: Standardize column names to what downstream scripts expect ---
df = df.rename(columns={
    "salary_standardized": "salary_year_avg",  # best normalized salary column
    "description_tokens":  "job_skills",        # skill tokens for this dataset
    "title":               "job_title",
})

# --- STEP 2: Drop rows with null salaries ---
print("\n🔄 Dropping rows with null salaries...")
df["salary_year_avg"] = pd.to_numeric(df["salary_year_avg"], errors="coerce")
df = df.dropna(subset=["salary_year_avg"])
print(f"   ✅ {len(df):,} rows remain after salary filter.")

# --- STEP 3: Parse skills column from messy string → Python list ---
def parse_skills(skill_str):
    """Safely parse a string like \"['python', 'sql']\" into a real list."""
    if pd.isna(skill_str) or str(skill_str).strip() == "":
        return []
    try:
        result = ast.literal_eval(str(skill_str))
        if isinstance(result, list):
            return result
        return [str(result)]
    except (ValueError, SyntaxError):
        cleaned = str(skill_str).strip("[]").replace("'", "").replace('"', "")
        return [s.strip() for s in cleaned.split(",") if s.strip()]

print("🔄 Parsing skills column...")
df["job_skills"] = df["job_skills"].apply(parse_skills)

# --- STEP 4: Explode — one skill per row ---
print("🔄 Exploding skills to individual rows...")
df = df.explode("job_skills")

# --- STEP 5: Normalize text to lowercase & drop empty skills ---
df["job_skills"] = df["job_skills"].str.lower().str.strip()
df = df.dropna(subset=["job_skills"])
df = df[df["job_skills"] != ""]
print(f"   ✅ {len(df):,} skill-rows after explode.")

# --- STEP 6: Keep only the columns needed downstream ---
KEEP_COLS = ["job_title", "job_skills", "salary_year_avg"]
df = df[KEEP_COLS]

# --- STEP 7: Save output ---
os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
df.to_csv(PROCESSED_PATH, index=False)
print(f"\n🎉 Cleaned data saved to: {PROCESSED_PATH}")
print(f"   Final shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"\n📊 Sample output:")
print(df.head(10).to_string(index=False))