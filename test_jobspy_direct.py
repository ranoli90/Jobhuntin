"""Test JobSpy integration directly."""
from jobspy import scrape_jobs


def test_jobspy_direct():
    print("Testing JobSpy direct call...")
    
    df = scrape_jobs(
        site_name=["indeed"],
        search_term="software engineer",
        location="Remote",
        results_wanted=5,
        hours_old=168,
    )
    
    print(f"Fetched {len(df)} jobs")
    print(f"Columns: {list(df.columns)}")
    
    if not df.empty:
        for idx, row in df.head(3).iterrows():
            print(f"\n--- Job {idx + 1} ---")
            for col in df.columns:
                val = row.get(col)
                if val is not None and str(val).strip():
                    print(f"  {col}: {str(val)[:80]}")
    else:
        print("No jobs found - may be rate limited or blocked")
    return df

if __name__ == "__main__":
    test_jobspy_direct()
