# Kế hoạch phát triển — hướng RPA, draw.io trước

> 🔒 **KHOÁ NGÀY 2026-09-20.** File này là hợp đồng thiết kế của dự án. Sửa nội
> dung (không tính việc tick checkbox ở `PLAN.md`, đó là trạng thái, không phải
> thiết kế) bắt buộc phải: (1) ghi lý do vào `RPA_docs/TRACE.md`, (2) cập nhật
> hash trong `RPA_docs/LOCKS.md`, (3) nếu đổi ngưỡng hoặc luật, thêm mục LẬT
> vào `DECISIONS.md`. Sửa mà không làm cả ba bước này là vi phạm quy trình.


Sáu giai đoạn, **G0 → G5**. Mỗi giai đoạn có một *Cổng*: danh sách điều kiện đo
được. **Chưa qua cổng thì không được làm việc của giai đoạn sau**, kể cả khi
việc sau trông hấp dẫn hơn hoặc dễ hơn.

Trạng thái hiện tại luôn nằm ở [`PROGRESS.md`](PROGRESS.md), không nằm ở file
này. File này mô tả *phải làm gì*, không mô tả *đã làm gì*.

Căn cứ: [`DIAGNOSIS.md`](DIAGNOSIS.md) (sáu lỗi gốc L1–L6),
[`ORACLE.md`](ORACLE.md) (đo *thực thi đúng* như thế nào) và
[`../REQUIREMENTS.md`](../REQUIREMENTS.md) (yêu cầu nguyên văn).

> Đề tài là **kiểm thử giao diện**. Mọi cổng dưới đây phát biểu bằng ngôn ngữ
> của `ORACLE.md`: mức phán định N0–N4, tỉ lệ báo đạt sai, độ lặp lại, độc lập
> giữa các bước. Một cổng nói "vẽ đẹp hơn" là một cổng viết sai.

---

## Bất biến — mười luật không bao giờ được vi phạm

Đây là phần quan trọng nhất của tài liệu. Khi phân vân, đọc lại mục này trước.

1. **Không leakage.** Đường thực thi (`image_to_scenario.py` → executor) chỉ
   được mở file `.png`. Tuyệt đối không mở `*.png.graph.json` (answer key) hay
   `*.xml` (nguồn). Answer key chỉ được mở trong `judge_*`, sau khi đã chạy
   xong và đã ghi kết quả ra đĩa.

2. **Không hard-code theo case.** Cấm mọi nhánh `if case_id == ...`, mọi bảng
   tra theo tên file, mọi danh sách hình đặc biệt. Rút kinh nghiệm từ case khó
   là hợp lệ; điều kiện là bản vá phải phát biểu được thành một quy tắc về
   *draw.io cư xử thế nào*, không phải về *case này trông thế nào*.

3. **Tập giữ kín.** Chia corpus thành **tập chỉnh** (được nhìn khi dò lỗi) và
   **tập giữ kín** (chỉ chạy một lần, lúc chốt số).

   | | |
   |---|---|
   | Cách chia | `sha256(case_id)` → 20% vào tập giữ kín |
   | Phạm vi | chia **trong từng band** (easy/medium/hard) để tỉ lệ band giữ nguyên ở cả hai tập |
   | Áp cho | cả `RPA_Datasets/data/drawio` (100) và `../data/datasets` (506); VP và Lucid chia cùng hàm khi tới G4/G5 |
   | Cố định từ | G0, ghi vào `RPA_docs/splits.json` cùng hạt giống và phiên bản hàm băm |
   | Tập giữ kín được chạy | **đúng một lần**, ở G3.5. Chạy lần hai thì nó hết là tập giữ kín — phải chia lại và ghi rõ |

   Báo cáo số của hai tập **riêng biệt**. Nếu tập giữ kín thấp hơn tập chỉnh quá
   0,10 thì coi như đã overfit và phải quay lại.

4. **Mỗi con số có đúng một lệnh tái sinh.** Nếu không tái sinh được thì không
   được trích dẫn — kể cả số do chính mình đo tuần trước. Lệnh đặt trong
   `RPA_docs/checks/`.

5. **Không chỉnh số cho khớp `main.tex`.** Bộ dữ liệu trên máy không phải bộ đã
   dùng viết bài (`DIAGNOSIS.md` §7). Tái hiện *phương pháp*, báo cáo số của
   mình, ghi chú sai lệch. Sửa số hoặc sửa dữ liệu cho khớp bảng là gian lận.

