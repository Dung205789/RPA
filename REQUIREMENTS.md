# Yêu cầu công việc — hướng RPA (ghi lại nguyên văn, 2026-09-03)

File này tồn tại để không quên và để đối chiếu khi cần. Phần 1 là nguyên văn
yêu cầu của người giao việc; phần 2 là cách tôi (Claude) hiểu nó; phần 3 là
trạng thái thực tế đo được tại thời điểm nhận việc.

---

## 1. Nguyên văn yêu cầu

> đây là dự án SVG_agent của tôi, chủ đề là SVG automation testing using web agent,
> mục tiêu là test khả năng vẽ của các web canvas. Trong repo trên máy này có 2 phần
> đáng lưu ý. 1. Là src code SVG_agent , tiếp cận theo hướng web 2.Là src code
> documents, tiếp cận theo hướng robot ( RPA) của 1 tiền bối đi trước. Tôi được giao
> nhiệm vụ tạo 1 benchmark gồm các ảnh để cả 2 có thể sử dụng, đó chính là
> data/datasets ( dành cho drawio). Trước tiên, tôi được yêu cầu chạy thực nghiệm cho
> hướng RPA trước, trong folder documents đã có sẵn các src code và datasets của tiền
> bối rồi. Nhưng do bản code đã lâu chưa được cập nhật, nên khi tôi chạy thực nghiệm
> trên bản RPA_datasets nó cho ra kết quả rất tệ (kết quả trong documents/results ),
> ngoài ra tôi còn được yêu cầu áp dụng benchmark mới vào repo documents này. Ban đầu
> để test độ tương thích giữa benchmarks mới và repo cũ, tôi cho chạy thử 30 cases ,
> kết quả thu được rất tồi tệ ( documents/result ). Nói chung hiện tại tôi cần sửa
> code RPA để chạy thực nghiệm full datasets cũ được và 30 cases datasets, trước khi
> chạy toàn bộ 500 cases x 3 web cho repo này. Tập chung vào vẽ drawio trước. Như bạn
> có thể sử dụng VLM của chính bạn để thấy được kết quả tồi tệ đến thế nào. Bài RPA và
> SVG_Agent là 2 bài khác nhau, trước tiên tôi muốn tập chung vào bào RPA trước. Bởi
> vì code đã cũ + thêm khả năng handle còn kém ( toi đoán thế ) . Tôi cần bạn làm theo
> quy trình sau đây.
>
> 1. Chạy full datasets cũ với src code cũ
> 2. Chạy 30 cases datasets mới với src code cũ ( 10 cases mỗi level, chỉ drawio
>    trước ), phần này đang được chạy rồi.
> 3. Tiếp theo cần nâng cấp src code RPA để chạy đạt kết quả trên datasets cũ ( bởi vì
>    vốn nó được dùng để làm thế)
> 4. Thêm cơ chế chuyển từ ảnh ( datasets mới ) thành dạng text ( như trong
>    RPA_datasets) . Phải chuyển thật chuẩn, giống format , lấy RPA_datasets làm mẫu và
>    chuyển từ đó cho chuẩn ( dùng few_shots hoặc kỹ thuật nào đó thật tốt, code ra 1
>    phần riêng trong RPA_drawio luôn).
> 5. Về phần ảnh (datasets mới, đã có gold answer sẵn ) dùng nó để verify output. Còn
>    về phần text( RPA_Datasets không có gold ) , nên cần sử dụng các tool trên drawio
>    để tự vẽ hoặc có cơ chế đọc text ra được ảnh chuẩn qua LLM, để có gold answêr còn
>    so sánh.
> 6. Luật là không hard code, không fix cứng, không leakage, code core thì sửa phần cần
>    sửa để chạy được thôi, nếu cần chạy api LLM thì có sử dụng .env trong folder
>    SVG_agent
> 7. Ghi đoạn yêu cầu này của tôi ra đâu đấy cho đỡ quên, xem lại để đối chiếu khi cần.
> 8. Cần đọc datasets (cả cũ và mới ) và src code RPA để biết nhiệm vụ của mình
> 9. Tôi sẽ trao máy , giao toàn quyền cho bạn, phải làm cho xong.
>
> Trước tiên push code folder documentss lên đây để lưu phiên bản đã
> https://github.com/Dung205789/RPA.git.

