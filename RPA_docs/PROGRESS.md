# Tiến độ

File duy nhất thay đổi thường xuyên. Ghi theo thứ tự thời gian, mới nhất ở trên.
Mỗi mục phải trả lời: **đo được gì**, bằng **lệnh nào**.

---

## Trạng thái

| | |
|---|---|
| **Giai đoạn hiện tại** | **G0 — dựng thước đo trung thực**. TẠM DỪNG 2026-09-23, không tiến trình nào đang chạy |
| Cổng đang treo | G0 (15/19 điều kiện) |
| Được phép làm | việc của G0; code của G1 đã viết nhưng **chưa được tính là qua cổng** |
| **Chưa được phép** | sửa converter (G2), chạy diện rộng (G3), Visual Paradigm (G4), Lucidchart (G5) |

### Cổng G0 — chi tiết ở [`PLAN.md`](PLAN.md)

**Năng lực phán định**

- [x] 11 hành động có hậu điều kiện N3 (`press` ở N2 kèm lý do; `click` trên kho icon hỗn hợp ở N2, xem D12) — `RPA_drawio/oracle_verdict.py`
- [x] `Move`/`Connect`/`Delete` có kiểm tra N4
- [ ] Báo đạt sai của thước mới = 0 (mẫu rà tay ≥50 bước) — **cần lượt chạy xong rồi mới rà được**
- [x] Đo được báo đạt sai của thước **cũ** — **0,21%** [0,06–0,78] (2/931) trên 20 case đã chạy
- [x] Oracle đọc mxGraph XML qua đường mã độc lập với executor — `checks/oracle_independence.py`: ép executor báo 100% đạt, oracle vẫn bắt 7–8 bước hỏng
- [x] Bộ chấm qua cả 9 ca đột biến, kể cả ca "vẽ thừa không được tăng điểm" — 9/9 trên **toàn bộ 506** answer key
- [x] Mọi chỉ số "tìm đúng" có "vẽ thừa" đi kèm — `node_excess` / `edge_excess` trong `checks/graph_score.py`

**Hạ tầng**

- [x] Đồ thị phụ thuộc tách được hỏng gốc ↔ hỏng kéo theo — `RPA_drawio/oracle_steps.py`
- [x] Ba baseline tầm thường chạy được — `checks/baselines.py`
- [x] Test leakage đỏ khi cố mở answer key — `RPA_drawio/leak_guard.py` + `checks/test_no_leakage.py`, 4/4
- [x] `RPA_docs/splits.json` tất định — `checks/verify_splits.py`
- [x] Baseline thật cho 30 case, in đúng mẫu `ORACLE.md` §6 — **30/30 case xong** 2026-09-24 (`result/g0_baseline/report.txt`); N3 99,69% [99,28–99,87] (1612/1617), move N3+N4 100% (739/739), overall hình 0,8831; `shape_type_accuracy` vẫn thấp (0,657, đúng L6)

**Môi trường**

- [x] ~~Chốt D9~~ — đã chốt: ghim `jgraph/drawio:28.2.5` cục bộ + lượt đối chứng
- [x] Dựng container và trỏ `DRAWIO_URL` vào đó — `rpa_env.py` đọc `.env` thay vì hard-code
- [ ] Kiểm lại `palette_matcher` trên bảng shape bản ghim — `checks/palette_check.py` đã viết, chưa chạy
- [ ] Lượt đối chứng 30 case: bản ghim vs `app.diagrams.net` — **lượt đầu hỏng vì hai harness chạy song song**, đã cách ly ở `result/_INVALID_contrast_20260923/`, phải chạy lại
- [x] `env.json` ghi cho mọi lượt chạy — kèm cả ba cờ G1
- [x] `requirements.lock.txt`

### Cổng G1 — code xong, **chưa có số**

Mọi ô dưới đây cần `result/g1_after` chạy xong mới tick được.

