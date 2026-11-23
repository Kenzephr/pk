"""Pokemon AI Price Checker — Stage 1.

No live market-price provider is connected. All demo prices are illustrative.
AI identification requires OPENAI_API_KEY and sends images to OpenAI.
"""
import base64
import io
import json
import os
import re
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Pokémon AI Price Checker", page_icon="🃏", layout="wide")

FIELDS = ["image_id", "card_name", "set_name", "card_number", "year", "language", "grading_company", "grade", "seller_price_usd", "market_value_usd", "market_source", "price_status"]
SAMPLE_CARDS = [
    {"card_name":"Galvantula ex", "set_name":"Stellar Crown", "card_number":"168/142", "year":"2024", "language":"English", "grading_company":"PSA", "grade":"10", "seller_price_usd":56.17, "market_value_usd":60.08},
    {"card_name":"Radiant Charizard", "set_name":"Crown Zenith", "card_number":"020/159", "year":"2023", "language":"English", "grading_company":"PSA", "grade":"9", "seller_price_usd":31.53, "market_value_usd":33.50},
    {"card_name":"Mew", "set_name":"Celebrations", "card_number":"011/025", "year":"2021", "language":"English", "grading_company":"PSA", "grade":"8", "seller_price_usd":14.85, "market_value_usd":15.75},
]

def empty_card(image_id=""):
    return {"image_id":image_id, "card_name":"", "set_name":"", "card_number":"", "year":"", "language":"", "grading_company":"", "grade":"", "seller_price_usd":None, "market_value_usd":None, "market_source":"Not provided", "price_status":"UNVERIFIED"}

def image_to_data_url(img):
    out = io.BytesIO()
    img.thumbnail((1800, 1800))
    img.convert("RGB").save(out, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(out.getvalue()).decode("ascii")

def detect_cards(img, api_key):
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    prompt = """Identify EVERY distinct graded Pokémon card visible in this image (including multi-card screenshots). Return ONLY valid JSON as an object with key 'cards', an array of objects. Each object has keys card_name, set_name, card_number, year, language, grading_company, grade, seller_price_usd. Read the exact label and card, and use null for unreadable values. Seller price is ONLY the seller's displayed asking price in USD (not a market valuation). If price is in SOL or another currency, set seller_price_usd to null. Never invent prices, grading details, or market values. Preserve cards left-to-right then top-to-bottom. Do not include market_value_usd."""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role":"user", "content":[{"type":"text","text":prompt}, {"type":"image_url","image_url":{"url":image_to_data_url(img)}}]}],
        response_format={"type":"json_object"},
        temperature=0,
    )
    parsed = json.loads(response.choices[0].message.content)
    cards = parsed.get("cards", [])
    if not isinstance(cards, list):
        raise ValueError("AI response did not contain a card list")
    return cards[:40]

def normalize(rows):
    clean = []
    for row in rows:
        c = empty_card(str(row.get("image_id") or ""))
        for k in FIELDS:
            if k in row and row[k] is not None:
                c[k] = row[k]
        for k in ["seller_price_usd", "market_value_usd"]:
            c[k] = pd.to_numeric(c[k], errors="coerce")
        clean.append(c)
    return pd.DataFrame(clean, columns=FIELDS)

if "cards" not in st.session_state:
    st.session_state.cards = normalize([])
if "images" not in st.session_state:
    st.session_state.images = {}

st.title("Pokémon AI Price Checker")
st.caption("Stage 1 • USD only • Image recognition + transparent price sources")
st.warning("No live pricing feed is connected. Demo prices are illustrative, and manually entered market values are UNVERIFIED until you confirm their source and date.")

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("OpenAI API key (optional)", value=os.getenv("OPENAI_API_KEY", ""), type="password", help="Needed only for AI card identification. Uploaded images are sent to OpenAI when you click Detect cards.")
    fee_pct = st.number_input("Selling fee (%)", 0.0, 100.0, 0.0, 0.5)
    extra_cost = st.number_input("Other costs per card (USD)", 0.0, 10000.0, 0.0, 0.5)
    st.caption("Prices and images remain in this browser session. No database or live price feed is configured.")

