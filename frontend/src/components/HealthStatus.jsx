import { useEffect, useState } from "react";

function HealthStatus() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function checkBackend() {
      try {
        const response = await fetch("http://localhost:8000/health");

        if (!response.ok) {
          throw new Error("The backend returned an error.");
        }

        const data = await response.json();
        setHealth(data);
      } catch (error) {
        setError(error.message);
      }
    }

    checkBackend();
  }, []);

  return (
    <section>
      <h2>System status</h2>

      {!health && !error && <p>Checking services...</p>}
      {error && <p>Backend unavailable: {error}</p>}

      {health && (
        <ul>
          <li>API: {health.services.api}</li>
          <li>Qdrant: {health.services.qdrant}</li>
          <li>Ollama: {health.services.ollama}</li>
        </ul>
      )}
    </section>
  );
}

export default HealthStatus;