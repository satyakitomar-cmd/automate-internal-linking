import { Router, Request, Response } from "express";
import { healthCheck } from "../services/pipeline";

const router = Router();

router.get("/", async (_req: Request, res: Response) => {
  try {
    const pythonHealth = await healthCheck();
    res.json({
      status: "ok",
      node_api: "0.1.0",
      python_engine: pythonHealth,
    });
  } catch (err) {
    res.json({
      status: "degraded",
      node_api: "0.1.0",
      python_engine: { status: "unreachable", error: String(err) },
    });
  }
});

export default router;
