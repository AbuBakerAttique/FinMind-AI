import { useState } from "react";
import { API_BASE_URL } from "../config";
function GrowthCalculator({ selectedDocument }) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [calculating, setCalculating] = useState(false);
  const [error, setError] = useState("");

  async function calculateGrowth(event) {
    event.preventDefault();

    if (!selectedDocument) {
      setError("Please select a document first.");
      return;
    }

    if (!question.trim()) {
      setError("Please enter a growth question.");
      return;
    }

    setCalculating(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
  `${API_BASE_URL}/documents/calculate-growth`,
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
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Could not calculate growth."
        );
      }

      setResult(data);
    } catch (error) {
      setError(error.message);
    } finally {
      setCalculating(false);
    }
  }

  return (
    <section>
      <h2>Verified Growth Calculator</h2>

      {!selectedDocument && (
        <p>Select a financial document before calculating growth.</p>
      )}

      {selectedDocument && (
        <p>
          Calculating from:{" "}
          <strong>{selectedDocument.filename}</strong>
        </p>
      )}

      <form onSubmit={calculateGrowth}>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Example: How much did total net sales grow from 2024 to 2025?"
          rows="4"
          disabled={!selectedDocument || calculating}
        />

        <button
          type="submit"
          disabled={!selectedDocument || calculating}
        >
          {calculating ? "Calculating..." : "Calculate growth"}
        </button>
      </form>

      {error && <p>{error}</p>}

      {result && (
        <div>
          <h3>Verified result</h3>

          <p>Metric: {result.metric}</p>
          <p>
            Previous period: {result.previous_period}
          </p>
          <p>
            Current period: {result.current_period}
          </p>
          <p>Unit: {result.unit}</p>

          <h4>Calculation</h4>

          <p>
            Previous value:{" "}
            {result.calculation.previous_value}
          </p>

          <p>
            Current value:{" "}
            {result.calculation.current_value}
          </p>

          <p>
            Absolute change:{" "}
            {result.calculation.absolute_change}
          </p>

          <p>
            Percentage change:{" "}
            <strong>
              {result.calculation.percentage_change}%
            </strong>
          </p>

          <p>Formula: {result.formula}</p>

          <p>
            Citation: Page {result.citation.page_number}
          </p>
        </div>
      )}
    </section>
  );
}

export default GrowthCalculator;