import { useEffect, useState } from "react";

function DocumentList({
  refreshKey,
  selectedDocument,
  onSelectDocument,
}) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDocuments() {
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/documents");
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not load documents.");
      }

      setDocuments(data.documents || []);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
  loadDocuments();
}, [refreshKey]);

  return (
    <section>
      <h2>Uploaded documents</h2>

      <button type="button" onClick={loadDocuments} disabled={loading}>
        {loading ? "Loading..." : "Refresh documents"}
      </button>

      {error && <p>{error}</p>}

      {!loading && !error && documents.length === 0 && (
        <p>No documents have been uploaded yet.</p>
      )}

      {documents.map((document) => (
       <article key={document.document_id}>
  <h3>{document.filename}</h3>
  <p>Document ID: {document.document_id}</p>
  <p>Total pages: {document.total_pages}</p>
  <p>Total chunks: {document.chunk_count}</p>

  <button
    type="button"
    onClick={() => onSelectDocument(document)}
    disabled={
      selectedDocument?.document_id === document.document_id
    }
  >
    {selectedDocument?.document_id === document.document_id
      ? "Selected"
      : "Select document"}
  </button>
</article>
      ))}
    </section>
  );
}

export default DocumentList;