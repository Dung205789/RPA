import json
from pathlib import Path

BASE_URL = "https://vnexpress.net/"

output_dir = Path("data") / "vnexpress"
output_dir.mkdir(exist_ok=True)

for i in range(1, 19):
    scenario_id = f"scenario_{i:03d}"
    file_path = output_dir / f"{scenario_id}.json"

    data = {
        "id": scenario_id,
        "url": BASE_URL,
        "environment": {
            "theme": "light"
        },
    }

    file_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

print("Okkkk")
