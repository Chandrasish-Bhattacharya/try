import React, { useState } from "react";
import axios from "axios";

export default function App() {
  const [pdfFile, setPdfFile] = useState(null);
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);

  const uploadPdf = async () => {
    if (!pdfFile) return alert("Please select a PDF first.");
    const formData = new FormData();
    formData.append("file", pdfFile);
    await axios.post("http://localhost:8000/upload-pdf/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    alert("PDF uploaded successfully!");
  };

  const processQuery = async () => {
    if (!query) return alert("Please enter a query.");
    const res = await axios.post("http://localhost:8000/process-query/", {
      user_text: query,
    });
    setResult(res.data);
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>Insurance Policy QA</h1>
      <input type="file" accept="application/pdf" onChange={(e) => setPdfFile(e.target.files[0])} />
      <button onClick={uploadPdf}>Upload PDF</button>

      <textarea
        placeholder="Enter your query..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        style={{ width: "100%", height: 100, marginTop: 10 }}
      />
      <button onClick={processQuery}>Submit Query</button>

      {result && (
        <div style={{ marginTop: 20 }}>
          <h3>Decision: {result.decision}</h3>
          <p>{result.justification}</p>
          <h4>Policy Clauses:</h4>
          <ul>
            {result.policy_clauses.map((clause, i) => (
              <li key={i}>{clause}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
