import sys
import os
import uuid
import shutil
import cv2
import numpy as np
from tqdm import tqdm
 
 
# --- THE ADAPTER: Fixes pytorchvideo crash for PyTorch 2.6.0 ---
import torchvision.transforms.functional
sys.modules["torchvision.transforms.functional_tensor"] = torchvision.transforms.functional
 
import torch
from torch import nn
from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
 
# Pytorchvideo imports
from torchvision.transforms.v2 import CenterCrop, Normalize
from torchvision.transforms import Compose, Lambda
from pytorchvideo.transforms import ApplyTransformToKey, ShortSideScale, UniformTemporalSubsample
from pytorchvideo.data import LabeledVideoDataset, UniformClipSampler
from torch.utils.data import DataLoader
 
# Gemini imports
from google import genai
from google.genai import types as genai_types
 
# Your custom model import
from model import Model
 
# ==========================================
# 1. Server Setup & Storage
# ==========================================
app = FastAPI(title="Video Anomaly Detection API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
 
# Create directory for temporary feature storage
CACHE_DIR = "feature_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
 
# ==========================================
# 2. Global Model Initialization
# ==========================================
print(f"Loading models onto {device}...")
 
x3d_model = torch.hub.load('facebookresearch/pytorchvideo', 'x3d_l', pretrained=True)
del x3d_model.blocks[-1]
x3d_model = x3d_model.eval().to(device)
 
anomaly_model = Model()
anomaly_model.load_state_dict(torch.load("913base.pkl", map_location=device))
anomaly_model = anomaly_model.to(device)
anomaly_model.eval()
 
print("Models loaded successfully!")
 
# ==========================================
# 2b. Gemini Client Initialization
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"   # free-tier supported model
 
print("Gemini client initialized!")
 
# ==========================================
# 3. Transform Configuration
# ==========================================
mean = [0.45, 0.45, 0.45]
std = [0.225, 0.225, 0.225]
frames_per_second = 30
transform_params = {"side_size": 320, "crop_size": 320, "num_frames": 16, "sampling_rate": 5}
 
class Permute(nn.Module):
    def __init__(self, dims):
        super().__init__()
        self.dims = dims
    def forward(self, x):
        return torch.permute(x, self.dims)
 
transform = ApplyTransformToKey(
    key="video",
    transform=Compose([
        UniformTemporalSubsample(transform_params["num_frames"]),
        Lambda(lambda x: x / 255.0),
        Permute((1, 0, 2, 3)),
        Normalize(mean, std),
        ShortSideScale(size=transform_params["side_size"]),
        CenterCrop((transform_params["crop_size"], transform_params["crop_size"])),
        Permute((1, 0, 2, 3))
    ]),
)
clip_duration = (transform_params["num_frames"] * transform_params["sampling_rate"]) / frames_per_second
 
# ==========================================
# 4. Pipeline & Visualization Functions
# ==========================================
def extract_video_features(video_path: str) -> np.ndarray:
    single_video_list = [(video_path, {'video_label': 0})]
    dataset = LabeledVideoDataset(
        labeled_video_paths=single_video_list,
        clip_sampler=UniformClipSampler(clip_duration),
        transform=transform, decode_audio=False
    )
    loader = DataLoader(dataset, batch_size=1)
 
    features_list = []
 
    with torch.no_grad():
        for inputs in loader:
            video_tensor = inputs['video'].to(device)
            preds = x3d_model(video_tensor).cpu().numpy()
            features_list.append(preds)
 
    if not features_list:
        raise ValueError("No clips could be extracted from the video.")
 
    current_features = np.concatenate(features_list, axis=0)
    return current_features
 
 
def predict_anomaly(features: np.ndarray) -> dict:
    features_tensor = torch.tensor(features).float()
    if len(features_tensor.shape) == 4:
        features_tensor = features_tensor.unsqueeze(0)
    features_tensor = features_tensor.to(device)
 
    with torch.no_grad():
        scores, _ = anomaly_model(features_tensor)
        scores = torch.sigmoid(scores).squeeze().cpu().numpy()
 
    if scores.ndim == 0:
        scores = np.expand_dims(scores, axis=0)
 
    max_score = float(scores.max())
    is_anomalous = max_score > 0.5
 
    return {
        "is_anomalous": is_anomalous,
        "max_score": max_score,
        "segment_scores": scores.tolist()
    }
 
 
def generate_feature_grid(features: np.ndarray, t: int, rows=12, cols=16, cell_size=36) -> np.ndarray:
    """Generates the visual grid for a specific time step t"""
    slice_t = features[:, t, :, :]  # Shape: (192, 10, 10)
    grid_img = np.zeros((rows * cell_size, cols * cell_size), dtype=np.uint8)
 
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx < slice_t.shape[0]:
                ch = slice_t[idx]
                ch = ch - ch.min()
                if ch.max() > 0:
                    ch = ch / ch.max()
                ch = (ch * 255).astype(np.uint8)
                ch_resized = cv2.resize(ch, (cell_size, cell_size), interpolation=cv2.INTER_CUBIC)
                grid_img[r * cell_size:(r + 1) * cell_size, c * cell_size:(c + 1) * cell_size] = ch_resized
                idx += 1
    return grid_img
 
 
# ==========================================
# 5. API Endpoints
# ==========================================
 
@app.post("/summarize/")
async def summarize_video_endpoint(file: UploadFile = File(...)):
    """
    Uploads a video to Gemini and returns a detailed summary.
    Uses the Gemini File API for videos larger than 20MB,
    and inline base64 for smaller ones.
    """
    temp_filename = f"temp_summary_{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    uploaded_gemini_file = None
 
    try:
        # Save uploaded file temporarily
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
 
        file_size_mb = os.path.getsize(temp_filename) / (1024 * 1024)
 
        prompt = (
            "You are a surveillance and security analyst. "
            "Watch this video carefully and provide: "
            "1. A general scene description. "
            "2. Any suspicious, violent, or anomalous activities detected. "
            "3. Key objects or people involved. "
            "4. An overall risk assessment (Low / Medium / High). "
            "Be concise but thorough."
        )
 
        if file_size_mb > 20:
            # --- Large video: use Gemini File API ---
            print(f"Video is {file_size_mb:.1f}MB — uploading via Gemini File API...")
 
            uploaded_gemini_file = gemini_client.files.upload(
                file=temp_filename,
                config=genai_types.UploadFileConfig(mime_type="video/mp4")
            )
 
            # Poll until Gemini has finished processing the file
            import time
            while uploaded_gemini_file.state.name == "PROCESSING":
                print("Waiting for Gemini to process the video...")
                time.sleep(3)
                uploaded_gemini_file = gemini_client.files.get(name=uploaded_gemini_file.name)
 
            if uploaded_gemini_file.state.name == "FAILED":
                raise HTTPException(status_code=500, detail="Gemini failed to process the uploaded video.")
 
            response = gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[uploaded_gemini_file, prompt]
            )
 
        else:
            # --- Small video (<20MB): send inline as base64 ---
            print(f"Video is {file_size_mb:.1f}MB — sending inline to Gemini...")
 
            with open(temp_filename, "rb") as f:
                video_bytes = f.read()
 
            response = gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=genai_types.Content(
                    parts=[
                        genai_types.Part(
                            inline_data=genai_types.Blob(
                                data=video_bytes,
                                mime_type="video/mp4"
                            )
                        ),
                        genai_types.Part(text=prompt)
                    ]
                )
            )
 
        summary = response.text.strip()
 
        return JSONResponse(content={
            "status": "success",
            "filename": file.filename,
            "summary": summary
        })
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
    finally:
        # Clean up temp file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        # Delete the file from Gemini servers to save quota
        if uploaded_gemini_file is not None:
            try:
                gemini_client.files.delete(name=uploaded_gemini_file.name)
            except Exception:
                pass  # Non-critical, ignore
 
 
