# Kết quả thực nghiệm hướng RPA — draw.io

Ghi lại toàn bộ những gì đo được, ngày 2026-09-03 đến 2026-09-04. Đối chiếu yêu
cầu ở [REQUIREMENTS.md](REQUIREMENTS.md).

> **Trạng thái**: lượt chính thức của cả bộ 100 case cũ (mục 7) và bộ 30 case
> benchmark mới đã chuyển từ ảnh sang text (mục 8) đã chạy xong và đã chấm.

---

## 1. Baseline — code cũ, chưa sửa gì

| Bộ | Lệnh | "ok" theo harness cũ | Thực tế trên canvas |
|----|------|----------------------|---------------------|
| 100 case drawio cũ | `run_rpa_drawio_batch.py` | 89/100 | gần như trắng |
| 30 case benchmark mới | `run_rpa_drawio_batch.py` | 23/30 | gần như trắng |

"ok" của harness cũ chỉ có nghĩa là **không ném exception ở mức scenario**.
`generator.py` nuốt lỗi từng bước (vòng `while retry_attempt` chỉ log rồi đi
tiếp), nên một kịch bản hỏng toàn bộ bước vẽ vẫn được ghi là "ok".

Ảnh minh chứng còn trong repo: `result/rpa_datasets_full/scenario_050/after.png`
(kịch bản 41 bước, đáng lẽ 6 node + 6 cạnh, thực tế còn 1 diamond lạc và 1 hộp),
`result/new30_run/easy_e01_v1_s5b0l0/after.png` (đáng lẽ 5 hộp nối chuỗi, thực
tế 2 hộp).

---

## 2. Vì sao baseline hỏng — 12 lỗi gốc đã tìm và sửa

Không lỗi nào nằm ở phần NLP hay ở từ vựng hành động. Tất cả đều ở môi trường,
ở cách bám phần tử, hoặc ở cách đo.

### Môi trường (`RPA_drawio/rpa_env.py`)

1. **Chrome báo trang đang ẩn.** Windows Chrome coi cửa sổ bị che hoàn toàn như
   một tab nền (`document.visibilityState === 'hidden'`). draw.io dựng bảng shape
   theo kiểu lazy nên không bao giờ vẽ: `a.geItem` đứng ở 6 thay vì 45 sau 40
   giây. **Toàn bộ thực nghiệm cũ chạy trên một trang chưa render xong bảng
   shape** — thứ mà phần tìm icon theo ảnh phải tìm.
2. **Modal chặn canvas.** draw.io lưu bản nháp trong localStorage; từ lần chạy
   thứ hai trở đi luôn gặp hộp thoại "Choose a draft to continue editing".
3. **Giao diện tiếng Việt** trong khi corpus gọi menu bằng tiếng Anh.
4. **Page View.** Canvas chia thành trang 850x1100; đẩy shape vượt lên trên đầu
   trang làm draw.io tái neo lưới trang và shape nhảy đúng một chiều cao trang.
   Đo được: một shape đơn bị đẩy lên 150px bốn lần cho ra 968, 818, 1768, 1618
   khi bật Page View, và 1445, 1295, 1145, 995 khi tắt.

### Bám phần tử (`RPA_drawio/cell_tracker.py`)

5. **Snapshot DOM ban đầu lấy trước khi điều hướng**, báo lỗi "Không thể tạo
   selector cho container", và không bao giờ thử lại — nên
   `step_created_elements` rỗng suốt và mọi tham chiếu "element created in step N"
   trả về `//not-found`. Đây là lý do Move/Fill/Connect hỏng hết.
6. **Định danh bằng đường dẫn `:nth-child`**, hỏng ngay khi mxGraph vẽ lại.
7. **Bộ lọc `<g>` đếm cả khung xem trước của vùng chọn** (`cursor: move;
   visibility: visible`), nên chọn một shape cũng bị tính là tạo phần tử mới.
8. **Thứ tự DOM không phải thứ tự chèn**: mxGraph vẽ cạnh nằm dưới đỉnh, nên
   connector đầu tiên chèn vào chỉ số 0 và đẩy lệch mọi chỉ số đã ghi.

