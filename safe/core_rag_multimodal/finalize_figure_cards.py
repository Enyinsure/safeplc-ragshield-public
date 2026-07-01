import json
from pathlib import Path

HOME = Path.home()

INP = HOME / "s7_multimodal_v1/figure_cards/figure_cards_v1_repaired.jsonl"
MANIFEST = HOME / "s7_multimodal_v1/figure_cards/selected_visual_manifest_enriched.jsonl"
OUT = HOME / "s7_multimodal_v1/figure_cards/figure_cards_v1_final.jsonl"

manifest = {}
with MANIFEST.open("r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            rec = json.loads(line)
            manifest[rec["figure_id"]] = rec

def infer_terms(text):
    candidates = [
        "PROFINET", "PROFIBUS", "PN/IE", "24 V DC", "CPU", "ET 200MP",
        "接口", "端子", "接线", "连接器", "电源", "负载电源",
        "系统电源", "拓扑", "模块", "插头", "针脚", "引脚"
    ]
    return [x for x in candidates if x in text][:8]

out_records = []
fixed = []

with INP.open("r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        obj = json.loads(line)
        fig_id = obj.get("figure_id")

        if obj.get("parse_ok"):
            out_records.append(obj)
            continue

        rec = manifest.get(fig_id, {})
        nearby_text = rec.get("nearby_text", "")
        terms = infer_terms(nearby_text)

        fallback = {
            "doc_id": obj.get("doc_id") or rec.get("doc_id", "1500_manual_collection_zh-CHS"),
            "page": obj.get("page") or rec.get("page"),
            "figure_id": fig_id,
            "image_path": obj.get("image_path") or rec.get("image_path"),
            "source_type": obj.get("source_type", "rendered_pdf_page"),
            "model": obj.get("model", "Qwen2.5-VL-3B-Instruct"),
            "visual_type": obj.get("visual_type", "unknown") if obj.get("visual_type") != "unknown" else "unknown",
            "summary_zh": "该页包含与 S7-1500 / ET 200MP 手册相关的图示或表格，但 VLM 输出未能稳定解析；请结合原图和页面上下文人工确认。",
            "objects": [],
            "connections": [],
            "ports_interfaces": [],
            "visible_text": [],
            "warnings_or_limits": [],
            "query_terms": terms,
            "confidence": 0.2,
            "needs_human_review": True,
            "parse_ok": True,
            "fallback_from_parse_failed": True
        }

        out_records.append(fallback)
        fixed.append(fig_id)

with OUT.open("w", encoding="utf-8") as f:
    for r in out_records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("written:", OUT)
print("records:", len(out_records))
print("fallback fixed:", len(fixed), fixed)
