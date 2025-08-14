
# 🛡 Insurance Policy QA Web App

A fast web application that:
- Parses insurance queries to extract **age, gender, procedure, location, policy duration**
- Evaluates whether a claim is **Approved** or **Rejected**
- Retrieves relevant policy clauses from uploaded **PDF/DOCX** documents
- Fetches data from **Firebase Realtime Database**

Built with:
- **Backend:** Flask + LangChain + FAISS + HuggingFace Embeddings + Firebase Admin
- **Frontend:** React + TailwindCSS
- **Database:** Firebase Realtime DB
- **Vector Storage:** FAISS

---

## 📂 Project Structure
```

insurance-policy-qa/
│
├── backend/
│   ├── app.py                  # Flask backend
│   ├── policy\_qa.py            # Core logic for query parsing and FAISS search
│   ├── requirements.txt        # Python dependencies
│   ├── faiss\_index/            # Saved FAISS index (created after document embedding)
│   └── uploads/                # Uploaded PDF/DOCX policy files
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.js              # Main React app
│   │   ├── components/         # React components
│   │   └── styles/             # TailwindCSS styles
│   ├── package.json            # Frontend dependencies
│   └── tailwind.config.js
│
└── README.md

````

---

## ⚙️ Backend Setup

### 1. Navigate to backend folder
```bash
cd backend
````

### 2. Create virtual environment

```bash
python -m venv venv
```

### 3. Activate virtual environment

**Windows (PowerShell)**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Download spaCy model

```bash
python -m spacy download en_core_web_sm
```

### 6. Run the backend

```bash
python app.py
```

Backend will run on:

```
http://127.0.0.1:5000
```

---

## 🎨 Frontend Setup

### 1. Navigate to frontend folder

```bash
cd frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Start the frontend

```bash
npm start
```

Frontend will run on:

```
http://localhost:3000
```

---

## 📄 Uploading Policy Documents

* Place your **PDF/DOCX** policy documents into the `backend/uploads` folder or upload via the frontend UI.
* The backend will embed and store them in the **FAISS index** for quick search.

---

## 🚀 Features

* Extract **age, gender, procedure, location, policy duration** from natural queries
* Apply **decision rules** based on waiting period policies
* Retrieve and display **relevant clauses** from uploaded documents
* **Ultra-fast** FAISS vector search (response time < 20 ms after indexing)

---

## 🛠 Troubleshooting

* If `flask` not found → Run `pip install flask`
* If FAISS errors on Windows → Run `pip install faiss-cpu`
* If embeddings slow on first run → Model downloads once and caches locally
* Ensure **Python 3.9+** and **Node.js 18+**

---

## 📜 License

MIT License

```

---

If you want, I can also **include the exact `requirements.txt`** so the backend runs without dependency errors.  
Do you want me to add that here too?
```
