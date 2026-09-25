# Nhật ký quyết định

> 🔒 **KHOÁ NGÀY 2026-09-20.** File này là hợp đồng thiết kế của dự án. Sửa nội
> dung (không tính việc tick checkbox ở `PLAN.md`, đó là trạng thái, không phải
> thiết kế) bắt buộc phải: (1) ghi lý do vào `RPA_docs/TRACE.md`, (2) cập nhật
> hash trong `RPA_docs/LOCKS.md`, (3) nếu đổi ngưỡng hoặc luật, thêm mục LẬT
> vào `DECISIONS.md`. Sửa mà không làm cả ba bước này là vi phạm quy trình.


Mỗi quyết định thiết kế ghi một mục: **chọn gì**, **vì sao**, **bằng chứng nào**,
**trạng thái**. Quyết định bị lật thì đánh dấu LẬT và ghi mục mới, không xoá mục
cũ — để sau này còn biết vì sao từng chọn thế.

Trạng thái: `CHỐT` · `TẠM` (chưa có bằng chứng, dùng đến khi có) · `LẬT` · `TREO`
(đang chờ người giao việc).

---

## D1 — Chấm bằng VLM nhìn ảnh, không dùng scorer XML của SVG_agent

**Trạng thái:** CHỐT (2026-09-03, người giao việc quyết)

Hướng RPA và hướng web agent là hai bài khác nhau; dùng chung scorer sẽ trói kết
quả của bài này vào thiết kế của bài kia.

**Cái giá:** bộ chấm dao động ±0,05–0,08 giữa các lần chấm cùng một lượt chạy
(`RESULTS.md` §7.2). Vì thế từ G0 có thêm **bộ chấm tất định đọc mxGraph XML**
chạy song song — VLM thành thước phụ, không phải thước chính. Xem `ORACLE.md`.

## D2 — Thứ tự nhà cung cấp LLM: Gemini → OpenAI → Anthropic

**Trạng thái:** CHỐT (2026-09-03, người giao việc quyết)

Hết quota thì rớt sang nhà kế tiếp. Khoá đọc từ `D:\SVG_agent\.env`.

## D3 — `MOVE_STEP_PX = 150`

**Trạng thái:** TẠM — dự kiến LẬT ở G2.1

Một `Move` trong DSL đáng giá 150px model. Đo 2026-09-03: 1, 5, 15 lần
Shift+Arrow dời shape 10, 50, 150px, nên `PX_PER_ARROW_PRESS = 10`.

**Vì sao sẽ lật:** 150px là quantum quá thô so với hình 48×24px, buộc converter
đặt `TARGET_MIN_SEP_PX = 1.7 × 150` và thổi phồng bố cục — `DIAGNOSIS.md` L3/L4.
Không được lật trước khi qua cổng G1, nếu không sẽ không biết bản vá nào có tác
dụng.

## D4 — Bộ icon shape dựng từ chính ô tìm kiếm của draw.io

**Trạng thái:** CHỐT

`build_shape_icons.py` dựng 9 icon từ giao diện thật thay vì cắt tay từ ảnh
chụp, để bộ khớp icon và draw.io nói về cùng một hình.

## D5 — Rounded rectangle được vẽ bằng icon rectangle

**Trạng thái:** TẠM — sẽ xét lại ở G2.4

Ở cỡ thumbnail, ink mask của hai hình giống nhau 97%. Khai báo trong
`_shape_substitutions` của từng kịch bản, không giấu.

**Cái giá:** `shape_type_accuracy` chỉ 0,659 trên bộ mới; 949/3516 node của
benchmark là rounded rectangle. G2.4 sẽ thử đường khác (tìm theo từ khoá, hoặc
sửa style sau khi chèn). Không sửa được thì phải **báo cáo tách riêng** chỉ số
có/không tính loại hình.

## D6 — Không sửa code gốc của người đi trước

**Trạng thái:** CHỐT

