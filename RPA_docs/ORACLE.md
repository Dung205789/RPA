# Tiêu chí phán định — đo "thực thi đúng" cho một công cụ kiểm thử

> 🔒 **KHOÁ NGÀY 2026-09-20.** File này là hợp đồng thiết kế của dự án. Sửa nội
> dung (không tính việc tick checkbox ở `PLAN.md`, đó là trạng thái, không phải
> thiết kế) bắt buộc phải: (1) ghi lý do vào `RPA_docs/TRACE.md`, (2) cập nhật
> hash trong `RPA_docs/LOCKS.md`, (3) nếu đổi ngưỡng hoặc luật, thêm mục LẬT
> vào `DECISIONS.md`. Sửa mà không làm cả ba bước này là vi phạm quy trình.


Đề tài là **kiểm thử giao diện**. Nên thứ phải chứng minh không phải "vẽ ra
hình đẹp" mà là: **công cụ phán định đúng việc kịch bản có chạy đúng hay
không**. Một bộ kiểm thử báo *đạt* khi ứng dụng làm sai thì nguy hiểm hơn là
không có bộ kiểm thử nào.

File này định nghĩa *đo cái gì*. Trình tự làm nằm ở [`PLAN.md`](PLAN.md).

---

## 1. Thang phán định — năm mức

Mỗi bước trong kịch bản được phán định ở một trong năm mức. Mức càng cao càng
khó gian lận.

| Mức | Nghĩa | Ví dụ với `Move ... up` |
|-----|-------|--------------------------|
| **N0** | Không ném ngoại lệ | hàm chạy xong, không crash |
| **N1** | Hành động có xảy ra | canvas có thay đổi gì đó |
| **N2** | Đúng phần tử đích | đúng ô được chọn, không phải ô khác |
| **N3** | **Đúng hậu điều kiện** | ô đó dịch lên đúng 150px ±2px |
| **N4** | **Không tác dụng phụ** | không ô nào khác bị xê dịch, thêm, xoá |

**Hiện tại toàn bộ hệ đang báo cáo ở N0**, và `RESULTS.md` gọi đó là "tỉ lệ
bước thành công 93,88%". `DIAGNOSIS.md` L1 cho thấy N0 chấp nhận cả trường hợp
dịch 75px trên yêu cầu 150px.

> **Luật.** Từ G0 trở đi, **không con số nào được báo cáo ở mức thấp hơn N3**.
> N4 bắt buộc cho `Move`, `Connect`, `Delete`. Khi báo cáo phải ghi rõ con số
> đang ở mức nào.

### Hậu điều kiện của từng hành động

Bảng này liệt kê **đủ** từ vựng mà executor cài đặt. Đối chiếu ngày 2026-09-20:
`StepParser.SUPPORTED_ACTIONS` có 15 mục, `DrawioExecutor._HANDLERS` gộp chúng
thành **10 hành vi phân biệt**. Không hành vi nào được bỏ trống oracle.

| # | Hành động (và bí danh) | Hậu điều kiện N3 | N4 |
|---|------------------------|------------------|-----|
| 1 | `open` | URL đã tải, palette shape render đủ (`a.geItem` ≥ ngưỡng), không modal chặn | canvas trống |
| 2 | `click` trên `[icon]` | đúng **một** ô mới xuất hiện, loại đúng như icon chỉ định | không ô cũ nào đổi |
| 2b | `click` trên `[icon]` của kho icon **hỗn hợp** | không ra được hậu điều kiện tổng quát — khai ở **N2**, báo cáo riêng (D12) | không ô nào đổi |
| 3 | `click` trên `<text>` | đúng phần tử mang chữ đó **và đang hiển thị** được kích hoạt | — |
| 4 | `double click` | trình soạn nhãn mở **trên đúng ô đích** (so khung soạn với khung ô) | không ô nào đổi |
| 5 | `fill` / `enter` | nhãn của ô đích **bằng đúng** chuỗi X, đã commit | không nhãn nào khác đổi |
| 6 | `move` | dời đúng khoảng cách, đúng hướng, ±2px, đo trong toạ độ mô hình | không ô nào khác dời |
| 7 | `connect` / `link` | đúng một cạnh mới, `source=A`, `target=B` theo mô hình | không cạnh cũ nào đổi neo |
| 8 | `extend` / `scale up` | kích thước tăng đúng chiều, đúng lượng ±2px | **cạnh đối diện đứng yên** ±2px (LẬT 2026-09-22, D11) |
| 9 | `shrink` / `scale down` | kích thước giảm đúng chiều, đúng lượng ±2px | **cạnh đối diện đứng yên** ±2px (LẬT 2026-09-22, D11) |
| 10 | `delete` / `remove` | ô đích biến mất khỏi mô hình | không ô nào khác biến mất |
| 11 | `press` | phím tới đúng phần tử đang nhận focus, và gây đúng hiệu ứng mong đợi | — |

