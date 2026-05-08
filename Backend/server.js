
import express from "express";
import connectDB from "./config/db.js";
import cors from "cors";
import dotenv from "dotenv";
dotenv.config({ path: "./config/.env" })
// Routes
import imageRoutes from "./routes/imageRoutes.js";
import videoRoutes from "./routes/videoRoutes.js";
import liveVideoRoutes from "./routes/liveVideoRoutes.js";
import sendAlertRoutes from "./routes/sendAlert.js";

const app = express();

// Middleware
app.use(express.json());
app.use(cors());

// Connect Database
connectDB();



app.use("/api", imageRoutes);
app.use("/api", videoRoutes);
app.use("/api", liveVideoRoutes);
app.use("/api", sendAlertRoutes);
// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