- [ ] `Move` đạt N3 ≥98% trên ≥200 bước
- [ ] `Move`/`Connect`/`Delete` đạt N4 100%
- [ ] Điểm chèn trôi <5px qua 10 lần chèn liên tiếp
- [ ] Kích thước hình đạt tỉ lệ khung mục tiêu ±10%
- [ ] `Connect` đạt N3 ≥95%
- [ ] Báo đạt sai = 0, cận trên KTC 95% <2%
- [ ] Báo hỏng sai ≤2%; hỏng thầm lặng ≤1%
- [ ] Đẳng cấu ≥95% qua 5 lần; vị trí p95 ≤5px; phán định ổn định ≥98%
- [x] Cơ chế điểm chèn ghi thành văn ở `DIAGNOSIS.md` §9.2
- [ ] Không nhánh nào rẽ theo id case (rà bằng grep, ghi kết quả)

---

## 2026-09-24 — khảo sát `Kết quả thực nghiệm.xlsx`, không đổi tiến độ G0/G1

Người giao việc cung cấp file mới. Đọc 16 sheet, đối chiếu `main.tex` và code
gốc. **Không thay đổi cổng nào đang treo** — 5 việc còn lại của G0/G1 (mục
"ĐANG LÀM DỞ" ở `TRACE.md`) vẫn y nguyên. Kết quả của lượt này:

- Xác nhận số của `main.tex` có nguồn thật (khớp workbook tuyệt đối).
- Xác nhận trực tiếp, bằng lời tác giả: pipeline cũ không có oracle hình học —
  đúng luận điểm nền của `ORACLE.md`.
- Ba lỗi gốc mới cho Lucidchart/Visual Paradigm, xếp vào `KNOWN_LIMITS.md`
  B6–B8, chờ tới G4/G5.

Chi tiết đầy đủ: `DIAGNOSIS.md` §10, `DECISIONS.md` D14, `TRACE.md` mục
2026-09-24.

```bash
for f in DIAGNOSIS PLAN ORACLE KNOWN_LIMITS DECISIONS; do
  sha256sum "RPA_docs/$f.md"
done   # đối chiếu RPA_docs/LOCKS.md
```

---

## 2026-09-23 — TẠM DỪNG. Baseline G0.6 xong 20/30, lượt đối chứng phải bỏ

**Trạng thái khi dừng.** Người giao việc yêu cầu tạm dừng. Mọi tiến trình harness
và Chrome cổng 9222 đã dừng sạch. Không có gì đang chạy.

### Đo được gì — `result/g0_baseline`

Executor **trước G1** (cả bốn cờ tắt), draw.io **bản ghim 28.2.5**, chấm bằng
thước mới. **20/30 case** — 10 case `medium_*` cuối không chạy được, xem mục
"Sự cố" bên dưới. Mọi tỉ lệ dưới đây tính trên 20 case đã chạy.

| | |
|---|---|
| Đạt N3 | **99,68%** [99,06 – 99,89] (929/932) |
| Hỏng gốc | 0,21% (2/932) |
| Hỏng kéo theo | 0,11% (1/932) |
| Không phán định được | **0,00%** (0/932) |
| Báo đạt sai **của thước cũ** | 0,21% [0,06 – 0,78] (2/931) |
| Hỏng thầm lặng | 0,11% (1/932) |

Theo hành động: `move` **398/398 (100%)** · `click_shape` 111/111 · `open` 20/20
· `double_click` 146/147 · `fill` 146/147 · `connect` 108/109.

Mức hình (bộ chấm tất định, mẫu số là số đếm bản tham chiếu, n=20):

| | |
|---|---|
| node_f1 / node_excess | 1,0000 / 0,0000 |
| edge_f1 / edge_recall / edge_excess | 0,9700 / 0,9667 / 0,0167 |
| label_accuracy | 0,9625 |
| **shape_type_accuracy** | **0,6650** |
| edge_label_accuracy | 0,9833 |
| layout_score | 0,8893 |
| overall | 0,8974 |
| sai số vị trí sau Procrustes | trung vị 0,0262 · p95 0,0502 |

Sàn: canvas trắng **0,0000** · toàn chữ nhật **0,4260** · node không cạnh
**0,8000**. Theo band: easy overall 0,869 · hard overall 0,925.

