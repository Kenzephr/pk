# Pokémon AI Price Checker — Stage 1

A Streamlit web app for identifying graded Pokémon cards in photos/screenshots, entering USD seller and market prices, and comparing resale profit.

## Setup (Windows PowerShell)

1. Install Python 3.11 or 3.12 from python.org.
2. Open PowerShell in this folder.
3. Run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, run `\.venv\Scripts\python.exe -m streamlit run app.py` instead.

## Optional AI detection

Set your OpenAI API key as an environment variable, or paste it into the app's sidebar (do not share it):

```powershell
$env:OPENAI_API_KEY="your_api_key_here"
streamlit run app.py
```

AI detection calls `gpt-4.1-mini` and requires an account with API access and available billing. It sends uploaded images to the model. Check and correct every detected field. The model is used for recognition, NOT pricing.

## Without an API key

Click **Load sample cards** to test illustrative data, or **Add a card manually**. Edit card names, seller prices, and market values in the table. For researched values, enter the source URL/date and set status to MANUAL RESEARCH.

## Pricing limitations

- **No live market data is fetched in Stage 1.**
- Demo market values are illustrative and labelled SAMPLE.
- AI never invents market values; it returns card identity and any visible USD asking price.
- No market value means no profit calculation for that card.
- Gross profit = market value − seller price.
- Estimated net profit = market value × (1 − selling fee %) − seller price − other costs per card.
- Always compare exact grade/company/edition and recent completed sales. CGC Pristine 10 is not the same as ordinary CGC 10.
- Images and results are session-only; download CSV before closing.
- Multi-card screenshots show the full source screenshot alongside each detected card, not automatically cropped individual cards.

## Stage 2 idea

Integrate a licensed/authorised pricing provider with exact card + grading-company/grade matching, completed-sales references, update timestamps, and low-confidence warnings. Never label a price LIVE VERIFIED without a real provider response.
