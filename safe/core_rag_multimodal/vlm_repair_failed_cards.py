import json
import re
import sys
from pathlib import Path

import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

HOME = Path.home()
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from safe.trusted_rag.local_env import resolve_llm_model_dir


MODEL_DIR = resolve_llm_model_dir()
MANIFEST = HOME / "s7_multimodal_v1/figure_cards/selected_visual_manifest_enriched.jsonl"
OLD = HOME / "s7_multimodal_v1/figure_cards/figure_cards_v1.jsonl"
NEW = HOME / "s7_multimodal_v1/figure_cards/figure_cards_v1_repaired.jsonl"
RAW_DIR = HOME / "s7_multimodal_v1/logs/vlm_raw_outputs_repair"

RAW_DIR.mkdir(parents=True, exist_ok=True)

VALID_TYPES = {
    "hardware_layout",
    "wiring_diagram",
    "topology",
    "terminal_assignment",
    "interface_layout",
    "power_connection",
    "installation_step",
    "table_with_figure",
    "text_with_small_figure",
    "unknown",
}


def extract_json(text: str):
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end + 1]

    try:
        return json.loads(text)
    except Exception:
        return None


def list_limit(value, n):
    if not isinstance(value, list):
        return []
    return value[:n]


def dedup_terms(value, n=8):
    if not isinstance(value, list):
        return []
    seen = set()
    out = []
    for x in value:
        if not isinstance(x, str):
            continue
        x = x.strip()
        if not x or x in seen:
            continue
        seen.add(x)
        out.append(x)
        if len(out) >= n:
            break
    return out


def clean_card(card):
    vt = card.get("visual_type", "unknown")
    if vt not in VALID_TYPES:
        card["visual_type"] = "unknown"

    card["objects"] = list_limit(card.get("objects"), 5)
    card["connections"] = list_limit(card.get("connections"), 5)
    card["ports_interfaces"] = list_limit(card.get("ports_interfaces"), 5)
    card["visible_text"] = list_limit(card.get("visible_text"), 8)
    card["warnings_or_limits"] = list_limit(card.get("warnings_or_limits"), 4)
    card["query_terms"] = dedup_terms(card.get("query_terms"), 8)

    try:
        card["confidence"] = float(card.get("confidence", 0.0))
    except Exception:
        card["confidence"] = 0.0

    if card["confidence"] < 0:
        card["confidence"] = 0.0
    if card["confidence"] > 1:
        card["confidence"] = 1.0

    card["needs_human_review"] = bool(card.get("needs_human_review", True))
    return card


def normalize(rec, parsed, raw_text):
    base = {
        "doc_id": rec.get("doc_id", "1500_manual_collection_zh-CHS"),
        "page": rec.get("page"),
        "figure_id": rec.get("figure_id"),
        "image_path": rec.get("image_path"),
        "source_type": rec.get("source_type", "rendered_pdf_page"),
        "model": "Qwen2.5-VL-3B-Instruct",
    }

    defaults = {
        "visual_type": "unknown",
        "summary_zh": "",
        "objects": [],
        "connections": [],
        "ports_interfaces": [],
        "visible_text": [],
        "warnings_or_limits": [],
        "query_terms": [],
        "confidence": 0.0,
        "needs_human_review": True,
    }

    if isinstance(parsed, dict):
        card = {**base, **defaults, **parsed}
        card["parse_ok"] = True
        return clean_card(card)

    card = {**base, **defaults}
    card["raw_output"] = raw_text
    card["parse_ok"] = False
    card["needs_human_review"] = True
    return clean_card(card)


def build_prompt(rec):
    nearby_text = rec.get("nearby_text", "")[:800]
    page = rec.get("page")

    return f"""
你是西门子 S7-1500 / ET 200MP 中文手册的工业图纸解析助手。

只输出一个合法 JSON 对象。
不要 Markdown。
不要代码块。
不要解释。
不要在 JSON 之外输出任何内容。

页面：{page}

页面上下文：
{nearby_text}

要求：
1. 只描述图片可见或上下文明确支持的信息。
2. 看不清就写“无法确认”。
3. 不要编造端子号、接口名、型号、接线关系。
4. visual_type 只能从以下枚举中选择一个：
   hardware_layout, wiring_diagram, topology, terminal_assignment,
   interface_layout, power_connection, installation_step,
   table_with_figure, text_with_small_figure, unknown
5. objects 最多 5 项。
6. connections 最多 5 项。
7. ports_interfaces 最多 5 项。
8. visible_text 最多 8 项。
9. warnings_or_limits 最多 4 项。
10. query_terms 最多 8 项，必须去重，禁止重复词。
11. confidence 为 0 到 1 之间的小数。
12. needs_human_review 为 true 或 false。

输出格式：
{{
  "visual_type": "unknown",
  "summary_zh": "",
  "objects": [],
  "connections": [],
  "ports_interfaces": [],
  "visible_text": [],
  "warnings_or_limits": [],
  "query_terms": [],
  "confidence": 0.0,
  "needs_human_review": true
}}
"""


manifest = {}
with MANIFEST.open("r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            rec = json.loads(line)
            manifest[rec["figure_id"]] = rec

old_cards = []
failed_ids = []

with OLD.open("r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        obj = json.loads(line)
        old_cards.append(obj)
        if not obj.get("parse_ok"):
            failed_ids.append(obj["figure_id"])

print("old cards:", len(old_cards))
print("failed:", len(failed_ids), failed_ids)

if not failed_ids:
    print("no failed cards, nothing to repair")
    raise SystemExit(0)

model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    str(MODEL_DIR),
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto",
    local_files_only=True,
)

processor = AutoProcessor.from_pretrained(
    str(MODEL_DIR),
    min_pixels=256 * 28 * 28,
    max_pixels=1024 * 28 * 28,
    local_files_only=True,
)

repaired = {}

for i, fig_id in enumerate(failed_ids, 1):
    rec = manifest[fig_id]
    image_path = rec["image_path"]
    prompt = build_prompt(rec)

    print(f"[repair] {i}/{len(failed_ids)} page={rec.get('page')} fig={fig_id}")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": "file://" + image_path},
                {"type": "text", "text": prompt},
            ],
        }
    ]

    text = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    image_inputs, video_inputs = process_vision_info(messages)

    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(model.device)

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=2048,
            do_sample=False,
            repetition_penalty=1.05,
        )

    generated_ids_trimmed = [
        out_ids[len(in_ids):]
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]

    raw_text = processor.batch_decode(
        generated_ids_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )[0]

    (RAW_DIR / f"{fig_id}.txt").write_text(raw_text, encoding="utf-8")

    parsed = extract_json(raw_text)
    card = normalize(rec, parsed, raw_text)
    repaired[fig_id] = card

    print("  parse_ok:", card["parse_ok"], "visual_type:", card.get("visual_type"))

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

with NEW.open("w", encoding="utf-8") as f:
    for obj in old_cards:
        fig_id = obj["figure_id"]
        if fig_id in repaired:
            f.write(json.dumps(repaired[fig_id], ensure_ascii=False) + "\n")
        else:
            obj = clean_card(obj)
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

print("written:", NEW)