`generator.py`, `step_parser.py`, `by_text.py`, `by_image*.py`,
`find_element.py`, `detect_new_g.py` giữ nguyên; code mới đặt file mới. Đổi lại
thì baseline không tái lập được. Ngoại lệ đã dùng: đường dẫn model tuyệt đối của
máy tác giả, và `RPA_CHROME_DEBUG_PORT` để chạy song song.

## D7 — Ưu tiên chiều sâu: draw.io trên cả hai bộ trước

**Trạng thái:** CHỐT (2026-09-20, người giao việc quyết)

Làm xong draw.io trên `RPA_Datasets` (100) và `../data/datasets` (506) rồi mới
sang Visual Paradigm; Lucidchart để cuối vì còn vướng đăng nhập.

## D8 — Báo cáo ở mức N3/N4, không phải N0

**Trạng thái:** CHỐT (2026-09-20)

Đề tài là kiểm thử, nên phải chứng minh *công cụ phán định đúng hay sai*. Toàn
bộ định nghĩa ở `ORACLE.md`.

**Bằng chứng buộc phải đổi:** thước cũ nhận 75px trên yêu cầu 150px là đạt; đo
lại thì chỉ 24,6% bước `Move` dời đúng khoảng cách (`DIAGNOSIS.md` §1).

**Cái giá:** mọi con số trong `RESULTS.md` thành không so sánh được với số mới.
Phải đánh dấu rõ, không xoá.

## D9 — Ghim `jgraph/drawio:28.2.5` cục bộ, kèm một lượt đối chứng

**Trạng thái:** CHỐT (2026-09-20). Người giao việc uỷ quyền — *"bản nào phù hợp
nhất là được"* — nên lý do chọn ghi đủ ở đây để sau này còn lật lại được.

**Chọn gì.** Dựng `docker run -d --name drawio-local -p 8080:8080
jgraph/drawio:28.2.5`, trỏ `DRAWIO_URL` vào đó. Chạy thêm **một lượt đối chứng**
trên 30 case so với `app.diagrams.net`, ghi chênh lệch vào `RESULTS.md` như một
giới hạn đã biết.

**Vì sao.** Đề tài là kiểm thử, nên đối tượng đo phải đứng yên. Trang công cộng
tự cập nhật, nên: chạy lại sau ba tháng ra số khác mà không biết vì sao; điểm
tụt thì không tách được "do bản vá" với "do draw.io đổi giao diện"; và
`palette_matcher` so ảnh với bảng shape thật nên jgraph đổi một icon là hỏng,
không báo trước. Lượt đối chứng giữ lại khả năng so với `main.tex`, vốn chạy
trên trang công cộng.

**Bằng chứng.** Đo 2026-09-20: `rpa_env.py:38` hard-code
`https://app.diagrams.net/`, trong khi `D:\SVG_agent\.env` có
`DRAWIO_URL=http://localhost:8080` **bị bỏ qua**; không có draw.io cục bộ nào
đang chạy. Toàn bộ số hiện có đều đo trên trang công cộng, không ghim bản.

**Cái giá.** Bản ghim có thể khác bản công cộng ở vài shape — chính lượt đối
chứng để định lượng chỗ đó. Phải kiểm lại `palette_matcher` trên bảng shape của
bản ghim trước khi chạy lô dài.

**Khả thi.** Docker 28.0.4 + Docker Desktop đã cài trên máy (kiểm 2026-09-20),
chỉ cần khởi động. `DRAWIO_URL` phải đọc từ `.env` thay vì hard-code — đây là
sửa tối thiểu ở `rpa_env.py`, thuộc ngoại lệ đã cho phép ở D6.

## D10 — Oracle đọc model qua một observer tiêm lúc tải trang

**Trạng thái:** CHỐT (2026-09-22)

**Chọn gì.** `RPA_drawio/mx_oracle.py` tiêm một đoạn JS bằng
`Page.addScriptToEvaluateOnNewDocument` **trước** khi script của draw.io chạy;
đoạn đó bọc `mxGraph.prototype.init` để mọi graph được dựng tự ghi tên mình vào
`window.__RPA_GRAPHS__`. Oracle lấy instance có container `.geDiagramContainer`,
rồi `mxUtils.getXml(new mxCodec().encode(graph.getModel()))`.

