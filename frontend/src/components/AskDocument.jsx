import { useState } from "react";

function AskDocument({ selectedDocument }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");

  async function askQuestion(event) {
    event.preventDefault();

    if (!selectedDocument) {
      setError("Please select a document first.");
      return;
    }

    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }

    setAsking(true);
    setError("");
    setAnswer("");
    setSources([]);

    try {
      const response = await fetch(
        "http://localhost:8000/documents/ask",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            document_id: selectedDocument.document_id,
            question: question,
            limit: 5,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not answer the question.");
      }

      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch (error) {
      setError(error.message);
    } finally {
      setAsking(false);
    }
  }

  return (
    <section>
      <h2>Ask your document</h2>

      {!selectedDocument && (
        <p>Select a document above before asking a question.</p>
      )}

      {selectedDocument && (
        <p>
          Asking: <strong>{selectedDocument.filename}</strong>
        </p>
      )}

      <form onSubmit={askQuestion}>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="For example: How much did total net sales grow?"
          rows="4"
          disabled={!selectedDocument || asking}
        />

        <button
          type="submit"
          disabled={!selectedDocument || asking}
        >
          {asking ? "Thinking..." : "Ask FinMind"}
        </button>
      </form>

      {error && <p>{error}</p>}

      {answer && (
        <div>
          <h3>Answer</h3>
          <p>{answer}</p>

          <h3>Sources</h3>

          {sources.map((source, index) => (
            <p key={`${source.page_number}-${index}`}>
              Page {source.page_number} — {source.source}
            </p>
          ))}
        </div>
      )}
    </section>
  );
}

export default AskDocument;