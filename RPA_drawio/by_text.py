import time
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import sys
import os
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Tắt TensorFlow warnings và logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Chỉ hiển thị ERROR
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Tắt oneDNN warnings
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Tắt thêm các warnings của TensorFlow
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

# Cache model toàn cục để tránh load lại nhiều lần
_cached_model = None
_model_loaded = False  # Flag để log chỉ 1 lần

# Helper: log ra stderr
def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def setup_chrome_driver(use_existing=False):
    """Thiết lập Chrome WebDriver với kích thước cố định"""
    if use_existing:
        # Kết nối vào Chrome đang chạy
        # Sửa 2026-09-02: cổng vốn hard-code "9222" -> đọc từ RPA_CHROME_DEBUG_PORT
        # (mặc định vẫn 9222) để 2 worker song song mỗi cái dùng 1 Chrome/cổng riêng,
        # không tranh nhau chung 1 tab. Theo yêu cầu, đây là ngoại lệ sửa duy nhất.
        chrome_options = Options()
        debug_port = os.environ.get("RPA_CHROME_DEBUG_PORT", "9222")
        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
        driver = webdriver.Chrome(options=chrome_options)
        return driver

    """Thiết lập Chrome WebDriver với kích thước cố định"""
    chromedriver_autoinstaller.install()
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1080,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--force-device-scale-factor=1")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1080, 1080)
    return driver

def get_sentence_model():
    """Load model một lần duy nhất và cache lại"""
    global _cached_model, _model_loaded

    if _cached_model is None:
        model_path = os.path.join("src", "main", "resources", "models",
                                  "sentence_transformers", "paraphrase-multilingual-MiniLM-L12-v2")

        if not os.path.exists(model_path):
            log(f"Lỗi: Mô hình SentenceTransformer không tồn tại tại {model_path}. "
                "Vui lòng chạy download_model.py để tải mô hình.")
            return None

        try:
            _cached_model = SentenceTransformer(model_path)
            if not _model_loaded:  # Chỉ log 1 lần duy nhất
                log("✅ Model AI đã được load vào cache (chỉ load 1 lần)")
                _model_loaded = True
        except Exception as e:
            log(f"Lỗi khi tải mô hình SentenceTransformer: {str(e)}")
            return None

    return _cached_model

def get_absolute_xpath(element):
    if not element or not hasattr(element, 'name'):
        return "/"

    path_components = []
    current = element

    while current and hasattr(current, 'name') and current.name:
        if current.name in ['[document]', 'document']:
            current = current.parent
            continue

        if current.parent:
            siblings = [sib for sib in current.parent.find_all(current.name, recursive=False)
                        if hasattr(sib, 'name') and sib.name and sib.name not in ['[document]', 'document']]

            if len(siblings) > 1:
                try:
                    index = siblings.index(current) + 1
                    path_components.insert(0, f"{current.name}[{index}]")
                except ValueError:
                    path_components.insert(0, current.name)
            else:
                path_components.insert(0, current.name)
        else:
            path_components.insert(0, current.name)

        current = current.parent

    xpath = "/" + "/".join(path_components) if path_components else "/"

    if not xpath.startswith("/html"):
        if xpath.startswith("/"):
            xpath = "/html" + xpath
        else:
            xpath = "/html/" + xpath

    return xpath

def get_xpath(el):
    """
    Trả về XPath dạng //*[@id='id'] nếu có ID, nếu không trả về absolute XPath.
    Cung cấp absolute XPath để so sánh nội bộ.
    """
    if not el or not getattr(el, "name", None):
        return "/", "/"  # Trả về tuple: (XPath để trả, XPath để so sánh)

    # Nếu có ID, trả về XPath dạng //*[@id='id']
    if el.has_attr("id") and el["id"].strip():
        return f"//*[@id='{el['id']}']", get_absolute_xpath(el)

    # Nếu không có ID, trả về absolute XPath cho cả hai
    abs_xpath = get_absolute_xpath(el)
    return abs_xpath, abs_xpath

