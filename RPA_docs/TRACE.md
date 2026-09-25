# Trace — nhật ký mức hành động

Khác với `PROGRESS.md` (mức cột mốc: qua cổng nào), file này ghi **mức hành
động**: từng lệnh đã chạy, từng file đã sửa, từng bằng chứng đo được, đối chiếu
với `main.tex` khi liên quan. Mục đích: một phiên mới **không có memory** vẫn
đọc file này là biết chính xác đang dở ở đâu, đã thử gì, thử đó ra sao, và lệnh
tiếp theo là gì — không phải suy luận lại từ đầu.

**Luật ghi.** Append-only, mới nhất lên đầu. Mỗi mục trả lời đủ bảy ô ở khung
dưới; thiếu ô nào ghi `—`, không bỏ qua. Không sửa mục cũ trừ việc gắn nhãn
`[CẬP NHẬT bởi mục YYYY-MM-DD-N]` nếu một phát hiện sau này bác bỏ mục trước.

```
### <ngày> · <mã phiên/việc, vd G0.2-a> · <tiêu đề ngắn>

- **Mục tiêu lượt này:**
- **Nguồn gốc / vì sao:**  (câu hỏi nào ở PLAN/ORACLE/DECISIONS thúc đẩy việc này)
- **Đã làm:**              (file sửa, lệnh chạy — dán nguyên lệnh)
- **Bằng chứng:**          (số đo được, output, hoặc "chưa đo — xem mục sau")
- **Đối chiếu main.tex:**  (section nào, hoặc "không liên quan")
- **Trạng thái:**          HOÀN TẤT / DỞ DANG / CHẶN — lý do
- **Tiếp theo, chính xác:** (lệnh hoặc file cụ thể, không mô tả chung chung)
```

---

## 🔴 ĐANG LÀM DỞ — đọc mục này trước tất cả

*(luôn cập nhật ô này thành mục mới nhất bên dưới; nếu ô này trống nghĩa là
không có việc dở, phiên trước dừng ở một điểm sạch)*

> **2026-09-24-3.** Mục 1 cũ (10 case `medium`) đã xong. Lượt đối chứng
> `app.diagrams.net` **khởi động rồi bị dừng** giữa case 1/30 (hệ thống ngoài
> tự dừng tiến trình vì cạn RAM) — **chưa có số, không phải đã thử và thất
> bại**. Nguyên nhân cạn RAM đã tìm ra và vá (mục log ngay dưới): 34
> `chromedriver.exe` mồ côi tích tụ, không liên quan gì tới `app.diagrams.net`.
> Đã dọn sạch, đã vá `restart_browser()`. **Cần chạy lại lượt đối chứng — người
> giao việc phải bấm nút, không tự khởi động lại.**
>
> **Chưa có, theo thứ tự cần làm khi chạy lại:**
>
> 1. **Lượt đối chứng `app.diagrams.net`** (CẦN CHẠY LẠI TỪ ĐẦU) — lệnh trong
>    `result/_INVALID_contrast_20260923/WHY_INVALID.md`, ghi ra
>    `result/g0_contrast_public` (đã có case 1 dở dang trong đó từ lượt bị dừng —
>    xoá thư mục case đó trước khi chạy lại, đừng để `report.py` tính nhầm nó là
>    "case chạy xong"). **Kiểm `env.json` phải có cả bốn cờ `false` trước khi
>    tin bất kỳ số nào.** Đây cũng là lượt sẽ phân biệt vì sao thước DOM cũ từng
>    đo Move 24,6% N3 (`DIAGNOSIS.md` §1) trong khi oracle mxGraph mới trên bản
>    ghim vừa đo Move **739/739 = 100% N3+N4** trên toàn bộ 30 case
>    (`result/g0_baseline/report.txt`, 2026-09-24).
> 2. **`result/g1_after`** — bốn cờ bật, cùng corpus, cùng bản ghim.
> 3. `palette_check.py`, `resize_fidelity.py` (mỗi cái ~5 phút).
> 4. Rà tay 200 bước (`false_pass.py --write-sample`), nhìn mắt ≥10 case
>    (`contact_sheet.py`), rồi `repeatability.py` 20 case × 5 lần.
>
> **Trước mỗi lượt chạy chính thức, kiểm cả chromedriver mồ côi (không chỉ
> Chrome debug và không chỉ harness), xem `ENVIRONMENT.md` mục
> "chromedriver.exe mồ côi".**
>
> **Bẫy môi trường mới phát hiện, nhớ trước khi chạy lại một tập con vào
> `--out` đã có dữ liệu:** `run_drawio_v2.py` ghi đè toàn bộ `summary.json`
> bằng đúng các case của lượt gọi đó — không gộp. Rerun 10 case `medium` vào
> `result/g0_baseline` đã xoá mất 20 dòng `easy`/`hard` khỏi `summary.json`
> (từng case vẫn còn `report.json`/`verdicts.json` nguyên vẹn trên đĩa, chỉ có
> bản tổng hợp bị mất). Đã phục hồi bằng script tái tạo `summary.json` từ
> `report.json` của từng thư mục case (cùng công thức `run_one()`/`_summarize()`
> trong chính `run_drawio_v2.py`). **Không chạy một tập con scenario vào một
> `--out` đã có case khác mà không kiểm tra lại `summary.json` sau đó.**
>
> **Luật phải nhớ trước mỗi lượt chạy chính thức** — khẳng định **đúng một**
> tiến trình harness đang sống, nếu không thì hai harness sẽ giết Chrome của
> nhau và lượt chạy thành rác (đã xảy ra 2026-09-23):
>
> ```powershell
> Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
>   Where-Object { $_.CommandLine -like '*run_drawio_v2*' } |
>   Select-Object ProcessId, CreationDate
> ```