### Hai điều phải đọc kỹ

**1. Con số 24,6% của `DIAGNOSIS.md` §1 không tái hiện được.** Cùng corpus, cùng
executor vòng hở, nhưng đo bằng `mxGeometry`: `move` đạt **398/398**. Ba khả
năng còn mở, và **lượt đối chứng chưa chạy nên chưa được kết luận cái nào**:
thước DOM cũ đo sai; `app.diagrams.net` khác bản ghim; hoặc máy lúc đó có Chrome
tranh CPU (mà `kill_chrome_on_port` khi ấy **im lặng không hoạt động** vì
Windows 11 đã bỏ `wmic` — xem `ENVIRONMENT.md`).

**2. Một phép đối chứng chéo ủng hộ bộ chấm mới.** `shape_type_accuracy` của bộ
chấm tất định ra **0,6650**; bộ chấm VLM đo trước đây ra **0,6587**
(`DIAGNOSIS.md` §6). Hai đường hoàn toàn độc lập cho cùng một con số — và nó
đúng bằng phần L6 (rounded rectangle) gây ra. Đây là bằng chứng độc lập rằng bộ
chấm mới không nói dối theo hướng có lợi.

### Sự cố 1 — 10 case `medium` không chạy: trình duyệt chết, khởi động lại hỏng

`restart failed: WebDriverException: Service ...chromedriver could not start`.
Xảy ra đúng lúc máy cạn bộ nhớ (hệ thống cũng đã tự dừng các tiến trình nền vì
lý do đó). Harness **không treo** — nó ghi lại và đi tiếp đủ 10 case, đúng yêu
cầu `ORACLE.md` §3.5. Cần chạy lại 10 case này khi máy rảnh bộ nhớ.

### Sự cố 2 — lượt đối chứng phải bỏ: **hai** harness chạy song song

Bản xếp hàng **cũ** (`chain_runs.sh`) vẫn còn sống và vẫn đang đợi baseline xong.
Khi baseline xong thì cả nó lẫn bản mới (`chain2.sh`) cùng khởi động lượt đối
chứng: hai tiến trình, cùng cổng 9222, cùng thư mục ra. Mỗi bên liên tục giết
Chrome của bên kia → `invalid session id` ngay bước 1, `N0 = 0/751`. Bản cũ còn
ghi đè `env.json` với cờ sai (`closed_loop_label: true`).

Thư mục đã chuyển sang `result/_INVALID_contrast_20260923/`, **không xoá**, kèm
`WHY_INVALID.md` ghi đủ nguyên nhân và lệnh chạy lại. **Không trích một con số
nào từ đó.**

### Sự cố 3 — `report.py` từng in một con số sai lệch, đã sửa

Nó gộp "case chưa từng chạy" vào "bước không phán định được", nên in ra **59,99%**
trong khi 20 case đã chạy đạt **99,68%**. Đúng loại số mà dự án này sinh ra để
chặn. Đã sửa: tỉ lệ tính trên case đã chạy, case không chạy được **đếm riêng và
gọi tên** ngay dòng đầu báo cáo.

### Lệnh tái sinh

```bash
python RPA_docs/checks/report.py result/g0_baseline --band
python RPA_docs/checks/graph_score.py result/g0_baseline
python RPA_docs/checks/false_pass.py result/g0_baseline --write-sample
python RPA_docs/checks/run_all_checks.py
```

## 2026-09-20 — soát tài liệu trước khi thực thi

**Làm gì.** Đối chiếu tài liệu với code thật để tìm chỗ còn thiếu trước khi bắt
đầu G0. Ra bốn lỗ.