---

## 2. Cách hiểu / phân rã công việc

| # | Việc | Ghi chú |
|---|------|---------|
| 0 | Push `documents/` lên `github.com/Dung205789/RPA` để lưu bản gốc | XONG — commit `dcc8d4e` |
| 1 | Chạy full 100 case drawio cũ bằng code cũ | XONG — `result/rpa_datasets_full` |
| 2 | Chạy 30 case benchmark mới (10 easy/10 medium/10 hard) bằng code cũ | XONG — `result/new30_run` |
| 3 | Nâng cấp RPA_drawio để **thật sự chạy đúng** trên bộ cũ | Đang làm |
| 4 | Module ảnh → mô tả text theo đúng format RPA_Datasets, đặt **trong RPA_drawio** | Few-shot / VLM, không dùng answer key |
| 5 | Chấm điểm: bộ mới có gold sẵn; bộ cũ phải tự dựng gold | |
| 6 | Sau khi bộ cũ + 30 case đạt, mới chạy 500 case × 3 web | drawio trước |

### Quyết định đã chốt (hỏi/đáp 2026-09-03)

| Câu hỏi | Trả lời |
|---------|---------|
| Thước đo output RPA | **Chấm bằng VLM nhìn ảnh.** Không dùng scorer XML của SVG_agent. |
| Chuẩn cho 100 case cũ | **Cả hai**: tỉ lệ step chạy đúng cho toàn bộ 100 case, + gold ở mức hình cho nhóm case có vẽ. |
| Provider LLM | **Gemini trước, hết quota sang OpenAI, Claude để cuối.** |
| Phạm vi trước mắt | **Toàn bộ 100 case drawio cũ + 30 case drawio mới.** Chưa chạy 500 case. |

### Luật bắt buộc (mục 6 của yêu cầu)
- Không hard-code, không fix cứng theo từng case.
- Không leakage: module ảnh→text **chỉ được đọc file PNG**, tuyệt đối không đọc
  `*.graph.json` (answer key) hay `*.xml` (source) của bộ benchmark.
- Sửa code core chỉ ở mức tối thiểu để chạy được.
- API LLM lấy khoá từ `D:\SVG_agent\.env`.

---

## 3. Trạng thái đo được lúc nhận việc (baseline)

`result/rpa_datasets_full` — 100 case cũ: 89 "ok" / 11 exception.
`result/new30_run` — 30 case mới: 23 "ok" / 7 chromedriver crash.

**"ok" ở đây KHÔNG có nghĩa là vẽ đúng.** Harness chỉ đánh dấu exception ở mức
scenario; `generator.py` nuốt lỗi từng step (vòng `while retry_attempt` chỉ log
rồi đi tiếp). Xem ảnh `after.png`:

- `rpa_datasets_full/scenario_050/after.png` — kịch bản 41 bước, đáng lẽ ra một
  flowchart 6 node; thực tế canvas gần như trống, chỉ còn 1 diamond "YES", 1 box
  "Take subway" và một "List" lạc chỗ.
- `new30_run/easy_e01_v1_s5b0l0/after.png` — đáng lẽ 5 hộp nối chuỗi; thực tế 2
  hộp, 1 hộp không có chữ.

Nguyên nhân đã nhìn thấy ngay (chưa xác minh hết):
1. Giao diện draw.io đang chạy **tiếng Việt** ("Tập tin/Chỉnh sửa/Xem"), trong khi
   kịch bản cũ tìm menu bằng chữ tiếng Anh ("Click on File", "Click on Extras").
2. Không có thước đo nào ở mức hình vẽ — chỉ có ảnh chụp màn hình, không xuất
   mxGraph XML nên không so được với gold.
3. `Move` = 15 lần Shift+Arrow, chưa từng được hiệu chỉnh ra pixel.
4. Bộ icon trong `RPA_Datasets/images/drawio` chỉ có ellipse/rectangle/diamond/
   parallelogram; benchmark mới còn hexagon/trapezoid/document/cylinder.
