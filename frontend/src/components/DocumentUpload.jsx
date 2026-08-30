import { useState } from "react";
import { API_BASE_URL } from "../config";
function DocumentUpload({ onUploadComplete }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState("");

  async function uploadDocument(event) {
    event.preventDefault();

    if (!selectedFile) {
      setUploadError("Please select a PDF file.");
      return;
    }

    setUploading(true);
    setUploadError("");
    setUploadResult(null);
    

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(
  `${API_BASE_URL}/documents/upload`,
  {
    method: "POST",
    body: formData,
  }
);

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "The upload failed.");
      }

      setUploadResult(data);
      onUploadComplete();
    } catch (error) {
      setUploadError(error.message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <section>
      <h2>Upload a financial document</h2>

      <form onSubmit={uploadDocument}>
        <input
          type="file"
          accept="application/pdf"
          onChange={(event) => {
            setSelectedFile(event.target.files[0]);
            setUploadError("");
          }}
        />

        <button type="submit" disabled={uploading}>
          {uploading ? "Processing PDF..." : "Upload PDF"}
        </button>
      </form>

      {uploadError && <p>{uploadError}</p>}

      {uploadResult && (
        <div>
          <h3>Upload complete</h3>
          <p>Filename: {uploadResult.filename}</p>
          <p>Document ID: {uploadResult.document_id}</p>
          <p>Total pages: {uploadResult.total_pages}</p>
          <p>Total chunks: {uploadResult.total_chunks}</p>
        </div>
      )}
    </section>
  );
}

export default DocumentUpload;