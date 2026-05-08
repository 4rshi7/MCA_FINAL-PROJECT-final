import express from "express";
import nodemailer from "nodemailer";
import { getLastEmailTime, updateLastEmailTime } from "./emailCooldown.js";

const router = express.Router();

const transporter = nodemailer.createTransport({
  host: "smtp.gmail.com",
  port: 587,
  secure: false,
  requireTLS: true,
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASS,
  },
});

const EMAIL_INTERVAL = 15 * 60 * 1000; // 15 minutes

router.post("/send-alert", async (req, res) => {
  const now = Date.now();
  const lastTime = getLastEmailTime();

  if (now - lastTime > EMAIL_INTERVAL) {
    const mailOptions = {
      from: `"Harmful Object Alert" <${process.env.EMAIL_USER}>`,
      to: process.env.TO_EMAIL,
      subject: "Harmful Object Detected!",
      text: "A harmful object has been detected. Please take necessary action.",
    };

    try {
      await transporter.sendMail(mailOptions);
      console.log("Email sent successfully.");
      updateLastEmailTime(now); // update cooldown
      res.status(200).send("Email sent!");
    } catch (err) {
      console.error("Email send error:", err);
      res.status(500).send("Failed to send email.");
    }
  } else {
    console.log("Cooldown: Email not sent (15-min interval).");
    res.status(200).send("Email not sent. Still in cooldown period.");
  }
});

export default router;