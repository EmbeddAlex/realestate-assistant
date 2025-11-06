#!/usr/bin/env python3
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from rea.engine import Filters, call_llm, filter_rank

DATA_PATH = ROOT / "data" / "properties.csv"

def print_results(df):
    if df.empty:
        print("No matches found.")
        return
    for _, row in df.head(10).iterrows():
        print("="*60)
        print(f"{row['bedrooms']}BR {row['type']} in {row['neighborhood']}, {row['city']}")
        print(f"Price: {row['price']} {row['currency']}")
        print(row["description"])

def main():
    print("🏠 Real Estate Assistant — CLI (Offline)")
    df = pd.read_csv(DATA_PATH)
    messages = [{"role":"assistant","content":"Hello! Describe what you're looking for."}]
    print("assistant>", messages[0]["content"])

    while True:
        user = input("you> ").strip()
        if user.lower() in ["quit","exit"]: break
        messages.append({"role":"user","content":user})
        data = call_llm(messages)
        filters = data["filters"]
        f = Filters(**filters)
        res = filter_rank(df, f)
        if data["follow_up"]:
            print("assistant>", data["follow_up"])
        else:
            print("assistant> Showing matches:")
            print_results(res)
        messages.append({"role":"assistant","content":data["follow_up"] or "Here are results."})

if __name__ == "__main__":
    main()
