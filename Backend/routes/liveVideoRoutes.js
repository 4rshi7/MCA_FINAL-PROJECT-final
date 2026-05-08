import express from "express";
import DetectedLiveVideoObject from "../models/liveVideoSchema.js";

const router = express.Router();

// POST Route - Save detections
router.post("/live-vdo-detect", async (req, res) => {
  try {
    const { objects } = req.body;

    if (!Array.isArray(objects) || objects.length === 0) {
      return res
        .status(400)
        .json({ error: "No objects detected or invalid format" });
    }

    // Map detected objects and save
    const detections = objects.map((obj) => ({
      class: obj.class || "unknown",
      score: obj.score || 0,
      timestamp: new Date(),
    }));

    const savedData = await DetectedLiveVideoObject.insertMany(detections);

    res
      .status(201)
      .json({ message: "Data stored successfully", data: savedData });
  } catch (error) {
    console.error("Error storing data:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

// GET Route - Retrieve stored detections
router.get("/live-vdo-detections", async (req, res) => {
  try {
    const detections = await DetectedLiveVideoObject.find().sort({
      timestamp: -1,
    });

    if (detections.length === 0) {
      return res.status(404).json({ message: "No detections found" });
    }

    res.json(detections);
  } catch (error) {
    console.error("Error fetching detections:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

export default router;