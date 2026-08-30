import { useState } from "react";
import "./App.css";

import AskDocument from "./components/AskDocument";
import DocumentList from "./components/DocumentList";
import DocumentUpload from "./components/DocumentUpload";
import GrowthCalculator from "./components/GrowthCalculator";
import HealthStatus from "./components/HealthStatus";

function App() {
  const [documentRefreshKey, setDocumentRefreshKey] = useState(0);
  const [selectedDocument, setSelectedDocument] = useState(null);

  function handleUploadComplete() {
    setDocumentRefreshKey((currentKey) => currentKey + 1);
  }

  function handleDocumentDeleted(deletedDocumentId) {
    setSelectedDocument((currentDocument) => {
      if (currentDocument?.document_id === deletedDocumentId) {
        return null;
      }

      return currentDocument;
    });

    setDocumentRefreshKey((currentKey) => currentKey + 1);
  }

  return (
    <main>
      <header className="app-header">
        <div className="hero-content">
          <p className="eyebrow">Local document intelligence</p>

          <h1>FinMind AI</h1>

          <p className="app-description">
            Analyse financial reports privately with local AI.
          </p>

          <div className="feature-badges">
            <span>100% local</span>
            <span>Source citations</span>
            <span>Verified calculations</span>
          </div>
        </div>

        <div className="privacy-badge">
          <span className="privacy-dot" />
          Private and local
        </div>
      </header>

      <HealthStatus />

      <div className="dashboard">
        <aside className="sidebar">
          <DocumentUpload
            onUploadComplete={handleUploadComplete}
          />

          <DocumentList
            refreshKey={documentRefreshKey}
            selectedDocument={selectedDocument}
            onSelectDocument={setSelectedDocument}
            onDocumentDeleted={handleDocumentDeleted}
          />
        </aside>

        <div className="workspace">
          <div className="selected-document">
            <span>Active document</span>

            <strong>
              {selectedDocument
                ? selectedDocument.filename
                : "No document selected"}
            </strong>
          </div>

          <AskDocument selectedDocument={selectedDocument} />

          <GrowthCalculator selectedDocument={selectedDocument} />
        </div>
      </div>

      <footer className="app-footer">
        <p>
          FinMind AI · Local RAG · FastAPI · React · Ollama ·
          Qdrant
        </p>
      </footer>
    </main>
  );
}

export default App;