6. **Không có khoảng thì không có kết quả.** Điểm đơn lẻ không phải kết quả.
   Mọi tỉ lệ đi kèm khoảng tin cậy; mọi so sánh đi kèm baseline tầm thường
   (canvas trắng, toàn chữ nhật, node không cạnh).

7. **Không báo cáo dưới mức N3.** Xem `ORACLE.md` §1. Con số ở mức "không ném
   ngoại lệ" (N0) không được gọi là tỉ lệ thành công. Mọi bảng phải ghi rõ nó
   đang ở mức phán định nào.

8. **Oracle độc lập với executor.** Bộ phận thực hiện hành động không được tự
   chấm hành động của mình. Xem `ORACLE.md` §2.

9. **Báo đạt sai là lỗi chặn.** Một bước được đánh `ok` trong khi hậu điều kiện
   bị vi phạm là lỗi nghiêm trọng nhất trong toàn bộ dự án — nặng hơn một bước
   hỏng thật. Phát hiện ra thì dừng, sửa, chạy lại; không đi tiếp.

10. **Không commit khi chưa được yêu cầu.**

---

## G0 — Dựng thước đo trung thực

> **Vì sao trước tiên.** `DIAGNOSIS.md` L1 cho thấy thước đo hiện tại chấp nhận
> 75px trên yêu cầu 150px. Mọi cải tiến đo bằng thước đó đều vô nghĩa. Không
> được sửa một dòng executor nào trước khi xong G0.

**Điều kiện vào:** không có.

### Việc

| # | Việc | File |
|---|------|------|
| G0.1 | Cài **hậu điều kiện N3** cho cả **11 hành động** theo bảng `ORACLE.md` §1, không riêng `Move` | `RPA_drawio/drawio_ops.py` |
| G0.1b | Cài kiểm tra **N4 — không tác dụng phụ** cho `Move`, `Connect`, `Delete`: chụp toàn bộ ô trước/sau, khẳng định chỉ ô đích đổi | executor |
| G0.2 | Viết bộ chấm **tất định** ở mức hình, đọc từ mxGraph XML xuất ra: số node, số cạnh, ma trận kề, nhãn node, nhãn cạnh, sai số vị trí chuẩn hoá sau khớp Procrustes | `RPA_docs/checks/` + module mới |
| G0.3 | Kiểm thử đột biến cho bộ chấm — **cả 9 ca** ở `ORACLE.md` §4 | test |
| G0.3b | Dựng **đồ thị phụ thuộc** của kịch bản để tách hỏng gốc / hỏng kéo theo (`ORACLE.md` §3.3) | harness |
| G0.3c | Dựng ba **baseline tầm thường** (`ORACLE.md` §5) và chạy chúng qua bộ chấm | `RPA_docs/checks/` |
| G0.4 | Cố định tập chỉnh / tập giữ kín bằng băm trên id | `RPA_docs/splits.json` |
| G0.5 | Khẳng định không leakage bằng một test chặn mọi lần mở `.graph.json`/`.xml` trong đường thực thi | test |
| G0.6 | Chạy lại đúng 30 case cũ bằng thước mới → baseline **thật**, theo mẫu báo cáo `ORACLE.md` §6 | `result/g0_baseline/` |
| G0.7 | Rà tay ≥50 bước được đánh `ok` để đo **tỉ lệ báo đạt sai** của thước cũ | `RPA_docs/checks/` |
| G0.8 | Chốt môi trường đích (`ENVIRONMENT.md`), ghi `env.json` cho mọi lượt chạy | `run_drawio_v2.py` |

### Cổng G0 — phải tick hết

**Năng lực phán định** — đây là sản phẩm của G0, không phải phần phụ:

- [ ] Cả **11** hành động có hậu điều kiện N3 cài đặt và kiểm thử được (hoặc khai báo N2 kèm lý do, riêng `press`).
- [ ] Không hành động nào còn ở N0. Rà bằng cách đếm handler trong `_HANDLERS` và đối chiếu với bảng oracle.
- [ ] `Move`, `Connect`, `Delete` có kiểm tra N4.
- [ ] **Báo đạt sai của thước mới = 0** trên mẫu rà tay ≥50 bước (`ORACLE.md` §3.1).
- [ ] Đo và ghi lại **báo đạt sai của thước cũ** — con số này định lượng đúng chỗ `RESULTS.md` sai.
- [ ] Oracle đọc từ mxGraph XML qua đường mã **độc lập** với executor (`ORACLE.md` §2). Kiểm chứng: ép executor trả `ok` cứng thì oracle vẫn bắt được lỗi.
- [ ] Bộ chấm qua **cả 9 ca đột biến** (`ORACLE.md` §4), kể cả ca 9 — vẽ thừa hình **không** làm tăng điểm.
- [ ] Mọi chỉ số "tìm đúng" có chỉ số "vẽ thừa" đi kèm; mẫu số là số đếm của bản tham chiếu.

