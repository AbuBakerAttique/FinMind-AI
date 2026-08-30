import { useState } from "react";
import "./App.css";
import DocumentList from "./components/DocumentList";
import DocumentUpload from "./components/DocumentUpload";
import HealthStatus from "./components/HealthStatus";
import AskDocument from "./components/AskDocument";
function App() {
  const [documentRefreshKey, setDocumentRefreshKey] = useState(0);
  const [selectedDocument, setSelectedDocument] = useState(null);

  function handleUploadComplete() {
    setDocumentRefreshKey((currentKey) => currentKey + 1);
  }

  return (
    <main>
      <h1>FinMind AI</h1>
      <p>Local financial document intelligence</p>

      <HealthStatus />

      <DocumentUpload onUploadComplete={handleUploadComplete} />

      <DocumentList
        refreshKey={documentRefreshKey}
        selectedDocument={selectedDocument}
        onSelectDocument={setSelectedDocument}
      />

      {selectedDocument && (
        <p>
          Selected document:{" "}
          <strong>{selectedDocument.filename}</strong>
        </p>
      )}
      <AskDocument selectedDocument={selectedDocument} />
    </main>
  );
}

export default App;