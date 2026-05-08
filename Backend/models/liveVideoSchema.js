import mongoose from "mongoose";

const liveVideoSchema = new mongoose.Schema({
  class: String,
  score: Number,
  timestamp: {
    type: Date,
    default: Date.now,
  },
});

const DetectedLiveVideoObject = mongoose.model(
  "DetectedLiveVideoObject",
  liveVideoSchema
);

export default DetectedLiveVideoObject;