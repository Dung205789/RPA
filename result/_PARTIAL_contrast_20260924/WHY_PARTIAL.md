# Lượt này DỞ DANG — không trích số chính thức, nhưng có thể tham khảo có điều kiện

**Ngày:** 2026-09-24. **Không xoá** — 22 case sạch là bằng chứng có giá trị cho
câu hỏi 24,6% vs 100%, dù chưa đủ điều kiện để công bố.

## Chuyện gì đã xảy ra

Lệnh đúng như `result/_INVALID_contrast_20260923/WHY_INVALID.md` mục "Việc
phải làm lại", chạy **một mình**, không tranh port với harness nào khác. Chạy
được 24/30 case rồi bị một tiến trình dọn dẹp hệ thống (bên ngoài Claude Code)
tự dừng vì máy báo cạn RAM. Nguyên nhân cạn RAM sau đó tìm ra: rò rỉ
`chromedriver.exe` mồ côi tích luỹ từ nhiều phiên làm việc trước, không liên
quan gì tới bản thân `app.diagrams.net` — xem `RPA_docs/ENVIRONMENT.md` mục
"chromedriver.exe mồ côi" và `RPA_docs/TRACE.md` 2026-09-24-3. Đã vá
`restart_browser()` để không tái diễn.

## Có gì dùng được

`env.json` đúng: cả bốn cờ `false`, `drawio_url: https://app.diagrams.net`.
22/23 case trong `summary.json` có số N3 sạch (case thứ 23, `medium_m07`, và
case thứ 24, `medium_m08`, chết ngay tại/gần thời điểm hệ thống cạn RAM — coi
hai case này là nhiễu môi trường, không phải tín hiệu về `app.diagrams.net`).

**Phát hiện đáng chú ý:** `drawio_build` mà site public trả về là **31.5.2**,
không phải bản 28.2.5 đã ghim cục bộ — chênh nhiều bản chính, đúng như lo ngại
gốc của việc ghim (`ENVIRONMENT.md`).

Trên 22 case sạch: `step_pass_rate_N3` **92,45%** (1060 bước), so với **99,69%**
của `g0_baseline` (bản ghim, toàn bộ 30 case). Không phải 24,6% (số DOM cũ)
cũng không phải 100% (oracle mxGraph mới trên bản ghim) — một điểm dữ liệu thứ
ba, thiên về giả thuyết "thước DOM cũ đo sai" hơn là "site public tệ đi rất
nhiều", nhưng **chưa đủ sạch để kết luận**: thiếu 8 case, 2 case cuối nhiễu bởi
sự cố RAM, và tính lặp lại chưa đo.

## Không được trích dẫn như số chính thức vì

* Không đủ 30/30 case.
* Hai case cuối cùng chạy trong điều kiện hệ thống đang suy giảm (chromedriver
  mồ côi tích luỹ dần trong chính lượt này trước khi được vá).
* Chưa đối chiếu bằng mắt case nào.

## Việc phải làm

Chạy lại từ đầu, ra một thư mục MỚI (không phải thư mục này), sau khi đã dọn
chromedriver mồ côi:

```bash
python -c "import sys; sys.path.insert(0,'RPA_drawio'); import rpa_env; print(rpa_env.kill_orphaned_chromedrivers())"

DRAWIO_URL=https://app.diagrams.net \
RPA_CLOSED_LOOP_MOVE=0 RPA_ANCHOR_INSERTS=0 RPA_CLOSED_LOOP_RESIZE=0 RPA_CLOSED_LOOP_LABEL=0 \
  RPA_drawio/venv_rpa/Scripts/python.exe run_drawio_v2.py --scenarios "RPA_Datasets_new30_v2/*.json" \
  --out result/g0_contrast_public --port 9222
```