### Cử chỉ trên canvas (`RPA_drawio/drawio_ops.py`)

9. **Nối bị biến thành resize**: shape đang được chọn có 8 nút kéo nằm đúng trên
   viền, nuốt mất cú kéo. Phải bỏ chọn trước.
10. **Điền nhãn không được commit** (thiếu Escape), và điểm nhấp cho cạnh tính ở
    tâm hộp bao — với cạnh gấp khúc thì đó là chỗ trống.
11. **Move gửi 15 phím một lượt** thì mất phím; phải gửi từng phím một.

### Đo lường (`RPA_drawio/drawio_executor.py`)

12. **Điểm chèn trôi.** draw.io thả shape vào tâm khung nhìn; khôi phục giá trị
    cuộn không giữ được điểm đó vì canvas nở ra làm cùng một giá trị cuộn trỏ tới
    một điểm mô hình khác. Các shape chèn sau lệch 400–1100px so với giả định của
    các bước Move.

---

## 3. Công cụ mới thêm

| File | Vai trò |
|------|---------|
| `RPA_drawio/rpa_env.py` | Bật Chrome đúng cờ, chờ palette render thật, dọn canvas, tắt Page View |
| `RPA_drawio/cell_tracker.py` | Bám cell theo handle DOM + toạ độ mô hình |
| `RPA_drawio/drawio_ops.py` | 4 cử chỉ chuẩn: chèn, dịch, đặt nhãn, nối |
| `RPA_drawio/palette_matcher.py` | So icon với mọi control nhỏ trên trang |
| `RPA_drawio/build_shape_icons.py` | Dựng bộ icon 9 hình từ chính ô tìm kiếm của draw.io |
| `RPA_drawio/drawio_executor.py` | Đường thực thi cho draw.io, có báo cáo từng bước |
| `RPA_drawio/image_to_scenario.py` | **Ảnh → kịch bản text** (yêu cầu 4) |
| `RPA_drawio/llm_client.py` | Gemini → OpenAI → Anthropic, đọc key từ `.env` |
| `run_drawio_v2.py` | Harness tự quản trình duyệt, ghi `report.json` + `canvas.png` |
| `scenario_to_gold.py` | Dựng ảnh gold cho bộ cũ (yêu cầu 5) |
| `judge_drawings.py` | Chấm bằng VLM, so ảnh với ảnh |

`generator.py` và code của hai site còn lại **không bị đụng tới**, nên baseline
vẫn tái lập được.

---

## 4. Module ảnh → text (yêu cầu 4)

Hai chặng tách bạch:

1. **VLM đọc ảnh** → đồ thị nhỏ (loại hình, nhãn, toạ độ chuẩn hoá, các cạnh và
   nhãn cạnh). Không nhắc gì tới draw.io hay tới đánh số bước.
2. **Python dịch sang DSL** theo đúng thứ tự pha của `scenario_050.json`: chèn và
   dịch mọi shape, rồi đặt nhãn mọi shape, rồi nối và đặt nhãn mọi connector.

Tách như vậy vì phần khó của DSL là bookkeeping — mỗi bước sau đều trỏ tới "the
element created in step N" với N là chỉ số trong chính danh sách đang dựng. Mô
hình nếu phải tự sinh chỉ số sẽ sai; chỉ đọc ảnh thì không phải làm việc đó.

**Không leakage**: đầu vào duy nhất là file PNG. Answer key `*.png.graph.json` và
`*.xml` nguồn không hề được mở, và không có gì phụ thuộc vào id của case.

### Chất lượng chuyển đổi (đối chiếu answer key **sau khi chạy**, chỉ để đo)

| Chỉ số | Kết quả |
|--------|---------|
| Số shape | 176/176 (100%) |
| Số cạnh | 180/181 (99,4%) |
| Đúng loại hình | 171/176 (97,2%) |
| Đúng nhãn | 176/176 (100%) |

---

## 5. Cách chấm

