import express from "express";
import DetectedVideoObject from "../models/videoSchema.js";

const router = express.Router();

// Save detected video objects
router.post("/vdo-detect", async (req, res) => {
  try {
    const { timestamp, objects } = req.body;

    if (!timestamp || !Array.isArray(objects)) {
      return res.status(400).json({ error: "Invalid data format" });
    }

    const newDetection = new DetectedVideoObject({ timestamp, objects });
    await newDetection.save();

    res.status(201).json({
      message: "Video detection saved successfully",
    });
  } catch (error) {
    console.error("Error saving video detections:", error);
    res.status(500).json({ error: "Error saving video detections" });
  }
});

// Retrieve all detected video objects
router.get("/vdo-detections", async (req, res) => {
  try {
    const detections = await DetectedVideoObject.find();

    if (!detections.length) {
      return res.status(200).json({
        message: "No detections found",
        detections: [],
      });
    }

    res.json(detections);
  } catch (error) {
    console.error("Error retrieving video detections:", error);
    res.status(500).json({ error: "Error retrieving video detections" });
  }
});

export default router;