@app.post("/analyze/")
async def analyze_video_endpoint(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    temp_filename = f"temp_video_{session_id}{file_ext}"

    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Extract Features (Returns 5D array: Batch, Channels, Time, H, W)
        features = extract_video_features(temp_filename)

        # 2. Run Anomaly Detection on the ENTIRE video (All batches)
        results = predict_anomaly(features)

        # 3. Prepare Visualizer Data (Grab ONLY the first clip)
        if features.ndim == 5:
            vis_features = features[0] 
        else:
            vis_features = np.squeeze(features)

        # 4. Cache ONLY the first clip for the visualizer
        os.makedirs(CACHE_DIR, exist_ok=True)
        np.save(os.path.join(CACHE_DIR, f"{session_id}.npy"), vis_features)

        return JSONResponse(content={
            "filename": file.filename,
            "status": "success",
            "file_id": session_id,
            "total_timesteps": vis_features.shape[1], # This will now correctly be 16
            "results": results
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
 
 
@app.get("/visualize/{file_id}/{t}")
async def get_visualization(file_id: str, t: int):
    """Returns a PNG image of the feature grid for the given time step."""
    feature_path = os.path.join(CACHE_DIR, f"{file_id}.npy")

    if not os.path.exists(feature_path):
        raise HTTPException(status_code=404, detail="Session expired or features not found.")

    # Load the features
    features = np.load(feature_path)
    
    # Bulletproof shape fix just in case an old file is read
    if features.ndim == 5:
        features = features[0]
    elif features.ndim > 4:
        features = np.squeeze(features)

    # Final safeguard
    if features.ndim != 4:
         raise HTTPException(status_code=500, detail=f"CRITICAL: Array is still not 4D. Shape is {features.shape}")

    if t < 0 or t >= features.shape[1]:
        raise HTTPException(status_code=400, detail=f"Time step {t} out of bounds.")

    grid_img = generate_feature_grid(features, t)

    success, encoded_img = cv2.imencode('.png', grid_img)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode image")

    return Response(content=encoded_img.tobytes(), media_type="image/png")
 
 
@app.delete("/cleanup/{file_id}")
async def cleanup_session(file_id: str):
    """Deletes the cached numpy file when the client is done."""
    feature_path = os.path.join(CACHE_DIR, f"{file_id}.npy")
    if os.path.exists(feature_path):
        os.remove(feature_path)
        return {"status": "success", "message": "Cache cleared."}
    return {"status": "not_found", "message": "File already deleted or not found."}
 
 
@app.get("/health")
def health_check():
    return {"status": "healthy", "device": str(device)}