def prioritize_interactive_elements(xpaths):
    """
    Ưu tiên các phần tử con tương tác được (button, input, a, select, textarea)
    và loại bỏ các phần tử cha nếu có con trong danh sách.
    xpaths: List các tuple (return_xpath, compare_xpath).
    """
    interactive_tags = ['button', 'input', 'a', 'img', 'label', 'div', 'span', 'select', 'textarea']
    non_interactive_parents = ['/html', '/html/body']

    # Loại bỏ các phần tử cha chung không tương tác
    prioritized = []
    for return_xpath, compare_xpath in xpaths:
        if compare_xpath in non_interactive_parents:
            continue
        # Ưu tiên các XPath thuộc thẻ tương tác
        if any(tag in compare_xpath.lower() for tag in interactive_tags):
            prioritized.append((return_xpath, compare_xpath))

    # Nếu không có phần tử tương tác, giữ danh sách đã lọc
    if not prioritized:
        prioritized = [(rx, cx) for rx, cx in xpaths if cx not in non_interactive_parents]

    # Sắp xếp theo độ dài compare_xpath (ưu tiên phần tử con nhỏ nhất)
    prioritized.sort(key=lambda x: len(x[1].split('/')), reverse=True)

    # Lọc để loại bỏ cha nếu có con và loại bỏ trùng lặp
    filtered = []
    seen_return_xpaths = set()  # Theo dõi return_xpath để tránh trùng
    for return_xpath, compare_xpath in prioritized:
        # Kiểm tra nếu compare_xpath là "cha" của bất kỳ compare_xpath nào đã thêm
        if any(f[1].startswith(compare_xpath + '/') for f in filtered):
            continue  # Bỏ qua vì đây là cha
        # Kiểm tra trùng lặp return_xpath
        if return_xpath in seen_return_xpaths:
            continue
        # Thêm vào filtered và seen
        filtered.append((return_xpath, compare_xpath))
        seen_return_xpaths.add(return_xpath)

    # Trả về danh sách chỉ chứa return_xpath
    return [rx for rx, _ in filtered] if filtered else [rx for rx, _ in xpaths]

def find_element_xpath(soup, search_text, similarity_threshold=0.0):
    search_text_lower = search_text.lower().strip()
    results = []

    tokens = search_text_lower.split()
    keyword = ""
    tag = None

    tag_map = {
        "button": "button, input, a",
        "input": "input",
        "textbox": "input",
        "text": "input",
        "password": "input",
        "checkbox": "input",
        "radio": "input",
        "link": "a",
        "a": "a",
        "image": "img",
        "img": "img",
        "label": "label",
        "div": "div",
        "span": "span",
        "dropdown": "select",
        "select": "select",
        "textarea": "textarea",
        "submit": "input"
    }

    if len(tokens) > 1 and tokens[-1] in tag_map:
        keyword = " ".join(tokens[:-1]).strip()
        tag = tokens[-1]
    elif len(tokens) == 1 and tokens[0] in tag_map:
        keyword = ""
        tag = tokens[0]
    else:
        keyword = search_text_lower
        tag = None

    def get_all_text_from_element(el):
        """Lấy tất cả text liên quan đến element từ nhiều nguồn"""
        texts = []

        text_content = el.get_text(strip=True).lower()
        if text_content:
            texts.append(text_content)

        important_attrs = ['value', 'placeholder', 'title', 'aria-label', 'alt', 'name', 'class']
        for attr in important_attrs:
            if el.has_attr(attr) and el[attr]:
                texts.append(str(el[attr]).lower().strip())

        if el.has_attr('id') and el['id']:
            label = soup.find('label', {'for': el['id']})
            if label:
                label_text = label.get_text(strip=True).lower()
                if label_text:
                    texts.append(label_text)

        if el.name == 'input' and el.get('type') in ['checkbox', 'radio']:
            parent = el.find_parent()
            if parent:
                parent_text = parent.get_text(strip=True).lower()
                if parent_text:
                    texts.append(parent_text)

            sibling_texts = " ".join([sib.get_text(strip=True).lower()
                                      for sib in el.find_next_siblings() if sib.get_text(strip=True)])
            if sibling_texts:
                texts.append(sibling_texts)

        return " ".join(texts)

    # Tìm kiếm thông thường
    if tag in tag_map:
        html_tags = tag_map[tag].split(", ")

        if tag in ["checkbox", "radio"]:
            for el in soup.find_all("input", {"type": tag}):
                combined_text = get_all_text_from_element(el)
                if keyword and keyword in combined_text:
                    return_xpath, compare_xpath = get_xpath(el)
                    results.append((return_xpath, compare_xpath))
                elif not keyword:
                    return_xpath, compare_xpath = get_xpath(el)
                    results.append((return_xpath, compare_xpath))
        else:
            for html_tag in html_tags:
                html_tag = html_tag.strip()
                for el in soup.find_all(html_tag):
                    combined_text = get_all_text_from_element(el)
                    if keyword:
                        if keyword in combined_text:
                            return_xpath, compare_xpath = get_xpath(el)
                            results.append((return_xpath, compare_xpath))
                    else:
                        return_xpath, compare_xpath = get_xpath(el)
                        results.append((return_xpath, compare_xpath))
    else:
        elements = soup.find_all(string=True)
        for element in elements:
            if element.strip().lower() == search_text_lower:
                parent = element.find_parent()
                return_xpath, compare_xpath = get_xpath(parent)
                results.append((return_xpath, compare_xpath))

        all_elements = soup.find_all(True)
        for el in all_elements:
            combined_text = get_all_text_from_element(el)
            if search_text_lower in combined_text:
                return_xpath, compare_xpath = get_xpath(el)
                if (return_xpath, compare_xpath) not in results:
                    results.append((return_xpath, compare_xpath))

    # Nếu không tìm thấy kết quả, chuyển sang so sánh bằng SentenceTransformer
    if not results:
        log("Không tìm thấy phần tử bằng tìm kiếm thông thường. Chuyển sang so sánh cosine similarity...")

        # Lấy model từ cache
        model = get_sentence_model()

        if model is None:
            return ["//not-found"]

        try:
            search_embedding = model.encode(search_text_lower, convert_to_tensor=True)
        except Exception as e:
            log(f"Lỗi khi mã hóa search_text: {str(e)}")
            return ["//not-found"]

        all_elements = soup.find_all(True)
        element_texts = []
        element_xpaths = []

        for el in all_elements:
            combined_text = get_all_text_from_element(el)
            if combined_text:
                return_xpath, compare_xpath = get_xpath(el)
                element_texts.append(combined_text)
                element_xpaths.append((return_xpath, compare_xpath))

        if not element_texts:
            log("Không có văn bản nào để so sánh trong DOM.")
            return ["//not-found"]

        try:
            element_embeddings = model.encode(element_texts, convert_to_tensor=True)
        except Exception as e:
            log(f"Lỗi khi mã hóa văn bản DOM: {str(e)}")
            return ["//not-found"]

        try:
            similarities = util.cos_sim(search_embedding, element_embeddings)[0]
        except Exception as e:
            log(f"Lỗi khi tính cosine similarity: {str(e)}")
            return ["//not-found"]

        # Lấy top 5 phần tử có độ tương đồng cao nhất
        top_k = 5
        top_indices = np.argsort(similarities.numpy())[-top_k:][::-1]
        for idx in top_indices:
            score = similarities[idx]
            if score > similarity_threshold:
                return_xpath, compare_xpath = element_xpaths[idx]
                results.append((return_xpath, compare_xpath))
                log(f"Phần tử khớp với score {score:.4f}: {return_xpath} (Text: {element_texts[idx]})")

        if not results:
            log(f"Không tìm thấy phần tử nào có độ tương đồng trên {similarity_threshold}")
            return ["//not-found"]

    # Ưu tiên các phần tử tương tác được
    results = prioritize_interactive_elements(results)

    return results

