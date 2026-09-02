# README

## Yêu cầu môi trường
- VSCode
- Python 3.x
- Google Chrome

---

## 1. Cài đặt dependencies

Chạy lệnh sau:

```bash
pip install selenium beautifulsoup4 chromedriver-autoinstaller webdriver-manager opencv-python numpy requests pytesseract Pillow sentence-transformers easyocr torch torchvision python-bidi pyyaml scikit-image google-generativeai
```

---

## 2. Mở Chrome với Remote Debugging

Chạy lệnh sau trong CMD:

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selenium\ChromeProfile"
```

---

## 3. Chạy project

```bash
python generator.py
```

(Có thể tham khảo thêm tại https://github.com/Ng-Vanh/rpa4web-be. Repository này có hướng dẫn chạy trong `README.md` với cách thiết lập tương tự dự án hiện tại; tuy nhiên, dự án hiện tại đã được hoàn thiện hơn.)