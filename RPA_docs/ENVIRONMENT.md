# Môi trường chạy

Đề tài là kiểm thử, nên **môi trường phải cố định được**. Một con số đo hôm nay
mà ba tháng sau không dựng lại được thì không dùng cho bài báo.

---

## draw.io chạy trên bản nào — ĐÃ CHỐT: bản ghim 28.2.5

**Tình trạng đo được 2026-09-20:**

| | |
|---|---|
| `RPA_drawio/rpa_env.py:38` | `DRAWIO_URL = "https://app.diagrams.net/?lang=en&splash=0"` |
| `D:\SVG_agent\.env` | `DRAWIO_URL=http://localhost:8080` |
| Đường RPA thực tế dùng | **trang công cộng đang chạy trực tuyến** — biến trong `.env` bị bỏ qua |
| draw.io cục bộ trên máy | **không có**. Docker không chạy, `localhost:8080` không phản hồi |

Nghĩa là mọi lượt chạy cho tới giờ đều đo trên một ứng dụng **không ghim phiên
bản, tự cập nhật, không kiểm soát được**. Mỗi lần jgraph phát hành bản mới là
một lần đối tượng đo thay đổi dưới chân mình.

Đây là rủi ro với cả bốn thứ:

* **Tái lập** — chạy lại sau ba tháng ra số khác mà không biết vì sao.
* **Quy trách nhiệm** — điểm tụt là do bản vá của mình hay do draw.io đổi giao
  diện? Không tách được.
* **Khớp icon** — `palette_matcher` so ảnh với bảng shape thật. draw.io đổi icon
  một lần là hỏng, không báo trước.
* **Chạy lô dài** — 506 case là nhiều giờ, phụ thuộc mạng và giới hạn tốc độ của
  một dịch vụ công cộng.

### Hai lựa chọn

| | A — giữ `app.diagrams.net` | B — ghim `jgraph/drawio:28.2.5` cục bộ |
|---|---|---|
| Tái lập | ✗ đối tượng đo tự đổi | ✓ ghim phiên bản, chạy lại ra đúng số |
| So với `main.tex` | ✓ tiền bối cũng chạy trên trang công cộng | ~ khác môi trường, phải ghi chú |
| Tốc độ, ổn định | ✗ phụ thuộc mạng, có thể bị chặn tốc độ | ✓ cục bộ, nhanh hơn, chạy song song thoải mái |
| Công bỏ ra | 0 | dựng Docker + kiểm lại `palette_matcher` trên bảng shape của bản ghim |
| Rủi ro riêng | giao diện đổi giữa chừng lượt chạy | bản ghim có thể khác bản công cộng ở vài shape |

**Đã chốt: B**, kèm **một lượt đối chứng A vs B trên cùng 30 case** để đo chênh
lệch, rồi ghi con số đó vào `RESULTS.md` như một giới hạn đã biết. Như vậy vừa
tái lập được, vừa nói được nó lệch bao nhiêu so với môi trường của bài gốc.
Lý do đầy đủ ở `DECISIONS.md` D9.

**Ba việc phải làm ở G0.8:**

1. Khởi động Docker Desktop, rồi
   `docker run -d --name drawio-local -p 8080:8080 jgraph/drawio:28.2.5`
2. Cho `rpa_env.py` đọc `DRAWIO_URL` từ `.env` thay vì hard-code — sửa tối thiểu,
   thuộc ngoại lệ D6.
3. Kiểm lại `palette_matcher` trên bảng shape của bản ghim trước khi chạy lô dài.

Kho cha đã dùng đúng bản này: `docker run -d --name drawio-local -p 8080:8080
jgraph/drawio:28.2.5`.

> Cổng G0 có ba điều kiện cho việc này. Chưa dựng xong thì chưa sang G1 — mọi
> số của G1 sẽ không quy trách nhiệm được.

---

## Những thứ đã cố định

