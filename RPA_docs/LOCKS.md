# Khoá — hash của các file thiết kế đã đóng băng

Năm file dưới đây là **hợp đồng thiết kế**: ngưỡng, luật, chẩn đoán. Chúng
không đổi theo từng phiên làm việc như `PROGRESS.md`/`TRACE.md`. Sửa nội dung
của chúng bắt buộc phải đi qua quy trình ở cuối file này.

**Kiểm tra khoá còn nguyên không:**

```bash
cd documents
for f in DIAGNOSIS PLAN ORACLE KNOWN_LIMITS DECISIONS; do
  h=$(sha256sum "RPA_docs/$f.md" | awk '{print $1}')
  printf "%-18s %s\n" "$f.md" "$h"
done
```

So kết quả với bảng dưới. Khác thì có nghĩa là file đã bị sửa **mà không** cập
nhật khoá — dừng lại, đọc `TRACE.md` xem ai sửa, vì sao, có đúng quy trình
không.

---

## Bảng khoá hiện hành

| File | sha256 | Số dòng | Khoá lúc |
|---|---|---|---|
| `DIAGNOSIS.md` | `1652f834ce8232b493879c1667b44b909a659e9765a752f880024e81cf4f3303` | 485 | 2026-09-24 |
| `PLAN.md` | `786e7328494316309e58d8a6d31ae00d1776db55265379fa1560587d849af6f6` | 299 | 2026-09-20 |
| `ORACLE.md` | `d7fb303f7741b06e7d492eeb69fbb0d53d3760ccc63dd3c28cc4ae6f41a961dd` | 259 | 2026-09-22 |
| `KNOWN_LIMITS.md` | `32c94e0bd1f0c8769c4d3642eb4d4bea6bf09faaf62e9f023c52ae654f1e5063` | 66 | 2026-09-24 |
| `DECISIONS.md` | `713fe4c66445d0329c23c00564dea7b5fc5ae8135829398f0c336710ec8d8fb9` | 234 | 2026-09-24 |

Lần cập nhật 2026-09-24 đụng ba file: `DIAGNOSIS.md` (thêm §10, đọc
`Kết quả thực nghiệm.xlsx` — không sửa số cũ), `KNOWN_LIMITS.md` (làm rõ
B2, thêm B6–B8 và C5) và `DECISIONS.md` (thêm D14, cách dùng workbook mới).
Lý do đầy đủ ở `TRACE.md` mục 2026-09-24. `PLAN.md` và `ORACLE.md` không đổi
so với lần khoá trước.

`PROGRESS.md`, `TRACE.md`, `README.md`, `ENVIRONMENT.md` và `checks/` **không**
khoá — chúng thay đổi theo tiến độ, đó là việc của chúng.

---

## Quy trình sửa một file đã khoá

Chỉ được sửa khi có **bằng chứng mới** (đo được một lỗi gốc mới, một quyết định
bị lật có lý do) — không sửa vì "viết lại cho gọn hơn".

1. Sửa nội dung.
2. Ghi một mục vào `TRACE.md`: file nào, sửa gì, vì sao, bằng chứng nào.
3. Nếu đổi ngưỡng/luật (không phải chỉ thêm bằng chứng) → thêm mục LẬT vào
   `DECISIONS.md`, không xoá mục cũ.
4. Tính lại hash, cập nhật bảng ở trên **trong cùng một lần sửa**.

```bash
sha256sum RPA_docs/<file>.md | awk '{print $1}'
```

Bỏ qua bước 4 nghĩa là khoá nói dối — coi như chưa khoá.