**Hạ tầng**

- [ ] Đồ thị phụ thuộc dựng được cho 100% kịch bản; tách được hỏng gốc ↔ hỏng kéo theo.
- [ ] Ba baseline tầm thường chạy được và cho điểm đúng như dự đoán ở `ORACLE.md` §5.
- [ ] Test leakage đỏ khi cố tình mở answer key, xanh khi chạy bình thường.
- [ ] `RPA_docs/splits.json` tồn tại, tất định, tái sinh được.
- [ ] Baseline thật cho 30 case, in **đúng mẫu** `ORACLE.md` §6, ghi vào `PROGRESS.md`.
- [ ] Chạy lại `result/new30_v2` bằng thước mới cho tỉ lệ đạt ≈24,6%, không phải 93,88%.

**Môi trường** (`ENVIRONMENT.md`)

- [ ] Dựng `jgraph/drawio:28.2.5` cục bộ và trỏ `DRAWIO_URL` vào đó (D9 đã chốt). `rpa_env.py` phải đọc `.env` thay vì hard-code.
- [ ] Kiểm lại `palette_matcher` trên bảng shape của bản ghim.
- [ ] Lượt đối chứng 30 case, bản ghim vs `app.diagrams.net`, ghi chênh lệch vào `RESULTS.md`.
- [ ] Mỗi thư mục kết quả có `env.json`: bản draw.io, bản Chrome, commit kho, ngày, cổng, nhà cung cấp LLM.
- [ ] `pip freeze` xuất ra `RPA_docs/requirements.lock.txt`.

> **Cảnh báo đã biết trước:** điểm mức hình sẽ **tụt** khi đo đúng — dự đoán
> 0,64 → khoảng 0,30–0,40. Đó là dấu hiệu thước đo đã hết nói dối, không phải
> dấu hiệu hồi quy. Nếu điểm *không* tụt thì bộ chấm mới vẫn còn lỏng.

---

## G1 — Sửa hình học ở tầng executor

**Điều kiện vào:** cổng G0 tick đủ.

> Chỉ đụng executor. **Không** đụng `image_to_scenario.py` ở giai đoạn này — vì
> L3/L4 là hệ quả của L1, sửa song song sẽ không biết cái nào có tác dụng.

### Việc

| # | Việc | Lỗi gốc |
|---|------|---------|
| G1.1 | `Move` **vòng kín**: bấm → đo dịch chuyển thật trong toạ độ mô hình mxGraph → bấm bù phần thiếu → lặp tối đa N lần → `failed` nếu không hội tụ | L1 |
| G1.2 | Viết script dò riêng, chạy trong trình duyệt thật, để xác định draw.io quyết định điểm thả shape **bằng gì** (tâm viewport? ô trống gần nhất? con trỏ?) | L2 |
| G1.3 | Đặt lại điểm chèn một cách tất định trước mỗi lần chèn, theo cơ chế tìm được ở G1.2 | L2 |
| G1.4 | Đặt kích thước hình bằng đúng từ vựng DSL đã có (`Extend`/`Shrink`) | L4 |
| G1.5 | Đo lại `Connect` **sau khi** G1.1–G1.4 xong, rồi mới quyết định nó có phải lỗi độc lập không | L5 |
| G1.6 | Đo **độ lặp lại**: 20 case × 5 lần chạy (`ORACLE.md` §3.2) | — |
| G1.7 | Đo **hỏng thầm lặng**: hành động thành công nhưng tác động sai phần tử (`ORACLE.md` §3.1) | — |

### Cổng G1 — phải tick hết

**Chính xác khi thực thi**

- [ ] `Move` đạt N3 **≥98%** trên ≥200 bước đo được.
- [ ] `Move`, `Connect`, `Delete` đạt N4 **100%** — không một tác dụng phụ nào.
- [ ] Điểm chèn trôi **<5px** qua 10 lần chèn liên tiếp (`cells_of.py` trên case không có lệnh dịch ngang).
- [ ] Kích thước hình đạt tỉ lệ khung mục tiêu trong **±10%**.
- [ ] `Connect` đạt N3 **≥95%** trên fixture có hình học đã đúng — và N3 nghĩa là đúng cặp `source`/`target` theo mô hình, không phải "có thêm một cạnh".

**Đáng tin như một bộ kiểm thử**

