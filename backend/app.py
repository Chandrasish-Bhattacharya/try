import os
import re
import tempfile
import spacy
import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

# ------------------------------
# 🔹 Firebase Initialization
# ------------------------------
cred = credentials.Certificate("firebase_service_key.json")  # Place your Firebase Admin SDK key in backend folder
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://finalyear-b4-default-rtdb.firebaseio.com/"
})

# ------------------------------
# 🔹 Flask App
# ------------------------------
app = Flask(__name__)
CORS(app)

# ------------------------------
# 🔹 Preload Models & Embeddings
# ------------------------------
nlp = spacy.load("en_core_web_sm")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = None  # will be loaded after PDF upload

# ------------------------------
# Known Data
# ------------------------------
known_procedures = [
    "knee surgery", "back surgery", "eye surgery", "heart surgery", "brain surgery",
    "neck surgery", "shoulder surgery", "hip replacement", "bypass surgery",
    "dental treatment", "appendix removal", "chemotherapy", "dialysis"
]
known_locations = [
    "pune", "delhi", "kolkata", "mumbai", "chennai", "bangalore", "hyderabad",
    "lucknow", "ahmedabad", "jaipur"
]

# ------------------------------
# 🔹 Query Parsing
# ------------------------------
def parse_query(text):
    text = text.lower()

    # Age
    age_match = re.search(r'aged\s+(\d+)|(\d+)[-\s]?year[-\s]?old', text)
    age = next((g for g in age_match.groups() if g), "N/A") if age_match else "N/A"

    # Gender
    if re.search(r'\b(female|wife|mother|she|f\b)\b', text):
        gender = "female"
    elif re.search(r'\b(male|husband|father|he|m\b)\b', text):
        gender = "male"
    else:
        gender = "N/A"

    # Procedure
    procedure = "N/A"
    for proc in known_procedures:
        if proc in text:
            procedure = proc
            break
    if procedure == "N/A":
        match = re.search(r'(knee|eye|back|heart|brain|neck|hip|shoulder|lung|spine|liver|skin)\s+(surgery|treatment)', text)
        if match:
            procedure = f"{match.group(1)} {match.group(2)}"

    # Location
    location = "N/A"
    for loc in known_locations:
        if loc in text:
            location = loc.capitalize()
            break

    # Policy Duration
    duration_match = re.search(r'(\d+)\s*(months|month|years|year)', text)
    policy_duration = f"{duration_match.group(1)} {duration_match.group(2)}" if duration_match else "N/A"

    return {
        "age": age,
        "gender": gender,
        "procedure": procedure,
        "location": location,
        "policy_duration": policy_duration
    }

# ------------------------------
# 🔹 Decision Logic
# ------------------------------
def evaluate_decision(parsed_query):
    try:
        months = int(re.search(r'\d+', parsed_query["policy_duration"]).group())
        if "year" in parsed_query["policy_duration"].lower():
            months *= 12
    except:
        months = 0

    if "surgery" in parsed_query['procedure'].lower() and months < 24:
        return {
            "Decision": "Rejected",
            "Justification": f"{parsed_query['procedure'].capitalize()} is subject to a 24-month waiting period."
        }
    return {
        "Decision": "Approved",
        "Justification": f"{parsed_query['procedure'].capitalize()} is covered under the policy."
    }

# ------------------------------
# 🔹 Load PDF and Create FAISS Index
# ------------------------------
@app.route("/upload", methods=["POST"])
def upload_pdf():
    global vectorstore
    file = request.files["file"]
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    temp_path = os.path.join(tempfile.gettempdir(), file.filename)
    file.save(temp_path)

    loader = PyPDFLoader(temp_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = splitter.split_documents(documents)

    vectorstore = FAISS.from_documents(split_docs, embeddings)
    vectorstore.save_local("faiss_index")

    return jsonify({"message": "PDF uploaded and indexed successfully"})

# ------------------------------
# 🔹 Process Query
# ------------------------------
@app.route("/query", methods=["POST"])
def query_policy():
    global vectorstore
    if vectorstore is None:
        return jsonify({"error": "No policy uploaded"}), 400

    data = request.get_json()
    user_text = data.get("query", "")

    parsed = parse_query(user_text)
    decision = evaluate_decision(parsed)
    clauses = [doc.page_content for doc in vectorstore.similarity_search(parsed["procedure"], k=2)]

    # Save to Firebase
    ref = db.reference("/insurance_queries")
    ref.push({
        "query": user_text,
        "parsed_info": parsed,
        "decision": decision["Decision"],
        "justification": decision["Justification"],
        "clauses": clauses
    })

    return jsonify({
        "parsed_info": parsed,
        "decision": decision["Decision"],
        "justification": decision["Justification"],
        "policy_clauses": clauses
    })

# ------------------------------
# 🔹 Run Server
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)
