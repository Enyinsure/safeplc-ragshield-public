from modelscope import snapshot_download
from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from safe.trusted_rag.local_env import resolve_llm_model_dir


target_dir = resolve_llm_model_dir()
target_dir.mkdir(parents=True, exist_ok=True)

model_dir = snapshot_download(
    "Qwen/Qwen2.5-VL-3B-Instruct",
    local_dir=str(target_dir),
)

print("model_dir:", model_dir)
