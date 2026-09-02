"""
by_image_helper.py
Phương pháp tìm kiếm dự phòng: Cuộn trang và tìm kiếm trong các vùng scrollable
Được gọi khi Multi-scale Template Matching và SIFT/ORB đều thất bại
"""

import cv2
import numpy as np
import time
from selenium.webdriver.common.by import By
from PIL import Image
import io
import sys


def log(*args, **kwargs):
    """Log ra stderr"""
    print(*args, file=sys.stderr, **kwargs)


def chup_man_hinh(driver):
    """Chụp màn hình và chuyển sang OpenCV format"""
    try:
        screenshot = driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(screenshot))
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    except Exception as e:
        log(f"❌ Lỗi chụp màn hình: {e}")
        return None


def so_khop_anh(screenshot, template, scales=None, threshold=0.7):
    """
    So khớp template với nhiều tỷ lệ

    Args:
        screenshot: Ảnh màn hình (OpenCV format)
        template: Ảnh template (đường dẫn hoặc OpenCV format)
        scales: Danh sách tỷ lệ zoom
        threshold: Ngưỡng confidence tối thiểu

    Returns:
        dict với thông tin vị trí và độ chính xác
    """
    if isinstance(template, str):
        template = cv2.imread(template)

    if template is None:
        log("❌ Không thể đọc template")
        return {'found': False, 'confidence': 0}

    if scales is None:
        scales = np.linspace(0.8, 1.2, 5)

    best = {'found': False, 'confidence': 0, 'x': 0, 'y': 0, 'w': 0, 'h': 0}

    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    th, tw = template_gray.shape

    for scale in scales:
        sw, sh = int(tw * scale), int(th * scale)
        if sw > screenshot_gray.shape[1] or sh > screenshot_gray.shape[0] or sw < 10 or sh < 10:
            continue

        resized = cv2.resize(template_gray, (sw, sh))
        result = cv2.matchTemplate(screenshot_gray, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best['confidence']:
            best = {
                'found': max_val >= threshold,
                'confidence': max_val,
                'x': max_loc[0],
                'y': max_loc[1],
                'w': sw,
                'h': sh
            }

    return best


def tim_vung_cuon(driver):
    """
    Tìm tất cả các vùng có thể cuộn trên trang

    Returns:
        list: Danh sách các vùng có thể cuộn với XPath và thông tin
    """
    try:
        data = driver.execute_script("""
            function getXPath(el) {
                if (el.id) return '//*[@id="' + el.id + '"]';
                if (el === document.body) return '//body';
                let ix = 0;
                const siblings = el.parentNode.childNodes;
                for (let i = 0; i < siblings.length; i++) {
                    const sib = siblings[i];
                    if (sib === el) {
                        return getXPath(el.parentNode) + '/' + el.tagName.toLowerCase() + '[' + (ix+1) + ']';
                    }
                    if (sib.nodeType === 1 && sib.tagName === el.tagName) ix++;
                }
            }
            
            const result = [];
            const html = document.documentElement;
            
            // Kiểm tra toàn trang
            if (html.scrollHeight > html.clientHeight) {
                result.push({
                    xpath: '//html',
                    scrollHeight: html.scrollHeight,
                    clientHeight: html.clientHeight
                });
            }
            
            // Tìm các element con có thể cuộn
            document.querySelectorAll('*').forEach(el => {
                try {
                    const style = window.getComputedStyle(el);
                    const hasScroll = el.scrollHeight > el.clientHeight;
                    const canScroll = ['auto', 'scroll'].includes(style.overflowY) || 
                                    ['auto', 'scroll'].includes(style.overflow);
                    if (hasScroll && canScroll && el !== html && el !== document.body) {
                        result.push({
                            xpath: getXPath(el),
                            scrollHeight: el.scrollHeight,
                            clientHeight: el.clientHeight
                        });
                    }
                } catch(e) {}
            });
            
            return result;
        """)

        # Lấy element từ XPath
        result = []
        for d in data:
            try:
                el = driver.find_element(By.XPATH, d['xpath'])
                d['element'] = el
                result.append(d)
            except:
                pass

        return result

    except Exception as e:
        log(f"❌ Lỗi khi tìm vùng cuộn: {e}")
        return []


def lay_xpath_tu_toa_do(driver, x, y):
    """
    Lấy XPath của element tại tọa độ x, y

    Args:
        driver: Selenium WebDriver
        x, y: Tọa độ pixel

    Returns:
        str: XPath hoặc None
    """
    try:
        return driver.execute_script("""
            function getXPath(el) {
                if (el.id) return '//*[@id="' + el.id + '"]';
                if (el === document.body) return '//body';
                let ix = 0;
                const siblings = el.parentNode.childNodes;
                for (let i = 0; i < siblings.length; i++) {
                    const sib = siblings[i];
                    if (sib === el) {
                        return getXPath(el.parentNode) + '/' + el.tagName.toLowerCase() + '[' + (ix+1) + ']';
                    }
                    if (sib.nodeType === 1 && sib.tagName === el.tagName) ix++;
                }
            }
            
            const el = document.elementFromPoint(arguments[0], arguments[1]);
            return el ? getXPath(el) : null;
        """, x, y)
    except Exception as e:
        log(f"❌ Lỗi lấy XPath từ tọa độ: {e}")
        return None


def kiem_tra_trong_container(driver, element_xpath, container_xpath):
    """
    Kiểm tra element có nằm trong container không

    Args:
        driver: Selenium WebDriver
        element_xpath: XPath của element cần kiểm tra
        container_xpath: XPath của container

    Returns:
        bool: True nếu element nằm trong container
    """
    if not element_xpath or not container_xpath:
        return False

    try:
        return driver.execute_script("""
            const child = document.evaluate(arguments[0], document, null, 
                XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            const parent = document.evaluate(arguments[1], document, null, 
                XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            
            if (!child || !parent) return false;
            
            let node = child;
            while (node) {
                if (node === parent) return true;
                node = node.parentNode;
            }
            return false;
        """, element_xpath, container_xpath)
    except:
        return False


def tim_kiem_trong_vung(driver, container, template, threshold=0.7, max_cuon=20):
    """
    Tìm kiếm template trong một vùng có thể cuộn

    Args:
        driver: Selenium WebDriver
        container: Dict chứa thông tin vùng cuộn
        template: Ảnh template (đường dẫn hoặc OpenCV format)
        threshold: Ngưỡng confidence
        max_cuon: Số bước cuộn tối đa

    Returns:
        dict hoặc None: Thông tin element tìm thấy
    """
    element = container['element']
    max_scroll = container['scrollHeight'] - container['clientHeight']

    if max_scroll <= 0:
        return None

    best_result = None
    best_confidence = 0

    # Chia thành các bước cuộn
    buoc_cuon = max(50, max_scroll // max_cuon)

    for pos in range(0, max_scroll + buoc_cuon, buoc_cuon):
        pos = min(pos, max_scroll)

        # Cuộn đến vị trí
        if container['xpath'] == '//html':
            driver.execute_script(f"window.scrollTo(0, {pos});")
        else:
            driver.execute_script(f"arguments[0].scrollTop = {pos};", element)

        time.sleep(0.3)

        # Chụp màn hình và so khớp
        screenshot = chup_man_hinh(driver)
        if screenshot is None:
            continue

        result = so_khop_anh(screenshot, template, threshold=threshold)

        log(f"  📍 Vị trí {pos}/{max_scroll}px - Confidence: {result['confidence']:.3f}")

        if result['confidence'] > best_confidence:
            # Lấy vị trí cuộn hiện tại
            if container['xpath'] == '//html':
                scroll_pos = driver.execute_script("return window.pageYOffset;")
            else:
                scroll_pos = driver.execute_script("return arguments[0].scrollTop;", element)

            # Lấy XPath từ tọa độ trung tâm
            center_x = result['x'] + result['w'] // 2
            center_y = result['y'] + result['h'] // 2
            xpath = lay_xpath_tu_toa_do(driver, center_x, center_y)

            # Kiểm tra element có trong container không
            trong_container = kiem_tra_trong_container(driver, xpath, container['xpath'])

            # Chỉ cập nhật nếu element nằm trong container
            if trong_container:
                best_confidence = result['confidence']
                best_result = {
                    'xpath': xpath,
                    'confidence': result['confidence'],
                    'toa_do': {
                        'x': result['x'],
                        'y': result['y'] + scroll_pos,
                        'width': result['w'],
                        'height': result['h']
                    },
                    'scroll_position': scroll_pos,
                    'container_xpath': container['xpath']
                }

    return best_result


def tim_phan_tu_fallback(driver, template_path, threshold=0.7):
    """
    HÀM CHÍNH: Tìm phần tử bằng cách cuộn trang (phương pháp dự phòng)

    Args:
        driver: Selenium WebDriver
        template_path: Đường dẫn ảnh template
        threshold: Ngưỡng confidence tối thiểu (mặc định 0.7)

    Returns:
        dict hoặc None: Thông tin element tìm thấy
    """
    log("\n" + "="*60)
    log("🔄 PHƯƠNG PHÁP DỰ PHÒNG: Cuộn trang + Tìm kiếm")
    log("="*60)

    # Tìm các vùng có thể cuộn
    log("\n🔍 Bước 1: Tìm các vùng có thể cuộn...")
    vung_cuon = tim_vung_cuon(driver)

    if not vung_cuon:
        log("❌ Không tìm thấy vùng nào có thể cuộn!")
        return None

    log(f"✅ Tìm thấy {len(vung_cuon)} vùng có thể cuộn:")
    for i, v in enumerate(vung_cuon, 1):
        log(f"  {i}. {v['xpath']} ({v['scrollHeight']}px)")

    # Tìm kiếm trong từng vùng
    best_overall = None
    best_confidence = 0

    for i, vung in enumerate(vung_cuon, 1):
        log(f"\n🔍 Bước {i+1}: Tìm kiếm trong vùng {i}/{len(vung_cuon)}")
        log(f"  📂 XPath: {vung['xpath']}")

        result = tim_kiem_trong_vung(driver, vung, template_path, threshold)

        if result and result['confidence'] > best_confidence:
            best_confidence = result['confidence']
            best_overall = result
            log(f"  ✅ Tìm thấy! Confidence: {result['confidence']:.3f}")
        else:
            log(f"  ❌ Không tìm thấy trong vùng này")

    if best_overall:
        log(f"\n✅ Kết quả tốt nhất: Confidence {best_overall['confidence']:.3f}")
        log(f"   XPath: {best_overall['xpath']}")
    else:
        log("\n❌ Không tìm thấy phần tử trong bất kỳ vùng nào")

    return best_overall