> **Sửa 2026-09-22 (D11).** Cột N4 của hàng 8 và 9 trước đây ghi *"vị trí tâm
> giữ nguyên"*. Đo trên bản ghim (`RPA_docs/probe_editor.json` mục B): Ctrl+Right
> tăng `w` và giữ nguyên `x`, nên tâm **buộc phải** dịch nửa lượng khi kéo một
> cạnh — hậu điều kiện cũ đánh hỏng mọi thao tác làm đúng. Xem `DIAGNOSIS.md`
> §9.4. Phần N3 không đổi.

> `press` là hành động khó ra hậu điều kiện tổng quát nhất (Enter trong ô tìm
> kiếm khác Enter trên canvas). Nếu không ra được N3 tổng quát thì **khai báo
> nó ở N2 và báo cáo riêng**, không lẳng lặng để nó ở N0.

---

## 2. Oracle phải độc lập với executor

Hiện tại `move_cell()` vừa thực hiện cú dịch **vừa tự chấm** cú dịch đó, bằng
chính hàm đo của mình. Đó là tự cấp chứng chỉ cho mình.

> **Luật.** Phán định N3/N4 phải đọc từ **mxGraph XML xuất ra**, qua một đường
> mã độc lập với đường đã thực hiện hành động. Executor được phép tự đo để biết
> khi nào cần bấm bù (vòng kín), nhưng **con số báo cáo** phải lấy từ oracle
> độc lập.

Kiểm chứng tính độc lập: cố tình làm executor báo sai (trả `ok` cứng) thì
oracle phải vẫn bắt được lỗi.

---

## 3. Chỉ số bắt buộc — và ngưỡng

### 3.1 Sai lệch phán định *(quan trọng nhất)*

| Chỉ số | Định nghĩa | Ngưỡng |
|--------|------------|--------|
| **Báo đạt sai** (false pass) | bước được đánh `ok` nhưng hậu điều kiện N3 bị vi phạm | **0** trên mẫu rà tay ≥50 bước; cận trên KTC 95% **<2%** |
| **Báo hỏng sai** (false fail) | bước bị đánh `failed` nhưng hậu điều kiện thật sự đạt | **≤2%** |
| **Hỏng thầm lặng** (silent wrong-element) | hành động thành công nhưng tác động lên **sai** phần tử | **≤1%** |

Ô "báo đạt sai" là chỉ số sống còn. `main.tex` §RQ1 tự thừa nhận điểm yếu này:
*"cơ chế fallback hiện tại chỉ kích hoạt khi hành động không thể thực hiện
được, chưa đủ để xử lý các trường hợp chọn sai phần tử nhưng hành động vẫn
được thực thi thành công"*. Đây chính là lớp lỗi phải đo, không phải né.

**Cách đo:** lấy mẫu ngẫu nhiên có hạt giống cố định từ các bước được đánh
`ok`, rà bằng oracle độc lập **và** bằng mắt, rồi báo cáo kèm KTC.

### 3.2 Độ lặp lại *(một bộ kiểm thử chập chờn thì vô dụng)*