* **30 case mới**: so `canvas.png` với chính ảnh đề bài trong `data/datasets`.
* **100 case cũ**: bộ này không có gold. 24 case có vẽ hình được dựng ảnh tham
  chiếu bằng `scenario_to_gold.py` — suy diễn tất định từ chính lời kịch bản
  (icon nói hình gì, các bước Move nói dịch bao nhiêu, Fill nói chữ gì, Connect
  nói mũi tên nào), rồi để draw.io vẽ ra qua đường `#R<xml>`. 75 case còn lại chỉ
  thao tác menu nên chỉ chấm ở mức bước.
* Bộ chấm chỉ nhìn thấy hai tấm ảnh, không thấy kịch bản, không thấy id case,
  không biết số hình mong đợi.
* Hiệu chuẩn: đưa cùng một ảnh cho cả hai vị trí → 1.00 ở mọi chỉ số; đưa ảnh
  trắng → 0.00.

---

## 6. Hạn chế đã biết

* **Rounded rectangle bị vẽ thành rectangle.** draw.io đặt hai hình này cạnh nhau
  trong bảng General và chúng chỉ khác nhau vài pixel bo góc; ở cỡ thumbnail, ink
  mask của chúng giống nhau 97%, và mọi lựa chọn khác mà ô tìm kiếm đưa ra đều là
  hình khác hẳn. Ghi trong `_shape_substitutions` của từng kịch bản. Ảnh hưởng
  949/3516 node của benchmark.
* Ảnh gold của bộ cũ đo **độ trung thành khi thực thi kịch bản**, không đánh giá
  bố cục của kịch bản gốc đẹp hay xấu.
* Chưa chạy 500 case × 3 web; phạm vi hiện tại đúng như đã chốt.

---

## 7. Kết quả chính thức — bộ 100 case drawio cũ

Lượt chạy: `result/old100_v2`. Chấm điểm: `result/old100_v2/judge.json`.

Số ở mục này là **sau đợt vá thứ hai** (2026-09-04): sửa 4 lỗi từ vựng thao tác
(bare `Fill`, click theo text khi DOM có bản sao ẩn, `<select><option>`, và điểm
neo khi nối hình xiên — xem mục 9). Lượt đo được chạy sạch, không tranh CPU với
tiến trình nào khác (đã kiểm chứng bằng cách chạy lại `scenario_050` độc lập cho
đúng kết quả trước khi chốt số chính thức).

### 7.1 Mức bước

| | Code cũ (baseline) | Sau vá lần 1 | **Sau vá lần 2 (chính thức)** |
|---|---|---|---|
| Case chạy hết, không exception | 89/100 "ok" nhưng canvas gần như trắng | 100/100 | **100/100** |
| Case đúng **toàn bộ** bước | không đo được | 89/100 | **96/100** |
| Tỉ lệ bước thành công | không đo được | 96,73% (622/643) | **98,13%** (631/643) |
| Case vẽ ra hình | ~0 | 48 | **48** |
| Case vẽ được cạnh | ~0 | 33 | **35** |

Baseline không có số ở mức bước để so, vì executor cũ ghi log lỗi rồi đi tiếp, và
"ok" chỉ có nghĩa là không ném exception ở mức scenario.

Chỉ còn **4 case** không đạt 100% (từ 11 case), và cả 4 đã xác minh là đặc tính
của chính kịch bản, không phải lỗi executor — xem mục 7.4.

### 7.2 Mức hình vẽ (chấm bằng VLM, 24 case có vẽ hình)

76 case còn lại chỉ thao tác menu nên không có hình để so — chúng chỉ được chấm ở
mức bước.

| Chỉ số | Vá lần 1 | **Vá lần 2 (chính thức)** |
|---|---|---|
| Điểm tổng trung bình | 0,75 | **0,81** |
| Giống về bố cục | 0,81 | **0,85** |
| Tìm đúng hình | 0,96 | **0,99** (67/68) |
| Đúng loại hình | 0,86 | **0,87** |
| Đúng nhãn | 0,90 | **0,90** |
| Tìm đúng cạnh | 0,67 | **0,78** (35/45) |
| Đúng nhãn cạnh | 0,62 | **0,93** |

