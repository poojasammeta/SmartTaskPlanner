import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [goal, setGoal] = useState("");
  const [plan, setPlan] = useState("");
  const [loading, setLoading] = useState(false);

  const generatePlan = async () => {
    if (!goal.trim()) return alert("Please enter a goal!");
    setLoading(true);
    setPlan("");

    try {
      const res = await axios.post("http://127.0.0.1:5000/generate-plan", {
        goal,
      });
      setPlan(res.data.plan || res.data.error);
    } catch (err) {
      setPlan("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h1>🧠 AI Smart Task Planner</h1>
      <textarea
        value={goal}
        onChange={(e) => setGoal(e.target.value)}
        placeholder="Enter your goal here..."
        rows="3"
      ></textarea>
      <button onClick={generatePlan} disabled={loading}>
        {loading ? "Generating..." : "Generate Plan"}
      </button>

      {plan && <div className="plan-output">{plan}</div>}
    </div>
  );
}

export default App;
