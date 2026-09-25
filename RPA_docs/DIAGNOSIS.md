# Chẩn đoán — vì sao bản vẽ vỡ cấu trúc

> 🔒 **KHOÁ NGÀY 2026-09-20.** File này là hợp đồng thiết kế của dự án. Sửa nội
> dung (không tính việc tick checkbox ở `PLAN.md`, đó là trạng thái, không phải
> thiết kế) bắt buộc phải: (1) ghi lý do vào `RPA_docs/TRACE.md`, (2) cập nhật
> hash trong `RPA_docs/LOCKS.md`, (3) nếu đổi ngưỡng hoặc luật, thêm mục LẬT
> vào `DECISIONS.md`. Sửa mà không làm cả ba bước này là vi phạm quy trình.


Đo ngày 2026-09-20 trên hai lượt chạy đã lưu trong `result/`. Mọi con số dưới
đây đều kèm lệnh tái sinh. File này **đóng băng**: khi đo lại ra số khác thì
thêm mục mới, không sửa số cũ.

> **Bối cảnh.** `RESULTS.md` báo tỉ lệ bước 98,13% (bộ cũ) và 93,88% (bộ mới).
> Người giao việc bác lại: nhìn bằng mắt thì hình phức tạp vỡ nặng. Bác bỏ này
> **đúng**, và phần dưới chỉ ra vì sao chỉ số bước không phát hiện được.

---

## 0. Kết luận trong một bảng

| Lỗi | Tầng | Thiệt hại đo được |
|-----|------|-------------------|
| L1 — `Move` chạy vòng hở, tiêu chí đạt lỏng 50% | executor | chỉ **24,6%** bước dịch đúng khoảng cách trên bộ mới |
| L2 — điểm chèn trôi giữa hai lần chèn | executor | x trải **268px** ngang khi kịch bản không có lệnh dịch ngang nào |
| L3 — quantum 150px quá thô ⇒ converter thổi phồng bố cục | mã hoá | giãn cách ≥255px trong khi hình chỉ 48×24px |
| L4 — không bao giờ đặt kích thước hình | mã hoá | mọi hình là 48×24 mặc định, tỉ lệ khung của ảnh gốc bị bỏ |
| L5 — `Connect` hỏng khi hình nhỏ và xa | executor | 18/180 hỏng hẳn, hỏng theo cụm |
| L6 — rounded rectangle luôn bị vẽ thành rectangle | nhận diện | `shape_type_accuracy` 0,66; ảnh hưởng 949/3516 node |

L3 và L4 là **hệ quả thiết kế của L1**: vì `Move` không tin được, người viết
converter phải giãn bố cục cho các node khỏi chồng nhau — đánh đổi độ chính xác
lấy độ an toàn. Không sửa L1 thì không có quyền đụng L3/L4.

L6 khác loại hẳn: không phải lỗi thực thi mà là giới hạn nhận diện icon. Đi
đường riêng.

---

## 1. L1 — `Move` chạy vòng hở, và thước đo tự nói dối

### Số đo

| | 100 case cũ | 30 case mới |
|---|---|---|
| Số bước `Move` | 98 | 739 |
| Dịch **đúng** 150px | 64 (**65,3%**) | 182 (**24,6%**) |
| Bị đánh dấu `ok` nhưng sai khoảng cách | 34 (34,7%) | 476 (**64,4%**) |
| Trung vị dịch chuyển | 150px | **98px** |
| Trung bình | 137px | 106px |

Phân bố khoảng cách thực tế trên bộ mới, khi mọi bước đều yêu cầu 150px:
`60, 75, 82, 83, 90, 97, 98, 105, 150` — gần như ngẫu nhiên.

### Vì sao

Hai chỗ cộng hưởng nhau:

* `RPA_drawio/drawio_ops.py` — `move_cell()` gửi 15 lần Shift+Arrow **vòng hở**,
  không đo lại. Dưới tải, phím bị rớt.
* Cùng hàm đó, tiêu chí đạt là `(|dx| + |dy|) >= distance_px // 2`. **Dịch 75px
  trên yêu cầu 150px vẫn được tính thành công.**