| Lỗ | Cách xử |
|---|---|
| `ORACLE.md` §1 chỉ có 7 hành động, code có **11** hành vi phân biệt (thiếu `open`, `double click`, `press`, bí danh `enter`) | đã bổ sung đủ 11; cổng G0 sửa theo |
| Chính sách chia tập giữ kín chưa nói tỉ lệ, phạm vi, chạy mấy lần | chốt: `sha256(id)` → 20%, chia trong từng band, chạy đúng một lần |
| Chưa có nhật ký quyết định, chưa có danh sách giới hạn không được vá | thêm `DECISIONS.md` (9 mục) và `KNOWN_LIMITS.md` |
| **Harness chạy trên `app.diagrams.net`, không ghim phiên bản** — `.env` có `DRAWIO_URL=http://localhost:8080` nhưng bị bỏ qua; không có draw.io cục bộ nào chạy | thêm `ENVIRONMENT.md`; chốt D9 — ghim `jgraph/drawio:28.2.5` + lượt đối chứng |

**Lệnh tái sinh.**

```bash
grep -n "diagrams.net" RPA_drawio/rpa_env.py
grep -i drawio ../.env
sed -n '/_HANDLERS = {/,/}/p' RPA_drawio/drawio_executor.py   # 11 hành vi
sed -n '/SUPPORTED_ACTIONS = {/,/}/p' RPA_drawio/step_parser.py  # 15 mục từ vựng
```

Cổng G0 từ 13 lên **19 điều kiện**; tổng cả sáu cổng: 56.

---

## 2026-09-20 — bổ sung `ORACLE.md`

**Vì sao.** Người giao việc nhắc: đề tài là **kiểm thử**, nên tiêu chí phải xoáy
vào *khả năng thực thi chính xác*, không phải vào bản vẽ trông thế nào.

**Thêm gì.** `ORACLE.md`: thang phán định N0–N4, luật oracle phải độc lập với
executor, ngưỡng cho báo đạt sai / báo hỏng sai / hỏng thầm lặng / độ lặp lại /
độc lập giữa các bước / bất biến môi trường / chi phí, 9 ca kiểm thử đột biến
cho chính bộ chấm, 3 baseline tầm thường, và mẫu báo cáo bắt buộc.

Các cổng G0–G5 trong `PLAN.md` đã viết lại theo ngôn ngữ đó. Số luật bất biến
lên 10 (thêm: không báo cáo dưới N3; oracle độc lập; báo đạt sai là lỗi chặn).

---

## 2026-09-20 — khảo sát và chẩn đoán

**Làm gì.** Khảo sát toàn bộ kho, khôi phục phần đã có ở git HEAD (bị xoá khỏi
worktree, chưa commit việc xoá), đo lại hai lượt chạy đã lưu, viết
`DIAGNOSIS.md` và `PLAN.md`.

**Đo được gì.** Bác bỏ được con số 93,88% của `RESULTS.md`:

| | 100 case cũ | 30 case mới |
|---|---|---|
| Bước `Move` dịch đúng khoảng cách | 65,3% | **24,6%** |
| Bị đánh dấu `ok` nhưng sai khoảng cách | 34,7% | **64,4%** |
| Trung vị dịch chuyển (yêu cầu 150px) | 150px | **98px** |

Nguyên nhân: tiêu chí đạt trong `drawio_ops.move_cell()` là `>= distance_px // 2`.
Sáu lỗi gốc L1–L6 ghi ở `DIAGNOSIS.md`.

Phát hiện phụ: bộ dữ liệu trên máy không khớp bảng `tab:thong_ke_2` của
`main.tex` — draw.io đo được 12/38 + 88/605 so với 15/36 + 89/429 trong bài.

**Lệnh tái sinh.**

```bash
python RPA_docs/checks/move_accuracy.py result/old100_v2 result/new30_v2
python RPA_docs/checks/cells_of.py result/new30_v2/easy_e06_v6_s4b0l0
python RPA_docs/checks/judge_summary.py result/old100_v2 result/new30_v2
python RPA_docs/checks/corpus_stats.py
```

**Trạng thái kho.** Đã `git restore` phần đã có; bản gốc của tiền bối cất ở
stash `pristine-vendor-state-before-restore`, và vẫn nguyên trong
`_git_vendor_backup/` của từng project. Chưa commit gì.

**Tiếp theo.** G0.1 — cài hậu điều kiện N3 cho cả 11 hành động.