def process_url_with_text(url: str, search_text: str, driver=None, return_all=False):
    """
    Xử lý URL và text, trả về danh sách XPath - CẬP NHẬT DOM MỚI

    Args:
        url: URL của trang web
        search_text: Text để tìm kiếm
        driver: Selenium WebDriver instance (optional)
        return_all: Nếu True, trả về list tất cả XPaths; False trả về XPath đầu tiên

    Returns:
        - Nếu return_all=True: List các XPaths
        - Nếu return_all=False: XPath đầu tiên (hoặc "//not-found")
    """
    own_driver = False
    if driver is None:
        driver = setup_chrome_driver()
        own_driver = True
        log("Đang mở trang web...")
        driver.get(url)
        time.sleep(10)
    else:
        log("Đợi DOM cập nhật sau action trước đó...")
        time.sleep(1)

    log("Lấy DOM hiện tại để phân tích...")
    page_source = driver.page_source

    if own_driver:
        driver.quit()

    log("Bắt đầu phân tích với BeautifulSoup...")
    soup = BeautifulSoup(page_source, "html.parser")

    xpaths = find_element_xpath(soup, search_text)

    if not xpaths:
        log(f"❌ Không tìm thấy phần tử nào với '{search_text}'")
        return ["//not-found"] if return_all else "//not-found"
    else:
        log(f"✅ Tìm thấy {len(xpaths)} phần tử khớp '{search_text}':")
        for i, xp in enumerate(xpaths):
            log(f"   [{i}] {xp}")

    if return_all:
        return xpaths
    else:
        return xpaths[0]

if __name__ == "__main__":
    url = input("Nhập URL: ").strip()
    search_text = input("Nhập phần tử cần tìm: ").strip()
    log(process_url_with_text(url, search_text))