| Thành phần | Bản | Ghi chú |
|---|---|---|
| Python hệ thống | 3.12.4 | |
| venv dự án | `RPA_drawio/venv_rpa/` | đã có đủ gói, không cần cài lại |
| Chrome | 153.0.8010.47 | `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe` |
| Cổng debug | 9222 | đổi bằng `RPA_CHROME_DEBUG_PORT`; mỗi worker song song một cổng |
| Stanza + sentence-transformers | `RPA_drawio/src/main/resources/models/` | ~1GB, gitignore, tải lại bằng `download_model.py` |
| Khoá LLM | `D:\SVG_agent\.env` | Gemini → OpenAI → Anthropic (`DECISIONS.md` D2) |

**Chưa ghim:** phiên bản các gói Python trong `venv_rpa`. Trước khi chốt số
chính thức phải xuất `pip freeze` ra `RPA_docs/requirements.lock.txt`.

---

## Bẫy đã dính, đừng dính lại

1. **Chrome debug còn sót.** Một tiến trình Chrome debug từ lúc dò lỗi chạy
   song song sẽ tranh CPU và làm **rớt phím Shift+Arrow**. `RESULTS.md` §9:
   `scenario_050` ra 34/41, chạy lại độc lập thì đúng 41/41. Dọn sạch trước mỗi
   lượt chính thức.

2. **Cửa sổ bị che hoàn toàn.** Windows Chrome coi cửa sổ bị che như tab nền
   (`document.visibilityState === 'hidden'`); draw.io dựng bảng shape kiểu lazy
   nên **không bao giờ render** — `a.geItem` đứng ở 6 thay vì 45 sau 40 giây.
   Toàn bộ thực nghiệm baseline chạy trên một trang chưa render xong bảng shape.
   `rpa_env.py` đã xử lý; đừng vô hiệu hoá.

3. **Modal "Choose a draft to continue editing".** draw.io lưu nháp trong
   localStorage, nên từ lần chạy thứ hai trở đi luôn gặp. `rpa_env` dọn.

4. **Giao diện tiếng Việt.** Corpus gọi menu bằng tiếng Anh. `?lang=en` bắt buộc.

5. **Page View.** Canvas chia trang 850×1100; đẩy shape vượt lên đầu trang làm
   draw.io tái neo lưới và shape nhảy đúng một chiều cao trang. Đo được: cùng
   một shape đẩy lên 150px bốn lần ra 968, 818, 1768, 1618 khi **bật**, và
   1445, 1295, 1145, 995 khi **tắt**. Phải tắt.

6. **Đường dẫn model tính theo cwd.** Harness phải `os.chdir` vào `RPA_drawio/`
   trước khi import, nếu không stanza không tìm thấy model.

---

## Trước mỗi lượt chạy chính thức

```bash
# 1. không còn Chrome nào sót
tasklist | grep -i chrome        # phải trống, hoặc chỉ còn Chrome cá nhân của bạn

# 2. môi trường đích sống (nếu chọn phương án B)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080   # phải 200

# 3. ghi lại bản của môi trường vào thư mục kết quả
```

Mỗi thư mục kết quả phải có một `env.json` ghi: bản draw.io, bản Chrome, commit
của kho, ngày chạy, cổng, và nhà cung cấp LLM đã dùng. Không có file đó thì lượt
chạy không được coi là chính thức.

---

## Trạng thái 2026-09-22 — đã dựng xong

| | |
|---|---|
| Container | `drawio-local`, ảnh `jgraph/drawio:28.2.5`, cổng 8080 |
| `EditorUi.VERSION` đọc từ trang | `28.2.5` |
| `rpa_env.DRAWIO_URL` | `http://localhost:8080/?lang=en&splash=0` — đọc từ `D:\SVG_agent\.env` |
| Chrome | 153.0.8010.53 |
| Python | 3.12.4, venv `RPA_drawio/venv_rpa`, đóng băng ở `RPA_docs/requirements.lock.txt` |

`rpa_env._dotenv()` đọc `.env` bằng cách đi ngược lên cây thư mục từ chính file
`rpa_env.py`, nên không phụ thuộc cwd. Biến môi trường thắng file, để chạy một
lượt trỏ đi nơi khác mà không phải sửa gì — đó là cách lượt đối chứng
`app.diagrams.net` được chạy.

### `env.json` — ghi cho mọi lượt chạy

