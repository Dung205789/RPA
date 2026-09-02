import os
import time
import base64
import cv2
import numpy as np
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import shutil
import requests
import sys
from by_image_helper import tim_phan_tu_fallback
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

# Helper: log ra stderr
def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def download_image(url, local_path):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type:
                log(f"Nội dung tải về từ {url} không phải ảnh: {content_type}")
                return None
            with open(local_path, 'wb') as f:
                f.write(response.content)
            if cv2.imread(local_path) is None:
                log(f"Ảnh tải về từ {url} không hợp lệ")
                return None
            log(f"Đã tải ảnh từ {url} về {local_path}")
            return local_path
        else:
            log(f"Lỗi tải ảnh từ {url}: Status code {response.status_code}")
            return None
    except Exception as e:
        log(f"Lỗi khi tải ảnh từ {url}: {e}")
        return None

def get_viewport_info(driver):
    """
    Lấy thông tin viewport và device pixel ratio
    """
    try:
        viewport_info = driver.execute_script("""
            return {
                width: window.innerWidth,
                height: window.innerHeight,
                devicePixelRatio: window.devicePixelRatio,
                outerWidth: window.outerWidth,
                outerHeight: window.outerHeight,
                screenWidth: window.screen.width,
                screenHeight: window.screen.height
            };
        """)
        log(f"Viewport info: {viewport_info}")
        return viewport_info
    except Exception as e:
        log(f"Không lấy được viewport info: {e}")
        return None

def setup_chrome_driver():
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

