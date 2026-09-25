# documents/ — hướng RPA

> **Đây không phải SVG_agent.** Thư mục này là một kho git **riêng**
> (`github.com/Dung205789/RPA`), tiếp cận bài toán bằng **RPA/Selenium** trên
> code của người đi trước. Kho cha `D:\SVG_agent` theo hướng **web agent** và có
> `CLAUDE.md` riêng của nó.
>
> **`D:\SVG_agent\CLAUDE.md` KHÔNG áp dụng cho thư mục này.** Cụ thể, ở đây
> không có `svgagent read/draw/bench`, không có `experiments/EXPERIMENT_LOG.md`,
> không có ba arm A/B/C, không có đợt reset tài liệu 2026-09-07. Gặp chỉ dẫn nào
> nhắc tới những thứ đó thì bỏ qua — nó nói về kho cha.

## Mở phiên mới: đọc ba thứ này trước khi đụng code

```bash
sed -n '1,40p' RPA_docs/PROGRESS.md           # đang ở giai đoạn nào, cổng nào còn treo
sed -n '/^## Bất biến/,/^## G0/p' RPA_docs/PLAN.md    # 10 luật cấm
sed -n '/^## 3. Chỉ số/,/^## 4/p' RPA_docs/ORACLE.md  # ngưỡng phải đạt
```

| File | Trả lời |
|------|---------|
| [`RPA_docs/README.md`](RPA_docs/README.md) | chỉ mục và luật của tài liệu |
| [`RPA_docs/PROGRESS.md`](RPA_docs/PROGRESS.md) | **đang ở đâu** — đọc trước tiên |
| [`RPA_docs/PLAN.md`](RPA_docs/PLAN.md) | G0–G5, 10 luật bất biến, 50 điều kiện cổng |
| [`RPA_docs/ORACLE.md`](RPA_docs/ORACLE.md) | "thực thi đúng" nghĩa là gì, đo bằng gì |
| [`RPA_docs/DIAGNOSIS.md`](RPA_docs/DIAGNOSIS.md) | 6 lỗi gốc L1–L6, có bằng chứng, đóng băng |
| [`RPA_docs/KNOWN_LIMITS.md`](RPA_docs/KNOWN_LIMITS.md) | cái gì hỏng mà **không được vá** — đọc trước khi "sửa" một case |
| [`RPA_docs/DECISIONS.md`](RPA_docs/DECISIONS.md) | vì sao chọn thế, còn quyết định nào đang treo |
| [`RPA_docs/ENVIRONMENT.md`](RPA_docs/ENVIRONMENT.md) | môi trường chạy phải cố định thế nào |
| [`REQUIREMENTS.md`](REQUIREMENTS.md) | yêu cầu nguyên văn của người giao việc |
| [`RESULTS.md`](RESULTS.md) | số liệu — **đọc kèm cảnh báo bên dưới** |

---

## Cảnh báo về `RESULTS.md`

`RESULTS.md` báo tỉ lệ bước **98,13%** (bộ cũ) và **93,88%** (bộ mới). Hai con số
đó đo ở **mức N0** — "không ném ngoại lệ" — với ngưỡng đạt lỏng 50%. Đo lại đúng
thì chỉ **24,6%** bước `Move` dịch đúng khoảng cách trên bộ mới.

Không trích dẫn hai con số đó như tỉ lệ thành công. Xem `RPA_docs/DIAGNOSIS.md`
§1 và `RPA_docs/ORACLE.md` §1.

---

## Luật không bao giờ được vi phạm

Bản đầy đủ ở `RPA_docs/PLAN.md` §Bất biến. Bốn luật hay bị quên nhất:

1. **Không leakage.** Đường thực thi chỉ được mở `.png`. `*.png.graph.json`
   (answer key) và `*.xml` (nguồn) chỉ được mở trong `judge_*`, sau khi đã chạy
   xong. Từ 2026-09-22 luật này được `RPA_drawio/leak_guard.py` thực thi bằng
   audit hook — harness tự arm, nên vi phạm là ném lỗi chứ không phải quên.
2. **Không hard-code theo case.** Cấm `if case_id == ...`, cấm bảng tra theo tên
   file. Bản vá phải phát biểu được thành quy tắc về *công cụ vẽ cư xử thế nào*.
3. **Không báo cáo dưới mức N3.** N3 = đúng hậu điều kiện. Mọi bảng phải ghi rõ
   nó đang ở mức phán định nào. Phán định do `RPA_drawio/oracle_verdict.py` đưa
   ra, đọc model mxGraph qua `mx_oracle.py` — **không** lấy từ trường `status`
   của executor. Trường đó vẫn được ghi, chỉ để đếm báo đạt sai.
4. **Báo đạt sai là lỗi chặn.** Một bước đánh `ok` trong khi ứng dụng làm sai là
   lỗi nặng nhất của dự án. Phát hiện ra thì dừng, sửa, chạy lại.

**Không qua cổng thì không sang giai đoạn sau.** Cổng ở `RPA_docs/PLAN.md`.

---

## Môi trường

```bash
python --version                       # 3.12.4 hệ thống
# venv riêng của dự án (đã có sẵn đủ gói):
RPA_drawio/venv_rpa/Scripts/python.exe
```

* **Chrome**: `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`
* **Cổng debug**: mặc định 9222, đổi bằng `RPA_CHROME_DEBUG_PORT`. Chạy nhiều
  worker song song thì mỗi worker một cổng.
* **Khoá LLM**: `D:\SVG_agent\.env` (Gemini trước → OpenAI → Anthropic).
* **Model NLP**: `RPA_drawio/src/main/resources/models/` (stanza + sentence-
  transformers, ~1GB, bị gitignore). Các đường dẫn này **tính theo cwd**, nên
  harness `os.chdir` vào `RPA_drawio/` trước khi import.