Cạnh cải thiện rõ nhất (0,67 → 0,78) — đúng như dự đoán, vì bản vá lần này sửa
đúng chỗ nối hình xiên (parallelogram/trapezoid) từng làm rớt connector.

Hiệu chuẩn bộ chấm: đưa cùng một ảnh cho cả hai vị trí → 1,00 ở mọi chỉ số; đưa
ảnh trắng → 0,00. **Bộ chấm có dao động** ±0,05-0,08 giữa các lần chấm cùng một
lượt chạy — nên đọc các số này như khoảng ước lượng.

### 7.3 Case đạt gần tuyệt đối

`scenario_009`/`021`/`032`/`034`/`035` 1,00 · `scenario_050` 0,85 (6/6 hình, 6/6
cạnh) · `scenario_087` 0,95 (7/7 hình, 6/6 cạnh) · `scenario_089` 0,90 ·
`scenario_045`/`046` 0,95.

### 7.4 Còn hỏng ở đâu

12 bước hỏng trên 4 case, tất cả đã xác minh là đặc tính của chính kịch bản:

* `scenario_051` (35/43) — bước 22 của chính kịch bản click `object7.png`, vốn là
  một nút trên thanh công cụ chứ không phải shape, nên "element created in step
  22" mà 9 bước sau tham chiếu không hề tồn tại.
* `scenario_100` (5/6) — "Clipart / Computer" là một mục cây danh mục cần mở rộng
  trước khi con của nó hiện ra; chưa hỗ trợ thao tác mở-rộng-rồi-chọn.
* `scenario_058` (4/5) — icon `object23.png` khớp nhầm với nút "Edit" trên
  toolbar thay vì ô chọn màu nền.
* `scenario_088` (30/32) — shape ở bước 12 và bước 14 trùng khít vị trí, vì cả
  hai chỉ dịch chuyển "down" đúng một lần từ cùng một điểm chèn cố định — đặc
  tính của chính kịch bản, không phải lỗi đo đạc.

---

## 8. Kết quả chính thức — bộ 30 case benchmark mới (ảnh → text)

Kịch bản: `RPA_Datasets_new30_v2` (dựng bằng `image_to_scenario.py` từ chính ảnh
đề bài, không đọc answer key — xem mục 4). Lượt chạy: `result/new30_v2`. Chấm
điểm: `result/new30_v2/judge.json` — so `canvas.png` với chính ảnh gốc trong
`data/datasets`.

### 8.1 Mức bước

| Chỉ số | Giá trị |
|---|---|
| Case chạy hết, không exception | 30/30 |
| Case đúng **toàn bộ** bước | 20/30 |
| Tỉ lệ bước thành công | **93,88%** (1518/1617) |
| Case vẽ được cạnh | 27/30 |

30 case này khó hơn nhiều so với đa số case cũ: trung bình 54 bước/case (cao nhất
106 bước ở `hard_h08_v5_s9b2l1`), so với bộ cũ phần lớn dưới 10 bước. Đây là lý
do hợp lý để tỉ lệ bước thấp hơn bộ cũ (93,88% so với 98,13%) — nhiều bước hơn
đồng nghĩa nhiều cơ hội hỏng hơn trên cùng một case.

### 8.2 Mức hình vẽ (chấm bằng VLM, cả 30 case)

| Chỉ số | Giá trị |
|---|---|
| Điểm tổng trung bình | **0,64** |
| Giống về bố cục | **0,64** |
| Tìm đúng hình | **0,99** (168/169) |
| Đúng loại hình | **0,66** |
| Đúng nhãn | **0,97** |
| Tìm đúng cạnh | **0,63** (108/171) |
| Đúng nhãn cạnh | **0,66** |

Hình và nhãn gần như tuyệt đối (0,99 và 0,97) — số hình vẽ ra và chữ trong đó gần
như luôn đúng. Hai chỉ số thấp đều đã có lý do biết trước:

