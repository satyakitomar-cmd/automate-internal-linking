import express from "express";
import cors from "cors";
import path from "path";
import analyzeRouter from "./routes/analyze";
import resultsRouter from "./routes/results";
import healthRouter from "./routes/health";

const app = express();
const PORT = parseInt(process.env.PORT || "3000", 10);

app.use(cors());
app.use(express.json({ limit: "1mb" }));

// API Routes
app.use("/api/health", healthRouter);
app.use("/api/analyze", analyzeRouter);
app.use("/api/results", resultsRouter);

// Serve frontend static build in production
const frontendDist = path.join(__dirname, "../../frontend/dist");
app.use(express.static(frontendDist));

// SPA fallback: serve index.html for non-API routes
app.get("*", (req, res) => {
  if (!req.path.startsWith("/api")) {
    res.sendFile(path.join(frontendDist, "index.html"));
  }
});

app.listen(PORT, () => {
  console.log(`[Node API] Internal Linker API running on http://localhost:${PORT}`);
  console.log(`[Node API] Python engine expected at ${process.env.PYTHON_API_URL || "http://localhost:8000"}`);
});

export default app;