⚠️ Một Chrome debug còn sót chạy song song sẽ tranh CPU và làm **rớt phím
Shift+Arrow** — `RESULTS.md` §9 đã dính một lần, `scenario_050` ra 34/41 thay vì
41/41. Dọn sạch tiến trình Chrome trước mỗi lượt chạy chính thức.

---

## Lệnh

```bash
# ảnh -> kịch bản text (chỉ đọc PNG, không đọc answer key)
python RPA_drawio/image_to_scenario.py \
    --images "../data/datasets/easy/*.png" --out RPA_Datasets_new30_v2

# chạy một lượt (harness tự quản trình duyệt, ghi report.json + canvas.png)
python run_drawio_v2.py --scenarios RPA_Datasets_new30_v2 --out result/<tên> [--limit N] [--port 9222]

# chấm bằng VLM, so ảnh với ảnh
python judge_drawings.py --results result/<tên> \
    --references "D:/SVG_agent/data/datasets/*/{id}.png"

# harness gốc, giữ lại để tái lập baseline — đừng sửa
python run_rpa_drawio_batch.py

# tái sinh từng con số trong tài liệu
python RPA_docs/checks/move_accuracy.py result/old100_v2 result/new30_v2
python RPA_docs/checks/cells_of.py result/new30_v2/<case>
python RPA_docs/checks/judge_summary.py result/old100_v2 result/new30_v2
python RPA_docs/checks/corpus_stats.py

# G0 trở đi: chấm bằng oracle độc lập, không phải bằng trạng thái của executor
python RPA_docs/checks/run_all_checks.py          # mọi kiểm tra ngoại tuyến, một lệnh
python RPA_docs/checks/report.py result/<tên>     # in đúng mẫu ORACLE.md §6
python RPA_docs/checks/graph_score.py result/<tên>   # mức hình, tất định
python RPA_docs/checks/false_pass.py result/<tên> --write-sample
python RPA_docs/checks/baselines.py --run result/<tên>
```

Bảng đầy đủ của `RPA_docs/checks/` nằm ở cuối [`RPA_docs/README.md`](RPA_docs/README.md).

### Cờ của executor

Bốn cờ bật/tắt các bản vá G1, để cặp so sánh trước/sau chạy trên **cùng một bản
code** thay vì hai bản khác nhau. Mặc định **bật**; `env.json` của mỗi lượt chạy
ghi lại trạng thái từng cờ.

```bash
RPA_CLOSED_LOOP_MOVE=0   # G1.1 tắt vòng kín của Move
RPA_ANCHOR_INSERTS=0     # G1.3 tắt neo điểm chèn theo toạ độ model
RPA_CLOSED_LOOP_RESIZE=0 # G1.4 tắt vòng kín của Extend/Shrink
RPA_CLOSED_LOOP_LABEL=0  # G1.8 tắt vòng kín của nhãn
```

---

## Bản đồ dữ liệu

| Bộ | Đường dẫn | Số case |
|---|---|---|
| RPA_Datasets, drawio (bộ cũ, text) | `RPA_Datasets/data/drawio/` | 100 |
| RPA_Datasets, Lucidchart | `RPA_Datasets/data/lucid_chart/` | 100 |
| RPA_Datasets, Visual Paradigm | `RPA_Datasets/data/visual_paradigm/` | 101 |
| Benchmark ảnh, drawio | `../data/datasets/` | 506 (42/252/212) |
| Benchmark ảnh, Visual Paradigm | `../data/datasetsVP/` | 497 (42/252/203) |
| Benchmark ảnh, Lucidchart | `../data/datasetsLucid/` | 497 (42/252/203) |

Bộ RPA_Datasets trên máy **không khớp** bảng `tab:thong_ke_2` của `main.tex` —
xem `RPA_docs/DIAGNOSIS.md` §7. Không chỉnh số cho khớp bài báo.

---

## Giữ nguyên, đừng đụng

* `RPA_drawio/generator.py`, `step_parser.py`, `by_text.py`, `by_image*.py`,
  `find_element.py`, `detect_new_g.py` — code gốc của người đi trước. Sửa thì
  baseline không tái lập được nữa. Code mới đặt ở file mới.
* `run_rpa_drawio_batch.py` — harness của lượt baseline.
* `_git_vendor_backup/` trong mỗi project — `.git` gốc của kho upstream, đã đổi
  tên sang một bên. Khôi phục bằng `mv <proj>/_git_vendor_backup <proj>/.git`.

---

## Cập nhật ở đâu khi có việc gì

| Việc | File phải sửa |
|------|---------------|
| Đo được một con số mới | `RPA_docs/PROGRESS.md` + một script trong `RPA_docs/checks/` |
| Tìm ra một lỗi gốc mới | `RPA_docs/DIAGNOSIS.md` (thêm mục, **không sửa số cũ**) |
| Qua được một cổng | tick ở `RPA_docs/PROGRESS.md`, đổi dòng "Giai đoạn hiện tại" |
| Đổi tiêu chí hoặc ngưỡng | `RPA_docs/ORACLE.md` hoặc `RPA_docs/PLAN.md`, **kèm lý do**, và báo người giao việc |
| Chốt số chính thức | `RESULTS.md`, theo mẫu `RPA_docs/ORACLE.md` §6 |
| Thực nghiệm thất bại | vẫn ghi vào `RPA_docs/PROGRESS.md`, kèm nguyên nhân gốc |

**Không commit khi chưa được yêu cầu.**
