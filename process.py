import os
import pandas as pd

def run():
    if os.path.exists("Metadate_Achizitii.csv"):
        try:
            df = pd.read_csv("Metadate_Achizitii.csv")
            print(f"Loaded metadata. Found {len(df)} records.")
            print(df.head())
        except Exception as e:
            print(f"Error reading metadata: {e}")
    else:
        print("Metadate_Achizitii.csv not found. Run scrape.py first.")

if __name__ == "__main__":
    run()
