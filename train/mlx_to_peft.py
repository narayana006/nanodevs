"""Convert an mlx-lm LoRA adapter to PEFT format (attention + dense MLP only; expert and router LoRAs are skipped)."""
import json, os, re, sys
import numpy as np
from safetensors import safe_open
from safetensors.numpy import save_file

src, dst = sys.argv[1], sys.argv[2]
cfg = json.load(open(os.path.join(src, "adapter_config.json")))
rank, scale = cfg["lora_parameters"]["rank"], cfg["lora_parameters"]["scale"]
f = safe_open(os.path.join(src, "adapters.safetensors"), "np")
out, mods = {}, set()
for k in f.keys():
    m = re.match(r"language_model\.model\.layers\.(\d+)\.(self_attn|mlp)\.(\w+)\.lora_([ab])$", k)
    if not m:
        continue
    layer, blk, proj, ab = m.groups()
    t = f.get_tensor(k).T.astype(np.float32).copy()
    name = f"base_model.model.model.language_model.layers.{layer}.{blk}.{proj}.lora_{'A' if ab == 'a' else 'B'}.weight"
    out[name] = t
    mods.add(proj)
os.makedirs(dst, exist_ok=True)
save_file(out, os.path.join(dst, "adapter_model.safetensors"))
json.dump({"peft_type": "LORA", "task_type": "CAUSAL_LM", "r": rank, "lora_alpha": rank * scale, "lora_dropout": 0.0,
           "target_modules": sorted(mods), "bias": "none", "base_model_name_or_path": cfg["model"],
           "use_rslora": False, "fan_in_fan_out": False}, open(os.path.join(dst, "adapter_config.json"), "w"), indent=1)
print(len(out), "tensors,", sorted(mods))
