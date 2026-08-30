import "./App.css";
import DocumentUpload from "./components/DocumentUpload";
import HealthStatus from "./components/HealthStatus";

function App() {
  return (
    <main>
      <h1>FinMind AI</h1>
      <p>Local financial document intelligence</p>

      <HealthStatus />
      <DocumentUpload />
    </main>
  );
}

export default App;