Vì mọi vị trí trong DSL đều tính tương đối so với một node neo, sai số **cộng
dồn** qua từng node. Đó chính là "vỡ cấu trúc".

### Vì sao chỉ số bước không phát hiện ra

Tỉ lệ bước 93,88% đếm số bước không ném lỗi, với ngưỡng đạt 50%. Nó **không đo
hình học**. Hai lượt chạy cho cùng một tỉ lệ bước có thể ra hai bản vẽ khác hẳn
nhau.

### Vì sao hình đơn giản trông vẫn ổn

65,3% đúng trên bộ cũ (98 bước, hình thưa) so với 24,6% trên bộ mới (739 bước,
hình dày). Case ít node thì sai số chưa kịp cộng dồn, và một node lệch 50px
trong bố cục thưa vẫn nhìn ra được ý. Đây đúng là hiện tượng người giao việc mô
tả: *bấm thì không sao, vẽ 1–2 hình cũng ổn, hình phức tạp thì hỏng*.

### Lệnh tái sinh

Script: `RPA_docs/checks/move_accuracy.py`

```bash
python RPA_docs/checks/move_accuracy.py result/old100_v2 result/new30_v2
```

---

## 2. L2 — điểm chèn trôi

### Bằng chứng: `easy_e06_v6_s4b0l0`

Ảnh gốc: 4 hộp 410×110 xếp **dọc**, cùng một trục x, nối bằng 3 mũi tên.
Kịch bản sinh ra: **không có một lệnh dịch ngang nào**. Vậy mà toạ độ cuối:

```
x:  496  →  688  →  764  →  764      (trôi +192, +76, 0)
y:  371  →  659  →  779  →  839
w×h: 48×24 ở cả bốn hình             (bước dịch là 150px)
```

`RESULTS.md` §2 mục 12 ghi lỗi này "đã sửa". Số liệu nói ngược lại.

### Lệnh tái sinh

```bash
python RPA_docs/checks/cells_of.py result/new30_v2/easy_e06_v6_s4b0l0
```

---

## 3. L3 + L4 — thang đo của bản vẽ không tự nhất quán

`RPA_drawio/image_to_scenario.py` đặt `TARGET_MIN_SEP_PX = 1.7 * MOVE_STEP_PX`
(= 255px): cặp node gần nhau nhất phải cách nhau ít nhất 1,7 bước dịch, nếu
không sẽ bị làm tròn về chung một ô lưới 150px.

Nhưng hình được chèn ở kích thước mặc định của draw.io và **không bao giờ được
đặt lại kích thước**, nên thực tế là 48×24px. Kết quả:

```
ảnh gốc : hộp 410×110, giãn cách ~250px   →  giãn cách ≈ 2,3 lần chiều cao hộp
bản vẽ  : hộp  48×24,  giãn cách ≥255px   →  giãn cách ≈ 10  lần chiều cao hộp
```

Bản vẽ giãn hơn ảnh gốc khoảng **4–9 lần** so với kích thước hình. Đó là lý do
bộ chấm mô tả "extremely sparse and poorly scaled", và cũng là lý do `Connect`
phải kéo qua quãng đường rất dài (xem L5).

Từ vựng DSL **đã có sẵn** `Extend` / `Shrink` (bảng `tab:bang4.5` của `main.tex`
liệt kê TS06 "Extend the right edge of the element created in step 1"), nhưng
converter không dùng.

---

## 4. L5 — `Connect`

| Bộ | `connect` ok | `connect` failed |
|---|---|---|
| 100 case cũ | 48 | 3 |
| 30 case mới | 162 | 18 |

Trong `easy_e06_v6_s4b0l0`, cả 3 lệnh `Connect` đều trả `before=4, after=4` —
không cạnh nào được tạo, dù 4 node đều tồn tại và đều có nhãn đúng.

**Chưa kết luận được** đây là lỗi độc lập hay hệ quả của L1–L4. Phải đo lại sau
khi hình học đã đúng. Ghi lại để không quên, không để suy đoán thành kết luận.

---

## 5. L6 — rounded rectangle

