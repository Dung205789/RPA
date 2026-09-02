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

# Helper: log ra stderr
def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def download_image(url, local_path):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type:
                log(f"❌ Nội dung tải về từ {url} không phải ảnh: {content_type}")
                return None
            with open(local_path, 'wb') as f:
                f.write(response.content)
            if cv2.imread(local_path) is None:
                log(f"❌ Ảnh tải về từ {url} không hợp lệ")
                return None
            log(f"✅ Đã tải ảnh từ {url} về {local_path}")
            return local_path
        else:
            log(f"❌ Lỗi tải ảnh từ {url}: Status code {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Lỗi khi tải ảnh từ {url}: {e}")
        return None

def get_viewport_info(driver):
    """
    ✅ HÀM MỚI: Lấy thông tin viewport và device pixel ratio
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
        log(f"📐 Viewport info: {viewport_info}")
        return viewport_info
    except Exception as e:
        log(f"⚠️ Không lấy được viewport info: {e}")
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
    time.sleep(0.5)

def capture_full_page_with_metadata(driver, output_path):
    """
    ✅ HÀM MỚI: Chụp ảnh và lưu metadata về kích thước
    """
    try:
        # Lấy thông tin viewport
        viewport = get_viewport_info(driver)
        
        # Chụp ảnh full page bằng CDP
        screenshot = driver.execute_cdp_cmd("Page.captureScreenshot", {
            "format": "png",
            "captureBeyondViewport": True,
            "fromSurface": True
        })
        screenshot_data = base64.b64decode(screenshot['data'])
        
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
        
        log(f"✅ Đã chụp ảnh: {actual_width}x{actual_height}")
        log(f"   Viewport: {metadata['viewport_width']}x{metadata['viewport_height']}")
        log(f"   DPR: {metadata['device_pixel_ratio']}")
        
        return metadata
        
    except Exception as e:
        log(f"❌ Lỗi khi chụp ảnh: {e}")
        
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
            log(f"❌ Fallback cũng thất bại: {e2}")
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
                log(f"⚠️ Lỗi khi xóa {item_path}: {e}")
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        log(f"❌ Lỗi khi tạo thư mục {directory}: {e}")

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
        time.sleep(0.3)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_full_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)

        # ✅ SỬ DỤNG HÀM MỚI
        metadata = capture_full_page_with_metadata(driver, filepath)
        
        if metadata:
            return metadata
        else:
            return None

    except Exception as e:
        log(f"❌ Lỗi: {e}")
        return None
    finally:
        if own_driver:
            driver.quit()

def find_and_mark_element(full_screenshot_metadata, template_path, output_path="template/marked_hybrid.png", 
                          threshold=0.6):
    """
    Tìm và đánh dấu phần tử bằng template matching với tối ưu tốc độ.
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

    log("👉 Multi-scale Template Matching tối ưu...")
    log(f"   Screenshot: {img_rgb.shape[1]}x{img_rgb.shape[0]}")
    log(f"   Template: {template_orig.shape[1]}x{template_orig.shape[0]}")

    # Thu nhỏ ảnh chụp màn hình về kích thước tiêu chuẩn
    max_width = 1920  # Chiều rộng tối đa, có thể điều chỉnh
    scale_factor = min(1.0, max_width / img_rgb.shape[1])
    if scale_factor < 1.0:
        new_width = int(img_rgb.shape[1] * scale_factor)
        new_height = int(img_rgb.shape[0] * scale_factor)
        img_rgb = cv2.resize(img_rgb, (new_width, new_height))
        log(f"   📏 Đã thu nhỏ ảnh: {img_rgb.shape[1]}x{img_rgb.shape[0]}")
    
    # Tính phạm vi tỷ lệ dựa trên DPR
    dpr = screenshot_metadata.get('device_pixel_ratio', 1.0)
    scale_min = max(0.8 / dpr, 0.5)  # Thu hẹp phạm vi dựa trên DPR
    scale_max = min(1.2 * dpr, 1.5)
    num_scales = 10  # Giảm từ 20 xuống 10 bước
    scales = np.linspace(scale_min, scale_max, num_scales)
    log(f"   Scale range: {scale_min:.2f}-{scale_max:.2f}, steps={num_scales}")

    best_val, best_loc, best_scale, best_wh = -1, None, None, None

    for scale in scales:
        w = int(template_orig.shape[1] * scale)
        h = int(template_orig.shape[0] * scale)
        
        if w < 10 or h < 10 or w > img_rgb.shape[1] or h > img_rgb.shape[0]:
            continue

        template = cv2.resize(template_orig, (w, h))
        
        # Chỉ sử dụng TM_CCOEFF_NORMED
        try:
            res = cv2.matchTemplate(img_rgb, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            
            if max_val > best_val:
                best_val = max_val
                best_loc = max_loc
                best_scale = scale
                best_wh = (w, h)
        except Exception as e:
            log(f"⚠️ Lỗi khi khớp template tại scale {scale:.2f}: {e}")
            continue

    log(f"🔍 Best match: score={best_val:.3f}, scale={best_scale:.2f}, method=TM_CCOEFF_NORMED")

    if best_val >= threshold and best_loc is not None:
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
        cv2.imwrite(output_path, img_rgb)
        log(f"✅ Phương pháp Template Matching thành công!")
        return output_path, top_left, bottom_right, (center_x, center_y)

    log("❌ Phương pháp Template Matching thất bại, chuyển sang phương pháp 2: SIFT/ORB...")
    # Giữ nguyên phần fallback SIFT/ORB như mã gốc
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template_orig, cv2.COLOR_BGR2GRAY)

    try:
        detector = cv2.SIFT_create(nfeatures=5000)
        method = "SIFT"
    except Exception:
        detector = cv2.ORB_create(nfeatures=5000)
        method = "ORB"

    kp1, des1 = detector.detectAndCompute(template_gray, None)
    kp2, des2 = detector.detectAndCompute(img_gray, None)

    if des1 is None or des2 is None:
        log(f"❌ {method} không tìm thấy đặc trưng")
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
        log(f"❌ Lỗi khi matching: {e}")
        return None, None, None, None

    good_matches = []
    for match_pair in matches:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < 0.7 * n.distance:
                good_matches.append(m)

    log(f"Số match tốt ({method}): {len(good_matches)}")

    if len(good_matches) >= 8:  # Giữ nguyên min_matches=8 như mã gốc
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        if M is not None:
            h, w = template_gray.shape
            pts = np.float32([[0, 0], [0, h], [w, h], [w, 0]]).reshape(-1, 1, 2)
            dst = cv2.perspectiveTransform(pts, M)

            img_marked = cv2.polylines(img_rgb, [np.int32(dst)], True, (0, 255, 0), 3)
            x, y, w_box, h_box = cv2.boundingRect(np.int32(dst))
            center_x = x + w_box // 2
            center_y = y + h_box // 2
            cv2.circle(img_marked, (center_x, center_y), 5, (0, 0, 255), -1)
            cv2.imwrite(output_path, img_marked)

            top_left = (x, y)
            bottom_right = (x + w_box, y + h_box)

            log(f"✅ Phương pháp 2 ({method}) thành công")
            return output_path, top_left, bottom_right, (center_x, center_y)

    log(f"❌ Phương pháp 2 thất bại")
    return None, None, None, None

