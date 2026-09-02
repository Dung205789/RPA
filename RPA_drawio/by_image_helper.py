"""
by_image_helper.py - Tối ưu hóa với Metadata
Phương pháp tìm kiếm dự phòng: Cuộn trang và tìm kiếm trong các vùng scrollable
Được gọi khi Multi-scale Template Matching và SIFT/ORB đều thất bại
Xử lý metadata viewport và DPR như code chính
Tìm kiếm nhị phân + Dừng sớm
"""
import cv2
import numpy as np
import time
import base64
from selenium.webdriver.common.by import By
from PIL import Image
import io
import sys
import re

def log(*args, **kwargs):
    """Log ra stderr"""
    print(*args, file=sys.stderr, **kwargs)

def get_viewport_info(driver):
    """
    Lấy thông tin viewport và device pixel ratio (GIỐNG CODE CHÍNH)
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

def chup_man_hinh(driver):
    """
    Chụp màn hình VÀ LƯU METADATA (GIỐNG CODE CHÍNH)
    Returns:
        tuple: (screenshot_opencv, metadata_dict)
    """
    try:
        # Lấy thông tin viewport
        viewport = get_viewport_info(driver)
        
        # Thử dùng CDP trước (chất lượng cao hơn)
        try:
            screenshot_data = driver.execute_cdp_cmd("Page.captureScreenshot", {
                "format": "png",
                "captureBeyondViewport": False,
                "fromSurface": True
            })
            screenshot_bytes = base64.b64decode(screenshot_data['data'])
            image = Image.open(io.BytesIO(screenshot_bytes))
            screenshot = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            log(f"Chụp màn hình bằng CDP")
        except:
            # Fallback sang get_screenshot_as_png
            screenshot_bytes = driver.get_screenshot_as_png()
            image = Image.open(io.BytesIO(screenshot_bytes))
            screenshot = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            log(f"Chụp màn hình bằng get_screenshot_as_png")
        
        # Tạo metadata
        actual_height, actual_width = screenshot.shape[:2]
        metadata = {
            'screenshot_width': actual_width,
            'screenshot_height': actual_height,
            'viewport_width': viewport['width'] if viewport else None,
            'viewport_height': viewport['height'] if viewport else None,
            'device_pixel_ratio': viewport['devicePixelRatio'] if viewport else 1.0
        }
        
        log(f"  Screenshot: {actual_width}x{actual_height}")
        log(f"  Viewport: {metadata['viewport_width']}x{metadata['viewport_height']}")
        log(f"  DPR: {metadata['device_pixel_ratio']}")
        
        return screenshot, metadata
        
    except Exception as e:
        log(f"Lỗi chụp màn hình: {e}")
        return None, None

def so_khop_anh(screenshot, template, scales=None, threshold=0.7, metadata=None):
    """
    So khớp template với metadata DPR
    """
    if isinstance(template, str):
        template = cv2.imread(template)
    if template is None:
        log("Không thể đọc template")
        return {'found': False, 'confidence': 0}

    # TÍNH TỶ LỆ DỰA TRÊN DPR
    if scales is None:
        if metadata and 'device_pixel_ratio' in metadata:
            dpr = metadata.get('device_pixel_ratio', 1.0)
            log(f"  DPR phát hiện: {dpr:.2f} → Tự động điều chỉnh scale")
        else:
            dpr = 1.0
            log("  Không có metadata DPR → dùng mặc định")

        scale_min = max(0.8 / dpr, 0.5)
        scale_max = min(1.2 * dpr, 1.5)

        raw_scales = sorted(set([
            scale_min,
            (scale_min + 1.0) / 2,
            1.0,
            (1.0 + scale_max) / 2,
            scale_max
        ]))
        scales = sorted({round(max(0.5, min(2.5, s)), 3) for s in raw_scales})
        log(f"  Các scale sẽ thử: {[f'{s:.3f}' for s in scales]}")
    
    # Đảm bảo ảnh ở định dạng RGB
    if len(screenshot.shape) == 2:  # Nếu là ảnh xám
        screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_GRAY2BGR)
    else:
        screenshot_rgb = screenshot
    
    if len(template.shape) == 2:  # Nếu template là ảnh xám
        template_rgb = cv2.cvtColor(template, cv2.COLOR_GRAY2BGR)
    else:
        template_rgb = template
    
    th, tw = template_rgb.shape[:2]
    
    # LƯU TẤT CẢ CANDIDATES ĐẠT THRESHOLD
    all_candidates = []
    
    for scale in scales:
        sw, sh = int(tw * scale), int(th * scale)
        
        # Kiểm tra kích thước hợp lệ
        if sw > screenshot_rgb.shape[1] or sh > screenshot_rgb.shape[0] or sw < 10 or sh < 10:
            continue
        
        # Resize template
        resized = cv2.resize(template_rgb, (sw, sh))
        
        # TEMPLATE MATCHING VỚI ẢNH MÀU
        try:
            result = cv2.matchTemplate(screenshot_rgb, resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            # LƯU TẤT CẢ KẾT QUẢ ĐẠT THRESHOLD
            if max_val >= threshold:
                # Tính độ ưu tiên (70% score + 30% gần scale 1.0)
                scale_distance = abs(scale - 1.0)
                priority_score = (max_val * 0.7) + ((1.0 - scale_distance) * 0.3)
                
                all_candidates.append({
                    'score': max_val,
                    'scale': scale,
                    'scale_distance': scale_distance,
                    'priority_score': priority_score,
                    'x': max_loc[0],
                    'y': max_loc[1],
                    'w': sw,
                    'h': sh
                })
                
                log(f"  ✓ Scale {scale:.2f}: score={max_val:.3f}, "
                    f"distance_from_1.0={scale_distance:.3f}, priority={priority_score:.3f}")
        
        except Exception as e:
            log(f"  Lỗi khi khớp template tại scale {scale:.2f}: {e}")
            continue
    
    # CHỌN KẾT QUẢ TỐT NHẤT DỰA TRÊN PRIORITY SCORE
    if all_candidates:
        # Sắp xếp theo priority_score giảm dần
        all_candidates.sort(key=lambda x: x['priority_score'], reverse=True)
        
        best = all_candidates[0]
        
        log(f"  Chọn kết quả tốt nhất:")
        log(f"     Score: {best['score']:.3f}")
        log(f"     Scale: {best['scale']:.2f} (distance from 1.0: {best['scale_distance']:.3f})")
        log(f"     Priority score: {best['priority_score']:.3f}")
        
        # Hiển thị top 3 ứng viên
        if len(all_candidates) > 1:
            log(f"  Top {min(3, len(all_candidates))} ứng viên:")
            for i, candidate in enumerate(all_candidates[:3], 1):
                log(f"     {i}. Scale={candidate['scale']:.2f}, "
                    f"Score={candidate['score']:.3f}, "
                    f"Priority={candidate['priority_score']:.3f}")
        
        return {
            'found': True,
            'confidence': best['score'],
            'x': best['x'],
            'y': best['y'],
            'w': best['w'],
            'h': best['h'],
            'scale': best['scale'],
            'priority_score': best['priority_score']
        }
    
    # Không tìm thấy kết quả nào đạt threshold
    return {
        'found': False,
        'confidence': 0,
        'x': 0,
        'y': 0,
        'w': 0,
        'h': 0
    }

def convert_screenshot_to_viewport_coords(screenshot_x, screenshot_y, metadata):
    """
    Chuyển đổi tọa độ từ screenshot space sang viewport space
    """
    if not metadata:
        return screenshot_x, screenshot_y
    
    dpr = metadata.get('device_pixel_ratio', 1.0)
    screenshot_width = metadata.get('screenshot_width', 1)
    viewport_width = metadata.get('viewport_width', 1)
    
    # Tính tỷ lệ scale
    scale_ratio = viewport_width / screenshot_width if screenshot_width > 0 else 1.0
    
    # Chuyển đổi tọa độ
    viewport_x = int(screenshot_x * scale_ratio)
    viewport_y = int(screenshot_y * scale_ratio)
    
    log(f"  Chuyển tọa độ: Screenshot({screenshot_x},{screenshot_y}) -> Viewport({viewport_x},{viewport_y})")
    
    return viewport_x, viewport_y

def tim_vung_cuon(driver):
    """Tìm tất cả các vùng có thể cuộn trên trang"""
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
            
            if (html.scrollHeight > html.clientHeight) {
                result.push({
                    xpath: '//html',
                    scrollHeight: html.scrollHeight,
                    clientHeight: html.clientHeight
                });
            }
            
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
        log(f"Lỗi khi tìm vùng cuộn: {e}")
        return []

def lay_xpath_tu_toa_do(driver, x, y):
    """Lấy XPath của element tại tọa độ x, y (VIEWPORT SPACE)"""
    try:
        # Debug marker
        try:
            driver.execute_script("""
                var marker = document.createElement('div');
                marker.id = 'debug-fallback-marker';
                marker.style.cssText = `
                    position: fixed;
                    left: ${arguments[0]}px;
                    top: ${arguments[1]}px;
                    width: 8px;
                    height: 8px;
                    background: lime;
                    border: 2px solid blue;
                    border-radius: 50%;
                    z-index: 999999;
                    pointer-events: none;
                    transform: translate(-50%, -50%);
                `;
                var old = document.getElementById('debug-fallback-marker');
                if (old) old.remove();
                document.body.appendChild(marker);
                setTimeout(() => marker.remove(), 2000);
            """, x, y)
        except:
            pass
        
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
        log(f"Lỗi lấy XPath từ tọa độ: {e}")
        return None

def kiem_tra_tai_vi_tri(driver, container, pos, template, threshold=0.7):
    """
    Kiểm tra template tại một vị trí cuộn cụ thể
    """
    element = container['element']
    
    # Cuộn đến vị trí
    if container['xpath'] == '//html':
        driver.execute_script(f"window.scrollTo(0, {pos});")
    else:
        driver.execute_script(f"arguments[0].scrollTop = {pos};", element)

    # Chụp màn hình với metadata
    screenshot, metadata = chup_man_hinh(driver)
    if screenshot is None:
        return None

    # So khớp với metadata
    result = so_khop_anh(screenshot, template, threshold=threshold, metadata=metadata)

    log(f"  📍 Vị trí {pos}px - Confidence: {result['confidence']:.3f}")

    if result['found']:
        # Lấy vị trí cuộn hiện tại
        if container['xpath'] == '//html':
            scroll_pos = driver.execute_script("return window.pageYOffset;")
        else:
            scroll_pos = driver.execute_script("return arguments[0].scrollTop;", element)

        # Chuyển đổi tọa độ
        center_x_screenshot = result['x'] + result['w'] // 2
        center_y_screenshot = result['y'] + result['h'] // 2
        
        center_x, center_y = convert_screenshot_to_viewport_coords(
            center_x_screenshot, 
            center_y_screenshot, 
            metadata
        )

        # Lấy XPath
        xpath = lay_xpath_tu_toa_do(driver, center_x, center_y)

        if not xpath:
            log(f"  Không lấy được XPath tại ({center_x}, {center_y})")
            return None

        return {
            'xpath': xpath,
            'confidence': result['confidence'],
            'toa_do': {
                'x_screenshot': center_x_screenshot,
                'y_screenshot': center_y_screenshot,
                'x_viewport': center_x,
                'y_viewport': center_y,
                'width': result['w'],
                'height': result['h']
            },
            'scroll_position': scroll_pos,
            'container_xpath': container['xpath'],
            'metadata': metadata
        }

    return None

def tinh_vung_an_toan(driver, container):
    """
    Tính vùng an toàn để tránh bị che bởi các phần tử fixed (header, sidebar, floating button...)
    Trả về: top_offset, bottom_offset (px) - phần bị che ở trên và dưới
    """
    script = """
    const fixedElements = [...document.querySelectorAll('*')].filter(el => {
        const style = window.getComputedStyle(el);
        return style.position === 'fixed' || style.position === 'sticky';
    });

    let top = 0;
    let bottom = 0;

    fixedElements.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.width < 50 || rect.height < 20) return; // bỏ qua nút nhỏ

        // Chỉ tính các phần tử che ở đầu hoặc cuối màn hình
        if (rect.top <= 50) { // ở trên cùng
            top = Math.max(top, rect.bottom);
        }
        if (rect.bottom >= window.innerHeight - 50) { // ở dưới cùng
            bottom = Math.max(bottom, window.innerHeight - rect.top);
        }
    });

    // Thêm một chút margin an toàn
    top = Math.max(top + 10, 60);     // ít nhất 60px tránh header
    bottom = Math.max(bottom + 10, 80); // ít nhất 80px tránh chat, footer

    return { topOffset: top, bottomOffset: bottom };
    """
    try:
        offsets = driver.execute_script(script)
        log(f"  Vùng an toàn: top_offset={offsets['topOffset']}px, bottom_offset={offsets['bottomOffset']}px")
        return offsets['topOffset'], offsets['bottomOffset']
    except Exception as e:
        log(f"  Không tính được vùng an toàn, dùng mặc định: {e}")
        return 60, 80  # giá trị an toàn mặc định

def tim_kiem_tuan_tu(driver, container, template, threshold=0.7, step_multiplier=0.8):
    """
    Tìm kiếm TUẦN TỰ từ trên xuống dưới
    step_multiplier: bước cuộn = viewport_height * multiplier (0.8 → chồng lấn 20% → không bỏ sót)
    """
    element = container['element']
    max_scroll = container['scrollHeight'] - container['clientHeight']
    
    if max_scroll <= 0:
        log("  Không cần cuộn (nội dung vừa màn hình)")
        return kiem_tra_tai_vi_tri(driver, container, 0, template, threshold)

    viewport_height = container['clientHeight']
    step = int(viewport_height * step_multiplier)  # chồng lấn 20%
    if step < 200:
        step = 200  # không bước quá nhỏ

    # Tính vùng an toàn (tránh fixed header/footer/chat)
    top_offset, bottom_offset = tinh_vung_an_toan(driver, container)
    safe_height = viewport_height - top_offset - bottom_offset
    if safe_height < 100:
        log("  Cảnh báo: Vùng an toàn quá nhỏ, có thể bị che hoàn toàn!")
        safe_height = viewport_height * 0.6  # fallback

    log(f"  Bắt đầu tìm kiếm tuần tự:")
    log(f"    Max scroll: {max_scroll}px")
    log(f"    Viewport height: {viewport_height}px")
    log(f"    Bước cuộn: {step}px (chồng lấn {100 - step_multiplier*100:.0f}%)")
    log(f"    Vùng an toàn: top {top_offset}px | bottom {bottom_offset}px")

    best_result = None
    best_confidence = 0
    pos = 0

    while pos <= max_scroll + step:  # +step để kiểm tra cuối cùng
        log(f"  Kiểm tra vị trí scroll: {pos}px")

        # Cuộn đến vị trí
        if container['xpath'] == '//html':
            driver.execute_script(f"window.scrollTo(0, {pos});")
        else:
            driver.execute_script(f"arguments[0].scrollTop = {pos};", element)

        result = kiem_tra_tai_vi_tri(driver, container, pos, template, threshold)

        if result and result['confidence'] > best_confidence:
            best_confidence = result['confidence']
            best_result = result
            log(f"  Tìm thấy tốt hơn! Confidence: {best_confidence:.3f}")

            # DỪNG SỚM
            if best_confidence >= 0.88:
                log(f"  Confidence cao ({best_confidence:.3f}) → DỪNG TÌM KIẾM!")
                return best_result

        # Nếu đã tìm thấy tạm ổn (≥0.8) thì giảm bước để tìm chính xác hơn
        if best_confidence >= 0.80:
            step = max(100, step // 2)  # bước nhỏ hơn để tìm vị trí đẹp nhất
            log(f"  Đã tìm thấy tạm ổn → giảm bước xuống {step}px")

        pos += step

    # Sau vòng lặp, kiểm tra lần cuối ở cuối trang
    if pos > max_scroll:
        final_pos = max_scroll
        if final_pos != pos - step:
            log(f"  Kiểm tra lần cuối ở cuối trang: {final_pos}px")
            driver.execute_script(
                f"{'window.scrollTo(0, arguments[0])' if container['xpath'] == '//html' else 'arguments[1].scrollTop = arguments[0]'}",
                final_pos,
                element
            )
            final_result = kiem_tra_tai_vi_tri(driver, container, final_pos, template, threshold)
            if final_result and final_result['confidence'] > best_confidence:
                best_result = final_result

    return best_result

def tim_kiem_trong_vung(driver, container, template, threshold=0.7, max_cuon=20):
    """
    Sử dụng tìm kiếm nhị phân với metadata
    """
    max_scroll = container['scrollHeight'] - container['clientHeight']

    if max_scroll <= 0:
        return None

    log(f"  Sử dụng tìm kiếm nhị phân (max scroll: {max_scroll}px)")
    
    # Sử dụng tìm kiếm nhị phân
    return tim_kiem_tuan_tu(driver, container, template, threshold)

def tim_phan_tu_fallback(driver, template_path, threshold=0.7):
    """
    HÀM CHÍNH: Tìm phần tử bằng cách cuộn trang
    """
    log("\n" + "="*60)
    log("PHƯƠNG PHÁP DỰ PHÒNG: Cuộn trang + Tìm kiếm")
    log("="*60)
    
    # Tìm các vùng có thể cuộn
    log("\nBước 1: Tìm các vùng có thể cuộn...")
    vung_cuon = tim_vung_cuon(driver)
    
    if not vung_cuon:
        log("Không tìm thấy vùng nào có thể cuộn!")
        return None
    
    log(f"Tìm thấy {len(vung_cuon)} vùng có thể cuộn:")
    for i, v in enumerate(vung_cuon, 1):
        log(f"  {i}. {v['xpath']} ({v['scrollHeight']}px)")
    
    # Tìm kiếm trong từng vùng
    best_overall = None
    best_confidence = 0
    
    for i, vung in enumerate(vung_cuon, 1):
        log(f"\nBước {i+1}: Tìm kiếm trong vùng {i}/{len(vung_cuon)}")
        log(f"  XPath: {vung['xpath']}")
        
        result = tim_kiem_trong_vung(driver, vung, template_path, threshold)
        
        if result and result['confidence'] > best_confidence:
            best_confidence = result['confidence']
            best_overall = result
            log(f"  Tìm thấy! Confidence: {result['confidence']:.3f}")
            
            # DỪNG SỚM nếu đã tìm thấy kết quả tốt
            if best_confidence >= 0.75:
                log(f"  Confidence cao ({best_confidence:.3f}), dừng tìm kiếm!")
                break
        else:
            log(f"  Không tìm thấy trong vùng này")
    
    if best_overall:
        log(f"\nKết quả tốt nhất: Confidence {best_overall['confidence']:.3f}")
        log(f"  XPath: {best_overall['xpath']}")
        log(f"  Viewport coords: ({best_overall['toa_do']['x_viewport']}, {best_overall['toa_do']['y_viewport']})")
        
        xpath = best_overall['xpath']
        if isinstance(xpath, str) and "/svg" in xpath:
            import re
            # Cắt bỏ TẤT CẢ từ /svg trở đi (bao gồm cả /g, /rect, v.v.)
            new_xpath = re.sub(r"/svg.*$", "", xpath)
            if new_xpath != xpath:
                log(f"  🔧 Chuyển từ SVG sang parent: {new_xpath}")
                best_overall['xpath'] = new_xpath
    else:
        log("\nKhông tìm thấy phần tử trong bất kỳ vùng nào")
    
    return best_overall