---

## Nhật ký

### 2026-09-24-3 · môi trường · Lượt đối chứng bị dừng vì cạn RAM → tìm ra 34 `chromedriver.exe` mồ côi, vá `restart_browser()`

- **Mục tiêu lượt này:** chạy lượt đối chứng `app.diagrams.net` (mục 1 của G0). Lượt bị một tiến trình reap bên ngoài dừng giữa case 24/30 (`medium_m08`, bước 27/45) vì hệ thống báo cạn RAM — 22/23 case trước đó đã có số N3 sạch trong `summary.json`. Đây không phải lỗi của bản thân lệnh — dừng để tìm nguyên nhân trước khi chạy lại mù, và giữ lại 22 case sạch làm bằng chứng tham khảo (`result/_PARTIAL_contrast_20260924/WHY_PARTIAL.md`).
- **Nguồn gốc / vì sao:** luật bất biến #9 — trước khi tin/bỏ qua một sự cố môi trường phải biết nguyên nhân thật, không đoán.
- **Đã làm:** kiểm tiến trình sau khi bị dừng: 0 harness Python sống, nhưng **34 `chromedriver.exe`** (từ `C:\Users\Admin\.cache\selenium\chromedriver\win64\153.0.8010.52\`) và 1 Chrome debug mồ côi trên cổng 9222. Đọc `restart_browser()` (`run_drawio_v2.py:97`): khi Chrome chết giữa lượt, hàm chỉ `kill_chrome_on_port` rồi mở Chrome mới — không bao giờ đụng chromedriver.exe của phiên chết. Một Chrome chết đột ngột (không qua `driver.quit()`) không tự tắt driver của nó. Viết `rpa_env.kill_orphaned_chromedrivers()` — giết đúng driver không còn Chrome con sống (kiểm `ParentProcessId` qua `Get-CimInstance`, an toàn với worker song song). Gọi hàm này trong `restart_browser()` và trong khối `finally` cuối `main()`. Dọn sạch 35 driver mồ côi + Chrome debug orphan hiện có.
- **Bằng chứng:** trước khi dọn — 34 chromedriver.exe, RAM trống 9,64GB/23,73GB. Sau khi dọn bằng chính hàm mới — 0 chromedriver.exe, 0 Chrome debug orphan, 27 chrome.exe còn lại đều thuộc trình duyệt cá nhân của người dùng (không đụng). `py_compile` xanh cho cả `rpa_env.py` và `run_drawio_v2.py`. Phụ: 22 case sạch trước khi lượt bị dừng cho `step_pass_rate_N3` **92,45%** (1060 bước) trên `app.diagrams.net` — so với 99,69% của `g0_baseline` (bản ghim). `env.json` của lượt này lộ thêm một dữ kiện: `drawio_build` public là **31.5.2**, cách bản ghim 28.2.5 nhiều phiên bản chính.
- **Đối chiếu main.tex:** không liên quan — đây là lỗi hạ tầng harness mới (`run_drawio_v2.py`, thêm 2026-09-03), không phải lỗi thuật toán RPA gốc.
- **Trạng thái:** HOÀN TẤT phần tìm nguyên nhân và vá. DỞ DANG phần đo tác dụng — chưa chạy lại một lượt dài để xác nhận rò rỉ không tái diễn.
- **Tiếp theo, chính xác:** xoá thư mục case dở dang trong `result/g0_contrast_public` (nếu có), rồi chạy lại đúng lệnh ở `result/_INVALID_contrast_20260923/WHY_INVALID.md` — nhưng **chỉ khi người giao việc yêu cầu**, không tự khởi động lại.

### 2026-09-24-2 · G0 mục 1/5 · Chạy nốt 10 case `medium`, gộp báo cáo 30/30, phát hiện bẫy ghi đè `summary.json`

- **Mục tiêu lượt này:** đóng nốt điều kiện "Baseline thật cho 30 case" của cổng G0 — chạy nốt 10 case `medium` chết trước đó vì thiếu RAM.
- **Nguồn gốc / vì sao:** `PROGRESS.md` cổng G0, dòng "Baseline thật cho 30 case... 20/30 case xong, còn 10 case `medium` phải chạy lại".
- **Đã làm:** kiểm môi trường trước khi chạy (đúng luật §51 dưới đây): không tiến trình harness/Chrome debug nào sống, container `drawio-local` up 4 ngày, 9,71/23,73 GB RAM trống, cache selenium sạch. Chạy
  `RPA_CLOSED_LOOP_MOVE=0 RPA_ANCHOR_INSERTS=0 RPA_CLOSED_LOOP_RESIZE=0 RPA_CLOSED_LOOP_LABEL=0 RPA_drawio/venv_rpa/Scripts/python.exe run_drawio_v2.py --scenarios "RPA_Datasets_new30_v2/medium_*.json" --out result/g0_baseline --port 9222`.
  10/10 case chạy hết, 0 exception. Phát hiện lượt này đã ghi đè `result/g0_baseline/summary.json`, xoá mất 20 dòng `easy`/`hard` cũ (dữ liệu case gốc trên đĩa còn nguyên). Viết script tái tạo `summary.json` cho cả 30 case, đọc trực tiếp `report.json` của từng thư mục, dùng đúng `run_one()`/`_summarize()` của `run_drawio_v2.py` để không tự chế công thức khác. Chạy lại `RPA_docs/checks/report.py result/g0_baseline --band`, lưu đè `result/g0_baseline/report.txt`.
- **Bằng chứng:** 30/30 case chạy xong, N3 99,69% [99,28–99,87] (1612/1617 bước). `move` N3+N4 **739/739 = 100%** [99,48–100,00]. Mức hình: node_f1 0,9877, edge_f1 0,9271, shape_type_accuracy 0,6570 (vẫn thấp, đúng L6), overall 0,8831. Theo band: easy 0,869, hard 0,925, medium 0,855. Kiểm chứng phép cộng: 932 (20 case cũ) + 685 (10 case mới) = 1617 bước tổng — khớp.
- **Đối chiếu main.tex:** không liên quan.
- **Trạng thái:** HOÀN TẤT mục 1/5 của G0. Move N3+N4 100% trên toàn bộ 30 case (không riêng 20 case đầu) càng làm mạnh mâu thuẫn với con số 24,6% của `DIAGNOSIS.md` §1 — chưa giải quyết được, cần mục 1 mới (lượt đối chứng) để phân biệt 3 giả thuyết.
- **Tiếp theo, chính xác:** lượt đối chứng `app.diagrams.net` vs bản ghim, lệnh ở `result/_INVALID_contrast_20260923/WHY_INVALID.md`, xác nhận đúng một tiến trình harness sống trước khi chạy.

### 2026-09-24 · khảo sát · Đọc `Kết quả thực nghiệm.xlsx`, cập nhật DIAGNOSIS/KNOWN_LIMITS/DECISIONS

- **Mục tiêu lượt này:** người giao việc cung cấp file mới — sổ tay thô 16 sheet của người đi trước, chưa từng thấy. Đọc, đối chiếu với `main.tex`, cập nhật tài liệu.
- **Nguồn gốc / vì sao:** `PLAN.md` §Bất biến 1–2 (không hard-code); `RPA_docs/README.md` luật 2 (không có số thì không có kết luận) — file mới cho số, phải ghi vào đúng chỗ trước khi dùng.
- **Đã làm:** đọc 16 sheet bằng `openpyxl` (`Thực nghiệm`, `Actions`, `drawio-2`, `Lucidchart`, `Visual Paradigm`, `few-shot`, `Nhận xét`, `Cypress`, `Test using Sikuli`, `so sánh`). Đối chiếu `generator.py::execute_python_action` (dòng 350) với ghi chú tay trong sheet `Nhận xét`. Thêm `DIAGNOSIS.md` §10 (không sửa số cũ), `KNOWN_LIMITS.md` B2 (làm rõ cơ chế) + B6–B8 (mới) + C5 (mới), `DECISIONS.md` D14.
- **Bằng chứng:** số tổng sheet `Thực nghiệm` khớp chính xác `tab:thong_ke_2`/`tab:drawio` của `main.tex`. Cột Pass/Fail là phán định người, không phải công thức — xác nhận bằng hai ví dụ ghi chú tay (`drawio-2` dòng 6, 13) và lời tác giả tự nhận ở `Nhận xét` dòng 8: *"hiện tại đang đảm bảo các test sẽ thành công — chỉ fail do mạng yếu"*. Sheet `few-shot` dòng 5 định lượng đúng lỗi L6 (60% tương đồng vì rounded rectangle → rectangle) nhưng chỉ ở tầng đọc ảnh, không ở tầng thực thi. Ba lỗi gốc mới cho Lucidchart/VP tìm thấy trong `Lucidchart` dòng 66/68/77 và `Visual Paradigm` dòng 50–56.
- **Đối chiếu main.tex:** §RQ1 (shadow-root, đường nối gấp khúc) — giờ có cơ chế cụ thể thay vì chỉ có tuyên bố. Phụ lục A (one-shot learning) — giờ biết nó có oracle riêng (LLM-giám khảo), không tất định.
- **Trạng thái:** HOÀN TẤT phần đọc và ghi tài liệu. Chưa chạy lại số nào — workbook không dùng để đo, chỉ dùng để hiểu và tìm lỗi gốc (D14).
- **Tiếp theo, chính xác:** quay lại danh sách việc còn treo của G0/G1 (xem mục dưới) — workbook mới không làm đổi thứ tự ưu tiên đó, chỉ thêm việc cho G4/G5 (B6–B8) khi tới lượt.


### 2026-09-23 · G0.6 · Baseline chạy được 20/30; hỏng lượt đối chứng vì hai harness

- **Mục tiêu lượt này:** chạy ba lượt chính thức nối nhau — baseline (trước G1), đối chứng `app.diagrams.net`, và g1_after — rồi đóng cổng G0.
- **Nguồn gốc / vì sao:** năm điều kiện G0 còn treo đều chờ số của các lượt này.
- **Đã làm:** chạy xong baseline 20/30 case. Phát hiện và xử ba sự cố: (1) 10 case `medium` chết vì `chromedriver could not start` lúc máy cạn bộ nhớ — harness ghi lại và đi tiếp, không treo; (2) lượt đối chứng có **hai** harness chạy song song cùng cổng 9222 vì bản xếp hàng cũ chưa được dừng, kết quả thành rác, đã chuyển sang `result/_INVALID_contrast_20260923/` kèm `WHY_INVALID.md`; (3) `report.py` gộp "case chưa chạy" vào "bước không phán định được" nên in 59,99% thay vì 99,68% — đã sửa để tính tỉ lệ trên case đã chạy và gọi tên case không chạy ngay dòng đầu.
- **Bằng chứng:** đạt N3 **929/932 (99,68%)** [99,06–99,89]; `move` **398/398**; báo đạt sai của thước cũ **2/931**; hỏng thầm lặng 1 (case `hard_h28_v2`, bước 97 `double_click` không mở trình soạn nhưng báo `ok`, bước 98 `fill` ghi chữ sang ô khác). Mức hình: overall 0,8974, edge_f1 0,9700, **shape_type 0,6650**. Sàn: 0,0000 / 0,4260 / 0,8000.
- **Đối chiếu main.tex:** cặp bước 97–98 đúng là lớp lỗi §RQ1 tự nhận chưa xử được — lần đầu bắt được bằng số. Và `shape_type` 0,6650 của bộ chấm tất định khớp 0,6587 của bộ chấm VLM (`DIAGNOSIS.md` §6) qua hai đường độc lập.
- **Trạng thái:** DỞ DANG — tạm dừng theo yêu cầu người giao việc. Không tiến trình nào còn chạy.
- **Tiếp theo, chính xác:** xem ô "ĐANG LÀM DỞ" ở đầu file, mục 1 tới 5.


### 2026-09-22 · G1.8–G1.9 · Hai lỗi gốc mới, tìm ra nhờ chính oracle vừa dựng

- **Mục tiêu lượt này:** chạy thử một case `medium` trước khi khởi động lô chính thức, để chắc oracle không có lỗ.
- **Nguồn gốc / vì sao:** `PLAN.md` §Bất biến 9 — báo đạt sai là lỗi chặn; thấy 8 bước báo đạt sai trên một case thì không được chạy tiếp.
- **Đã làm:** chạy `medium_m08_v3_s5b2l0`, soi 8 bước lệch. Ra hai lỗi gốc **mới**: (L7) `StepParser` ghép token nên `Fill "Documents complete?"` tới executor thành `Documents complete ?` — 35/246 bước `Fill` của bộ mới dính; (L8) `Connect` tạo cạnh không có `target`, mà `connect_cells` vẫn báo đạt vì chỉ đếm số ô. Sửa: thêm `drawio_ops.label_cell_exact` (vòng kín trên `mxCell.value`, cờ `RPA_CLOSED_LOOP_LABEL`), thêm `drawio_executor.QUOTED_RE` lấy nguyên văn chuỗi trong ngoặc kép, sửa `oracle_steps.dependencies` để một tham chiếu connector trỏ vào lần `Connect` **gần nhất trước nó** thay vì lần cuối cùng trong kịch bản. Ghi `DIAGNOSIS.md` §9.5, §9.6.
- **Bằng chứng:** case đó từ **37/45 N3, 8 báo đạt sai** lên **45/45 N3, 0 báo đạt sai**. Còn 1 báo hỏng sai: kịch bản nối cùng một cặp hai lần, tracker của executor trỏ vào cạnh thứ nhất còn oracle trỏ vào cạnh thứ hai — bản vẽ đúng, sổ sách của executor sai.
- **Đối chiếu main.tex:** L8 đúng là lớp lỗi §RQ1 tự nhận chưa xử lý được ("chọn sai phần tử nhưng hành động vẫn thực thi thành công").
- **Trạng thái:** HOÀN TẤT phần sửa. L8 chưa quy được nguyên nhân gốc — để G1.5 đo lại.
- **Tiếp theo, chính xác:** ba lượt chạy chính thức, cùng một bản code, cờ khác nhau.


### 2026-09-22 · G1.2–G1.4 · Đo cơ chế thật của draw.io rồi sửa executor theo

- **Mục tiêu lượt này:** trả lời câu hỏi G1.2 bằng số, không bằng suy đoán: draw.io quyết định điểm thả hình click-chèn bằng gì, Ctrl+Arrow đổi kích thước bao nhiêu, Shift+Arrow có rớt phím không.
- **Nguồn gốc / vì sao:** `PLAN.md` G1.2 viết thẳng "viết script dò riêng, chạy trong trình duyệt thật"; cổng G1 đòi cơ chế đó "được ghi lại thành văn trong `DIAGNOSIS.md` — không được sửa mù".
- **Đã làm:** viết `RPA_docs/checks/probe_editor.py` (4 phép đo A–D, đọc `mxGeometry`), chạy `python RPA_docs/checks/probe_editor.py --port 9403`. Kết quả thô ở `RPA_docs/probe_editor.json`. Sửa `drawio_ops.py`: thêm `move_cell_exact` (vòng kín, G1.1), `resize_cell_exact` (G1.4), `anchor_to` (G1.3), ba cờ `RPA_CLOSED_LOOP_MOVE` / `RPA_ANCHOR_INSERTS` / `RPA_CLOSED_LOOP_RESIZE` mặc định bật, tắt được để tái lập hành vi trước G1. Sửa `drawio_executor.py`: `_do_move`, `_nudge`, `_do_resize`, thêm `_anchor_insert`.
- **Bằng chứng:** Shift+Arrow đúng 10 đơn vị/phím, **0 phím mất** qua 5 loạt. Ctrl+Arrow **1** đơn vị/phím (executor đang tưởng 10 → mọi `Extend` chỉ làm được 1/10 lượng). Hình chèn ra **120×60**, không phải 48×24. Điểm chèn: chèn liên tiếp không trôi (trải 0/0); chèn xen kẽ dịch thì y trôi 400 dù có `reset_view`, và trôi 2230 khi không có. Ghi vào `DIAGNOSIS.md` §9.
- **Đối chiếu main.tex:** không liên quan.
- **Trạng thái:** HOÀN TẤT phần đo và phần code. Chưa đo tác dụng — cần cặp lượt chạy trước/sau.
- **Tiếp theo, chính xác:** `result/g1_after` (ba cờ bật), so với `result/g0_baseline` (ba cờ tắt).

### 2026-09-22 · G0.1–G0.8 · Dựng oracle độc lập, bộ chấm tất định, và các chốt chặn

- **Mục tiêu lượt này:** làm xong cổng G0 — năng lực phán định ở N3/N4, bộ chấm tất định có kiểm thử đột biến, ba baseline tầm thường, chốt chặn leakage, môi trường ghim.
- **Nguồn gốc / vì sao:** `PLAN.md` G0; luật `ORACLE.md` §2 (oracle độc lập) và §1 (không báo cáo dưới N3).
- **Đã làm:** thêm `RPA_drawio/mx_oracle.py` (đọc model qua observer tiêm, D10), `oracle_steps.py` (ngữ pháp riêng + đồ thị phụ thuộc, G0.3b), `oracle_verdict.py` (hậu điều kiện 11 hành động), `mx_control.py` (đường đo riêng cho vòng kín của executor), `leak_guard.py` (G0.5). Thêm `RPA_docs/checks/`: `graph_score.py` (G0.2), `mutations.py` (G0.3), `baselines.py` (G0.3c), `test_no_leakage.py`, `verify_splits.py`, `stats.py`, `false_pass.py` (G0.7), `report.py` (mẫu `ORACLE.md` §6), `oracle_independence.py`, `probe_editor.py`, `palette_check.py`, `repeatability.py`. Sửa `rpa_env.py` đọc `DRAWIO_URL` từ `.env` và thay `wmic` bằng CIM. Sửa `run_drawio_v2.py`: arm leak guard, ghi `env.json`, `model.xml`, `verdicts.json`, báo cáo N3 song song N0.
- **Bằng chứng:** 9/9 ca đột biến qua trên **toàn bộ 506** answer key. Kiểm chứng độc lập: ép executor trả `ok` cứng + chỉ bấm nửa số phím → executor báo 100% đạt, oracle vẫn bắt 7–8 bước hỏng (`oracle_independence.py`). Ba baseline: canvas trắng 0,0000 toàn bộ; toàn chữ nhật overall 0,4226; node không cạnh overall **0,8000**. `splits.json` dựng lại trùng khít, 20,8% giữ kín, đúng luật băm. 4/4 test leakage xanh.
- **Đối chiếu main.tex:** §RQ1 nhận là chưa xử được "chọn sai phần tử nhưng hành động vẫn thành công" — đã cài phép đo (`report.py::silent_wrong_element`), chưa có số.
- **Trạng thái:** DỞ DANG — code xong, còn thiếu số của lượt chạy thật, lượt đối chứng bản ghim ↔ `app.diagrams.net`, `palette_check`, và phần rà tay 200 bước.
- **Tiếp theo, chính xác:** chờ `result/g0_baseline` xong → `python RPA_docs/checks/report.py result/g0_baseline`.

### 2026-09-22 · môi trường · `kill_chrome_on_port` đã im lặng không làm gì

- **Mục tiêu lượt này:** dọn Chrome của harness trước một lượt chạy chính thức.
- **Nguồn gốc / vì sao:** `CLAUDE.md` cảnh báo Chrome debug còn sót làm rớt phím Shift+Arrow — `RESULTS.md` §9, `scenario_050` ra 34/41.
- **Đã làm:** phát hiện `rpa_env.kill_chrome_on_port` gọi `wmic`, mà Windows 11 (10.0.26200) **đã bỏ `wmic`**; lời gọi nằm trong `except Exception` trần nên hàm trả 0 và coi như đã dọn xong. Thay bằng `Get-CimInstance Win32_Process` qua PowerShell, giữ `wmic` làm đường lui. Vẫn lọc đúng `--remote-debugging-port=<port>` nên không đụng Chrome của người dùng.
- **Bằng chứng:** `rpa_env._chrome_pids_on_port(9222)` trả `[26072, 26444, ...]` khi harness đang chạy, `[]` khi không.
- **Đối chiếu main.tex:** không liên quan.
- **Trạng thái:** HOÀN TẤT.
- **Tiếp theo, chính xác:** không còn việc; cảnh báo trong `CLAUDE.md` giờ mới thật sự được thực thi.

