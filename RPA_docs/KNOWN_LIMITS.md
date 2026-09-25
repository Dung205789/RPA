# Giới hạn đã biết — **không** được "sửa" bằng hard-code

> 🔒 **KHOÁ NGÀY 2026-09-20.** File này là hợp đồng thiết kế của dự án. Sửa nội
> dung (không tính việc tick checkbox ở `PLAN.md`, đó là trạng thái, không phải
> thiết kế) bắt buộc phải: (1) ghi lý do vào `RPA_docs/TRACE.md`, (2) cập nhật
> hash trong `RPA_docs/LOCKS.md`, (3) nếu đổi ngưỡng hoặc luật, thêm mục LẬT
> vào `DECISIONS.md`. Sửa mà không làm cả ba bước này là vi phạm quy trình.


Danh sách này tồn tại để chặn đúng một cám dỗ: thấy một case hỏng, nhận ra nó
hỏng vì chính kịch bản chứ không vì executor, rồi vẫn "sửa" nó bằng một nhánh
đặc biệt để con số đẹp lên. Đó là gian lận, và `PLAN.md` §Bất biến luật 2 cấm.

Trạng thái: `THUỘC KỊCH BẢN` (dữ liệu vốn thế, không sửa) · `GIỚI HẠN CÔNG CỤ`
(có thể sửa được nếu tìm ra đường khác) · `ĐÃ SỬA`.

---

## A. Thuộc về chính kịch bản — tuyệt đối không vá

Bốn case này đã rà từng bước và xác minh (`RESULTS.md` §7.4). Chúng **phải** tiếp
tục hỏng. Nếu một bản vá làm chúng đạt, bản vá đó gần như chắc chắn đã hard-code.

| Case | Hỏng ở đâu | Vì sao không phải lỗi executor |
|------|-----------|-------------------------------|
| `scenario_051` (35/43) | bước 22 click `object7.png` | `object7.png` là một nút trên thanh công cụ, không phải shape — nên "element created in step 22" mà 9 bước sau tham chiếu **không tồn tại** |
| `scenario_100` (5/6) | "Clipart / Computer" | là mục cây danh mục cần mở rộng trước; thao tác mở-rộng-rồi-chọn chưa có trong từ vựng DSL |
| `scenario_058` (4/5) | icon `object23.png` | khớp nhầm nút "Edit" trên toolbar thay vì ô chọn màu nền |
| `scenario_088` (30/32) | bước 12 và 14 | hai shape trùng khít vị trí vì cả hai chỉ dịch "down" đúng một lần từ cùng điểm chèn — **kịch bản vốn thế** |

> `scenario_058` là ca ranh giới: khớp icon sai **là** lỗi công cụ. Nhưng sửa nó
> phải bằng một quy tắc chung về cách phân biệt nút toolbar với ô chọn màu,
> không phải bằng ngoại lệ cho `object23.png`.

## B. Giới hạn công cụ — được phép sửa, nhưng phải bằng quy tắc chung

| # | Giới hạn | Ảnh hưởng | Định sửa ở |
|---|----------|-----------|------------|
| B1 | Rounded rectangle không tách được khỏi rectangle ở cỡ thumbnail (ink mask giống 97%) | `shape_type_accuracy` 0,659; 949/3516 node | G2.4 |
| B2 | Phần tử trong shadow-root không có XPath trực tiếp — cơ chế cụ thể (2026-09-24, `Kết quả thực nghiệm.xlsx` sheet `Visual Paradigm`): toạ độ **xác định đúng**, nhưng click theo XPath bị lệch; đôi khi `document.querySelector` xuyên shadow-root trả `NULL` (nghi CSP) | `main.tex` §RQ1 nêu; định lượng được cơ chế nhưng chưa định lượng tỉ lệ | G4 — thử click theo toạ độ tuyệt đối (`ActionChains` offset) thay vì `find_element(...).click()` khi phần tử trong shadow-root, trước khi thử giải bài toán XPath xuyên shadow-root nói chung |
| B3 | Chọn **sai** phần tử nhưng hành động vẫn thành công — fallback không bắt được | chưa đo trên bộ mới; xác nhận có thật trên bộ cũ, xem `DIAGNOSIS.md` §9.6, §10.1 | G1.7, ngưỡng ≤1% |
| B4 | Đường nối gấp khúc: tâm khung bao không nằm trên đường, nên double-click đặt nhãn trượt | `arrow_label_accuracy` 0,657 bộ mới | G1.5 |
| B5 | Phần tử canvas của Lucidchart không xuất hiện trên DOM | chặn oracle N3/N4 cho Lucid | G5 |
| B6 | **Lucidchart:** nhãn dài làm hình tự giãn, tâm hình đổi theo — ghi nhận từ `Kết quả thực nghiệm.xlsx` sheet `Lucidchart`, chưa đo trên hệ thống hiện tại | chưa xếp lịch (chờ G5 mở) | G5 — nếu định vị theo tâm hình sau khi đặt nhãn, phải đọc lại kích thước hình *sau* khi gõ nhãn, không dùng kích thước lúc chèn |
| B7 | **Lucidchart:** luồng dài làm hình trượt khỏi màn hình hoặc chồng lên nhau ("2 hình thoi đè lên nhau, không thể move") | chưa xếp lịch (chờ G5 mở) | G5 |
| B8 | **Visual Paradigm:** quan hệ DOM anh em (text và checkbox) bị đọc nhầm thành cha-con, khiến gán nhãn cho ô sai | chưa xếp lịch (chờ G4 mở) | G4 |

## C. Giới hạn của bộ đo, không phải của phương pháp

| # | Giới hạn | Xử lý |
|---|----------|-------|
| C1 | Bộ chấm VLM dao động ±0,05–0,08 giữa các lần chấm cùng lượt chạy | đọc như khoảng, không như điểm; từ G0 có bộ chấm tất định chạy song song |
| C2 | Bộ 100 case cũ **không có gold**; ảnh tham chiếu dựng bằng `scenario_to_gold.py` từ chính lời kịch bản | nó đo *độ trung thành khi thực thi kịch bản*, **không** đánh giá bố cục gốc đẹp hay xấu — phải ghi rõ mỗi lần trích |
| C3 | 76/100 case cũ chỉ thao tác menu, không vẽ gì | chỉ chấm được ở mức bước; không gộp vào điểm mức hình |
| C4 | Bộ dữ liệu trên máy không khớp `tab:thong_ke_2` của `main.tex` | không chỉnh số cho khớp; xem `DIAGNOSIS.md` §7 |
| C5 | `Kết quả thực nghiệm.xlsx` (2026-09-24) là sổ tay thô của người đi trước, xác nhận số của `main.tex` có nguồn thật — nhưng cột Pass/Fail trong đó là phán định **người**, đo ở mức N1–N2, không có hậu điều kiện hình học | dùng làm bằng chứng lịch sử và nguồn lỗi gốc mới (`DIAGNOSIS.md` §10); **không** dùng làm đáp án N3 để so sánh số mới |

---

## Quy tắc khi gặp một case hỏng mới

1. Đọc kỹ chính kịch bản trước khi đổ lỗi cho executor.
2. Hỏng vì kịch bản → thêm vào mục A, **không vá**.
3. Hỏng vì công cụ → phát biểu thành quy tắc chung về *công cụ vẽ cư xử thế
   nào*. Phát biểu không nổi thì đó là hard-code.
4. Bản vá phải chạy đúng trên **tập giữ kín** nữa, không chỉ trên case vừa sửa.
