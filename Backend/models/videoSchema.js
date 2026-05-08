import mongoose from "mongoose";

const videoSchema = new mongoose.Schema({
  timestamp: {
    type: Number,
    required: true,
  },
  objects: [
    {
      class: {
        type: String,
        required: true,
      },
      score: {
        type: Number,
        required: true,
      },
      bbox: {
        type: [Number], // [x, y, width, height]
        required: true,
      },
    },
  ],
});

const DetectedVideoObject = mongoose.model(
  "DetectedVideoObject",
  videoSchema
);

export default DetectedVideoObject;