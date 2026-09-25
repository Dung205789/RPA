# RPA_docs/ — sổ tay điều hành hướng RPA

Mười mục, mười vai trò khác nhau. Đọc theo thứ tự này khi mở phiên làm việc mới.

> Đặt tên `RPA_docs/` chứ không phải `docs/` là có chủ ý: kho cha `D:\SVG_agent`
> có `docs/` riêng của hướng web agent. Hai hướng không được lẫn vào nhau.

| File | Trả lời câu hỏi | Ai được sửa, khi nào |
|------|-----------------|----------------------|
| [`DIAGNOSIS.md`](DIAGNOSIS.md) | **Hỏng ở đâu, bằng chứng nào?** | Đóng băng. Chỉ thêm khi đo được một lỗi gốc mới, kèm số. Không sửa số cũ. |
| [`ORACLE.md`](ORACLE.md) | **"Thực thi đúng" nghĩa là gì, đo bằng gì?** | Gần như đóng băng. Hạ một ngưỡng nào ở đây là hạ chuẩn cả dự án — phải ghi lý do và cho người giao việc biết. |
| [`PLAN.md`](PLAN.md) | **Làm gì, theo thứ tự nào, xong là thế nào?** | Sửa khi một quyết định thiết kế đổi. Mọi thay đổi tiêu chí phải ghi lý do. |
| [`PROGRESS.md`](PROGRESS.md) | **Đang ở đâu, đã qua cổng nào?** | Cập nhật sau mỗi lần đo. Đây là file duy nhất thay đổi thường xuyên. |
| [`DECISIONS.md`](DECISIONS.md) | **Vì sao chọn thế, ai quyết, còn treo gì?** | Thêm mục khi có quyết định mới. Lật thì đánh dấu LẬT, **không xoá** mục cũ. |
| [`KNOWN_LIMITS.md`](KNOWN_LIMITS.md) | **Cái gì hỏng mà không được vá?** | Thêm khi xác minh được một case hỏng vì chính kịch bản. |
| [`LOCKS.md`](LOCKS.md) | **Năm file hợp đồng còn nguyên không?** | Cập nhật hash **trong cùng lần sửa** với file bị khoá. Bỏ bước này là khoá nói dối. |
| [`TRACE.md`](TRACE.md) | **Phiên trước dở ở đâu, đã thử gì?** | Append-only, mỗi lượt làm việc một mục đủ bảy ô. |
| [`ENVIRONMENT.md`](ENVIRONMENT.md) | **Chạy trên cái gì, ghim thế nào?** | Cập nhật khi môi trường đổi. |
| [`checks/`](checks/) | **Lệnh tái sinh cho từng con số.** | Thêm một script mỗi khi `DIAGNOSIS.md` hay `PROGRESS.md` trích một con số mới. |

Chỉ dẫn nạp tự động mỗi phiên nằm ở [`../CLAUDE.md`](../CLAUDE.md) — nó trỏ
ngược về đây. Số liệu chính thức vẫn nằm ở [`../RESULTS.md`](../RESULTS.md). Yêu cầu gốc của
người giao việc nằm ở [`../REQUIREMENTS.md`](../REQUIREMENTS.md). Hai file đó
không bị thay bởi thư mục này.

---

## Luật của tài liệu này

Thư mục `RPA_docs/` tồn tại để chống hai thứ: **lạc đề** và **tự huyễn hoặc**. Nên
bốn luật dưới đây quan trọng hơn nội dung của chính nó.

1. **Không qua cổng thì không được sang giai đoạn sau.** Mỗi giai đoạn trong
   `PLAN.md` có một *Cổng* — một danh sách điều kiện đo được. Chưa tick đủ thì
   việc của giai đoạn sau là vi phạm, kể cả khi nó trông hấp dẫn hơn.

2. **Không có số thì không có kết luận.** Một câu như "chắc là do X" không được
   ghi vào `DIAGNOSIS.md`. Phải có lệnh chạy ra số, và lệnh đó phải ghi kèm.

