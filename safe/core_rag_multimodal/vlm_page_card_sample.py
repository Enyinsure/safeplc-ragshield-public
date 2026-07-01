import argparse
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
OUT = HOME / "s7_multimodal_v1/figure_cards/figure_cards_v1.jsonl"
RAW_DIR = HOME / "s7_multimodal_v1/logs/vlm_raw_outputs"

RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)


def extract_json(text: str):
    text = text.strip()

    # 兼容 ```json ... ```
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except Exception:
        pass

    # 从输出中截取第一个 JSON 对象
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            return None

    return None


def normalize_card(rec, parsed, raw_text):
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
    else:
        card = {**base, **defaults}
        card["raw_output"] = raw_text
        card["parse_ok"] = False
        card["needs_human_review"] = True

    return card


def build_prompt(rec):
    nearby_text = rec.get("nearby_text", "")[:1600]
    page = rec.get("page")

    return f"""
你是西门子 S7-1500 / ET 200MP 中文手册的工业图纸解析助手。

任务：根据整页图片和页面上下文，生成结构化中文语义描述。

严格要求：
1. 只描述图片可见或上下文明确支持的信息。
2. 不要凭经验补全未显示的端子号、接口名、型号、接线关系。
3. 如果文字模糊或符号不可辨认，写“无法确认”。
4. visual_type 必须从以下枚举中选择一个：
   hardware_layout, wiring_diagram, topology, terminal_assignment,
   interface_layout, power_connection, installation_step,
   table_with_figure, text_with_small_figure, unknown
5. warnings_or_limits 只放真正的“警告、注意、限制、必须、禁止、仅在……情况下”等内容。
6. 只输出合法 JSON，不要 Markdown，不要 ```json 代码块。

页面：{page}

页面上下文：
{nearby_text}

请输出 JSON，字段为：
{{
  "visual_type": "",
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="只处理前 N 条；0 表示全部")
    parser.add_argument("--resume", action="store_true", help="跳过已写入的 figure_id")
    args = parser.parse_args()

    records = []
    with MANIFEST.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    if args.limit and args.limit > 0:
        records = records[:args.limit]

    done = set()
    if args.resume and OUT.exists():
        with OUT.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        obj = json.loads(line)
                        done.add(obj.get("figure_id"))
                    except Exception:
                        pass

    print("model:", MODEL_DIR)
    print("manifest:", MANIFEST)
    print("records to consider:", len(records))
    print("already done:", len(done))

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        str(MODEL_DIR),
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
        local_files_only=True,
    )

    processor = AutoProcessor.from_pretrained(
        str(MODEL_DIR),
        min_pixels=256 * 28 * 28,
        max_pixels=1280 * 28 * 28,
        local_files_only=True,
    )

    mode = "a" if args.resume else "w"

    with OUT.open(mode, encoding="utf-8") as out_f:
        for idx, rec in enumerate(records, 1):
            fig_id = rec.get("figure_id")
            if args.resume and fig_id in done:
                print(f"[skip] {idx}/{len(records)} {fig_id}")
                continue

            image_path = rec["image_path"]
            prompt = build_prompt(rec)

            print(f"[run] {idx}/{len(records)} page={rec.get('page')} fig={fig_id}")

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
            )

            inputs = inputs.to(model.device)

            with torch.no_grad():
                generated_ids = model.generate(
                    **inputs,
                    max_new_tokens=1024,
                    do_sample=False,
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

            raw_path = RAW_DIR / f"{fig_id}.txt"
            raw_path.write_text(raw_text, encoding="utf-8")

            parsed = extract_json(raw_text)
            card = normalize_card(rec, parsed, raw_text)

            out_f.write(json.dumps(card, ensure_ascii=False) + "\n")
            out_f.flush()

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    print("done:", OUT)


if __name__ == "__main__":
    main()