**Vì sao.** `ORACLE.md` §2 buộc phán định phải đọc mxGraph XML qua đường độc lập
với executor. Đo 2026-09-22: draw.io **không** xuất `EditorUi` instance ra
`window` (đã dò `App`, `EditorUi`, `Editor`, `Graph`, `mxCodec`, `editorUi`, và
quét toàn bộ khoá của `window`) — không có đường nào lấy model mà không tiêm.

**Đã cân nhắc và bỏ.** Mở `Extras > Edit Diagram` rồi đọc textarea: đúng là
đường UI thuần, nhưng nó là modal — mở giữa hai bước sẽ xoá selection và đóng
trình soạn nhãn, tức là **làm thay đổi** đúng trạng thái đang cần chấm. Oracle
không được phép can thiệp vào thứ nó đo.

**Cái giá.** Chấm phụ thuộc một chi tiết nội bộ của mxGraph. Nếu jgraph đổi
`mxGraph.prototype.init` thì hook gãy — nhưng gãy **ồn ào**: `model_xml()` ném
`OracleUnavailable`, và `Oracle.after()` trả `no-verdict`, không bao giờ trả
"đạt". Đây là lý do hàm đó không có nhánh nào biến lỗi đọc thành điểm.

**Observer chỉ quan sát.** Nó không tạo, không dời, không xoá ô nào, và đường
thực thi không bao giờ hỏi nó cái gì.

## D11 — LẬT một phần `ORACLE.md` §1 hàng 8–9: N4 của resize là "cạnh đối diện đứng yên"

**Trạng thái:** CHỐT (2026-09-22). **LẬT** phần "vị trí tâm giữ nguyên" của
`ORACLE.md` §1 hàng 8 và 9. Phần N3 của hai hàng đó giữ nguyên.

**Bằng chứng.** `RPA_docs/probe_editor.json` mục B, đo trên bản ghim: Ctrl+Right
tăng `w` 1 đơn vị mỗi phím và **giữ nguyên `x`**. Kéo một cạnh ra thì tâm **buộc
phải** dịch nửa lượng. Hậu điều kiện cũ sẽ đánh hỏng 100% các bước `Extend` làm
đúng.

**Thay bằng.** N4 = (a) không ô nào khác đổi, **và** (b) cạnh mà bước **không**
nhắc tới đứng yên trong sai số ±2. Với `Extend the right edge` thì `x` phải giữ;
với `Extend the left edge` thì cạnh phải giữ, tức `x + w` không đổi. Độ dịch của
tâm vẫn được ghi ra hàng phán định (`centre_moved`) để không mất thông tin.

**Cái giá.** N4 của resize giờ yếu hơn một chút so với chữ trong hợp đồng cũ:
một thao tác vừa kéo cạnh vừa dời cả hình đúng bằng lượng kéo sẽ lọt. Chưa thấy
draw.io làm thế; nếu thấy thì siết lại.

## D12 — `click` trên ảnh thuộc thư mục icon hỗn hợp báo cáo ở N2, không phải N3

**Trạng thái:** CHỐT (2026-09-22)

**Chọn gì.** `oracle_steps` tách `Click on [x.png]` làm hai hành động:
`click_shape` khi ảnh nằm trong một **thư mục từ vựng hình** (≤15 png, như
`RPA_drawio/shape_icons` — 9 hình), và `click_control` khi nằm trong một kho
icon hỗn hợp (`RPA_Datasets/images/drawio` — 64 file, phần lớn là nút toolbar và
mục menu). `click_shape` chấm ở N3+N4 như `ORACLE.md` §1 hàng 2.
`click_control` chấm ở **N2+N4** và báo cáo tách riêng.

