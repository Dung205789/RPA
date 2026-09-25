# Lượt chạy này KHÔNG dùng được — đừng trích một con số nào từ đây

**Ngày:** 2026-09-23. **Không xoá** vì nó là bằng chứng của một lỗi quy trình.

## Chuyện gì đã xảy ra

**Hai** tiến trình `run_drawio_v2.py` cùng chạy, cùng ghi vào thư mục này, cùng
dùng cổng debug **9222**:

| PID | Khởi động | Nguồn |
|---|---|---|
| 23176 | 09:01:26 | `chain2.sh` — bản xếp hàng đang dùng |
| 8 | 09:02:16 | `chain_runs.sh` — bản xếp hàng **cũ**, quên chưa dừng |

Bản xếp hàng cũ vẫn đang đợi `result/g0_baseline/summary.json` đủ 30 case. Khi
baseline xong thì **cả hai** cùng khởi động lượt đối chứng.

## Hậu quả, đo được

1. **Trình duyệt bị tranh.** Mỗi harness gọi `kill_chrome_on_port(9222)` rồi mở
   Chrome mới, tức là mỗi bên liên tục giết Chrome của bên kia. Kết quả:
   `invalid session id` ngay từ bước 1 của case đầu, `N0 = 0/751`, và
   `no-verdict` gần như toàn bộ vì oracle không đọc nổi model.
2. **Cấu hình cờ lẫn lộn.** `env.json` ghi `closed_loop_label: True`, trong khi
   lượt này đáng lẽ phải **tắt cả bốn cờ** để so được với `g0_baseline`. Bản
   xếp hàng cũ được viết **trước** khi cờ `RPA_CLOSED_LOOP_LABEL` ra đời nên
   không đặt nó — và chính nó là bên ghi đè `env.json`.

Hai lỗi này cộng lại nghĩa là thư mục này không nói lên điều gì về
`app.diagrams.net`, cũng không nói lên điều gì về executor.

## Đúng ra phải làm gì

* Dừng bản xếp hàng cũ **trước** khi khởi động bản mới. Bản cũ là một tiến trình
  nền còn sống, không phải một file đã bị ghi đè.
* Trước mỗi lượt chạy chính thức, khẳng định **đúng một** tiến trình
  `run_drawio_v2.py` đang sống:

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*run_drawio_v2*' } |
  Select-Object ProcessId, CreationDate, CommandLine
```

* Và đây chính là cảnh báo `CLAUDE.md` đã ghi sẵn — *"một Chrome debug còn sót
  chạy song song sẽ tranh CPU và làm rớt phím Shift+Arrow"* — chỉ khác là lần
  này nguồn tranh chấp là **harness thứ hai**, không phải Chrome thừa.

## Việc phải làm lại

Chạy lại lượt đối chứng từ đầu, một tiến trình duy nhất:

```bash
DRAWIO_URL=https://app.diagrams.net \
RPA_CLOSED_LOOP_MOVE=0 RPA_ANCHOR_INSERTS=0 RPA_CLOSED_LOOP_RESIZE=0 RPA_CLOSED_LOOP_LABEL=0 \
  python run_drawio_v2.py --scenarios "RPA_Datasets_new30_v2/*.json" \
  --out result/g0_contrast_public --port 9222
```

Kiểm `env.json` phải có **cả bốn cờ `false`** trước khi tin bất kỳ số nào.
