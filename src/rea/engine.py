import os
import re
import json
import pandas as pd
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

# ---- Offline LLM via Ollama ----
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

USE_OLLAMA = True
try:
    import ollama  # local offline LLM
    ollama_client = ollama.Client(host=OLLAMA_HOST)
except Exception:
    USE_OLLAMA = False
    ollama_client = None

SYSTEM_PROMPT = """
You are a concise real-estate assistant.
Given the conversation so far and the latest user message, return STRICT JSON ONLY (no prose).
Keys:
- filters: {
    city: str|Null,
    neighborhood: str|Null,
    price_min: int|Null,
    price_max: int|Null,
    property_type: "apartment"|"house"|"condo"|Null,
    bedrooms_min: int|Null,
    amenities: list[str]  (subset of ["parking","garden","pool"]),
    near_schools: true|false|Null,
    near_transit: true|false|Null
  }
- follow_up: str
- finalize: bool
Rules:
- Use Null for missing fields.
- If user gives "800-1200", set price_min=800, price_max=1200.
- If user gives "up to 1200", set price_max=1200.
- If user says "near schools/transit", set corresponding boolean true.
Return JSON only.
""".strip()

@dataclass
class Filters:
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    property_type: Optional[str] = None
    bedrooms_min: Optional[int] = None
    amenities: Optional[List[str]] = None
    near_schools: Optional[bool] = None
    near_transit: Optional[bool] = None

    def normalized(self):
        f = asdict(self)
        if f["city"]:
            f["city"] = f["city"].strip().title()
        if f["neighborhood"]:
            f["neighborhood"] = f["neighborhood"].strip()
        if f["property_type"]:
            f["property_type"] = f["property_type"].lower()
        if f["amenities"]:
            f["amenities"] = [a for a in f["amenities"] if a in ["parking","garden","pool"]]
        return f

# --- Regex fallback parser ---
CITY_WORDS = {"tbilisi":"Tbilisi","batumi":"Batumi","kutaisi":"Kutaisi","yerevan":"Yerevan","baku":"Baku"}
TYPE_WORDS = {"apartment":"apartment","flat":"apartment","house":"house","condo":"condo"}
AMENITY_WORDS = {"parking":"parking","garden":"garden","yard":"garden","pool":"pool"}

def cheap_local_parse(user_text: str) -> Dict[str, Any]:
    txt = user_text.lower()
    price_min = price_max = None
    m = re.search(r'(\d{3,5})\s*[-to]+\s*(\d{3,5})', txt)
    if m:
        a,b = int(m.group(1)), int(m.group(2))
        price_min, price_max = min(a,b), max(a,b)
    else:
        m2 = re.search(r'\b(\d{3,5})\b', txt)
        if m2:
            price_max = int(m2.group(1))

    bedrooms_min = None
    m3 = re.search(r'(\d)\s*(bed|br|bedroom)s?', txt)
    if m3:
        bedrooms_min = int(m3.group(1))

    city = next((c for w,c in CITY_WORDS.items() if w in txt), None)
    ptype = next((t for w,t in TYPE_WORDS.items() if re.search(r'\b'+re.escape(w)+r's?\b',txt)), None)
    amenities = [a for w,a in AMENITY_WORDS.items() if w in txt]
    near_schools = True if "school" in txt else None
    near_transit = True if any(k in txt for k in ["metro","bus","subway"]) else None

    follow_up = ""
    needed = []
    if not city: needed.append("city")
    if bedrooms_min is None: needed.append("bedrooms")
    if price_min is None and price_max is None: needed.append("budget")
    if needed:
        follow_up = "Could you share your " + ", ".join(needed) + "?"
    finalize = not needed

    return {"filters":{
        "city":city,"neighborhood":None,"price_min":price_min,"price_max":price_max,
        "property_type":ptype,"bedrooms_min":bedrooms_min,"amenities":amenities,
        "near_schools":near_schools,"near_transit":near_transit},
        "follow_up":follow_up,"finalize":finalize}

def call_llm(messages: List[Dict[str,str]]) -> Dict[str, Any]:
    if USE_OLLAMA and ollama_client is not None:
        try:
            convo = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages[-6:])
            res = ollama_client.generate(
                model=OLLAMA_MODEL,
                prompt=f"{SYSTEM_PROMPT}\n\nCONVERSATION:\n{convo}\n\nReturn JSON now.",
                options={"temperature":0.1}
            )
            raw = res.get("response","").strip()
            if raw.startswith("```"):
                raw = "\n".join(l for l in raw.splitlines() if not l.startswith("```") and not "json" in l)
            data = json.loads(raw)
            if "filters" in data:
                return data
        except Exception:
            pass
    return cheap_local_parse(messages[-1]["content"])

def filter_rank(df: pd.DataFrame, f: Filters) -> pd.DataFrame:
    d = f.normalized()
    out = df.copy()
    if d["city"]:
        out = out[out["city"].str.lower() == d["city"].lower()]
    if d["neighborhood"]:
        out = out[out["neighborhood"].str.lower() == d["neighborhood"].lower()]
    if d["property_type"]:
        out = out[out["type"] == d["property_type"]]
    if d["bedrooms_min"]:
        out = out[out["bedrooms"] >= int(d["bedrooms_min"])]
    if d["price_min"]:
        out = out[out["price"] >= int(d["price_min"])]
    if d["price_max"]:
        out = out[out["price"] <= int(d["price_max"])]
    if d["amenities"]:
        for a in d["amenities"]:
            out = out[out[a] == True]
    if d["near_schools"] is True:
        out = out[out["near_schools"] == True]
    if d["near_transit"] is True:
        out = out[out["near_transit"] == True]

    if out.empty: return out
    out["score"] = 0
    if d["bedrooms_min"]:
        out["score"] += (out["bedrooms"] - d["bedrooms_min"]).clip(lower=0)*0.2
    target = d["price_max"] or d["price_min"]
    if target:
        out["score"] -= abs(out["price"]-target)/1000
    return out.sort_values(["score","price"], ascending=[False,True])
