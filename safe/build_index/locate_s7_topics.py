import json
from pathlib import Path

CHUNKS = Path.home() / "s7_rag_processed/s7_chunks_v2.jsonl"

TOPICS = {
    "profinet_diagnosis": [
        "PROFINET 诊断",
        "诊断 PROFINET",
        "诊断方法",
        "诊断信息",
        "在线与诊断",
        "STEP 7 中显示诊断",
        "使用 STEP 7 查看诊断信息",
        "诊断缓冲区",
    ],
    "step7_diagnosis": [
        "使用 STEP 7 查看诊断信息",
        "在线与诊断",
        "诊断缓冲区",
        "模块信息",
        "诊断状态",
        "在 STEP 7 中",
    ],
    "cpu_display_diagnosis": [
        "CPU 显示屏",
        "显示屏",
        "诊断功能",
        "诊断缓冲区",
        "诊断信息",
        "菜单",
    ],
    "firmware_update": [
        "固件更新",
        "更新固件",
        "固件版本",
        "通过 STEP 7 更新固件",
        "SIMATIC 存储卡 更新固件",
        "Web 服务器 更新固件",
    ],
    "temperature_range": [
        "运行中的环境温度",
        "环境温度",
        "水平安装，最小值",
        "水平安装，最大值",
        "垂直安装，最小值",
        "垂直安装，最大值",
        "工作温度范围",
    ],
}

def score_obj(obj, terms):
    text = obj.get("text", "")
    md = obj.get("metadata", {})
    section = md.get("section", "")
    hay = section + "\n" + text

    score = 0
    for t in terms:
        if t in hay:
            score += 10 + len(t)

    # 降低目录页、无关设备页权重
    if "目录" in section:
        score -= 20
    if "Web 服务器 > 4 Web 页面 > 4.4 运动控制诊断" in section:
        score -= 15

    return score

objs = []
with CHUNKS.open("r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            objs.append(json.loads(line))

for topic, terms in TOPICS.items():
    hits = []
    for obj in objs:
        sc = score_obj(obj, terms)
        if sc > 0:
            md = obj.get("metadata", {})
            hits.append((sc, md.get("page_no"), obj.get("id"), md.get("section", ""), obj.get("text", "")))

    hits.sort(key=lambda x: (-x[0], x[1] or 0))

    print("\n" + "=" * 120)
    print("TOPIC:", topic)
    print("=" * 120)

    for sc, page, cid, section, text in hits[:12]:
        print("\n" + "-" * 100)
        print("score:", sc)
        print("page:", page)
        print("id:", cid)
        print("section:", section)

        # 打印第一个命中词附近
        positions = [text.find(t) for t in terms if text.find(t) >= 0]
        if positions:
            start = max(0, min(positions) - 250)
        else:
            start = 0
        print(text[start:start+1200])
