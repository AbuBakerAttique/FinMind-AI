import { useEffect, useState } from "react";
import { API_BASE_URL } from "../config";
async function fetchDocuments() {
  const response = await fetch(`${API_BASE_URL}/documents`);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Could not load documents.");
  }

  return data.documents || [];
}

function DocumentList({
  refreshKey,
  selectedDocument,
  onSelectDocument,
  onDocumentDeleted,
}) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingDocumentId, setDeletingDocumentId] = useState(null);

  async function loadDocuments() {
    setLoading(true);
    setError("");

    try {
      const loadedDocuments = await fetchDocuments();
      setDocuments(loadedDocuments);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function refreshDocuments() {
      try {
        const loadedDocuments = await fetchDocuments();

        if (!cancelled) {
          setDocuments(loadedDocuments);
          setError("");
        }
      } catch (error) {
        if (!cancelled) {
          setError(error.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    refreshDocuments();

    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  async function deleteDocument(document) {
    const confirmed = window.confirm(
      `Delete "${document.filename}"?\n\nThis will remove its chunks and vectors from Qdrant.`
    );

    if (!confirmed) {
      return;
    }

    setDeletingDocumentId(document.document_id);
    setError("");

    try {
      const response = await fetch(
  `${API_BASE_URL}/documents/${document.document_id}`,
  {
    method: "DELETE",
  }
);

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Could not delete document."
        );
      }

      onDocumentDeleted(document.document_id);
    } catch (error) {
      setError(error.message);
    } finally {
      setDeletingDocumentId(null);
    }
  }

  return (
    <section>
      <h2>Uploaded documents</h2>

      <button
        type="button"
        onClick={loadDocuments}
        disabled={loading}
      >
        {loading ? "Loading..." : "Refresh documents"}
      </button>

      {error && <p>{error}</p>}

      {!loading && !error && documents.length === 0 && (
        <p>No documents have been uploaded yet.</p>
      )}

      {documents.map((document) => {
        const isSelected =
          selectedDocument?.document_id === document.document_id;

        const isDeleting =
          deletingDocumentId === document.document_id;

        return (
          <article key={document.document_id}>
            <h3>{document.filename}</h3>

            <p>Document ID: {document.document_id}</p>
            <p>Total pages: {document.total_pages}</p>
            <p>Total chunks: {document.chunk_count}</p>

            <button
              type="button"
              onClick={() => onSelectDocument(document)}
              disabled={isSelected || isDeleting}
            >
              {isSelected ? "Selected" : "Select document"}
            </button>

            <button
              type="button"
              onClick={() => deleteDocument(document)}
              disabled={isDeleting}
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </button>
          </article>
        );
      })}
    </section>
  );
}

export default DocumentList;