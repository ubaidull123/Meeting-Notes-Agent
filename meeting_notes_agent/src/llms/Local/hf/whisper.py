import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from langchain_community.llms import HuggingFacePipeline

# Model ID
model_id = "openai/whisper-large-v3"

# Device setup
device = "cuda:0" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if torch.cuda.is_available() else torch.float32

# Load model + processor
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id,
    torch_dtype=dtype,
    low_cpu_mem_usage=True,
    use_safetensors=True
)
model.to(device)

processor = AutoProcessor.from_pretrained(model_id)

# Create HF pipeline
asr_pipeline = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    device=0 if device.startswith("cuda") else -1,
    chunk_length_s=30,
    return_timestamps=True,
)

# Wrap in LangChain
llm = HuggingFacePipeline(pipeline=asr_pipeline)

# Run transcription
result = llm.invoke("path/to/audio.wav")

print(result)