left, right = st.columns([2, 1])
with left:
    uploads = st.file_uploader("Upload graded card photos or multi-card screenshots", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
    if uploads:
        for upload in uploads:
            try:
                img = Image.open(upload).convert("RGB")
                st.session_state.images[upload.name] = img.copy()
            except Exception:
                st.error(f"Could not open {upload.name}")
        if st.button("Detect cards with AI", type="primary"):
            if not api_key:
                st.error("Enter an OpenAI API key in Settings to use AI detection. Manual and demo modes work without one.")
            else:
                detected = []
                for upload in uploads:
                    if upload.name not in st.session_state.images:
                        continue
                    try:
                        with st.spinner(f"Identifying cards in {upload.name}..."):
                            cards = detect_cards(st.session_state.images[upload.name].copy(), api_key)
                        for card in cards:
                            card["image_id"] = upload.name
                            card["market_value_usd"] = None
                            card["market_source"] = "Not provided"
                            card["price_status"] = "UNVERIFIED"
                            detected.append(card)
                    except Exception as exc:
                        st.error(f"Detection failed for {upload.name}: {exc}")
                if detected:
                    st.session_state.cards = normalize(detected)
                    st.success(f"Detected {len(detected)} card(s). Please verify every field below.")
with right:
    st.subheader("Quick start")
    if st.button("Load sample cards"):
        rows = []
        for sample in SAMPLE_CARDS:
            row = {**sample, "image_id":"DEMO — no uploaded photo", "market_source":"Illustrative demo value (NOT LIVE)", "price_status":"SAMPLE"}
            rows.append(row)
        st.session_state.cards = normalize(rows)
        st.rerun()
    if st.button("Add a card manually"):
        st.session_state.cards = pd.concat([st.session_state.cards, normalize([empty_card()])], ignore_index=True)
        st.rerun()
    if st.button("Clear cards"):
        st.session_state.cards = normalize([])
        st.session_state.images = {}
        st.rerun()

st.subheader("Review and edit cards")
st.caption("AI may misread small text, grades and prices. Check the slab label. Enter a market value only if you have researched it; record its source and date in Market source.")
column_config = {
    "seller_price_usd":st.column_config.NumberColumn("Seller price (USD)", min_value=0, format="$%.2f"),
    "market_value_usd":st.column_config.NumberColumn("Market reference (USD)", min_value=0, format="$%.2f"),
    "price_status":st.column_config.SelectboxColumn("Market data status", options=["UNVERIFIED", "SAMPLE", "MANUAL RESEARCH", "LIVE VERIFIED"]),
}
edited = st.data_editor(st.session_state.cards, num_rows="dynamic", use_container_width=True, hide_index=True, column_config=column_config, key="editor")
# Recalculate from current edited data; no automatic claims of live verification.
df = edited.copy()
for col in ["seller_price_usd", "market_value_usd"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
valid = df["seller_price_usd"].notna() & df["market_value_usd"].notna()
df["gross_profit_usd"] = (df["market_value_usd"] - df["seller_price_usd"]).where(valid)
df["estimated_net_profit_usd"] = (df["market_value_usd"] * (1 - fee_pct / 100) - df["seller_price_usd"] - extra_cost).where(valid)
df["gross_roi_pct"] = (100 * df["gross_profit_usd"] / df["seller_price_usd"].replace(0, float("nan"))).where(valid)

st.subheader("Results dashboard")
valid_rows = df.loc[valid]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Cards with both prices", f"{len(valid_rows)} / {len(df)}")
c2.metric("Total seller cost", f"${valid_rows['seller_price_usd'].sum():,.2f}")
c3.metric("Estimated market total", f"${valid_rows['market_value_usd'].sum():,.2f}")
c4.metric("Potential gross profit", f"${valid_rows['gross_profit_usd'].sum():,.2f}")
if valid_rows.empty:
    st.info("Add cards and enter seller + market prices to calculate profits. Market values are not fetched automatically in Stage 1.")
else:
    st.caption("Totals cover only cards with BOTH prices. They are not guaranteed sale proceeds. Net profit includes your chosen fees and other costs.")

cols = ["card_name", "card_number", "grading_company", "grade", "seller_price_usd", "market_value_usd", "gross_profit_usd", "estimated_net_profit_usd", "gross_roi_pct", "market_source", "price_status"]
st.dataframe(df[cols].sort_values("gross_profit_usd", ascending=False, na_position="last"), use_container_width=True, hide_index=True,
    column_config={k:st.column_config.NumberColumn(k.replace("_", " ").title(), format=("%.1f%%" if k=="gross_roi_pct" else "$%.2f")) for k in ["seller_price_usd", "market_value_usd", "gross_profit_usd", "estimated_net_profit_usd", "gross_roi_pct"]})

st.subheader("Card photos and individual results")
for idx, row in df.iterrows():
    title = f"{row.get('card_name') or 'Unidentified card'} — {row.get('grading_company') or 'Grade unknown'} {row.get('grade') or ''}"
    with st.expander(title, expanded=idx < 3):
        pic, details = st.columns([1, 2])
        with pic:
            if str(row.get("image_id")) in st.session_state.images:
                st.image(st.session_state.images[str(row["image_id"])], caption="Uploaded source image (may contain multiple cards)", use_container_width=True)
            else:
                st.caption("No uploaded image for this card")
        with details:
            st.write(f"**Set:** {row.get('set_name') or 'Unknown'} | **Number:** {row.get('card_number') or 'Unknown'}")
            st.write(f"**Seller:** {('$%.2f' % row['seller_price_usd']) if pd.notna(row['seller_price_usd']) else 'Unknown'}")
            st.write(f"**Market reference:** {('$%.2f' % row['market_value_usd']) if pd.notna(row['market_value_usd']) else 'NOT AVAILABLE'}")
            st.write(f"**Gross profit:** {('$%.2f' % row['gross_profit_usd']) if pd.notna(row['gross_profit_usd']) else 'Cannot calculate'}")
            st.write(f"**Source:** {row.get('market_source') or 'Not provided'}")
            st.write(f"**Status:** {row.get('price_status') or 'UNVERIFIED'}")

csv = df.to_csv(index=False).encode("utf-8-sig")
st.download_button("Download results as CSV", csv, file_name="pokemon_profit_results.csv", mime="text/csv")
st.caption(f"Dashboard generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}. This timestamp is NOT a market-price update time.")
