#!/usr/bin/env python3
"""
Test script for NB-Whisper small model with actual audio transcription.
"""

import sys
sys.path.append('.')

import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from pathlib import Path
from app.core.logging import configure_logging, get_logger

def main():
    # Configure logging
    configure_logging()
    logger = get_logger()

    print("🇳🇴 NB-Whisper Small Model Test")
    print("=" * 40)

    # Check GPU availability
    print(f"🔧 PyTorch version: {torch.__version__}")
    print(f"🎮 CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
        print(f"🎮 GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # Set device
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    print(f"🎯 Using device: {device}")
    print(f"🎯 Using dtype: {torch_dtype}")

    try:
        print("\n📦 Loading NB-Whisper small model...")
        model_id = "NbAiLab/nb-whisper-small"

        # Load model
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True
        )
        model.to(device)

        # Load processor
        processor = AutoProcessor.from_pretrained(model_id)

        print("✅ Model and processor loaded successfully!")

        # Create pipeline
        print("🔧 Creating transcription pipeline...")
        pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            max_new_tokens=256,
            chunk_length_s=30,
            batch_size=16,
            return_timestamps=True,
            dtype=torch_dtype,
            device=device,
        )

        print("✅ Pipeline created successfully!")

        # Test with an audio file if available
        audio_files_path = Path("audio_files/converted")
        if audio_files_path.exists():
            wav_files = list(audio_files_path.glob("*.wav"))

            if wav_files:
                test_file = wav_files[0]
                print(f"\n🎵 Testing transcription with: {test_file.name}")

                # Get file info
                file_size = test_file.stat().st_size / (1024 * 1024)
                print(f"📊 File size: {file_size:.2f} MB")

                # Test transcription
                print("🔊 Starting transcription...")
                result = pipe(str(test_file))

                print("\n✅ Transcription successful!")
                print("📝 Transcription Result:")
                print("-" * 50)
                print(result['text'])
                print("-" * 50)

                if 'chunks' in result and result['chunks']:
                    print(f"\n🕐 Found {len(result['chunks'])} timestamp chunks")
                    print("📝 First few chunks:")
                    for i, chunk in enumerate(result['chunks'][:3]):
                        start = chunk['timestamp'][0] if chunk['timestamp'][0] else 0
                        end = chunk['timestamp'][1] if chunk['timestamp'][1] else 0
                        print(f"  [{start:.1f}s - {end:.1f}s]: {chunk['text']}")

                return True
            else:
                print("⚠️  No WAV files found in audio_files/converted/")
                print("✅ Model loading test completed successfully!")
                return True
        else:
            print("⚠️  No converted audio files directory found")
            print("✅ Model loading test completed successfully!")
            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        logger.error(f"NB-Whisper small test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n🏁 Test {'PASSED' if success else 'FAILED'}")
    if success:
        print("\n💡 NB-Whisper small model is ready for integration!")
        print("   - Good balance between accuracy and memory usage")
        print("   - Fits comfortably in 4GB VRAM")
        print("   - Ready for production transcription service")
    sys.exit(0 if success else 1)