- [ ] **Báo đạt sai = 0**, cận trên KTC 95% **<2%**.
- [ ] **Báo hỏng sai ≤2%**.
- [ ] **Hỏng thầm lặng ≤1%** — đây là lớp lỗi `main.tex` §RQ1 tự thừa nhận chưa xử lý được.
- [ ] Đồ thị cuối **đẳng cấu ≥95%** qua 5 lần chạy; vị trí **p95 ≤5px**; phán định ổn định **≥98%** (`ORACLE.md` §3.2).
- [ ] Không kịch bản nào treo harness; trình duyệt chết giữa chừng thì ghi lại và đi tiếp **100%**.

**Vệ sinh**

- [ ] Cơ chế điểm chèn ở G1.2 được **ghi lại thành văn** trong `DIAGNOSIS.md` — không được sửa mù.
- [ ] Không có nhánh nào rẽ theo id case (rà bằng grep, ghi kết quả).

---

## G2 — Sửa tầng mã hoá ảnh → text

**Điều kiện vào:** cổng G1 tick đủ. Trước đó, `Move` chưa tin được thì mọi
tính toán thang đo đều dựa trên cát.

### Việc

| # | Việc | Lỗi gốc |
|---|------|---------|
| G2.1 | Hạ `MOVE_STEP_PX` xuống mức tương xứng kích thước hình; bỏ ràng buộc `1.7 × MOVE_STEP` đang thổi phồng bố cục | L3 |
| G2.2 | Chọn thang đo sao cho bản vẽ **tự nhất quán**: giãn cách tính theo bội số chiều cao hình, không theo pixel tuyệt đối của ảnh gốc | L3 |
| G2.3 | Đo chất lượng đọc ảnh của VLM **tách khỏi** chất lượng thực thi: so đồ thị VLM đọc ra với `*.graph.json` (chỉ ở bước chấm) → ba số riêng: đúng node / đúng cạnh / đúng loại hình | — |
| G2.4 | Rounded rectangle, thử theo thứ tự: (a) ô tìm kiếm shape của draw.io bằng từ khoá thay vì khớp icon; (b) đổi style sau khi chèn qua panel Format hoặc `Edit Style`; (c) nếu cả hai bất khả thi → ghi nhận là giới hạn và **báo cáo tách riêng** chỉ số có/không tính loại hình | L6 |

> **G2.3 là điểm quyết định chi tiêu.** Nếu VLM không phải nút thắt thì đừng
> đổi model, đừng tăng số lần gọi. Yêu cầu gốc nói rõ: chi phí phải tối giản.

### Cổng G2 — phải tick hết

- [ ] Có ba con số riêng cho chất lượng đọc ảnh, kèm khoảng tin cậy — **tách hẳn** khỏi chất lượng thực thi.
- [ ] Sai số vị trí chuẩn hoá (sau khớp Procrustes) trung vị **≤0,05** đường chéo bản vẽ, **p95 ≤0,12**.
- [ ] Tỉ lệ giãn cách / chiều cao hình khớp ảnh gốc trong **±25%**.
- [ ] **Vẽ thừa ≤2%**: số node và cạnh vẽ ra vượt bản tham chiếu.
- [ ] L6 hoặc đã sửa được, hoặc đã ghi thành giới hạn **và** điểm được báo cáo ở cả hai dạng có/không tính loại hình.
- [ ] Mọi cổng của G1 **vẫn giữ** sau khi đổi tầng mã hoá — chạy lại và chứng minh, không giả định.
- [ ] Chi phí đo đủ bộ (`ORACLE.md` §3.6): thời gian trung vị + p95, số lần gọi LLM, token vào/ra, quy ra tiền.

---

## G3 — Chạy diện rộng trên draw.io

**Điều kiện vào:** cổng G2 tick đủ.

### Việc

| # | Việc | Quy mô |
|---|------|--------|
| G3.1 | 100 case `RPA_Datasets/data/drawio` (bộ cũ) | 100 |
| G3.2 | 506 case `../data/datasets` qua đường ảnh → text | 506 |
| G3.3 | Báo cáo: mức bước **và** mức hình, tách theo band độ khó, kèm khoảng tin cậy | — |
| G3.4 | Baseline tầm thường: canvas trắng, toàn chữ nhật, node không cạnh | — |
| G3.5 | Tập giữ kín chạy **đúng một lần**, báo cáo riêng | — |
| G3.6 | **Bất biến môi trường** (`ORACLE.md` §3.4): sáng ↔ tối, DPR 1,0 ↔ 1,25, trên cùng tập con ≥20 case | — |
| G3.7 | Dựng lại bảng kiểu `tab:drawio` của `main.tex`: tỉ lệ đạt ở **mức kịch bản** và **mức bước**, tách kịch bản thuần text ↔ text+ảnh | — |