`RESULTS.md` §6 đã ghi: ở cỡ thumbnail, ink mask của "rectangle" và "rounded
rectangle" giống nhau 97%, nên bộ khớp icon không tách được. Converter khai báo
thay thế trong `_shape_substitutions` của từng kịch bản.

Hệ quả trên bộ mới: `shape_type_accuracy` = **0,6587**, trong khi
`shape_recall` = 0,994 và `label_accuracy` = 0,9702. Tức là **số hình đúng, chữ
đúng, riêng loại hình sai**. 949/3516 node của toàn bộ benchmark là rounded
rectangle.

Đây là hạn chế **được khai báo**, không phải cheating. Nhưng nó đang bị tính
gộp vào điểm tổng, làm điểm tổng khó đọc.

---

## 6. Điểm hình hiện tại (để đối chiếu về sau)

Chấm bằng VLM, `judge_drawings.py`. Bộ chấm dao động ±0,05–0,08 giữa các lần
chấm cùng một lượt chạy, nên đọc như khoảng ước lượng.

| Chỉ số | 100 case cũ (24 case có hình) | 30 case mới |
|---|---|---|
| Điểm tổng | 0,81 | **0,64** |
| Giống bố cục | 0,85 | **0,64** |
| Tìm đúng hình | 0,985 | 0,994 |
| **Đúng loại hình** | 0,866 | **0,659** |
| Đúng nhãn | 0,897 | 0,970 |
| **Tìm đúng cạnh** | 0,778 | **0,632** |
| Đúng nhãn cạnh | 0,929 | 0,657 |

Hai cột thấp nhất — bố cục và cạnh — đúng là hai thứ L1–L5 phá.

```bash
python RPA_docs/checks/judge_summary.py result/old100_v2 result/new30_v2
```

---

## 7. Bộ dữ liệu trên đĩa không khớp bảng trong `main.tex`

`main.tex` bảng `tab:thong_ke_2` so với đo trực tiếp `RPA_Datasets/data/`:

| Website | Paper: text | Đo: text | Paper: text+ảnh | Đo: text+ảnh |
|---|---|---|---|---|
| Draw.io | 15 kb / 36 thao tác | **12 / 38** | 89 kb / 429 thao tác | **88 / 605** |
| Lucidchart | 20 / 46 | **20 / 46** ✓ | 80 / 1010 | **80 / 1073** |
| Visual Paradigm | 24 / 80 | **24 / 80** ✓ | 76 / 756 | **77 / 808** |

Bộ trên máy **không phải** đúng bộ đã dùng viết bài. Tái hiện tuyệt đối bảng đó
là bất khả thi. Tái hiện *phương pháp* và báo cáo số của mình kèm ghi chú sai
lệch — xem `PLAN.md` §Bất biến, luật 5.

```bash
python RPA_docs/checks/corpus_stats.py
```

---

## 8. Quy mô công việc còn lại

| Bộ | Vị trí | Số case |
|---|---|---|
| RPA_Datasets drawio (bộ cũ) | `RPA_Datasets/data/drawio/` | 100 |
| Benchmark mới, drawio | `../data/datasets/` | **506** (42 easy / 252 medium / 212 hard) |
| Benchmark mới, Visual Paradigm | `../data/datasetsVP/` | **497** (42 / 252 / 203) |
| Benchmark mới, Lucidchart | `../data/datasetsLucid/` | **497** (42 / 252 / 203) |

Đến 2026-09-20, **chỉ 30/506 case** của bộ mới từng được chạy, và chỉ trên
draw.io. Visual Paradigm và Lucidchart **chưa được đụng tới** — `RESULTS.md` §3
ghi rõ "`generator.py` và code của hai site còn lại không bị đụng tới".

---

## 9. Đo lại ngày 2026-09-22, trên bản ghim — ba con số ở trên phải đọc lại

> Mục này **không sửa** số nào ở trên. Nó ghi một lượt đo mới, bằng thước khác,
> trên môi trường khác, và nói rõ chỗ nào lệch. Chỗ lệch chưa quy được trách
> nhiệm cho đến khi chạy xong **lượt đối chứng** bản ghim ↔ `app.diagrams.net`
> (D9) — cho tới lúc đó, đừng kết luận L1/L2/L4 là sai.