def find_most_specific_clickable_element(driver, x, y, search_radius=30, debug=True):
    """Tìm element clickable tại tọa độ x, y"""
    
    # ✅ THÊM: Highlight vị trí click để debug
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
                
                // Xóa marker cũ nếu có
                var old = document.getElementById('debug-click-marker');
                if (old) old.remove();
                
                document.body.appendChild(marker);
                
                // Tự động xóa sau 3 giây
                setTimeout(() => marker.remove(), 3000);
            """, x, y)
            log(f"🎯 DEBUG: Đã đánh dấu vị trí click tại ({x}, {y})")
            time.sleep(0.5)  # Cho người dùng thấy marker
        except Exception as e:
            log(f"⚠️ Không thể tạo debug marker: {e}")
    
    best_element = None
    best_tag = None
    best_specificity = -1

    for radius in range(0, search_radius + 1, 5):
        if best_element is not None:
            break
            
        if radius == 0:
            positions = [(x, y)]
            log(f"   🎯 Tìm tại tâm: ({x}, {y})")
        else:
            positions = [
                (x + radius, y), (x - radius, y),
                (x, y + radius), (x, y - radius),
                (x + radius, y + radius), (x - radius, y - radius),
                (x + radius, y - radius), (x - radius, y + radius)
            ]
            log(f"   🔍 Tìm với bán kính {radius}px...")
        
        for pos_x, pos_y in positions:
            try:
                element = driver.execute_script("""
                    return document.elementFromPoint(arguments[0], arguments[1]);
                """, pos_x, pos_y)

                if not element:
                    continue

                elements_to_check = []
                current = element

                while current and current.tag_name.lower() != 'html':
                    elements_to_check.append(current)
                    try:
                        current = current.find_element(By.XPATH, "./..")
                    except:
                        break

                for i, elem in enumerate(elements_to_check):
                    tag = elem.tag_name.lower()
                    specificity = 0

                    has_onclick = False
                    try:
                        onclick_attr = elem.get_attribute('onclick')
                        if onclick_attr:
                            has_onclick = True
                    except:
                        pass

                    has_listener = False
                    try:
                        cursor_style = elem.value_of_css_property('cursor')
                        if cursor_style == 'pointer':
                            has_listener = True
                    except:
                        pass

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
                        log(f"      ✓ Tìm thấy ứng viên: <{tag}> tại ({pos_x}, {pos_y}), score={specificity}")
                        
            except:
                continue
        
        if best_element:
            break

    if best_element:
        log(f"🎯 Tìm thấy: <{best_tag}> (độ ưu tiên: {best_specificity})")
        return best_element, best_tag

    log(f"❌ Không tìm thấy element tại ({x}, {y})")
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
        log(f"❌ Lỗi khi tạo XPath: {e}")
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
        log(f"❌ Lỗi khi phân tích: {e}")
        return None

def process_url_with_image(url, template_path, output_dir="template", driver=None):
    log("=== BẮT ĐẦU QUY TRÌNH TÌM PHẦN TỬ ===")
    log("✅ KHÔNG THAY ĐỔI KÍCH THƯỚC CỬA SỔ - Giữ nguyên như hiện tại")

    own_driver = False
    if driver is None:
        driver = setup_chrome_driver()
        own_driver = True

    # ✅ CHỤP ẢNH VỚI METADATA
    screenshot_metadata = take_full_page_screenshot(url, output_dir, driver=driver)
    if not screenshot_metadata:
        log("❌ Không thể chụp ảnh")
        if own_driver:
            driver.quit()
        return "//not-found"

    if template_path.startswith("http"):
        local_template_path = os.path.join(output_dir, "template_image.png")
        local_template_path = download_image(template_path, local_template_path)
        if not local_template_path:
            log("❌ Không thể tải ảnh template")
            if own_driver:
                driver.quit()
            return "//not-found"
    else:
        local_template_path = template_path

    # ✅ TÌM VÀ ĐÁNH DẤU VỚI METADATA
    marked_path, top_left, bottom_right, center = find_and_mark_element(
        screenshot_metadata, local_template_path,
        os.path.join(output_dir, "marked_element.png")
    )

    xpath = None

    if marked_path and center:
        log(f"✅ Tìm thấy tại: {center}")

        try:
            if own_driver:
                log(f"Mở lại trang: {url}")
                driver.get(url)
            
            wait_for_page_load(driver)

            target_x_abs = center[0]
            target_y_abs = center[1]
            viewport_height = driver.get_window_size()['height']
            scroll_y_position = max(0, target_y_abs - (viewport_height // 2))

            log(f"📜 Cuộn đến y={scroll_y_position}...")
            driver.execute_script(f"window.scrollTo(0, {scroll_y_position});")
            time.sleep(0.5)

            # Chụp viewport
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            viewport_screenshot_path = os.path.join(output_dir, f"screenshot_viewport_{timestamp}.png")
            
            viewport_metadata = capture_full_page_with_metadata(driver, viewport_screenshot_path)
            
            if viewport_metadata:
                # ✅ TÌM LẠI TRONG VIEWPORT VỚI METADATA
                new_marked_path, new_top_left, new_bottom_right, new_center = find_and_mark_element(
                    viewport_metadata, local_template_path,
                    os.path.join(output_dir, f"marked_viewport_{timestamp}.png")
                )

                if new_marked_path and new_center:
                    log(f"✅ Tìm lại thấy tại viewport: {new_center}")

                    # ✅ CHUYỂN ĐỔI TỌA ĐỘ: Screenshot space → Viewport space
                    dpr = viewport_metadata.get('device_pixel_ratio', 1.0)
                    screenshot_width = viewport_metadata.get('screenshot_width', 1)
                    viewport_width = viewport_metadata.get('viewport_width', 1)
                    
                    # Tính tỷ lệ scale giữa screenshot và viewport
                    scale_ratio = viewport_width / screenshot_width if screenshot_width > 0 else 1.0
                    
                    # Chuyển đổi tọa độ
                    viewport_x = int(new_center[0] * scale_ratio)
                    viewport_y = int(new_center[1] * scale_ratio)
                    
                    log(f"🔄 Chuyển đổi tọa độ:")
                    log(f"   Screenshot: {new_center[0]}x{new_center[1]} (DPR={dpr})")
                    log(f"   Scale ratio: {scale_ratio:.3f}")
                    log(f"   Viewport: {viewport_x}x{viewport_y}")

                    element, tag_name = find_most_specific_clickable_element(
                        driver, viewport_x, viewport_y
                    )

                    if element:
                        xpath = get_precise_xpath(driver, element)
                        log(f"✅ XPath: {xpath}")
                    else:
                        xpath = None
                else:
                    log("❌ Không tìm thấy trong viewport")
                    xpath = None

        except Exception as e:
            log(f"❌ Lỗi: {e}")
            xpath = None

    # Phương pháp 3: Fallback
    if not xpath:
        log("\n🔄 PHƯƠNG PHÁP 3: Cuộn trang tìm kiếm...")

        try:
            fallback_result = tim_phan_tu_fallback(driver, local_template_path, threshold=0.6)

            if fallback_result:
                xpath = fallback_result['xpath']
                log(f"✅ Phương pháp 3 thành công: {xpath}")
            else:
                xpath = "//not-found"

        except Exception as e:
            log(f"❌ Lỗi phương pháp 3: {e}")
            xpath = "//not-found"

    if not xpath:
        xpath = "//not-found"

    # Xử lý SVG
    elif isinstance(xpath, str) and "/svg" in xpath:
        import re
        new_xpath = re.sub(r"/svg(\[\d+\])?$", "", xpath)
        if new_xpath != xpath:
            log(f"🔧 Chuyển từ SVG sang parent: {new_xpath}")
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