`run_drawio_v2.py::environment_record()` ghi `env.json` vào mỗi thư mục kết quả:
ngày, URL draw.io, bản draw.io đọc từ trang, bản Chrome và chromedriver, commit
kho và cây làm việc có bẩn không, ảnh Docker, cổng debug, nhà cung cấp LLM, và
**ba cờ của executor** (`closed_loop_move`, `anchor_inserts`,
`closed_loop_resize`) cùng ba hằng số hình học. Không có khối cờ đó thì một
thư mục kết quả không nói được nó do executor nào sinh ra, và cặp so sánh
trước/sau G1 mất nghĩa.

### Một lỗi môi trường đã sửa: `kill_chrome_on_port` không làm gì cả

`CLAUDE.md` cảnh báo Chrome debug còn sót tranh CPU làm rớt phím Shift+Arrow
(`RESULTS.md` §9, `scenario_050` ra 34/41). Hàm đáng lẽ chặn chuyện đó gọi
`wmic`, mà **Windows 11 đã bỏ `wmic`** (kiểm 2026-09-22 trên 10.0.26200), và lời
gọi nằm trong `except Exception` trần — hàm trả 0 và coi như dọn xong.

Đã thay bằng `Get-CimInstance Win32_Process` qua PowerShell, giữ `wmic` làm
đường lui. Vẫn lọc đúng token `--remote-debugging-port=<port>`, nên **không bao
giờ đụng Chrome của người dùng** — chỉ tiến trình do harness khởi động.

```bash
python -c "import sys; sys.path.insert(0,'RPA_drawio'); import rpa_env; print(rpa_env._chrome_pids_on_port(9222))"
```

### Một lỗi môi trường mới: `chromedriver.exe` mồ côi tích tụ qua mỗi lần restart

Phát hiện 2026-09-24. `restart_browser()` (`run_drawio_v2.py`) khi Chrome chết
giữa lượt chỉ gọi `kill_chrome_on_port` rồi mở Chrome mới — **không** đụng tới
tiến trình `chromedriver.exe` từng điều khiển phiên đã chết. Khác với
`driver.quit()` (tắt sạch, tự bảo chromedriver thoát), một Chrome chết đột ngột
(`invalid session id`) để lại chromedriver.exe sống mãi, không còn Chrome con
nào để điều khiển. Mỗi lần restart giữa lượt cộng thêm một tiến trình mồ côi.

Đo được: **34 tiến trình `chromedriver.exe` mồ côi** tích tụ qua nhiều phiên
làm việc trước đó. Đây nhiều khả năng là nguyên nhân thật của "chromedriver
could not start" (10 case `medium`, xem `TRACE.md` 2026-09-22) và của một lượt
chạy nền bị hệ thống tự dừng vì cạn RAM (2026-09-24) — cả hai từng bị quy cho
"máy cạn RAM ngẫu nhiên", nhưng rò rỉ có quy luật khớp hơn.

Đã sửa: `rpa_env.kill_orphaned_chromedrivers()` — chỉ giết `chromedriver.exe`
**không có Chrome con nào còn sống** (an toàn với nhiều worker chạy song song,
mỗi driver có Chrome con riêng thì không bị đụng), gọi trong `restart_browser()`
và trong khối `finally` cuối `main()`. Không giết theo tên tiến trình mù, luôn
kiểm `ParentProcessId` trước.

**Trước mỗi lượt chạy chính thức, kiểm luôn cả chromedriver mồ côi, không chỉ
Chrome debug:**

```powershell
(Get-CimInstance Win32_Process -Filter "Name='chromedriver.exe'").Count
```

Nếu > 0 mà không có `run_drawio_v2.py` nào đang sống, dọn bằng:

```bash
python -c "import sys; sys.path.insert(0,'RPA_drawio'); import rpa_env; print(rpa_env.kill_orphaned_chromedrivers())"
```

### Chạy song song

Vẫn **không** chạy song song cho số chính thức. Lý do ở `ORACLE.md` §3.2: độ
chập chờn do tranh CPU chính là thứ phải đo, không phải thứ được phép gây thêm.
Mỗi lượt chạy chính thức chiếm một mình máy; các lượt xếp hàng nối nhau.
