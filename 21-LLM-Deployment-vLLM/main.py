import os
import sys

# --- CONFIGURATION SECTION ---
# 1. Fix Multiprocessing for 'spawn' method
if __name__ == "__main__":
    # These must be set before importing vllm
    os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
    
    # 2. Disable the experimental V1 engine (Source of the "Core died" crash)
    os.environ["VLLM_USE_V1"] = "0" 
    
    # 3. Disable NCCL P2P (Crucial for RTX 4050/Laptop GPUs)
    os.environ["NCCL_P2P_DISABLE"] = "1"
    os.environ["NCCL_IB_DISABLE"] = "1"

    # 4. Force CUDA device order to ensure we see the GPU correctly
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"

    from vllm import LLM, SamplingParams

    def main():
        print("=============== Initializing vLLM (Stable Engine) ================")
        
        # Initialize LLM with settings optimized for RTX 4050 (6GB VRAM)
        llm = LLM(
            model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            # Lower memory usage to prevent OOM/Segfaults
            gpu_memory_utilization=0.6,
            # Force standard float16 (bf16 can be unstable on some laptop drivers)
            dtype="float16",
            # Disable CUDA graphs to prevent memory pointer crashes
            enforce_eager=True,
            # Ensure we don't try to shard the model
            tensor_parallel_size=1
        )

        print("=============== Model Loaded Successfully ================")
        
        params = SamplingParams(max_tokens=300, temperature=0.8)
        outputs = llm.generate(["Tell me most sweet food list."], params)

        print("\nGenerated Output:")
        print(outputs[0].outputs[0].text.strip())

    # Execute main
    main()