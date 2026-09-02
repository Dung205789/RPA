import json
import re
from pathlib import Path


def parse_input_to_json(
    raw_input,
    scenario_id="scenario_001",
    asset_base_path="images/vnexpress/"
):
    descriptions = []

    # =========================
    # 1. Chuẩn hóa input
    # =========================
    if isinstance(raw_input, list):
        # Input là list Python
        descriptions = [line.strip() for line in raw_input if line.strip()]
    else:
        # Input là string
        lines = raw_input.strip().splitlines()

        for line in lines:
            # Bỏ số thứ tự: 1. , 2. ...
            line = re.sub(r"^\s*\d+\.\s*", "", line)

            # Bỏ dấu , ở cuối dòng
            line = re.sub(r",\s*$", "", line)

            # Bỏ dấu nháy đơn bao ngoài '...'
            line = re.sub(r"^'(.*)'$", r"\1", line.strip())

            if line:
                descriptions.append(line)

    # =========================
    # 2. Tìm asset ảnh
    # =========================
    assets = {}
    image_pattern = re.compile(
        r"\[([^\]]+\.(png|jpg|jpeg|svg))\]",
        re.IGNORECASE
    )

    for desc in descriptions:
        for match in image_pattern.findall(desc):
            image_name = match[0]
            assets[image_name] = {
                "type": "image",
                "path": f"{asset_base_path}{image_name}"
            }

    # =========================
    # 3. Trả về JSON
    # =========================
    return {
        "id": scenario_id,
        "url": "https://vnexpress.net/",
        "environment": {
            "theme": "light",
        },
        "descriptions": descriptions,
        "assets": assets
    }


def save_json(data, file_name="scenario_example.json"):
    Path(file_name).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


# ================== Ví dụ sử dụng ==================

if __name__ == "__main__":
    user_input = """
2. 'Click on [o9.png]'
"""

    scenario_json = parse_input_to_json(
        user_input,
        scenario_id="scenario_001"
    )

    save_json(scenario_json, "scenario_example.json")

    print("JSON saved successfully:")
    print(json.dumps(scenario_json, indent=2, ensure_ascii=False))
