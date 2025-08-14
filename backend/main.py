import os
import re
import spacy
import tempfile
import firebase_admin
from firebase_admin import credentials, db
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel
from typing import List
import uvicorn

FAISS_INDEX_PATH = "faiss_index"
KNOWN_PROCEDURES = [
    "knee surgery", "back surgery", "eye surgery", "heart surgery", "brain surgery",
    "neck surgery", "shoulder surgery", "hip replacement", "bypass surgery",
    "dental treatment", "appendix removal", "chemotherapy", "dialysis"
]
KNOWN_LOCATIONS = [
    "pune", "delhi", "kolkata", "mumbai", "chennai", "bangalore", "hyderabad",
    "lucknow", "ahmedabad", "jaipur"
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

nlp = spacy.load("en_core_web_sm")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://finalyear-b4-default-rtdb.firebaseio.com/'
    })

def load_vector_store():
    return FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)

def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_documents(documents)

def parse_query(text: str):
    text = text.lower()
    age_match = re.search(r'aged\s+(\d+)|(\d+)[-\s]?year[-\s]?old|^(\d+)\s*[fm]\b|(\d+)\s*[fm]\b', text)
    age = next((g for g in age_match.groups() if g), "N/A") if age_match else "N/A"
    if re.search(r'\b(female|wife|mother|she|f\b)\b', text):
        gender = "female"
    elif re.search(r'\b(male|husband|father|he|m\b)\b', text):
        gender = "male"
    else:
        gender = "N/A"
    procedure = "N/A"
    for proc in KNOWN_PROCEDURES:
        if proc in text:
            procedure = proc
            break
    if procedure == "N/A":
        match = re.search(r'(knee|eye|back|heart|brain|neck|hip|shoulder|lung|spine|liver|skin)\s+(surgery|treatment)', text)
        if match:
            procedure = f"{match.group(1)} {match.group(2)}"
    location = "N/A"
    for loc in KNOWN_LOCATIONS:
        if loc in text:
            location = loc.capitalize()
            break
    if location == "N/A":
        loc_match = re.search(r"(in|from)\s+([a-z]+)", text)
        if loc_match:
            location = loc_match.group(2).capitalize()
    duration_match = re.search(r'(\d+)\s*(months|month|years|year)', text)
    policy_duration = f"{duration_match.group(1)} {duration_match.group(2)}" if duration_match else "N/A"
    return {
        "age": age, "gender": gender,
        "procedure": procedure, "location": location,
        "policy_duration": policy_duration
    }

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

def retrieve_clauses(query, k=2):
    vectorstore = load_vector_store()
    matches = vectorstore.similarity_search(query, k=k)
    return [doc.page_content.strip() for doc in matches]

class QueryRequest(BaseModel):
    user_text: str

class QueryResponse(BaseModel):
    parsed_info: dict
    decision: str
    justification: str
    policy_clauses: List[str]

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    tmp_path = tempfile.mktemp(suffix=".pdf")
    with open(tmp_path, "wb") as f:
        f.write(await file.read())
    loader = PyPDFLoader(tmp_path)
    documents = loader.load()
    chunks = split_documents(documents)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(FAISS_INDEX_PATH)
    return {"message": "PDF processed and indexed successfully."}

@app.post("/process-query/", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    parsed = parse_query(request.user_text)
    decision = evaluate_decision(parsed)
    clauses = retrieve_clauses(parsed["procedure"] or "surgery")
    ref = db.reference("/queries").push()
    ref.set({
        "input": request.user_text,
        "parsed": parsed,
        "decision": decision["Decision"],
        "justification": decision["Justification"]
    })
    return QueryResponse(
        parsed_info=parsed,
        decision=decision["Decision"],
        justification=decision["Justification"],
        policy_clauses=clauses
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