3. **Mỗi con số có đúng một lệnh tái sinh.** Nếu không tái sinh được thì không
   được trích dẫn — kể cả số do chính mình đo tuần trước.

4. **Sửa cơ chế, không sửa dữ liệu.** Mọi bản vá phải phát biểu được thành một
   quy tắc về *draw.io cư xử thế nào*. Nếu chỉ phát biểu được thành *case này
   trông thế nào* thì đó là hard-code, và bị cấm — xem `PLAN.md` §Bất biến.

5. **Đây là đề tài kiểm thử.** Nên thứ phải chứng minh là *công cụ phán định
   đúng hay sai*, không phải *bản vẽ trông đẹp*. Một bước báo `ok` trong khi
   ứng dụng làm sai là lỗi nặng nhất của dự án — nặng hơn một bước hỏng thật.
   Ngưỡng ở `ORACLE.md` §3.1: **báo đạt sai = 0**.

---

## Khi mở phiên mới, làm đúng ba việc này trước

```bash
sed -n '1,40p' RPA_docs/PROGRESS.md      # đang ở giai đoạn nào, cổng nào còn treo
sed -n '/^## Bất biến/,/^## /p' RPA_docs/PLAN.md   # đọc lại 10 luật cấm
sed -n '/^## 3. Chỉ số/,/^## 4/p' RPA_docs/ORACLE.md  # ngưỡng phải đạt
git -C . log --oneline -10           # phiên trước đã làm gì
```

Chỉ sau đó mới được đụng vào code.


---

## `checks/` — cái gì trả lời câu hỏi nào

Chạy hết phần ngoại tuyến bằng một lệnh:

```bash
python RPA_docs/checks/run_all_checks.py
```

| Script | Trả lời | Cần trình duyệt |
|---|---|---|
| `run_all_checks.py` | toàn bộ kiểm tra ngoại tuyến, một dòng một điều kiện cổng | không |
| `graph_score.py` | chấm một lượt chạy ở **mức hình**, tất định, đọc `model.xml` so với answer key | không |
| `mutations.py` | 9 ca đột biến của `ORACLE.md` §4 — **kiểm thử chính bộ chấm** | không |
| `baselines.py` | ba baseline tầm thường, sàn điểm của `ORACLE.md` §5 | không |
| `report.py` | in một lượt chạy đúng mẫu `ORACLE.md` §6 | không |
| `false_pass.py` | báo đạt sai của thước cũ; sinh mẫu rà tay cho thước mới | không |
| `stats.py` | khoảng tin cậy Wilson; cỡ mẫu cần để cận trên xuống dưới một ngưỡng | không |
| `test_no_leakage.py` | chốt chặn answer key, cả động lẫn tĩnh | không |
| `verify_splits.py` | `splits.json` tất định, tái sinh được, chia đều theo band | không |
| `no_case_hardcoding.py` | rà `PLAN.md` §Bất biến 2 bằng grep, in kết quả | không |
| `insert_drift.py` | điểm chèn trôi bao nhiêu trong một lượt chạy thật | không |
| `build_splits.py` | dựng lại `splits.json` | không |
| `move_accuracy.py`, `cells_of.py`, `judge_summary.py`, `corpus_stats.py` | các số của `DIAGNOSIS.md` §1–§7 | không |
| `oracle_independence.py` | ép executor nói dối, xem oracle có tin không | **có** |
| `probe_editor.py` | draw.io thật cư xử thế nào: điểm chèn, resize, nudge | **có** |
| `palette_check.py` | `palette_matcher` trên bảng shape của bản ghim | **có** |
| `resize_fidelity.py` | executor có đặt được hình đúng tỉ lệ khung không | **có** |
| `repeatability.py` | 20 case x 5 lần, ba ngưỡng của `ORACLE.md` §3.2 | **có** |

Bốn script cuối chiếm trình duyệt vài phút tới vài giờ. **Không chạy song song
với một lượt chạy chính thức** — `ORACLE.md` §3.2 nói rõ độ chập chờn do tranh
CPU là thứ phải đo, không phải thứ được phép gây thêm.
