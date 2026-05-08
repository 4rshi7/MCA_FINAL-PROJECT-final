import express from "express";
import DetectedImageObject from "../models/imageSchema.js";

const router = express.Router();

// Save detected image objects
router.post("/img-detect", async (req, res) => {
  try {
    if (!Array.isArray(req.body) || req.body.length === 0) {
      return res.status(400).json({ error: "Invalid data format" });
    }

    await DetectedImageObject.insertMany(req.body);

    res.status(201).json({ message: "Image objects saved successfully" });
  } catch (error) {
    res.status(500).json({ error: "Error saving image objects" });
  }
});

// Retrieve all detected image objects
router.get("/img-detections", async (req, res) => {
  try {
    const detections = await DetectedImageObject.find();
    res.json(detections);
  } catch (error) {
    res.status(500).json({ error: "Error retrieving image detections" });
  }
});

export default router;