**Vì sao.** Hàng 2 của `ORACLE.md` giả định ảnh trong ngoặc là một hình, nên hậu
điều kiện là "đúng một ô mới xuất hiện". `KNOWN_LIMITS.md` A ghi rõ `object7.png`
là một nút toolbar và `object2.png` là ô điều khiển zoom — với những bước đó,
"một ô mới xuất hiện" là hậu điều kiện **sai**, và ép nó sẽ tạo ra báo hỏng sai
hàng loạt. Không có cách nào đọc từ model để biết một icon *đáng lẽ* làm gì.

**Đây không phải hard-code theo case.** Luật phát biểu trên **thư mục**, không
trên tên file hay id case, và áp cho mọi kịch bản dùng thư mục đó.

**Ảnh hưởng.** Bộ 30 case mới dùng `RPA_drawio/shape_icons` nên 100% ở N3+N4.
Bộ 100 case cũ có 167 bước loại này rơi xuống N2 — phải ghi rõ mỗi lần báo cáo
bộ đó, và phải tìm đường nâng lên N3 trước khi G3 chốt số bộ cũ.

## D13 — Khớp bố cục bằng Procrustes **không xoay**

**Trạng thái:** CHỐT (2026-09-22)

**Chọn gì.** `RPA_docs/checks/graph_score.py` khớp bản vẽ với bản tham chiếu
bằng phép đồng dạng gồm **tịnh tiến + một hệ số co giãn đều**, không có thành
phần xoay và không có phản chiếu.

**Vì sao.** Procrustes cổ điển có xoay. Với lưu đồ thì xoay là mất thông tin:
"trên" nghĩa là "trước". Một bản vẽ quay 90° sẽ được chấm hoàn hảo, mà nó sai.

**Cái giá.** Chữ "Procrustes" trong `PLAN.md` G0.2 và trong cổng G2 phải đọc là
"Procrustes không xoay". Ghép cặp node làm bằng Hungarian **chỉ trên vị trí** —
không dùng nhãn, không dùng loại hình — vì `ORACLE.md` §4 ca 4 và ca 5 đòi các
chỉ số khác đứng yên khi đổi nhãn/đổi loại; ghép theo nhãn thì hai ca đó hỏng.

## D14 — `Kết quả thực nghiệm.xlsx` dùng làm bằng chứng lịch sử, không làm đáp án N3

**Trạng thái:** CHỐT (2026-09-24, người giao việc cung cấp file)

**Chọn gì.** Workbook `documents/Kết quả thực nghiệm.xlsx` (16 sheet, log thô
của người đi trước) được dùng cho hai việc: (1) xác nhận số trong `main.tex` có
nguồn thật — số ở sheet `Thực nghiệm` khớp chính xác `tab:thong_ke_2`/
`tab:drawio`; (2) nguồn lỗi gốc mới cho Lucidchart/Visual Paradigm, ghi ở
`KNOWN_LIMITS.md` B6–B8. **Không** dùng cột Pass/Fail của workbook làm đáp án
để chấm lại số mới, và không đổi bất kỳ ngưỡng nào trong `ORACLE.md`/`PLAN.md`
theo số trong đó.

**Vì sao.** File tự chứng minh nó không đạt mức N3: sheet `Nhận xét` dòng 8, lời
tác giả — *"hiện tại đang đảm bảo các test sẽ thành công — chỉ fail do mạng
yếu"* — xác nhận Pass/Fail của workbook đo ở mức *"hành động có chạy được
không"*, khớp đúng lỗ hổng mà `ORACLE.md` toàn bộ được viết ra để vá. Dùng nó
làm đáp án sẽ lặp lại chính sai lầm dự án đang sửa.

**Cái giá.** Không có cách nào tái lập được nguyên bản môi trường đã sinh ra
workbook này (backend `localhost:8123` không còn, không rõ hồ sơ Chrome, không
ghim bản draw.io) — xem `DIAGNOSIS.md` §10. Nên workbook chỉ dùng để *hiểu
phương pháp cũ* và *tìm manh mối lỗi*, không dùng để *đo lại*.
