import torch
import transformers
from transformers import AutoModelForCausalLM, AutoProcessor, BitsAndBytesConfig
import transformers.dynamic_module_utils as dynamic_utils

# --- THE BYPASS (v1) : Import Scanner Bypass ---
original_check = dynamic_utils.check_imports

def custom_check_imports(filename):
    try:
        return original_check(filename)
    except ImportError as e:
        # Ignore phantom requirements that we know we either have or don't need
        ignore_list = ["flash_attn", "ffmpeg", "decord", "imageio"]
        if any(pkg in str(e) for pkg in ignore_list):
            return []  
        else:
            raise e

dynamic_utils.check_imports = custom_check_imports

# --- THE BYPASS (v2) : Accelerate 4-bit Shortcut Bypass ---
original_to = transformers.PreTrainedModel.to

def custom_to(self, *args, **kwargs):
    try:
        return original_to(self, *args, **kwargs)
    except ValueError as e:
        if "4-bit" in str(e) and "bitsandbytes" in str(e):
            return self
        raise e

transformers.PreTrainedModel.to = custom_to
# ---------------------------------------------------------

# 1. Point this directly to your newly downloaded folder
model_name = "DAMO-NLP-SG/VideoLLaMA3-2B"

# 2. Compress the model to save VRAM
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

print(f"Loading model from local directory: {model_name}...")

# 3. Load locally 
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    trust_remote_code=True,
    device_map="auto",
    torch_dtype=torch.float16,
    quantization_config=quantization_config,
)

processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)

video_path = "Abuse001_x264.mp4" 
question = "Describe this video in detail, noting any unusual events."

# Video conversation
conversation = [
    {"role": "system", "content": "You are a helpful assistant."},
    {
        "role": "user",
        "content": [
            {"type": "video", "video": {"video_path": video_path, "fps": 2, "max_frames": 18}}, 
            {"type": "text", "text": question},
        ]
    },
]

inputs = processor(conversation=conversation, return_tensors="pt")
inputs = {k: v.cuda() if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}

# 4. Ensure video frames match the model's float16 data type
if "pixel_values" in inputs:
    inputs["pixel_values"] = inputs["pixel_values"].to(torch.float16)
torch.cuda.empty_cache()
print("Analyzing video...")
output_ids = model.generate(**inputs, max_new_tokens=128)
response = processor.batch_decode(output_ids, skip_special_tokens=True)[0].strip()

print("\n--- Video Summary ---")
print(response)