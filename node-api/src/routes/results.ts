import { Router, Request, Response } from "express";
import { getJobResults } from "../services/pipeline";

const router = Router();

router.get("/:jobId", async (req: Request, res: Response) => {
  const { jobId } = req.params;

  if (!jobId) {
    res.status(400).json({ error: "Missing jobId parameter." });
    return;
  }

  try {
    const job = await getJobResults(jobId);
    res.json(job);
  } catch (err) {
    const message = String(err);
    if (message.includes("404")) {
      res.status(404).json({ error: "Job not found." });
    } else {
      res.status(502).json({
        error: "Failed to reach Python engine.",
        detail: message,
      });
    }
  }
});

export default router;