**Đo bằng gì.** `RPA_docs/checks/probe_editor.py`, đọc thẳng `mxGeometry` qua
`RPA_drawio/mx_oracle.py` (đường mã độc lập với executor, `ORACLE.md` §2), chạy
trên `jgraph/drawio:28.2.5` cục bộ. Kết quả thô: `RPA_docs/probe_editor.json`.

### 9.1 Shift+Arrow **không** rớt phím, và đúng 10 đơn vị

| Số phím gửi | Model dịch được | Mỗi phím | Phím mất |
|---|---|---|---|
| 1 | 10 | 10,0 | 0 |
| 5 | 50 | 10,0 | 0 |
| 15 | 150 | 10,0 | 0 |
| 15 (lần 2) | 150 | 10,0 | 0 |
| 15 (lần 3) | 150 | 10,0 | 0 |

§1 quy 24,6% cho hai nguyên nhân cộng hưởng: vòng hở làm rớt phím, và tiêu chí
đạt lỏng 50%. Lượt đo này **không tái hiện được** vế rớt phím khi máy rảnh. Vế
thứ hai — `(|dx| + |dy|) >= distance_px // 2` — vẫn nguyên trong code và vẫn sai.

Còn một khả năng thứ ba mà §1 không tách ra: con số 98px trung vị được đo bằng
**thước DOM** (`cell_tracker` chia ngược canvas transform), chứ không phải bằng
`mxGeometry`. Chính docstring của `_INFO_JS` ghi thước đó từng đọc một cú dịch
150 thành 22. Nên "24,6% bước Move dịch đúng" có thể là số của **thước**, không
phải của **cú dịch**. Lượt chạy `result/g0_baseline` (cờ G1 tắt, thước mới) là
phép đo tách được hai thứ đó.

### 9.2 Điểm chèn: cơ chế đã đo được (L2)

Chèn 10 hình liên tiếp, không dịch gì giữa chừng, có gọi `reset_view`:

```
x: 365 ×10   (trải 0)
y: 351 ×10   (trải 0)
```

Chèn 6 hình theo **đúng mẫu của corpus** — chèn, dịch nó đi, chèn tiếp:

| | x | y |
|---|---|---|
| có `reset_view` | 357 ×6 (trải **0**) | 414 → 814 → 814 ×4 (trải **400**) |
| không `reset_view` | 353 → 333, mỗi lần −4 (trải **20**) | 727 → 2957 (trải **2230**) |

**Cơ chế:** draw.io thả hình click-chèn vào **tâm khung nhìn hiện tại**.
`reset_view` khôi phục `scrollLeft/scrollTop`, và điều đó giữ được x nhưng
không giữ được y: khi canvas lớn thêm, cùng một số scroll trỏ vào một điểm model
khác. Đây đúng là điều docstring `_insert_origin` đã ngờ; giờ có số.

**Hệ quả cho G1.3:** giữ điểm chèn trong **toạ độ model**, không qua scroll. Lần
chèn đầu của kịch bản định nghĩa điểm; mọi lần sau đo lệch rồi nhích về. Lệch đo
được (400, và 4/lần khi không reset) — 400 là bội của 10 nên lưới phím nhích về
đúng; 4 thì không, đó là lý do vẫn phải giữ `reset_view`.

### 9.3 Kích thước hình mặc định là **120×60**, không phải 48×24

§3 (L3+L4) tính "giãn cách ≈ 10 lần chiều cao hộp" dựa trên hình 48×24. Đo trên
bản ghim: hình chèn ra **120×60**. Với giãn cách 255px thì tỉ lệ là **4,25 lần**
chiều cao, không phải 10. Kết luận định tính của §3 — bản vẽ giãn hơn ảnh gốc —
vẫn đứng (ảnh gốc ≈2,3 lần), nhưng **độ lớn của sai lệch nhỏ hơn khoảng 2,4 lần**
so với con số đang ghi. Khi tới G2.1/G2.2 phải tính lại từ 120×60.

### 9.4 Ctrl+Arrow đổi kích thước **1 đơn vị** mỗi phím, không phải 10