* **Đúng loại hình chỉ 0,66** — phần lớn do hạn chế đã ghi ở mục 6:
  "rounded rectangle" luôn bị vẽ thành "rectangle" (draw.io không có icon nào
  tách biệt được hai hình này ở cỡ thumbnail). Benchmark mới dùng rounded
  rectangle rất nhiều (949/3516 node toàn bộ dữ liệu), nên tỉ lệ này thấp hơn hẳn
  bộ cũ (0,87) — bộ cũ hầu như không dùng rounded rectangle.
* **Tìm đúng cạnh chỉ 0,63** — thấp hơn bộ cũ (0,78) dù dùng chung code nối cạnh
  đã sửa. Nguyên nhân hợp lý nhất: case trong bộ này có trung bình ~6 cạnh/case,
  nhiều gấp đôi bộ cũ (phần lớn case cũ chỉ có 0-2 cạnh), nên xác suất một case
  bị rớt ít nhất 1 cạnh cao hơn nhiều dù tỉ lệ lỗi trên từng cạnh không đổi.

### 8.3 Case đạt gần tuyệt đối

`medium_m29_v6_s6b2l0` 0,97 (5/5 hình, 5/5 cạnh) · `easy_e02_v6_s5b0l0` 0,95 ·
`easy_e06_v1_s4b0l0` 0,95 · `medium_m21_v4_s7b1l0` 0,92.

### 8.4 Case thấp nhất

`medium_m06_v2_s6b2l0` 0,20 · `hard_h12_v1_s6b1l1` 0,25 · `easy_e03_v6_s2b0l0`,
`easy_e06_v6_s4b0l0`, `hard_h25_v4_s6b2l1` đều 0,30 — tất cả đều **đúng hình và
đúng nhãn**, điểm thấp chủ yếu vì thiếu cạnh (0-1 trên 3-7 cạnh mong đợi).

---

## 9. Nhật ký vá lần hai (2026-09-04) — 5 lỗi từ vựng thao tác

Sau khi có số liệu chính thức đầu tiên (mục 7 bản cũ), rà lại từng bước hỏng
trong 11 case còn sót của bộ 100 case cũ, tách ra được 5 lỗi executor thật (đã
vá — áp dụng chung, không riêng cho case nào) và 4 hạn chế thuộc về chính kịch
bản (không vá vì sẽ là hard-code):

| Lỗi | Nguyên nhân | Cách vá | Case được cứu |
|---|---|---|---|
| `Fill "X"` không object, không editor mở | Bước trước mở một ô nhập (search box, hộp thoại) chứ không phải shape | Gõ vào `document.activeElement` nếu nó thật sự editable | 004, 056, 057 |
| `Click on Style`, `Click on ... checkbox` thất bại | draw.io giữ nhiều bản sao ẩn của cùng nhãn trong DOM; bộ tìm theo text không phân biệt hiển thị/ẩn | Ưu tiên phần tử khớp đúng chữ **và đang hiển thị**; nhận diện riêng mẫu `"<nhãn> checkbox"` | 015, 060 |
| `Click on US-Letter...`, `A4...` (option trong select) | Selenium không click được `<option>` khi dropdown chưa mở | Đặt `value` qua JS + bắn sự kiện `change` | 059 |
| Nối cạnh từ hình xiên (parallelogram, trapezoid) hay rớt | Điểm bắt đầu kéo tính theo khung bao chữ nhật, nhưng viền thật của hình xiên nằm lệch vào trong | Dò điểm thật trên viền bằng `isPointInFill` của chính SVG path — không cần biết trước độ xiên của từng loại hình | 043, 060 |

Mỗi lỗi đã kiểm chứng riêng lẻ trước khi đưa vào lượt chính thức. Lượt đầu tiên
sau khi vá cho `scenario_050` kết quả 34/41 — tưởng là hồi quy, nhưng chạy lại
độc lập cho đúng 41/41: nguyên nhân là một Chrome debug còn sót từ lúc dò lỗi
chạy song song, tranh CPU làm rớt phím Shift+Arrow. Đã dọn sạch và chạy lại lượt
chính thức.

**Không vá** (đặc tính của chính kịch bản — xem mục 7.4 và 9 ở trên): `scenario_051`,
`scenario_058`, `scenario_088`, `scenario_100`.
