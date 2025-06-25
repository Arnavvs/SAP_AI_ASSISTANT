from flask import Flask, request, jsonify
import openai
import requests
import json
import os
import re
import traceback
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# --- Security Enhancements ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SAP_AUTH = (os.getenv("SAP_USER"), os.getenv("SAP_PASS"))

limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

# --- CDS View Field Guide ---
CDS_FIELD_GUIDE = {
    "GWSAMPLE_BASIC": {
        "CompanyField": "CompanyName",
        "CountryField": "Country",
        "CityField": "Address/City",
        "Currency": "CurrencyCode"
    }
}


# --- Prompt Template ---
PROMPT_TEMPLATE = """
You are an SAP Query Interpreter.
Given a vague or confusing user request, your job is to:
1. Understand what the user really wants.
2. Identify the correct OData entity and filters from SAP ES5 system.
3. Return strictly valid JSON in this format:
{{
  "views": [
    {{ "view": "GWSAMPLE_BASIC", "entity": "BusinessPartnerSet", "filter": "$filter=Country eq 'DE'" }}
  ],
  "interpretation": "Explain what the query returns in plain language",
  "suggestion": "Suggest how the user could refine their query"
}}

Only use the following entity set and fields from the GWSAMPLE_BASIC OData service:
- Entity: BusinessPartnerSet
- Fields: CompanyName, BusinessPartnerID, CurrencyCode, EmailAddress, Country, Address/City

User query: {query}
"""


def fetch_sap_view(view, entity, odata_filter):
    url = f"https://sapes5.sapdevcenter.com/sap/opu/odata/IWBEP/{view}/{entity}?{odata_filter}"
    print(f"[SAP CALL] GET {url}")

    try:
        response = requests.get(
            url,
            auth=SAP_AUTH,
            headers={"Accept": "application/json"}
        )
        print(f"[SAP STATUS] {response.status_code}")
        print("[SAP RAW TEXT]")
        print(response.text[:1000])  # only print first 1000 chars

        json_data = response.json()
        return json_data.get("d", {}).get("results", [])
    except Exception as e:
        print("[SAP REQUEST ERROR]")
        print(str(e))
        return []



@app.route("/ask", methods=["POST"])
@limiter.limit("10/minute")
def ask():
    data = request.json
    user_query = data.get("user_query", "")

    field_guide_json = json.dumps(CDS_FIELD_GUIDE)
    prompt = PROMPT_TEMPLATE.format(query=user_query, field_guide=field_guide_json)

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful SAP expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        raw_output = response.choices[0].message.content.strip()
        print("[GPT RESPONSE RAW]\n", raw_output)

        match = re.search(r"{.*}", raw_output, re.DOTALL)
        if not match:
            raise ValueError("No valid JSON object found in GPT response.")

        result = json.loads(match.group(0))

    except Exception as e:
        print("[GPT ERROR TRACEBACK]")
        traceback.print_exc()
        return jsonify({"error": "GPT response parsing failed", "details": str(e)}), 500

    views = result.get("views", [])
    interpretation = result.get("interpretation", "")
    suggestion = result.get("suggestion", "")

    sap_data_grouped = {}
    errors = {}

    def flatten_entry(entry):
        flat = {}
        for k, v in entry.items():
            if isinstance(v, dict):
                for subk, subv in v.items():
                    flat[f"{k}/{subk}"] = subv
            else:
                flat[k] = v
        return flat

    for view_def in views:
        try:
            view = view_def["view"]
            entity = view_def["entity"]
            odata_filter = view_def["filter"]
            data = fetch_sap_view(view, entity, odata_filter)
            print(f"[SAP RAW DATA for {view}]")
            print(json.dumps(data, indent=2))

            sap_data_grouped[view] = [flatten_entry(e) for e in data]

        except Exception as e:
            errors[view] = str(e)
            sap_data_grouped[view] = []

    return jsonify({
        "data": sap_data_grouped,
        "interpretation": interpretation,
        "suggestion": suggestion,
        "errors": errors
    })

if __name__ == "__main__":
    app.run(debug=True)