### Cổng G3 — phải tick hết

**Đầy đủ**

- [ ] Cả 606 case chạy hết, không case nào treo harness.
- [ ] Báo cáo in **đúng mẫu** `ORACLE.md` §6 — thiếu dòng nào thì chưa coi là đã báo cáo.
- [ ] Bảng kết quả có khoảng tin cậy và có cả ba baseline tầm thường ở đầu bảng.
- [ ] Tỉ lệ đạt tách làm ba: **đạt / hỏng gốc / hỏng kéo theo**. Cấm gộp thành một số.
- [ ] Có bảng ở **mức kịch bản** (một bước hỏng thì cả kịch bản hỏng) song song với mức bước — đây mới là tiêu chí của một bộ kiểm thử.

**Không gian lận**

- [ ] **Báo đạt sai = 0** trên mẫu rà tay của chính lượt chạy này.
- [ ] Chênh lệch tập chỉnh ↔ tập giữ kín **≤0,10**. Vượt thì quay lại G1/G2.
- [ ] Bất biến môi trường: chênh lệch sáng↔tối và DPR **≤2 điểm phần trăm** mỗi chiều; vượt thì ghi thành giới hạn, **không** im lặng bỏ qua.

**Có người thật nhìn**

- [ ] Ít nhất 10 case được **nhìn bằng mắt** và mô tả bằng lời sai ở đâu, không chỉ bằng số.
- [ ] `RESULTS.md` cập nhật; các số cũ được đánh dấu rõ là đo ở mức N0 bằng thước lỏng.

---

## G4 — Visual Paradigm

**Điều kiện vào:** cổng G3 tick đủ.

`RPA_VisualParadigm` dùng chung `by_text.py`, `by_image_helper.py`,
`find_element.py` với draw.io; `generator.py` và `step_parser.py` khác nhau.
Phần hình học (`rpa_env` / `cell_tracker` / `ops` / `executor`) phải viết bản
riêng vì canvas khác engine — **không** giả định mượn được từ draw.io.

Corpus: `../data/datasetsVP` — 497 case (42 / 252 / 203).

### Cổng G4

- [ ] Đo baseline VP bằng code gốc trước, ghi lại, rồi mới sửa.
- [ ] **Toàn bộ** cổng G1 và G3 áp nguyên cho VP — cùng ngưỡng, không hạ chuẩn vì "canvas khác engine".
- [ ] Hậu điều kiện N3/N4 viết lại cho engine của VP và kiểm thử lại; **không** giả định mượn được từ draw.io.
- [ ] Bộ chấm qua lại 9 ca đột biến trên dữ liệu VP.
- [ ] Chạy hết 497 case, báo cáo đúng mẫu `ORACLE.md` §6.

---

## G5 — Lucidchart

**Điều kiện vào:** cổng G4 tick đủ.

Vướng thêm: cần tài khoản đăng nhập; URL trong dataset trỏ tới document của
tiền bối, nhiều khả năng đã chết. Người giao việc đã nói *"cứ để sau"*.

### Cổng G5

- [ ] Giải quyết được đăng nhập, hoặc ghi rõ đây là rào chặn và dừng có kiểm soát.
- [ ] Lucidchart không đưa phần tử canvas ra DOM (`main.tex` §RQ1) — nên hậu điều kiện N3/N4 phải dựa trên đường khác (API tài liệu, hoặc so ảnh). Chốt đường đó **trước** khi viết executor.
- [ ] Còn lại như G4, cùng ngưỡng.

---

## Bảng tra nhanh: lỗi gốc → giai đoạn sửa

| Lỗi | Sửa ở | Không được sửa sớm hơn vì |
|-----|-------|---------------------------|
| L1 `Move` vòng hở | G1.1 | cần thước đo đúng (G0) mới biết đã sửa được chưa |
| L2 điểm chèn trôi | G1.2–G1.3 | phải đo cơ chế thật trước, không đoán |
| L3 quantum quá thô | G2.1–G2.2 | là hệ quả của L1; sửa trước sẽ che mất tác dụng của G1 |
| L4 không đặt kích thước | G1.4 | — |
| L5 `Connect` | G1.5 | có thể tự hết khi hình học đúng; đo trước, kết luận sau |
| L6 rounded rectangle | G2.4 | khác loại hẳn, đi đường riêng |
