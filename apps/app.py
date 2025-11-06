import sys, os
import pandas as pd
import streamlit as st

from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from rea.engine import Filters, call_llm, filter_rank


st.set_page_config(page_title="Real Estate Assistant (Offline)", page_icon="🏠")
st.title("🏠 Real Estate Assistant - Offline LLM Demo")

st.markdown("Use a **local Ollama LLM** (e.g., llama3.1)")

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "properties.csv"

df = pd.read_csv(DATA_PATH)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role":"assistant","content":"Hi! Tell me what you’re looking for - city, budget, bedrooms, and amenities."}
    ]

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

user_input = st.chat_input("Your message")
if user_input:
    st.session_state.messages.append({"role":"user","content":user_input})
    data = call_llm(st.session_state.messages)
    filters = data["filters"]
    follow_up = data["follow_up"]
    f = Filters(**filters)
    res = filter_rank(df, f)
    with st.chat_message("assistant"):
        if follow_up:
            st.write(follow_up)
        else:
            st.write("Here are some options:")
            if res.empty:
                st.warning("No matches found.")
            else:
                for _, row in res.head(10).iterrows():
                    st.image(row["image_url"], use_container_width=True)
                    st.markdown(f"**{row['type'].title()} in {row['neighborhood']}, {row['city']} — {row['price']} {row['currency']}**")
                    st.caption(row["description"])
    st.session_state.messages.append({"role":"assistant","content": follow_up or "Here are some matches!"})
