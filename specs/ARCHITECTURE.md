# tinycoder architecture

Goal: an open, private, test-verified coding system built from small customized models, small enough to run in one CPU-only container. It does not try to beat the largest cloud agents on the hardest tasks. It competes on cost, privacy and reliability.

## One container, one base model, ten specialist models
- One Docker container, CPU only, sized from a few GB up to 128 GB.
- One shared base model, loaded once: Gemma 4 26B A4B (Apache 2.0), 4-bit, served by llama.cpp.
- Ten customized models, each a small LoRA fine-tune of that base for one task: `planner`, `python`, `java`, `ui`, `data`, `devops`, `ops`, `qa`, `debugger`, `reviewer`. Only one is active at a time, switched at run time through llama-server's `/lora-adapters`, so there is a single copy of the big weights.
- The router, retry budget and playbook cards are ordinary code, not a model.

## Workflow
1. The orchestrator reads the task and routes it (the `planner` model splits larger work into ordered, parallelizable steps).
2. The chosen specialist works on a tiny context (a function or a few files) in a fixed recipe.
3. Every answer runs in a locked-down sandbox (no network, read-only, capped). Tests decide: pass means keep, fail means resample a fresh candidate, with at most 2 repair rounds.
4. Output is a tested patch with the test evidence.

## Training recipe
- Verified self-distillation: a teacher model solves task-factory tasks and only solutions that pass the hidden tests are kept.
- QLoRA with Apple's MLX on a Mac (peak memory 19.6 GB for a smoke run on the 26B model).
- The trained adapter is converted to GGUF and loaded by llama.cpp.

## What is verified so far
- Gemma 26B A4B trains with LoRA under MLX on a 64 GB Mac (smoke run: 21 examples, 20 steps, validation loss 2.92 to 0.78).
- The adapter converts to GGUF (5 MB for rank 8 on attention and dense MLP layers of 8 layers), loads in llama-server, hot-swaps on and off at run time, and changes the model's output. Expert and router layers are skipped because llama.cpp's LoRA does not cover them.
- This was one tiny run. It shows the pipeline works, not that specialists beat the untrained base. That is the next measurement.

## Not yet verified
- That trained specialists beat the base model on held-out tasks.
- Speed and memory on small CPU-only VMs inside Docker.
- That separate adapters beat one shared adapter.

## Specialists and their task factories
Each folder under `specialists/` holds a seeded, validated task set with hidden tests or graders: see each folder's README.