def wait_for_page_load(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def capture_full_page_with_metadata(driver, output_path):
    """
    Chụp ảnh và lưu metadata về kích thước
    """
    try:
        # CỐ ĐỊNH VỊ TRÍ CUỘN CỦA TẤT CẢ CÁC PHẦN TỬ
        driver.execute_script("""
            // Lưu vị trí cuộn hiện tại
            window._scrollPositions = [];
            
            // Lấy tất cả các phần tử có thể cuộn
            const scrollableElements = document.querySelectorAll('*');
            scrollableElements.forEach((el, index) => {
                const style = window.getComputedStyle(el);
                const hasScroll = (style.overflow === 'scroll' || 
                                 style.overflow === 'auto' || 
                                 style.overflowY === 'scroll' || 
                                 style.overflowY === 'auto' ||
                                 style.overflowX === 'scroll' || 
                                 style.overflowX === 'auto');
                
                if (hasScroll && (el.scrollTop > 0 || el.scrollLeft > 0)) {
                    window._scrollPositions.push({
                        element: el,
                        scrollTop: el.scrollTop,
                        scrollLeft: el.scrollLeft,
                        index: index
                    });
                    
                    // Cố định vị trí bằng cách thêm style
                    el.style.scrollBehavior = 'auto';
                }
            });
            
            console.log('Đã lưu ' + window._scrollPositions.length + ' vị trí cuộn');
        """)
        
        # Lấy thông tin viewport
        viewport = get_viewport_info(driver)
        
        # Chụp ảnh full page bằng CDP
        screenshot = driver.execute_cdp_cmd("Page.captureScreenshot", {
            "format": "png",
            "captureBeyondViewport": False,
            "fromSurface": True
        })
        screenshot_data = base64.b64decode(screenshot['data'])

        # KHÔI PHỤC LẠI VỊ TRÍ CUỘN (nếu cần)
        driver.execute_script("""
            if (window._scrollPositions) {
                window._scrollPositions.forEach(item => {
                    if (item.element) {
                        item.element.scrollTop = item.scrollTop;
                        item.element.scrollLeft = item.scrollLeft;
                    }
                });
                console.log('Đã khôi phục ' + window._scrollPositions.length + ' vị trí cuộn');
                delete window._scrollPositions;
            }
        """)
        
        # Lưu ảnh
        with open(output_path, 'wb') as f:
            f.write(screenshot_data)
        
        # Đọc ảnh để lấy kích thước thực tế
        img = cv2.imread(output_path)
        actual_height, actual_width = img.shape[:2]
        
        metadata = {
            'screenshot_path': output_path,
            'screenshot_width': actual_width,
            'screenshot_height': actual_height,
            'viewport_width': viewport['width'] if viewport else None,
            'viewport_height': viewport['height'] if viewport else None,
            'device_pixel_ratio': viewport['devicePixelRatio'] if viewport else 1.0
        }
        
        log(f"   Đã chụp ảnh: {actual_width}x{actual_height}")
        log(f"   Viewport: {metadata['viewport_width']}x{metadata['viewport_height']}")
        log(f"   DPR: {metadata['device_pixel_ratio']}")
        
        return metadata
        
    except Exception as e:
        log(f"Lỗi khi chụp ảnh: {e}")
        
        # Fallback sang save_screenshot
        try:
            driver.save_screenshot(output_path)
            img = cv2.imread(output_path)
            actual_height, actual_width = img.shape[:2]
            viewport = get_viewport_info(driver)
            
            return {
                'screenshot_path': output_path,
                'screenshot_width': actual_width,
                'screenshot_height': actual_height,
                'viewport_width': viewport['width'] if viewport else None,
                'viewport_height': viewport['height'] if viewport else None,
                'device_pixel_ratio': viewport['devicePixelRatio'] if viewport else 1.0
            }
        except Exception as e2:
            log(f"Fallback cũng thất bại: {e2}")
            return None

def clear_directory(directory):
    if os.path.exists(directory):
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
            except Exception as e:
                log(f"Lỗi khi xóa {item_path}: {e}")
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        log(f"Lỗi khi tạo thư mục {directory}: {e}")

def take_full_page_screenshot(url="https://bing.com/", output_dir="template", driver=None):
    if driver is None:
        clear_directory(output_dir)
    else:
        os.makedirs(output_dir, exist_ok=True)

    own_driver = False
    if driver is None:
        driver = setup_chrome_driver()
        own_driver = True

    try:
        if own_driver:
            log(f"Truy cập: {url}")
            driver.get(url)

        wait_for_page_load(driver, timeout=30)

        # Scroll về đầu trang
        driver.execute_script("window.scrollTo(0, 0);")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_full_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)

        # SỬ DỤNG HÀM MỚI
        metadata = capture_full_page_with_metadata(driver, filepath)
        
        if metadata:
            return metadata
        else:
            return None

    except Exception as e:
        log(f"Lỗi: {e}")
        return None
    finally:
        if own_driver:
            driver.quit()

def match_at_scale(args):
    """Hàm helper để chạy song song"""
    img_rgb, template_orig, scale, threshold = args
    
    w = int(template_orig.shape[1] * scale)
    h = int(template_orig.shape[0] * scale)
    
    if w < 10 or h < 10 or w > img_rgb.shape[1] or h > img_rgb.shape[0]:
        return None
        
    template = cv2.resize(template_orig, (w, h))
    
    try:
        res = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        
        if max_val >= threshold:
            scale_distance = abs(scale - 1.0)
            priority_score = (max_val * 0.7) + ((1.0 - scale_distance) * 0.3)
            
            return {
                'score': max_val,
                'scale': scale,
                'scale_distance': scale_distance,
                'priority_score': priority_score,
                'location': max_loc,
                'size': (w, h)
            }
    except Exception as e:
        log(f"Lỗi khi khớp template tại scale {scale:.2f}: {e}")
        
    return None

