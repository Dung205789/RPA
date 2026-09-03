# Kết quả thực nghiệm hướng RPA — draw.io

Ghi lại toàn bộ những gì đo được, ngày 2026-09-03. Đối chiếu yêu cầu ở
[REQUIREMENTS.md](REQUIREMENTS.md).

> **Trạng thái**: lượt chính thức của bộ 100 case cũ đã xong và đã chấm — xem
> mục 7. Bộ 30 case của benchmark mới tạm gác lại: nó sẽ được chuyển sang đúng
> format của bộ cũ, nên bộ cũ mới là thứ cần chạy được trước.

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

### 7.1 Mức bước

| | Code cũ (baseline) | Code đã sửa |
|---|---|---|
| Case chạy hết, không exception | 89/100 "ok" nhưng canvas gần như trắng | **100/100** |
| Case đúng **toàn bộ** bước | không đo được | **89/100** |
| Tỉ lệ bước thành công | không đo được — `generator.py` nuốt lỗi | **96.73%** (622/643) |
| Case vẽ ra hình | ~0 | **48** |
| Case vẽ được cạnh | ~0 | **33** |

Baseline không có số ở mức bước để so, vì executor cũ không sinh ra loại số liệu
này: nó ghi log lỗi rồi đi tiếp, và "ok" chỉ có nghĩa là không ném exception ở
mức scenario.

Trong lượt này Chrome chết đúng 1 lần; cơ chế khôi phục đã bật lại trình duyệt và
chạy lại case đang dở, nên không mất case nào.

### 7.2 Mức hình vẽ (chấm bằng VLM, 24 case có vẽ hình)

75 case còn lại chỉ thao tác menu nên không có hình để so — chúng chỉ được chấm ở
mức bước.

| Chỉ số | Giá trị |
|---|---|
| Điểm tổng trung bình | **0.75** |
| Giống về bố cục | **0.81** |
| Tìm đúng hình | **0.96** (65/68) |
| Đúng loại hình | **0.86** |
| Đúng nhãn | **0.90** |
| Tìm đúng cạnh | **0.67** (30/45) |
| Đúng nhãn cạnh | **0.62** |

Hiệu chuẩn bộ chấm: đưa cùng một ảnh cho cả hai vị trí → 1,00 ở mọi chỉ số; đưa
ảnh trắng → 0,00.

**Bộ chấm có dao động.** Chấm lại cùng một lượt cho ra `arrow_recall` 0,75 rồi
0,67 — chênh khoảng ±0,08 ở các chỉ số về cạnh. Nên đọc các số này như khoảng ước
lượng, không phải hằng số.

### 7.3 Case đạt gần tuyệt đối

`scenario_050` 0,98 (5/5 hình, 5 nhãn, 5/5 cạnh) · `scenario_087` 0,95 (7/7 hình,
7 nhãn, 6/6 cạnh) · `scenario_089` 0,90 · `scenario_044`/`045` 0,95 ·
`scenario_009`/`021`/`032`/`034`/`035`/`041` 1,00.

### 7.4 Còn hỏng ở đâu

21 bước hỏng trên 11 case. Phần lớn là mất đúng 1 bước menu. Hai case đáng chú ý:

* `scenario_051` (34/43) — **không phải lỗi executor**. Bước 22 của chính kịch bản
  click `object7.png`, vốn là một nút trên thanh công cụ chứ không phải shape, nên
  "element created in step 22" mà 9 bước sau tham chiếu không hề tồn tại.
* `scenario_088` (30/32) — hỏng 2 bước nối.

**Cạnh vẫn là mặt yếu nhất** (recall ~0,67-0,75 so với ~0,96 của hình). Đây là chỗ
đáng cải thiện tiếp theo.