| Chỉ số | Định nghĩa | Ngưỡng |
|--------|------------|--------|
| **Đồ thị cuối ổn định** | chạy cùng kịch bản 5 lần → đồ thị cuối đẳng cấu (cùng node, cùng cạnh, cùng nhãn) | **≥95%** cặp lần chạy |
| **Vị trí ổn định** | độ lệch vị trí giữa các lần chạy | **p95 ≤5px** |
| **Phán định ổn định** | cùng một bước cho cùng kết quả đạt/hỏng qua 5 lần | **≥98%** |

Chạy trên tập con ≥20 case, trải đều ba band độ khó. Con số chập chờn phải
được báo cáo là chập chờn, **không** được lấy lần chạy đẹp nhất.

> `RESULTS.md` §9 đã từng gặp đúng chuyện này: `scenario_050` ra 34/41 rồi
> 41/41 vì một Chrome debug còn sót tranh CPU. Lần đó xử lý bằng cách chạy lại;
> lần này phải **đo** độ chập chờn thành một con số.

### 3.3 Độc lập giữa các bước

`main.tex` §RQ1 tuyên bố: *"sự thành công/thất bại của bước trước sẽ đảm bảo để
không ảnh hưởng tới bước sau trong quá trình thống kê"*.

Tuyên bố này **hiện đang sai** và phải được xử lý minh bạch: mọi vị trí trong
DSL đều tính tương đối so với node neo, nên một `Move` hỏng làm sai vị trí của
mọi node sau nó.

| Chỉ số | Định nghĩa | Ngưỡng |
|--------|------------|--------|
| **Bước phụ thuộc** | với mỗi bước hỏng, liệt kê các bước sau phụ thuộc vào nó | phải liệt kê được 100% |
| **Tỉ lệ bước độc lập** | tỉ lệ bước hỏng **không** kéo theo bước nào | báo cáo, không đặt ngưỡng |