def find_and_mark_element(full_screenshot_metadata, template_path, output_path="template/marked_hybrid.png", 
                          threshold=0.8):
    """
    Tìm và đánh dấu phần tử bằng template matching.
    ƯU TIÊN: Chọn kết quả có scale gần 1.0 nhất
    """
    if isinstance(full_screenshot_metadata, str):
        # Backward compatibility
        screenshot_path = full_screenshot_metadata
        img = cv2.imread(screenshot_path)
        screenshot_metadata = {
            'screenshot_path': screenshot_path,
            'screenshot_width': img.shape[1],
            'screenshot_height': img.shape[0],
            'viewport_width': None,
            'viewport_height': None,
            'device_pixel_ratio': 1.0
        }
    else:
        screenshot_metadata = full_screenshot_metadata
        screenshot_path = screenshot_metadata['screenshot_path']
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Không tìm thấy tệp template: {template_path}")

    img_rgb = cv2.imread(screenshot_path)
    template_orig = cv2.imread(template_path)

    if img_rgb is None:
        raise FileNotFoundError(f"Không đọc được ảnh: {screenshot_path}")
    if template_orig is None:
        raise FileNotFoundError(f"Không đọc được template: {template_path}")

    log("Multi-scale Template Matching...")
    log(f"   Screenshot: {img_rgb.shape[1]}x{img_rgb.shape[0]}")
    log(f"   Template: {template_orig.shape[1]}x{template_orig.shape[0]}")

    # Thu nhỏ ảnh chụp màn hình về kích thước tiêu chuẩn
    max_width = 1920
    scale_factor = min(1.0, max_width / img_rgb.shape[1])
    if scale_factor < 1.0:
        new_width = int(img_rgb.shape[1] * scale_factor)
        new_height = int(img_rgb.shape[0] * scale_factor)
        img_rgb = cv2.resize(img_rgb, (new_width, new_height))
        log(f"   Đã thu nhỏ ảnh: {img_rgb.shape[1]}x{img_rgb.shape[0]}")

    # Tính phạm vi tỷ lệ dựa trên DPR
    dpr = screenshot_metadata.get('device_pixel_ratio', 1.0)
    scale_min = max(0.8 / dpr, 0.5)
    scale_max = min(1.2 * dpr, 1.5)

    # ĐẢM BẢO CÓ SCALE = 1.0 TRONG 5 BƯỚC
    if scale_min <= 1.0 <= scale_max:
        scales = sorted(set([
            scale_min,
            (scale_min + 1.0) / 2,
            1.0,
            (1.0 + scale_max) / 2,
            scale_max
        ]))
    else:
        scales = np.linspace(scale_min, scale_max, 5)

    log(f"   Scale range: {scale_min:.2f}-{scale_max:.2f}")
    log(f"   Scales to test: {[f'{s:.2f}' for s in scales]}")

    log("Smart Multi-scale Search với Early Stopping...")

    # Tạo 5 tỷ lệ thông minh dựa trên DPR
    dpr = screenshot_metadata.get('device_pixel_ratio', 1.0)
    smart_scales = [
        0.8 / dpr,
        0.9 / dpr, 
        1.0,
        1.1 * dpr,
        1.2 * dpr
    ]

    # Đảm bảo scales nằm trong phạm vi hợp lý
    smart_scales = [max(0.5, min(1.5, s)) for s in smart_scales]
    smart_scales = sorted(set(smart_scales))  # Loại trùng lặp

    log(f"   Testing scales: {[f'{s:.2f}' for s in smart_scales]}")

    # Chuẩn bị arguments
    args_list = [(img_rgb, template_orig, scale, threshold) for scale in smart_scales]

    # Chạy song song TẤT CẢ
    num_workers = min(len(smart_scales), multiprocessing.cpu_count())
    all_candidates = []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = executor.map(match_at_scale, args_list)
        
        for result in results:
            if result:
                all_candidates.append(result)
                
                # EARLY STOPPING: Dừng ngay khi tìm được kết quả gần hoàn hảo
                if result['score'] >= 0.85 and abs(result['scale'] - 1.0) < 0.1:
                    log(f"⚡ Early stop: Score {result['score']:.3f} @ scale {result['scale']:.2f}")
                    all_candidates = [result]  # Chỉ giữ kết quả này
                    break

    log(f"   Tìm được {len(all_candidates)} ứng viên")

    # CHỌN KẾT QUẢ TỐT NHẤT DỰA TRÊN PRIORITY SCORE
    if all_candidates:
        # Sắp xếp theo priority_score giảm dần
        all_candidates.sort(key=lambda x: x['priority_score'], reverse=True)
        
        best = all_candidates[0]
        best_val = best['score']
        best_scale = best['scale']
        best_loc = best['location']
        best_wh = best['size']
        
        log(f"\n Chọn kết quả tốt nhất:")
        log(f"   Score: {best_val:.3f}")
        log(f"   Scale: {best_scale:.2f} (distance from 1.0: {best['scale_distance']:.3f})")
        log(f"   Priority score: {best['priority_score']:.3f}")
        log(f"   Method: TM_CCOEFF_NORMED")
        
        # Hiển thị top 3 ứng viên để so sánh
        if len(all_candidates) > 1:
            log(f"\n Top {min(3, len(all_candidates))} ứng viên:")
            for i, candidate in enumerate(all_candidates[:3], 1):
                log(f"   {i}. Scale={candidate['scale']:.2f}, "
                    f"Score={candidate['score']:.3f}, "
                    f"Priority={candidate['priority_score']:.3f}")
        
        # Điều chỉnh tọa độ nếu ảnh đã được thu nhỏ
        top_left = (int(best_loc[0] / scale_factor), int(best_loc[1] / scale_factor))
        bottom_right = (int((best_loc[0] + best_wh[0]) / scale_factor), 
                       int((best_loc[1] + best_wh[1]) / scale_factor))
        
        # Đọc lại ảnh gốc để đánh dấu
        img_rgb = cv2.imread(screenshot_path)
        cv2.rectangle(img_rgb, top_left, bottom_right, (0, 0, 255), 3)
        center_x = top_left[0] + (bottom_right[0] - top_left[0]) // 2
        center_y = top_left[1] + (bottom_right[1] - top_left[1]) // 2
        cv2.circle(img_rgb, (center_x, center_y), 5, (0, 0, 255), -1)
        
        # GHI CHÚ SCALE LÊN ẢNH
        text = f"Scale: {best_scale:.2f}"
        cv2.putText(img_rgb, text, (top_left[0], top_left[1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imwrite(output_path, img_rgb)
        log(f"Phương pháp Template Matching thành công!")
        return output_path, top_left, bottom_right, (center_x, center_y)
    
    log("Không tìm thấy kết quả nào đạt threshold, chuyển sang phương pháp 2: SIFT/ORB...")
    
    # Giữ nguyên phần fallback SIFT/ORB
    img_gray = cv2.cvtColor(cv2.imread(screenshot_path), cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template_orig, cv2.COLOR_BGR2GRAY)

    try:
        detector = cv2.SIFT_create(nfeatures=0)
        method = "SIFT"
    except Exception:
        detector = cv2.ORB_create(nfeatures=0)
        method = "ORB"

    kp1, des1 = detector.detectAndCompute(template_gray, None)
    kp2, des2 = detector.detectAndCompute(img_gray, None)

    if des1 is None or des2 is None:
        log(f"{method} không tìm thấy đặc trưng")
        return None, None, None, None

    if method == "SIFT":
        index_params = dict(algorithm=1, trees=5)
        search_params = dict(checks=100)
        matcher = cv2.FlannBasedMatcher(index_params, search_params)
    else:
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    try:
        matches = matcher.knnMatch(des1, des2, k=2)
    except Exception as e:
        log(f"Lỗi khi matching: {e}")
        return None, None, None, None

    good_matches = []
    for match_pair in matches:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < 0.8 * n.distance:
                good_matches.append(m)

    log(f"Số match tốt ({method}): {len(good_matches)}")

    if len(good_matches) >= 8:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        if M is not None:
            h, w = template_gray.shape
            pts = np.float32([[0, 0], [0, h], [w, h], [w, 0]]).reshape(-1, 1, 2)
            dst = cv2.perspectiveTransform(pts, M)

            img_rgb = cv2.imread(screenshot_path)
            img_marked = cv2.polylines(img_rgb, [np.int32(dst)], True, (0, 255, 0), 3)
            x, y, w_box, h_box = cv2.boundingRect(np.int32(dst))
            center_x = x + w_box // 2
            center_y = y + h_box // 2
            cv2.circle(img_marked, (center_x, center_y), 5, (0, 0, 255), -1)
            cv2.imwrite(output_path, img_marked)

            top_left = (x, y)
            bottom_right = (x + w_box, y + h_box)

            log(f"Phương pháp 2 ({method}) thành công")
            return output_path, top_left, bottom_right, (center_x, center_y)

    log(f"Phương pháp 2 thất bại")
    return None, None, None, None

def find_most_specific_clickable_element(driver, x, y, debug=True):
    """Tìm element clickable tại tọa độ x, y"""
    
    # Highlight vị trí click để debug
    if debug:
        try:
            driver.execute_script("""
                var marker = document.createElement('div');
                marker.id = 'debug-click-marker';
                marker.style.cssText = `
                    position: fixed;
                    left: ${arguments[0]}px;
                    top: ${arguments[1]}px;
                    width: 10px;
                    height: 10px;
                    background: red;
                    border: 2px solid yellow;
                    border-radius: 50%;
                    z-index: 999999;
                    pointer-events: none;
                    transform: translate(-50%, -50%);
                `;
                
                var old = document.getElementById('debug-click-marker');
                if (old) old.remove();
                
                document.body.appendChild(marker);
                setTimeout(() => marker.remove(), 3000);
            """, x, y)
            log(f"DEBUG: Đánh dấu vị trí click tại ({x}, {y})")
        except Exception as e:
            log(f"Không thể tạo debug marker: {e}")
    
    # CHỈ TÌM TẠI TỌA ĐỘ CHÍNH XÁC
    log(f"   Tìm element tại tọa độ chính xác: ({x}, {y})")
    
    try:
        element = driver.execute_script("""
            return document.elementFromPoint(arguments[0], arguments[1]);
        """, x, y)

        if not element:
            log(f"Không tìm thấy element tại ({x}, {y})")
            return None, None

        # Duyệt lên các phần tử cha để tìm element clickable
        elements_to_check = []
        current = element

        while current and current.tag_name.lower() != 'html':
            elements_to_check.append(current)
            try:
                current = current.find_element(By.XPATH, "./..")
            except:
                break

        best_element = None
        best_tag = None
        best_specificity = -1

        for i, elem in enumerate(elements_to_check):
            tag = elem.tag_name.lower()
            specificity = 0

            # Kiểm tra onclick
            has_onclick = False
            try:
                onclick_attr = elem.get_attribute('onclick')
                if onclick_attr:
                    has_onclick = True
            except:
                pass

            # Kiểm tra cursor pointer
            has_listener = False
            try:
                cursor_style = elem.value_of_css_property('cursor')
                if cursor_style == 'pointer':
                    has_listener = True
            except:
                pass

            # Tính điểm ưu tiên
            interactive_tags = ['button', 'a', 'input', 'select', 'textarea', 'img']
            if tag in interactive_tags:
                specificity = 150 - i
            elif has_onclick or has_listener:
                specificity = 100 - i
            else:
                specificity = 10 - i

            if specificity > best_specificity:
                best_specificity = specificity
                best_element = elem
                best_tag = tag
                log(f"      ✓ Tìm thấy: <{tag}>, độ ưu tiên={specificity}")

        if best_element:
            log(f"Chọn element: <{best_tag}> (điểm: {best_specificity})")
            return best_element, best_tag
        else:
            log(f"Không tìm thấy element clickable tại ({x}, {y})")
            return None, None
            
    except Exception as e:
        log(f"Lỗi khi tìm element: {e}")
        return None, None

def get_precise_xpath(driver, element):
    try:
        element_id = element.get_attribute('id')
        if element_id:
            return f"//*[@id='{element_id}']"

        xpath = driver.execute_script("""
        function getOptimalXPath(element) {
            if (element.id !== '') {
                return "//*[@id='" + element.id + "']";
            }
            
            if (element === document.body) {
                return '/html/body';
            }
            
            var path = '';
            var current = element;
            
            while (current && current.nodeType === Node.ELEMENT_NODE) {
                var tagName = current.tagName.toLowerCase();
                
                if (current === document.documentElement) {
                    path = '/html' + path;
                    break;
                }
                
                var parent = current.parentNode;
                if (!parent || parent.nodeType !== Node.ELEMENT_NODE) {
                    path = '/' + tagName + path;
                    break;
                }
                
                var siblings = Array.from(parent.children).filter(child => 
                    child.tagName.toLowerCase() === tagName
                );
                
                if (siblings.length === 1) {
                    path = '/' + tagName + path;
                } else {
                    var index = siblings.indexOf(current) + 1;
                    path = '/' + tagName + '[' + index + ']' + path;
                }
                
                current = parent;
            }
            
            return path;
        }
        return getOptimalXPath(arguments[0]);
        """, element)

        return xpath

    except Exception as e:
        log(f"Lỗi khi tạo XPath: {e}")
        return None

def analyze_element_structure(driver, element, center_pos):
    try:
        info = {
            'tag_name': element.tag_name.lower(),
            'id': element.get_attribute('id') or '',
            'class': element.get_attribute('class') or '',
            'text': element.text[:50] + '...' if len(element.text) > 50 else element.text,
            'center_position': center_pos
        }
        return info
    except Exception as e:
        log(f"Lỗi khi phân tích: {e}")
        return None

def is_element_in_viewport(driver, element_y, element_height=50):
    """
    Kiểm tra xem phần tử có đang hiển thị trong viewport không
    
    Args:
        driver: WebDriver instance
        element_y: Tọa độ Y tuyệt đối của phần tử (trên toàn bộ trang)
        element_height: Chiều cao ước tính của phần tử
        
    Returns:
        dict: {
            'is_visible': bool,
            'scroll_y': int,  # Vị trí cuộn hiện tại
            'viewport_height': int,
            'element_viewport_y': int  # Tọa độ Y trong viewport nếu visible
        }
    """
    try:
        viewport_info = driver.execute_script("""
            return {
                scrollY: window.pageYOffset || document.documentElement.scrollTop,
                viewportHeight: window.innerHeight,
                viewportWidth: window.innerWidth
            };
        """)
        
        scroll_y = viewport_info['scrollY']
        viewport_height = viewport_info['viewportHeight']
        
        # Tính vị trí phần tử trong viewport
        element_viewport_y = element_y - scroll_y
        
        # Kiểm tra phần tử có trong viewport không (với buffer 10px)
        buffer = 10
        is_visible = (
            element_viewport_y >= -buffer and 
            element_viewport_y + element_height <= viewport_height + buffer
        )
        
        return {
            'is_visible': is_visible,
            'scroll_y': scroll_y,
            'viewport_height': viewport_height,
            'element_viewport_y': element_viewport_y if is_visible else None,
            'viewport_width': viewport_info['viewportWidth']
        }
        
    except Exception as e:
        log(f"Lỗi khi kiểm tra viewport: {e}")
        return {
            'is_visible': False,
            'scroll_y': 0,
            'viewport_height': 0,
            'element_viewport_y': None,
            'viewport_width': 0
        }

def process_url_with_image(url, template_path, output_dir="template", driver=None):
    log("=== BẮT ĐẦU QUY TRÌNH TÌM PHẦN TỬ ===")
    log("KHÔNG THAY ĐỔI KÍCH THƯỚC CỬA SỔ - Giữ nguyên như hiện tại")

    own_driver = False
    if driver is None:
        driver = setup_chrome_driver()
        own_driver = True

    # CHỤP ẢNH VỚI METADATA
    screenshot_metadata = take_full_page_screenshot(url, output_dir, driver=driver)
    if not screenshot_metadata:
        log("Không thể chụp ảnh")
        if own_driver:
            driver.quit()
        return "//not-found"

    if template_path.startswith("http"):
        local_template_path = os.path.join(output_dir, "template_image.png")
        local_template_path = download_image(template_path, local_template_path)
        if not local_template_path:
            log("Không thể tải ảnh template")
            if own_driver:
                driver.quit()
            return "//not-found"
    else:
        local_template_path = template_path

    # TÌM VÀ ĐÁNH DẤU VỚI METADATA
    marked_path, top_left, bottom_right, center = find_and_mark_element(
        screenshot_metadata, local_template_path,
        os.path.join(output_dir, "marked_element.png")
    )

    xpath = None

    if marked_path and center:
        log(f"Tìm thấy tại: {center}")

        try:
            if own_driver:
                log(f"Mở lại trang: {url}")
                driver.get(url)
            
            wait_for_page_load(driver)

            target_x_abs = center[0]
            target_y_abs = center[1]
            
            # KIỂM TRA PHẦN TỬ CÓ TRONG VIEWPORT KHÔNG
            viewport_check = is_element_in_viewport(driver, target_y_abs)

            if viewport_check['is_visible']:
                log(f"✓ Phần tử đang hiển thị trong viewport")
                log("→ Sử dụng luôn tọa độ từ ảnh chụp ban đầu")
                
                # CHUYỂN ĐỔI TỌA ĐỘ: Screenshot space → Viewport space
                # (Vì ảnh ban đầu đã chụp full page, cần chuyển sang tọa độ viewport)
                dpr = screenshot_metadata.get('device_pixel_ratio', 1.0)
                screenshot_width = screenshot_metadata.get('screenshot_width', 1)
                viewport_width = screenshot_metadata.get('viewport_width', 1)
                
                # Tính tỷ lệ scale
                scale_ratio = viewport_width / screenshot_width if screenshot_width > 0 else 1.0
                
                # Lấy vị trí Y trong viewport (trừ đi phần đã cuộn)
                current_scroll_y = viewport_check['scroll_y']
                viewport_x = int(target_x_abs * scale_ratio)
                viewport_y = int((target_y_abs - current_scroll_y) * scale_ratio)
                
                log(f"Chuyển đổi tọa độ:")
                log(f"   Full page: {target_x_abs}x{target_y_abs}")
                log(f"   Current scroll Y: {current_scroll_y}")
                log(f"   Scale ratio: {scale_ratio:.3f}")
                log(f"   Viewport: {viewport_x}x{viewport_y}")
                
                # TÌM ELEMENT TẠI TỌA ĐỘ VIEWPORT
                element, tag_name = find_most_specific_clickable_element(
                    driver, viewport_x, viewport_y
                )
                
                if element:
                    xpath = get_precise_xpath(driver, element)
                    log(f"✓ XPath: {xpath}")
                else:
                    log("✗ Không tìm thấy element, thử fallback...")
                    xpath = None

            else:
                log(f"✗ Phần tử KHÔNG hiển thị trong viewport")
                log("→ Cần cuộn đến vị trí phần tử và chụp lại")
                
                viewport_height = driver.get_window_size()['height']
                scroll_y_position = max(0, target_y_abs - (viewport_height // 2))
                
                log(f"Cuộn đến y={scroll_y_position}...")
                driver.execute_script(f"window.scrollTo(0, {scroll_y_position});")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                viewport_screenshot_path = os.path.join(output_dir, f"screenshot_viewport_{timestamp}.png")
                
                viewport_metadata = capture_full_page_with_metadata(driver, viewport_screenshot_path)
                
                if viewport_metadata:
                    new_marked_path, new_top_left, new_bottom_right, new_center = find_and_mark_element(
                        viewport_metadata, local_template_path,
                        os.path.join(output_dir, f"marked_viewport_{timestamp}.png"),
                        threshold=0.7  
                    )
                    
                    if new_marked_path and new_center:
                        log(f"✓ Tìm lại thấy tại viewport: {new_center}")
                        
                        dpr = viewport_metadata.get('device_pixel_ratio', 1.0)
                        screenshot_width = viewport_metadata.get('screenshot_width', 1)
                        viewport_width = viewport_metadata.get('viewport_width', 1)
                        
                        # Tính tỷ lệ scale giữa screenshot và viewport
                        scale_ratio = viewport_width / screenshot_width if screenshot_width > 0 else 1.0
                        
                        # Sau khi cuộn, phần tử đã ở vị trí mới trong ảnh
                        # Cần lấy vị trí cuộn hiện tại để tính đúng tọa độ viewport
                        current_scroll_info = driver.execute_script("""
                            return {
                                scrollY: window.pageYOffset || document.documentElement.scrollTop
                            };
                        """)
                        current_scroll_y = current_scroll_info['scrollY']
                        
                        # Chuyển đổi tọa độ: từ full-page screenshot sang viewport coordinates
                        # new_center là tọa độ trong ảnh full page (sau cuộn)
                        # Cần trừ đi phần đã cuộn để được tọa độ viewport
                        viewport_x = int(new_center[0] * scale_ratio)
                        viewport_y = int((new_center[1] - current_scroll_y) * scale_ratio)
                        
                        log(f"Chuyển đổi tọa độ:")
                        log(f"   Screenshot: {new_center[0]}x{new_center[1]}")
                        log(f"   Current scroll Y: {current_scroll_y}")
                        log(f"   Scale ratio: {scale_ratio:.3f}")
                        log(f"   Viewport: {viewport_x}x{viewport_y}")
                        
                        # TÌM ELEMENT TẠI TỌA ĐỘ VIEWPORT
                        element, tag_name = find_most_specific_clickable_element(
                            driver, viewport_x, viewport_y
                        )
                        
                        if element:
                            xpath = get_precise_xpath(driver, element)
                            log(f"✓ XPath: {xpath}")
                        else:
                            xpath = None
                    else:
                        log("✗ Không tìm thấy sau khi cuộn")
                        xpath = None
                else:
                    log("✗ Không thể chụp viewport")
                    xpath = None

        except Exception as e:
            log(f"Lỗi: {e}")
            import traceback
            log(traceback.format_exc())
            xpath = None


    # Phương pháp 3: Fallback
    if not xpath:
        log("\nPHƯƠNG PHÁP 3: Cuộn trang tìm kiếm...")

        try:
            fallback_result = tim_phan_tu_fallback(driver, local_template_path, threshold=0.6)

            if fallback_result:
                xpath = fallback_result['xpath']
                log(f"Phương pháp 3 thành công: {xpath}")
            else:
                xpath = "//not-found"

        except Exception as e:
            log(f"Lỗi phương pháp 3: {e}")
            xpath = "//not-found"

    if not xpath:
        xpath = "//not-found"

    # Xử lý SVG
    elif isinstance(xpath, str) and "/svg" in xpath:
        import re
        new_xpath = re.sub(r"/svg(\[\d+\])?$", "", xpath)
        if new_xpath != xpath:
            log(f"Chuyển từ SVG sang parent: {new_xpath}")
            xpath = new_xpath

    if own_driver:
        driver.quit()

    clear_directory(output_dir)

    return xpath

if __name__ == "__main__":
    template_path = r"http://localhost:8123/uploads/stepImg/stepImg__13__20250922.png"
    url = "https://app.diagrams.net/"

    result = process_url_with_image(url, template_path)

    log("\n" + "="*60)
    log(f"XPath: {result}")
    log("="*60)