| Phím | Đổi gì, mỗi phím | Tâm dịch |
|---|---|---|
| Ctrl+Right | `w` +1, `x` giữ nguyên | +0,5 |
| Ctrl+Left | `w` −1 | −0,5 |
| Ctrl+Down | `h` +1, `y` giữ nguyên | +0,5 |
| Ctrl+Up | `h` −1 | −0,5 |

`drawio_executor._do_resize` gửi `MOVE_STEP_PX // PX_PER_ARROW_PRESS` = 15 phím
để mong 150 đơn vị, nên mọi bước `Extend` chỉ đổi **15** đơn vị — một phần mười
— mà vẫn báo đạt, vì tiêu chí là `(|dw| + |dh|) > 0`. Đây là một lỗi gốc **mới**,
cùng họ với L1: vòng hở cộng tiêu chí đạt lỏng.

Hai hệ quả:

* G1.4 phải đóng vòng trên `mxGeometry` và ép đúng lượng.
* `ORACLE.md` §1 hàng 8–9 đặt N4 là *"vị trí tâm giữ nguyên"*. Đo cho thấy tâm
  **buộc phải** dịch nửa lượng khi kéo một cạnh. Hậu điều kiện đúng là **cạnh
  đối diện đứng yên**. Xem `DECISIONS.md` D11.

### Lệnh tái sinh

```bash
python RPA_docs/checks/probe_editor.py --port 9403
```

### 9.5 L7 — `StepParser` sửa chính chuỗi nó phải gõ

Bảng ở §0 có sáu lỗi gốc L1–L6. Đây là lỗi thứ bảy, tìm ra 2026-09-22 nhờ oracle
độc lập; bảng §0 viết trước nên không có nó.

`StepParser.process_step` tách câu bằng stanza rồi ghép token lại bằng dấu cách,
nên **mọi dấu câu trong chuỗi cần gõ đều bị đẩy ra một khoảng trắng**:

| Câu trong kịch bản | `step.value` executor nhận được |
|---|---|
| `Fill "Documents complete?"` | `Documents complete ?` |
| `Fill "50% done"` | `50 % done` |
| `Fill "Check e-mail, then wait"` | `Check e-mail , then wait` |

Tái sinh:

```bash
cd RPA_drawio && ./venv_rpa/Scripts/python.exe -c "from step_parser import StepParser; print(repr(StepParser().process_step('Fill \"Documents complete?\" into the element created in step 5').value))"
```

**Quy mô.** 35 trên 246 bước `Fill` của bộ 30 case mới — **14,2%** — có dấu câu.
Mỗi bước đó gõ ra một nhãn sai.

**Vì sao chưa ai thấy.** `drawio_ops._label_result` kiểm bằng cách tìm chuỗi
trong `canvas_labels(driver)`, tức là đọc DOM và hỏi "chuỗi có nằm đâu đó gần ô
không". Nó **đạt** với cả nhãn sai. Đọc `mxCell.value` thì lệch lộ ra ngay.

**Sửa ở đâu.** `step_parser.py` bị đóng băng (D6), nên bản vá nằm ở
`drawio_executor.QUOTED_RE`: chuỗi trong ngoặc kép của chính câu là thứ được gõ,
`step.value` chỉ dùng khi câu không có ngoặc kép. Hàng báo cáo ghi `text_from`
là `literal` hay `parser` để biết đường nào đã dùng.

### 9.6 L8 — `Connect` tạo được cạnh nhưng cạnh không neo vào đâu

Trong `medium_m08_v3_s5b2l0`, ba bước `Connect` tạo ra ba `mxCell` có `edge="1"`,
có `source`, và **không có `target`**:

```xml
<mxCell id="...-8" style="edgeStyle=orthogonalEdgeStyle;..." edge="1" parent="1"
        source="...-2"/>            <!-- không có target -->
```

`drawio_ops.connect_cells` báo đạt bằng điều kiện `len(after) > len(before)` —
"có thêm một ô" — nên một cạnh lơ lửng vẫn được tính là nối thành công. Đây
chính là lớp lỗi `main.tex` §RQ1 tự nhận chưa xử lý được, và là lý do hậu điều
kiện N3 của `connect` phải phát biểu bằng `source`/`target` theo mô hình chứ
không bằng số ô.