Harness phải dựng **đồ thị phụ thuộc** của kịch bản (bước N tham chiếu "element
created in step K" thì N phụ thuộc K). Khi báo cáo, tách ba nhóm:

* **hỏng gốc** — bước tự nó sai
* **hỏng kéo theo** — bước đúng nhưng đầu vào đã sai từ trước
* **đạt**

Gộp ba nhóm này vào một tỉ lệ duy nhất là cách con số 93,88% ra đời.

### 3.4 Bất biến môi trường

`main.tex` §RQ1 tuyên bố phương pháp không bị ảnh hưởng bởi giao diện sáng/tối
và bởi DPR 1,25 → 1,0. Tuyên bố kiểm chứng được thì phải kiểm chứng.

| Cấu hình | Ngưỡng |
|----------|--------|
| sáng ↔ tối | chênh lệch tỉ lệ đạt N3 **≤2 điểm phần trăm** |
| DPR 1,0 ↔ 1,25 | chênh lệch **≤2 điểm phần trăm** |

Chạy trên cùng một tập con ≥20 case cho cả bốn tổ hợp.

### 3.5 Phục hồi và fallback

| Chỉ số | Định nghĩa | Ngưỡng |
|--------|------------|--------|
| **Kích hoạt fallback đúng lúc** | fallback chạy khi và chỉ khi bước chính hỏng | ≤1% kích hoạt thừa |
| **Không treo** | không kịch bản nào làm harness treo vô hạn | **0** |
| **Sống sót khi trình duyệt chết** | trình duyệt chết giữa chừng → ghi lại và đi tiếp case sau | **100%** |

### 3.6 Chi phí *(RQ2 của bài)*

| Chỉ số | Ghi nhận |
|--------|----------|
| Thời gian thực thi mỗi case | trung vị + p95, tách theo band |
| Số lần gọi LLM mỗi case | trung vị |
| Token vào / ra mỗi case | trung vị, quy ra tiền |

Yêu cầu gốc nói rõ chi phí phải tối giản vì phải gọi nhiều lần. Không có số thì
không chứng minh được.

---

## 4. Kiểm thử chính bộ chấm

> Luật số 6 trong `CLAUDE.md` của kho cha: *"Test the evaluator, not just the
> agent. A bug in scoring invalidates every decision made from it."*

Bộ chấm phải qua **kiểm thử đột biến**: lấy một bản vẽ đúng, gieo vào đó một
lỗi đã biết, rồi kiểm tra điểm có đổi đúng hướng và đúng độ lớn không.

| # | Đột biến gieo vào | Kỳ vọng |
|---|-------------------|---------|
| 1 | giống hệt bản gốc | mọi chỉ số = 1,00 |
| 2 | canvas trắng | mọi chỉ số = 0,00 |
| 3 | xoá 1 cạnh trên n | tìm đúng cạnh giảm đúng 1/n |
| 4 | hoán vị nhãn 2 node | đúng nhãn giảm, tìm đúng hình **không** đổi |
| 5 | đổi 1 loại hình | đúng loại hình giảm đúng 1/n, các chỉ số khác giữ nguyên |
| 6 | dời 1 node 20px | giống bố cục giảm nhẹ, các chỉ số khác giữ nguyên |
| 7 | dời 1 node 300px | giống bố cục giảm mạnh hơn ca 6 |
| 8 | đảo chiều 1 cạnh | tìm đúng cạnh giảm (cạnh có hướng) |
| 9 | thêm 1 node thừa | tìm đúng hình **không** tăng; độ chính xác giảm |

Ca 9 chống đúng một kiểu gian lận: vẽ thừa hình để tăng recall. Vì thế mọi chỉ
số dạng "tìm đúng" phải đi kèm chỉ số "vẽ thừa".

> **Luật.** Mẫu số luôn là số đếm của **bản tham chiếu**, không bao giờ là số
> đã khớp được.

---

## 5. Ba baseline tầm thường — sàn điểm

Không có sàn thì không biết điểm cao là do phương pháp hay do bài dễ.

| Baseline | Cách dựng | Nó bắt được gì |
|----------|-----------|----------------|
| Canvas trắng | không làm gì | bộ chấm có cho điểm miễn phí không |
| Toàn chữ nhật | đúng số node, đúng vị trí, sai hết loại hình, không cạnh | phần điểm đến từ riêng bố cục |
| Node không cạnh | đúng node + đúng nhãn + đúng loại, bỏ hết cạnh | phần điểm đến từ riêng cạnh |

Mọi bảng kết quả phải in ba dòng này ở đầu.

---

## 6. Mẫu báo cáo bắt buộc

Mọi lượt chạy báo cáo theo đúng khung này. Thiếu dòng nào thì lượt chạy đó chưa
được coi là đã báo cáo.

```
Lượt chạy : <đường dẫn>          Ngày: <yyyy-mm-dd>
Corpus    : <tên>  n=<số case>   Tập: chỉnh | giữ kín
Mức phán định báo cáo: N3 + N4

-- Sàn --
  canvas trắng        : <điểm>
  toàn chữ nhật       : <điểm>
  node không cạnh     : <điểm>

-- Mức bước --
  đạt N3              : <x>% [KTC]
  hỏng gốc            : <x>%
  hỏng kéo theo       : <x>%
  báo đạt sai         : <x>% [KTC]      <- phải là 0
  báo hỏng sai        : <x>% [KTC]
  hỏng thầm lặng      : <x>% [KTC]

-- Mức hình (oracle tất định) --
  node / cạnh / nhãn / loại hình / vẽ thừa
  sai số vị trí sau Procrustes: trung vị, p95

-- Ổn định --
  đồ thị cuối đẳng cấu qua 5 lần: <x>%
  phán định ổn định             : <x>%

-- Chi phí --
  thời gian/case: trung vị, p95
  gọi LLM/case  : trung vị       token: vào/ra       tiền: <x>

-- Đã nhìn bằng mắt --
  <≥10 case, mỗi case một dòng mô tả sai ở đâu>
```

Dòng cuối không phải trang trí. Số có thể đúng mà bản vẽ vẫn vô nghĩa — đó
chính là cách lượt chạy trước lọt qua.
