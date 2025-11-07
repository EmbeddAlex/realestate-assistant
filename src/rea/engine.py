import os
import json
import pandas as pd
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ---- Offline LLM via Ollama ----
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct-q4_K_M")
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
    transaction_type: "rent"|"buy"|Null,
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
- If user mentions rent/lease/monthly, set transaction_type="rent".
- If user mentions buy/purchase/for sale/mortgage, set transaction_type="buy".
Return JSON only.
""".strip()


@dataclass
class Filters:
    city: Optional[str] = None
    neighborhood: Optional[str] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    property_type: Optional[str] = None
    transaction_type: Optional[str] = None
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
        if f.get("transaction_type"):
            f["transaction_type"] = f["transaction_type"].lower()
            if f["transaction_type"] not in ("rent", "buy"):
                f["transaction_type"] = None
        if f["amenities"]:
            f["amenities"] = [a for a in f["amenities"] if a in ["parking", "garden", "pool"]]
        return f


def call_llm(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    logger.info("Calling LLM...")
    if USE_OLLAMA and ollama_client is not None:
        try:
            convo = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages[-6:])
            res = ollama_client.generate(
                model=OLLAMA_MODEL,
                prompt=f"{SYSTEM_PROMPT}\n\nCONVERSATION:\n{convo}\n\nReturn JSON now.",
                options={
                    "temperature": 0.1
                },
                format="json"
            )
            raw = res.get("response", "").strip()
            data = json.loads(raw)
            if "filters" in data:
                logger.info("LLM returned valid response.")
                return data
        except Exception:
            logger.exception("LLM call failed.")
    logger.warning("Returning default response due to LLM failure.")
    # Return empty structured default if LLM fails
    return {
        "filters": {
            "city": None,
            "neighborhood": None,
            "price_min": None,
            "price_max": None,
            "property_type": None,
            "transaction_type": None,
            "bedrooms_min": None,
            "amenities": [],
            "near_schools": None,
            "near_transit": None
        },
        "follow_up": "Please share your city, budget, and minimum bedrooms.",
        "finalize": False
    }


def filter_rank(df: pd.DataFrame, f: Filters) -> pd.DataFrame:
    d = f.normalized()
    out = df.copy()
    if d["city"]:
        out = out[out["city"].str.lower() == d["city"].lower()]
    if d["neighborhood"]:
        out = out[out["neighborhood"].str.lower() == d["neighborhood"].lower()]
    if d["property_type"]:
        out = out[out["type"] == d["property_type"]]
    if d.get("transaction_type"):
        out = out[out["listing_type"] == d["transaction_type"]]
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
        out["score"] += (out["bedrooms"] - d["bedrooms_min"]).clip(lower=0) * 0.2
    target = d["price_max"] or d["price_min"]
    if target:
        out["score"] -= abs(out["price"] - target) / 1000
    return out.sort_values(["score", "price"], ascending=[False, True])