Chưa quy được nguyên nhân: có thể do thả chuột trượt khỏi hình đích, có thể do
hình đích nằm ngoài khung nhìn. Đo lại sau G1 (việc G1.5) rồi mới kết luận.

---

## 10. Nguồn mới 2026-09-24: `Kết quả thực nghiệm.xlsx` — sổ tay thô của người đi trước

Người giao việc cung cấp thêm `documents/Kết quả thực nghiệm.xlsx` — **không**
nằm trong git của người đi trước (`RPA_drawio/_git_vendor_backup`), không nằm
trong phần bàn giao trước đó. Đây là workbook thô: 16 sheet, log từng test case
với cột Pass/Fail và ghi chú tay. Số tổng ở sheet `Thực nghiệm` (dòng 10–12,
24–26) khớp **chính xác từng chữ số** với bảng `tab:thong_ke_2` và `tab:drawio`
của `main.tex` — xác nhận các con số trong `main.tex` có nguồn thật, không bịa.
Nhưng đọc kỹ nội dung thì lộ ra chính xác cơ chế đo mà §7–§9 đã suy luận gián
tiếp từ code, giờ có bằng chứng trực tiếp bằng lời của tác giả.

> **Luật đọc file này.** Nó là bằng chứng sơ cấp có giá trị cao để hiểu phương
> pháp cũ, và là nguồn cho các lỗi gốc mới ở Lucidchart/Visual Paradigm (§10.3).
> Nó **không phải** đáp án ở mức N3 — cột "Pass/Fail" trong đó đo ở mức tương
> đương N1–N2 (có chạy được, đúng đối tượng), không có hậu điều kiện hình học
> nào. Không dùng workbook này làm chuẩn để so sánh số N3 mới.

### 10.1 Xác nhận trực tiếp: tiêu chí "đạt" của pipeline cũ không kiểm hình học

Sheet `drawio-2`, dòng 6 — bước `Click on Help` → **Fail**, ghi chú tay:
> *"cả 2 button đều mang ý nghĩa giống nhau, nhưng 1 cái trên giao diện là icon,
> một cái giao diện là text"*

Dòng 13 — `Click on Edit button` → **Fail**:
> *"nhầm sang phần tử khác"*

Không công thức nào trong sheet tính ra hai ô này — người gõ tay sau khi tự
xem kết quả. Cột Pass/Fail của toàn bộ workbook là **phán định người**, không
phải output của một hàm so sánh.

Xác nhận nặng nhất nằm ở sheet `Nhận xét`, dòng 8 — ghi chú làm việc của chính
tác giả, viết cho bản thân, không phải cho người đọc:

> *"việc xác minh kết quả test (assertion): hiện tại đã có cơ chế fall back →
> thực thi hành động thành công rồi mới chuyển sang bước khác. Nếu không thành
> công vẫn chuyển sang bước khác nhưng thường test sẽ fail — **hiện tại đang
> đảm bảo các test sẽ thành công** — chỉ fail do mạng yếu"*

Đối chiếu với code: `generator.py::execute_python_action` (dòng 350) không có
một dòng nào so sánh vị trí/kích thước/nhãn với giá trị mong đợi — chỉ có
try/except quanh lệnh Selenium. Lời ghi chú và code khớp nhau tuyệt đối. Đây là
bằng chứng trực tiếp, không còn là suy luận, cho luận điểm nền của toàn bộ
`ORACLE.md`: **pipeline cũ không có oracle hình học, chỉ có oracle "hành động
có chạy được không"**.

### 10.2 Bước ảnh→kịch bản có oracle riêng — dạng LLM-giám khảo, không tất định

Sheet `few-shot` là log của bước one-shot learning (ảnh flowchart → câu lệnh,
`main.tex` Phụ lục A). Mỗi hàng gọi **một lệnh Gemini thứ hai** so sánh flowchart
gốc với flowchart Gemini vừa đọc ra, trả về văn xuôi + phần trăm tương đồng thủ
công. Ví dụ dòng 5:

> *"Khác biệt: Bước `Process step 4` có nội dung text giống nhau nhưng hình
> dạng khác biệt (Flowchart 1 là `rectangle`, Flowchart 2 là `rounded
> rectangle`)... (3/5) × 100 = 60.00%"*

Đây **chính là lỗi L6** (rounded rectangle không tách được), tác giả **đã tự
phát hiện và định lượng** — nhưng chỉ ở tầng đọc ảnh. Không có gì tương đương
đo tầng thực thi (bước 4/5 của kiến trúc mới). Nói cách khác: pipeline cũ có
**hai** oracle rời rạc — một LLM-giám khảo cho bước đọc ảnh (không tất định,
sheet `few-shot`), một "không văng lỗi" cho bước thực thi (sheet
`drawio-2`/`Lucidchart`/`Visual Paradigm`) — và **không có oracle nào ở giữa**
kiểm tra bản vẽ cuối cùng có đúng cấu trúc hay không. Đây đúng là khoảng trống
mà `mx_oracle.py` + `graph_score.py` lấp — không phải phát minh lại bánh xe, mà
là nối hai đầu vốn đã có sẵn nhưng chưa từng nối.

### 10.3 Hai lỗi gốc mới, riêng cho Lucidchart và Visual Paradigm

Chưa từng đo trên hệ thống hiện tại (G4/G5 chưa mở), nhưng tác giả cũ đã ghi
nhận bằng tay. Ghi lại đây để không mất, xếp vào `KNOWN_LIMITS.md` mục B.

**L-Lucid-1 — nhãn dài làm hình tự giãn, đổi luôn tâm hình.** Sheet
`Lucidchart`, dòng 77:
> *"do text quá dài → shape tự giãn ra → tọa độ tâm thay đổi (khó xác định
> chính xác)"*

Khác L2 (điểm chèn trôi do dịch chuyển tích luỹ) ở chỗ tác nhân là **độ dài
nhãn**, không phải số lần thao tác. Bất kỳ logic nào định vị theo tâm hình sau
khi đặt nhãn dài đều có nguy cơ trật.

**L-Lucid-2 — hình chồng lên nhau khi luồng dài.** Cùng sheet, dòng 66 và 68:
> *"flow dài → trượt khỏi màn hình/các shape đè lên nhau"*
> *"2 hình thoi đè lên nhau, không thể move"*

**L-VP-1 — shadow-root chặn cả tọa độ lẫn XPath.** Sheet `Visual Paradigm`,
dòng 50–53:
> *"nằm trong shadow-root, selenium cũng không bắt được, ❌ JavaScript trả về
> NULL (có thể do CSP hoặc lỗi JS)"*
> *"mặc dù xác định đúng tọa độ, nhưng vì phần tử nằm trong shadow-root nên
> click theo xpath bị lệch"*

Đây là **cơ chế cụ thể** đằng sau `KNOWN_LIMITS.md` B2 (trước đó chỉ ghi "chưa
định lượng ở hướng này"). Quan trọng: tọa độ **xác định đúng**, chỉ riêng thao
tác click theo XPath bị lệch — nghĩa là hướng sửa khả dĩ là click theo toạ độ
tuyệt đối (`ActionChains` offset) thay vì `driver.find_element(...).click()`
khi phần tử nằm trong shadow-root, không cần giải quyết bài toán XPath xuyên
shadow-root nói chung.

**L-VP-2 — quan hệ DOM anh em bị đọc nhầm thành cha-con.** Dòng 56:
> *"xác định được vị trí text nhưng text và checkbox ngang hàng thay vì mối
> quan hệ cha con nên không thành công"*

### Lệnh tái sinh

```bash
python -c "
import openpyxl
wb = openpyxl.load_workbook('Kết quả thực nghiệm.xlsx', data_only=True)
for name in ('drawio-2','Lucidchart','Visual Paradigm','few-shot','Nhận xét'):
    ws = wb[name]
    for row in ws.iter_rows():
        pass  # xem toàn bộ log gốc, sheet theo tên
"
```
