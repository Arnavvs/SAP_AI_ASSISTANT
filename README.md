# SAP_AI_ASSISTANT
📊 SAP Fiori AI Query Assistant
An AI-powered frontend and backend system that mimics querying live SAP data using natural language. Users can ask questions like:

“Show vendors from Germany with high dues”
“Give top 5 business partners from US”

This assistant uses OpenAI GPT to interpret vague queries and simulate OData-based SAP responses.

🔧 How It Works
Component	Role
fiori.html	SAPUI5 + ag-Grid frontend (Fiori-style)
sapaiquesrybackend.py	Flask backend that connects GPT with SAP OData
GPT (OpenAI)	Translates natural queries into OData-style filters
SAP ES5	Public test system used for demo data (no real finance data)

⚙️ Current Features
Natural language query input (AI-powered)

Dynamic table rendering using ag-Grid

Filter simulation using $filter OData parameters

Plain-English AI interpretation and suggestions

🛠 Prerequisites
Python 3.7+

Flask (pip install flask flask-cors flask-limiter openai)

SAPUI5 frontend runs in any browser

An OpenAI API key (OPENAI_API_KEY in .env or environment)

🔌 Plug In Your Own SAP System
This project currently uses SAP ES5, a public sandbox from SAP with fake demo data. It does not support finance, payments, or custom views.

To make this production-ready:

Plug in your own SAP backend URL

Add real CDS views (e.g., ZVENDOROPEN, ZPURCHASEORDERS)

Replace the fetch_sap_view() logic with your actual OData service endpoints and authentication

(Optional) Enhance prompts to include metadata from your CDS views

🚀 Running the Project
Backend

bash
Copy
Edit
export OPENAI_API_KEY=your-key
python sapaiquesrybackend.py
Frontend
Just open fiori.html in Chrome

🧠 Sample Query Ideas
Top 5 business partners from US

Vendors who haven't paid

Orders above ₹1L from UP

Purchase orders from 2023

📎 Credits
Built using:

SAPUI5

ag-Grid (Community)

Flask + OpenAI

SAP ES5 (https://sapes5.sapdevcenter.com)
