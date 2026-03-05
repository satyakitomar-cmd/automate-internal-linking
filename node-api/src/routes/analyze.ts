import { Router, Request, Response } from "express";
import { submitAnalysis } from "../services/pipeline";
import { AnalyzeRequest } from "../types";

const router = Router();

router.post("/", async (req: Request, res: Response) => {
  const body = req.body as AnalyzeRequest;

  if (!body.urls || !Array.isArray(body.urls) || body.urls.length < 2) {
    res.status(400).json({
      error: "Request must include 'urls' array with at least 2 URLs.",
    });
    return;
  }

  if (body.urls.length > 500) {
    res.status(400).json({
      error: "Maximum 500 URLs per request.",
    });
    return;
  }

  try {
    const job = await submitAnalysis(body);
    res.status(202).json(job);
  } catch (err) {
    res.status(502).json({
      error: "Failed to reach Python engine.",
      detail: String(err),
    });
  }
});

export default router;
