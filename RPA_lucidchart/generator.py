#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import json
import re
import find_element
from step_parser import Step, StepParser
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from by_text import setup_chrome_driver
import detect_new_g

import os
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from detect_shapes.element.check_element import check_element
from detect_shapes.diff_ui import create_difference_mask
from detect_shapes.canvas.check_canvas import check_canvas

# === Hàm chụp ảnh từ Chrome đang chạy qua CDP ===
# === HÀM MỚI - CHỤP ẢNH FULL PAGE + TRẢ VỀ TỌA ĐỘ ĐÃ CHUẨN HÓA VỀ VIEWPORT
def capture_screenshot_with_coords(driver, step_num=None):
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    filename = os.path.join(screenshots_dir, f"screenshot_step_{step_num or 0}.png")
    
    try:
        # Lấy thông tin viewport + DPR
        viewport_info = driver.execute_script("""
            return {
                innerWidth: window.innerWidth,
                innerHeight: window.innerHeight,
                devicePixelRatio: window.devicePixelRatio || 1,
                pageOffsetX: window.pageXOffset || 0,
                pageOffsetY: window.pageYOffset || 0
            };
        """)
        
        dpr = viewport_info['devicePixelRatio']
        viewport_width = viewport_info['innerWidth']
        viewport_height = viewport_info['innerHeight']
        
        # Chụp full page (bắt buộc vì canvas có thể lớn hơn viewport)
        result = driver.execute_cdp_cmd("Page.captureScreenshot", {
            "format": "png",
            "captureBeyondViewport": True,
            "fromSurface": True
        })
        
        png_data = base64.b64decode(result["data"])
        
        # Lưu ảnh gốc
        with open(filename, "wb") as f:
            f.write(png_data)
        
        # Đọc ảnh để lấy kích thước ảnh thực tế
        import cv2
        img = cv2.imread(filename)
        if img is None:
            raise Exception("Không đọc được ảnh")
        img_h, img_w = img.shape[:2]
        
        log(f"Đã chụp full page: {img_w}x{img_h} | Viewport: {viewport_width}x{viewport_height} | DPR: {dpr}")
        
        metadata = {
            "path": filename,
            "full_width": img_w,
            "full_height": img_h,
            "viewport_width": viewport_width,
            "viewport_height": viewport_height,
            "dpr": dpr,
            "scale_x": viewport_width / img_w,   # Tỷ lệ chuyển đổi X
            "scale_y": viewport_height / img_h    # Tỷ lệ chuyển đổi Y
        }
        
        return metadata  # Trả về metadata chứa scale để convert tọa độ
        
    except Exception as e:
        log(f"Lỗi chụp ảnh CDP: {e}")
        try:
            fallback_name = filename.replace(".png", "_fallback.png")
            driver.save_screenshot(fallback_name)
            return {"path": fallback_name, "scale_x": 1.0, "scale_y": 1.0, "dpr": 1.0}
        except:
            return None
        
# Helper: log ra stderr để không làm bẩn stdout
def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class Generator:
    def __init__(self, driver_var="driver", actions_var="actions"):
        self.driver_var = driver_var
        self.actions_var = actions_var
        self.object_count = 0
        self.related_count = 0
        self.tab_index = -1
        # THÊM: Lưu trữ fallback locators cho mỗi step
        self.fallback_locators = {}  # {step_index: {'object': [locators], 'related': [locators]}}
        self.current_locator_index = {}  # {step_index: {'object': idx, 'related': idx}}
        self.steps_info = []  # List lưu thông tin các step đã thực thi
        self.step_coordinates = {}  # {step_num: (x, y)} Lưu tọa độ của element

    def _new_object_var(self):
        self.object_count += 1
        return f"object{self.object_count}"

    def _new_related_var(self):
        self.related_count += 1
        return f"relatedObject{self.related_count}"
    
    def _check_step_needs_reference(self, step):
        """Kiểm tra xem step có tham chiếu đến 'element created in step X' không"""
        pattern = r"(element created in step \d+|connector_from_step\d+_to_step\d+)"
        text = f"{step.object} {step.related_object}".lower()
        return bool(re.search(pattern, text))

    def generate_code_for_step(self, url: str, step: Step, driver, step_created_elements=None,
                               created_connectors=None, step_index=None, retry_attempt=0) -> tuple:
        """
        Sinh code cho 1 step - HỖ TRỢ FALLBACK

        Args:
            retry_attempt: Số lần retry (dùng để chọn locator từ fallback list)
        """
        if step_created_elements is None:
            step_created_elements = {}
        if created_connectors is None:
            created_connectors = {}

        action = step.action.lower()
        obj = step.object.strip()
        val = step.value.strip()
        rel_obj = step.related_object.strip()

        code_lines = []

        # Phát hiện xem có phải created element không
        is_object_created = bool(re.search(r"element created in step \d+", obj.lower()))
        is_related_created = bool(re.search(r"element created in step \d+", rel_obj.lower()))

        # 🆕 KIỂM TRA XEM CÓ TỌA ĐỘ ĐÃ LƯU KHÔNG
        object_step_ref = None
        related_step_ref = None
        use_object_coords = False
        use_related_coords = False

        if is_object_created:
            match = re.search(r"step (\d+)", obj.lower())
            if match:
                object_step_ref = int(match.group(1))
                if object_step_ref in self.step_coordinates:
                    use_object_coords = True
                    log(f"✅ Sử dụng tọa độ đã lưu cho object từ step {object_step_ref}")
        
        if is_related_created:
            match = re.search(r"step (\d+)", rel_obj.lower())
            if match:
                related_step_ref = int(match.group(1))
                if related_step_ref in self.step_coordinates:
                    use_related_coords = True
                    log(f"✅ Sử dụng tọa độ đã lưu cho related object từ step {related_step_ref}")

        # Phát hiện xem có phải connector reference không
        is_object_connector_ref = bool(re.search(r"connector_from_step\d+_to_step\d+", obj.lower()))
        is_related_connector_ref = bool(re.search(r"connector_from_step\d+_to_step\d+", rel_obj.lower()))

        # Xác định loại locator ban đầu (sẽ cập nhật lại sau khi lấy locator thực tế)
        object_locator_type = "cssSelector" if (is_object_created or is_object_connector_ref) else "xpath"
        related_locator_type = "cssSelector" if (is_related_created or is_related_connector_ref) else "xpath"

        object_locator = "//not-found"
        related_locator = "//not-found"

        # Helper: Xác định loại selector dựa trên format string
        def detect_locator_type(locator_str):
            """
            Phát hiện loại selector dựa trên cấu trúc string:
            - XPath: bắt đầu với "/" hoặc "(" hoặc chứa "//"
            - CSS Selector: chứa ".", "#", ":", hoặc ">" hoặc khoảng trắng (space)
            """
            if not locator_str or locator_str == "//not-found":
                return "xpath"

            # Kiểm tra XPath
            if locator_str.startswith("/") or locator_str.startswith("(") or "//" in locator_str:
                return "xpath"

            # Kiểm tra CSS Selector
            if any(char in locator_str for char in ['.', '#', ':', ' ', '>']):
                return "cssSelector"

            # Mặc định là xpath
            return "xpath"

        # TÌM OBJECT với hỗ trợ fallback (chỉ khi không dùng tọa độ)
        if obj and not use_object_coords:
            log(f"🔍 Đang tìm object: '{obj}'")

            # Lần đầu tiên (retry_attempt = 0): Lấy tất cả locators và lưu vào fallback
            if retry_attempt == 0 and step_index is not None:
                all_locators = find_element.find_element(
                    url, obj, driver=driver,
                    step_created_elements=step_created_elements,
                    created_connectors=created_connectors,
                    return_all=True
                )

                if step_index not in self.fallback_locators:
                    self.fallback_locators[step_index] = {}
                    self.current_locator_index[step_index] = {}

                self.fallback_locators[step_index]['object'] = all_locators
                self.current_locator_index[step_index]['object'] = 0
                object_locator = all_locators[0] if all_locators else "//not-found"

                # Cập nhật loại locator dựa trên locator thực tế
                object_locator_type = detect_locator_type(object_locator)

                log(f"📋 Lưu {len(all_locators)} locators cho object. Sử dụng: {object_locator}")

            # Lần retry: Lấy locator tiếp theo từ fallback list
            elif retry_attempt > 0 and step_index in self.fallback_locators:
                locators = self.fallback_locators[step_index].get('object', [])
                current_idx = self.current_locator_index[step_index].get('object', 0)

                if current_idx < len(locators):
                    object_locator = locators[current_idx]
                    object_locator_type = detect_locator_type(object_locator)
                    log(f"🔄 Retry {retry_attempt}: Thử locator [{current_idx}]: {object_locator}")
                else:
                    log(f"⚠️ Đã hết locators để fallback cho object!")
                    object_locator = "//not-found"
                    object_locator_type = "xpath"
            else:
                # Trường hợp không có step_index (backward compatibility)
                object_locator = find_element.find_element(
                    url, obj, driver=driver, step_created_elements=step_created_elements, return_all=False
                )
                object_locator_type = detect_locator_type(object_locator)

            log(f"🔍 Object Locator ({object_locator_type}): {object_locator}")

        # TÌM RELATED OBJECT với hỗ trợ fallback (tương tự) (chỉ khi không dùng tọa độ)
        if rel_obj and not use_related_coords:
            log(f"🔍 Đang tìm related object: '{rel_obj}'")

            if retry_attempt == 0 and step_index is not None:
                all_locators = find_element.find_element(
                    url, rel_obj, driver=driver, step_created_elements=step_created_elements,
                    created_connectors=created_connectors, return_all=True
                )

                if step_index not in self.fallback_locators:
                    self.fallback_locators[step_index] = {}
                    self.current_locator_index[step_index] = {}

                self.fallback_locators[step_index]['related'] = all_locators
                self.current_locator_index[step_index]['related'] = 0
                related_locator = all_locators[0] if all_locators else "//not-found"

                # Cập nhật loại locator dựa trên locator thực tế
                related_locator_type = detect_locator_type(related_locator)

                log(f"📋 Lưu {len(all_locators)} locators cho related object. Sử dụng: {related_locator}")

            elif retry_attempt > 0 and step_index in self.fallback_locators:
                locators = self.fallback_locators[step_index].get('related', [])
                current_idx = self.current_locator_index[step_index].get('related', 0)

                if current_idx < len(locators):
                    related_locator = locators[current_idx]
                    related_locator_type = detect_locator_type(related_locator)
                    log(f"🔄 Retry {retry_attempt}: Thử locator [{current_idx}]: {related_locator}")
                else:
                    log(f"⚠️ Đã hết locators để fallback cho related object!")
                    related_locator = "//not-found"
                    related_locator_type = "xpath"
            else:
                related_locator = find_element.find_element(
                    url, rel_obj, driver=driver, step_created_elements=step_created_elements, return_all=False
                )
                related_locator_type = detect_locator_type(related_locator)

            log(f"🔍 Related Locator ({related_locator_type}): {related_locator}")

        # Sinh code theo action - Sử dụng locator_type động
        if action == "open":
            code_lines = [f'{self.driver_var}.get("{val}");']

        elif action in ["fill", "enter"]:
            if use_object_coords:
                # 🆕 CLICK VÀO TỌA ĐỘ RỒI NHẬP TEXT
                x, y = self.step_coordinates[object_step_ref]
                code_lines.append(f'// Click vào tọa độ từ step {object_step_ref} rồi nhập text')
                code_lines.append(
                    f'{self.actions_var}.moveByOffset({x}, {y}).click().moveByOffset(-{x}, -{y}).perform();'
                )
                code_lines.append(f'{self.actions_var}.sendKeys("{val}").perform();')
            elif obj:
                if is_object_created:
                    code_lines.append(f'{self.actions_var}.sendKeys("{val}").perform();')
                else:
                    code_lines.append(
                        f'{self.driver_var}.findElement(By.{object_locator_type}("{object_locator}")).sendKeys("{val}");'
                    )
            else:
                code_lines.append(f'WebElement textBox = {self.driver_var}.switchTo().activeElement();')
                code_lines.append(f'textBox.sendKeys("{val}");')

        elif action == "click":
            if use_object_coords:
                # 🆕 SỬ DỤNG TỌA ĐỘ ĐÃ LƯU
                x, y = self.step_coordinates[object_step_ref]
                code_lines.append(f'// Click vào tọa độ đã lưu từ step {object_step_ref}: ({x}, {y})')
                code_lines.append(
                    f'{self.actions_var}.moveByOffset({x}, {y}).click().moveByOffset(-{x}, -{y}).perform();'
                )
            else:
                # Click bình thường bằng locator
                code_lines.append(
                    f'{self.driver_var}.findElement(By.{object_locator_type}("{object_locator}")).click();'
                )

        elif action == "double click":
            if use_object_coords:
                # 🆕 DOUBLE CLICK VÀO TỌA ĐỘ
                x, y = self.step_coordinates[object_step_ref]
                code_lines.append(f'// Double click vào tọa độ từ step {object_step_ref}')
                code_lines.append(
                    f'{self.actions_var}.moveByOffset({x}, {y}).doubleClick().moveByOffset(-{x}, -{y}).perform();'
                )
            else:
                object_var = self._new_object_var()
                code_lines.append(
                    f'WebElement {object_var} = {self.driver_var}.findElement(By.{object_locator_type}("{object_locator}"));'
                )
                code_lines.append(f'{self.actions_var}.doubleClick({object_var}).perform();')

        elif action == "press":
            key_map = {
                "esc": "ESCAPE",
                "enter": "ENTER",
                "tab": "TAB",
                "space": "SPACE"
            }
            key_val = key_map.get(val.lower(), val.upper())
            if not obj and not rel_obj:
                code_lines.append(
                    f'{self.driver_var}.switchTo().activeElement().sendKeys(Keys.{key_val});'
                )
            else:
                code_lines.append(
                    f'{self.driver_var}.findElement(By.{object_locator_type}("{object_locator}")).sendKeys(Keys.{val.upper()});'
                )

        elif action == "move":
            object_var = self._new_object_var()
            code_lines.append(
                f'WebElement {object_var} = {self.driver_var}.findElement(By.{object_locator_type}("{object_locator}"));'
            )
            code_lines.append(f'{object_var}.click();')
            code_lines.append('Thread.sleep(500);')
            
            if val == "right":
                code_lines.append(f'for(int i=0; i<15; i++) {{ {self.actions_var}.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }}')
            elif val == "left":
                code_lines.append(f'for(int i=0; i<15; i++) {{ {self.actions_var}.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }}')
            elif val in ["up", "top"]:
                code_lines.append(f'for(int i=0; i<15; i++) {{ {self.actions_var}.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }}')
            elif val in ["down", "bottom"]:
                code_lines.append(f'for(int i=0; i<15; i++) {{ {self.actions_var}.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }}')

        elif action in ["extend", "scale up"]:
            object_var = self._new_object_var()
            code_lines.append(
                f'WebElement {object_var} = {self.driver_var}.findElement(By.{object_locator_type}("{object_locator}"));'
            )
            code_lines.append(f'{object_var}.click();')  
            code_lines.append('Thread.sleep(500);')  
            
            if val == "right":
                code_lines.append(f'for(int i=0; i<30; i++) {{ {self.actions_var}.keyDown(Keys.CONTROL).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.CONTROL).perform(); }}')
            elif val == "left":
                code_lines.append(f'''{self.actions_var}.moveToElement({object_var})
        .moveByOffset(-{object_var}.getSize().width / 2, 0)
        .clickAndHold()
        .moveByOffset(-50, 0)
        .release()
        .perform();''')
            elif val in ["bottom", "down"]:
                code_lines.append(f'for(int i=0; i<30; i++) {{ {self.actions_var}.keyDown(Keys.CONTROL).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.CONTROL).perform(); }}')
            elif val in ["top", "up"]:
                code_lines.append(f'''{self.actions_var}.moveToElement({object_var})
        .moveByOffset(0, -{object_var}.getSize().height / 2)
        .clickAndHold()
        .moveByOffset(0, -50)
        .release()
        .perform();''')
                
        elif action in ["shrink", "scale down"]:
            object_var = self._new_object_var()
            code_lines.append(
                f'WebElement {object_var} = {self.driver_var}.findElement(By.{object_locator_type}("{object_locator}"));'
            )
            code_lines.append(f'{object_var}.click();')
            code_lines.append('Thread.sleep(500);')
            
            # Shrink = Ctrl + Arrow ngược hướng với extend
            if val == "right":
                # Thu nhỏ từ phải = Ctrl + Left
                code_lines.append(f'for(int i=0; i<30; i++) {{ {self.actions_var}.keyDown(Keys.CONTROL).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.CONTROL).perform(); }}')
            elif val == "left":
                code_lines.append(f'''{self.actions_var}.moveToElement({object_var})
        .moveByOffset(-{object_var}.getSize().width / 2, 0)
        .clickAndHold()
        .moveByOffset(50, 0)
        .release()
        .perform();''')
            elif val in ["bottom", "down"]:
                # Thu nhỏ từ dưới = Ctrl + Up
                code_lines.append(f'for(int i=0; i<30; i++) {{ {self.actions_var}.keyDown(Keys.CONTROL).sendKeys(Keys.ARROW_UP).keyUp(Keys.CONTROL).perform(); }}')
            elif val in ["top", "up"]:
                code_lines.append(f'''{self.actions_var}.moveToElement({object_var})
        .moveByOffset(0, -{object_var}.getSize().height / 2)
        .clickAndHold()
        .moveByOffset(0, 50)
        .release()
        .perform();''')
                
        elif action in ["delete", "remove"]:
            object_var = self._new_object_var()
            code_lines.append(
                f'WebElement {object_var} = {self.driver_var}.findElement(By.{object_locator_type}("{object_locator}"));'
            )
            code_lines.append(
                f'{self.actions_var}.click({object_var}).perform();'
            )
            code_lines.append(
                f'{self.actions_var}.sendKeys(Keys.DELETE).perform();'
            )

        elif action in ["connect", "link"]:
            # ===================================
            # THÊM XỬ LÝ CÁC TRƯỜNG HỢP NỘI NHƯ python action
            # ===================================
            if use_object_coords and use_related_coords:
                # 🆕 KẾT NỐI BẰNG TỌA ĐỘ
                x1, y1 = self.step_coordinates[object_step_ref]
                x2, y2 = self.step_coordinates[related_step_ref]
                code_lines.append(f'// Kết nối bằng tọa độ: step {object_step_ref} ({x1},{y1}) → step {related_step_ref} ({x2},{y2})')
                code_lines.append(
                    f'''{self.actions_var}.moveByOffset({x1}, {y1})
            .clickAndHold()
            .moveByOffset({x2 - x1}, {y2 - y1})
            .release()
            .moveByOffset(-{x2}, -{y2})
            .perform();'''
                )
            else:
                object_var = self._new_object_var()
                related_var = self._new_related_var()
                code_lines.append(
                    f'WebElement {object_var} = {self.driver_var}.findElement(By.{object_locator_type}("{object_locator}"));'
                )
                code_lines.append(
                    f'WebElement {related_var} = {self.driver_var}.findElement(By.{related_locator_type}("{related_locator}"));'
                )
                code_lines.append(f'''{self.actions_var}.moveToElement({object_var}, 0, {object_var}.getSize().getHeight() / 2)
            .clickAndHold()
            .moveToElement({related_var}, 0, -{related_var}.getSize().getHeight() / 2)
            .release()
            .perform();''')

        step_code = "\n".join(code_lines)

        return step_code, action, object_locator, related_locator, val, obj, rel_obj, object_locator_type, related_locator_type


    def execute_python_action(self, driver, action, object_locator, related_locator, val, obj, rel_obj,
                              object_locator_type="xpath", related_locator_type="xpath",
                              use_object_coords=False, object_coords=None,
                              use_related_coords=False, related_coords=None):
        """Thực thi action trên Python driver - HỖ TRỢ locator_type"""
        def wait_for_page_load(d, timeout=30):
            WebDriverWait(d, timeout).until(lambda drv: drv.execute_script("return document.readyState") == "complete")
            time.sleep(3)

        def scroll_to_element(element):
            """Cuộn phần tử vào giữa viewport và đợi một chút"""
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'center'});", 
                    element
                )
                time.sleep(0.5)  # Đợi animation scroll hoàn tất
            except Exception as e:
                log(f"⚠️ Không thể scroll đến element: {e}")

        def ensure_element_visible(element):
            """Đảm bảo element visible và clickable"""
            try:
                # Scroll vào view
                scroll_to_element(element)
                
                # Kiểm tra element có bị che khuất không
                is_displayed = driver.execute_script(
                    "return arguments[0].offsetWidth > 0 && arguments[0].offsetHeight > 0;",
                    element
                )
                
                if not is_displayed:
                    log("⚠️ Element không hiển thị, thử scroll lại...")
                    driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(0.3)
                
                return True
            except Exception as e:
                log(f"âŒ KhÃ´ng thá»ƒ Ä‘áº£m báº£o element visible: {e}")
                return False

        # Phát hiện created element
        is_object_created = object_locator_type == "cssSelector"

        # Chuyển đổi locator type sang By constant
        object_by = By.CSS_SELECTOR if object_locator_type == "cssSelector" else By.XPATH
        related_by = By.CSS_SELECTOR if related_locator_type == "cssSelector" else By.XPATH

        actions = ActionChains(driver)
        try:
            if action == "open":
                driver.get(val)
                wait_for_page_load(driver)
            elif action in ["fill", "enter"]:
                if use_object_coords and object_coords:
                    # 🆕 CLICK VÀO TỌA ĐỘ RỒI NHẬP TEXT
                    x, y = object_coords
                    log(f"🎯 Click vào tọa độ ({x}, {y}) rồi nhập text")
                    actions.move_by_offset(x, y).click().move_by_offset(-x, -y).perform()
                    time.sleep(0.3)
                    actions.send_keys(val).perform()
                elif obj:  
                    if is_object_created:
                        actions.send_keys(val).perform()
                    else:
                        elem = driver.find_element(object_by, object_locator)
                        elem.send_keys(val)
                else:  
                    active_elem = driver.switch_to.active_element
                    active_elem.send_keys(val)
                wait_for_page_load(driver)
            elif action == "click":
                if use_object_coords and object_coords:
                    # 🆕 CLICK BẰNG TỌA ĐỘ
                    x, y = object_coords
                    log(f"🎯 Click vào tọa độ ({x}, {y})")
                    actions.move_by_offset(x, y).click().move_by_offset(-x, -y).perform()
                else:
                    elem = driver.find_element(object_by, object_locator)
                    ensure_element_visible(elem)  
                    window_handles_before = len(driver.window_handles)
                    elem.click()
                
                wait_for_page_load(driver)
                
                if len(driver.window_handles) > window_handles_before:
                    new_handles = driver.window_handles
                    driver.switch_to.window(new_handles[-1])
                    wait_for_page_load(driver)
                    return True


            elif action == "double click":
                if use_object_coords and object_coords:
                    # 🆕 DOUBLE CLICK BẰNG TỌA ĐỘ
                    x, y = object_coords
                    log(f"🎯 Double click vào tọa độ ({x}, {y})")
                    actions.move_by_offset(x, y).double_click().move_by_offset(-x, -y).perform()
                else:
                    elem = driver.find_element(object_by, object_locator)
                    actions.double_click(elem).perform()
                wait_for_page_load(driver)
            elif action == "press":
                key_map = {
                    "esc": Keys.ESCAPE,
                    "escape": Keys.ESCAPE,
                    "enter": Keys.ENTER,
                    "tab": Keys.TAB,
                    "space": Keys.SPACE,
                    "delete": Keys.DELETE,
                    "backspace": Keys.BACKSPACE,
                    "shift": Keys.SHIFT,
                    "ctrl": Keys.CONTROL,
                    "alt": Keys.ALT
                }
                val_lower = val.lower()
                key_to_send = key_map.get(val_lower, val.upper())

                if not obj and not rel_obj:
                    active_elem = driver.switch_to.active_element
                    active_elem.send_keys(key_to_send)
                else:
                    elem = driver.find_element(object_by, object_locator)
                    elem.send_keys(key_to_send)

                wait_for_page_load(driver)
            elif action == "move":
                if use_object_coords and object_coords:
                    old_x, old_y = object_coords
                    log(f"Di chuyển shape từ tọa độ ({old_x}, {old_y}) theo hướng '{val}'")

                    actions.move_by_offset(old_x, old_y).perform()
                    actions.click_and_hold().perform()
                    time.sleep(0.15)

                    direction = val.strip().lower()
                    distance = 100  

                    offset_map = {
                        "right":   (distance, 0),
                        "left":    (-distance, 0),
                        "up":      (0, -distance),
                        "top":     (0, -distance),
                        "down":    (0, distance),
                        "bottom":  (0, distance),
                    }
                    dx, dy = offset_map.get(direction, (distance, 0))

                    actions.move_by_offset(dx, dy).perform()
                    actions.release().perform()
                    actions.move_by_offset(-old_x - dx, -old_y - dy).perform()

                    # TÍNH TỌA ĐỘ MỚI
                    new_x = old_x + dx
                    new_y = old_y + dy

                    # XÁC ĐỊNH STEP GỐC (step mà element được tạo ra)
                    ref_step_match = re.search(r"step (\d+)", obj.lower())

                    if ref_step_match:
                        target_step = int(ref_step_match.group(1))
                        log(f"Đang di chuyển element của STEP {target_step} → cập nhật tọa độ cho STEP {target_step}")
                    
                    # CẬP NHẬT LẠI TỌA ĐỘ CHO STEP GỐC (step 1, 2, 3... chứ không phải step hiện tại)
                    self.step_coordinates[target_step] = (new_x, new_y)

                    log(f"ĐÃ CẬP NHẬT tọa độ STEP {target_step}: ({old_x}, {old_y}) → ({new_x}, {new_y})")
                    log(f"   Δx = {dx:+d}, Δy = {dy:+d} ({direction})")
                else:
                    elem = driver.find_element(object_by, object_locator)
                    ensure_element_visible(elem)
                    elem.click()
                    time.sleep(0.5)
                    for _ in range(8):
                        if val == "right":
                            actions.key_down(Keys.SHIFT).send_keys(Keys.ARROW_RIGHT).key_up(Keys.SHIFT).perform()
                        elif val == "left":
                            actions.key_down(Keys.SHIFT).send_keys(Keys.ARROW_LEFT).key_up(Keys.SHIFT).perform()
                        elif val in ["up", "top"]:
                            actions.key_down(Keys.SHIFT).send_keys(Keys.ARROW_UP).key_up(Keys.SHIFT).perform()
                        elif val in ["down", "bottom"]:
                            actions.key_down(Keys.SHIFT).send_keys(Keys.ARROW_DOWN).key_up(Keys.SHIFT).perform()
                        time.sleep(0.05)
                wait_for_page_load(driver)
            elif action in ["extend", "scale up", "shrink", "scale down"]:
                is_extend = action in ["extend", "scale up"]
                direction = val.lower().strip()

                HANDLE_OFFSET_X = 40
                HANDLE_OFFSET_Y = 30
                EXTEND_DISTANCE = 50
                SHRINK_DISTANCE = 15

                if direction in ["right"]:
                    hx, hy = HANDLE_OFFSET_X, 0
                    dx = EXTEND_DISTANCE if is_extend else -SHRINK_DISTANCE
                    dy = 0
                elif direction in ["left"]:
                    hx, hy = -HANDLE_OFFSET_X, 0
                    dx = -EXTEND_DISTANCE if is_extend else SHRINK_DISTANCE
                    dy = 0
                elif direction in ["bottom", "down"]:
                    hx, hy = 0, HANDLE_OFFSET_Y
                    dx = 0
                    dy = EXTEND_DISTANCE if is_extend else -SHRINK_DISTANCE
                elif direction in ["top", "up"]:
                    hx, hy = 0, -HANDLE_OFFSET_Y
                    dx = 0
                    dy = -EXTEND_DISTANCE if is_extend else SHRINK_DISTANCE
                else:
                    hx, hy = HANDLE_OFFSET_X, 0
                    dx = EXTEND_DISTANCE if is_extend else -SHRINK_DISTANCE
                    dy = 0

                target_step = None
                old_x = old_y = None

                if use_object_coords and object_coords:
                    old_x, old_y = object_coords
                    center_x, center_y = old_x, old_y

                    # Tìm step gốc tạo ra shape này
                    match = re.search(r"step (\d+)", obj.lower())
                    if match:
                        target_step = int(match.group(1))

                    log(f"{'Mở rộng' if is_extend else 'Thu nhỏ'} shape từ STEP {target_step} "
                        f"| Hướng: {direction} | Kéo: ({dx}, {dy})px")
                    
                    actions.move_by_offset(center_x, center_y)
                    actions.move_by_offset(hx, hy)          # đến đúng tay cầm
                    actions.click_and_hold()
                    actions.move_by_offset(dx, dy)          # kéo mạnh một phát
                    actions.release()
                    actions.move_by_offset(-center_x - hx - dx, -center_y - hy - dy)  # về vị trí ban đầu
                    actions.perform()

                    # ================== TỰ ĐỘNG CẬP NHẬT TỌA ĐỘ TÂM MỚI ==================
                    if target_step is not None and old_x is not None:
                        # Khi kéo giãn/thu nhỏ, tâm dịch chuyển = 1/2 đoạn kéo theo hướng đó
                        delta_cx = dx // 2
                        delta_cy = dy // 2

                        new_x = old_x + delta_cx
                        new_y = old_y + delta_cy

                        self.step_coordinates[target_step] = (new_x, new_y)

                        log(f"ĐÃ CẬP NHẬT TỌA ĐỘ TÂM STEP {target_step}")
                        log(f"   Cũ → ({old_x}, {old_y})")
                        log(f"   Mới → ({new_x}, {new_y})")
                        log(f"   Δtâm = ({delta_cx:+d}, {delta_cy:+d})")
                    # ====================================================================
                else:
                    elem = driver.find_element(object_by, object_locator)
                    ensure_element_visible(elem)
                    actions.move_to_element_with_offset(elem, hx, hy) \
                        .click_and_hold() \
                        .move_by_offset(dx, dy) \
                        .release() \
                        .perform()
                time.sleep(0.6)
            elif action in ["delete", "remove"]:
                if use_object_coords and object_coords:
                    # DÙNG TỌA ĐỘ ĐÃ LƯU 
                    x, y = object_coords
                    ref_step_match = re.search(r"step (\d+)", obj.lower())
                    ref_step = ref_step_match.group(1) if ref_step_match else "?"

                    log(f"XÓA ELEMENT BẰNG TỌA ĐỘ: step {ref_step} tại ({x}, {y})")

                    # Click vào tâm element trước (để chọn nó)
                    actions.move_by_offset(x, y).click().move_by_offset(-x, -y).perform()
                    time.sleep(0.2)

                    # Nhấn phím Delete
                    actions.send_keys(Keys.DELETE).perform()

                    log(f"ĐÃ XÓA thành công element step {ref_step} bằng tọa độ")

                    # (Tùy chọn) Xóa tọa độ khỏi dict nếu không muốn dùng lại
                    # if ref_step_match:
                    #     target_step = int(ref_step_match.group(1))
                    #     self.step_coordinates.pop(target_step, None)

                else:
                    # FALLBACK: dùng locator như cũ
                    elem = driver.find_element(object_by, object_locator)
                    actions.click(elem).perform()
                    actions.send_keys(Keys.DELETE).perform()
                    log("Đã xóa element bằng locator (fallback)")

            elif action in ["connect", "link"]:
                if use_object_coords and use_related_coords and object_coords and related_coords:
                    # ƯU TIÊN CAO NHẤT: CẢ HAI ĐỀU CÓ TỌA ĐỘ → DÙNG TỌA ĐỘ TRỰC TIẾP
                    x1, y1 = object_coords
                    x2, y2 = related_coords

                    # ĐIỂM BẮT ĐẦU KÉO: Tâm nguồn + dịch xuống 40px (trục Y+)
                    start_x = x1
                    start_y = y1 + 40

                    from_match = re.search(r"step (\d+)", obj.lower())
                    to_match = re.search(r"step (\d+)", rel_obj.lower())
                    from_step = from_match.group(1) if from_match else "?"
                    to_step = to_match.group(1) if to_match else "?"

                    log(f"KẾT NỐI BẰNG TỌA ĐỘ:")
                    log(f"   Từ: step {from_step} tâm ({x1}, {y1}) → điểm kéo ({start_x}, {start_y}) [+40px Y]")
                    log(f"   Đến: step {to_step} tâm ({x2}, {y2})")

                    actions.move_by_offset(x1, y1).click().move_by_offset(-x1, -y1).perform()

                    time.sleep(0.2)  # Đợi một chút để UI phản hồi sau click

                    actions.move_by_offset(x1, y1 + 40).perform()

                    actions.click_and_hold() \
                        .move_by_offset(x2 - x1, y2 - (y1 + 40)) \
                        .release() \
                        .move_by_offset(-x2, -y2) \
                        .perform()

                    log(f"ĐÃ KẾT NỐI THÀNH CÔNG từ tâm step {from_step} → tâm step {to_step}")

                else:
                    # Fallback: dùng locator + logic offset cũ (giữ nguyên code hiện tại của bạn)
                    elem1 = driver.find_element(object_by, object_locator)
                    elem2 = driver.find_element(related_by, related_locator)

                    loc1 = elem1.location
                    size1 = elem1.size
                    loc2 = elem2.location
                    size2 = elem2.size

                    center1_x = loc1['x'] + size1['width'] / 2
                    center1_y = loc1['y'] + size1['height'] / 2
                    center2_x = loc2['x'] + size2['width'] / 2
                    center2_y = loc2['y'] + size2['height'] / 2

                    delta_x = center2_x - center1_x
                    delta_y = center2_y - center1_y

                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem1)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem2)
                    time.sleep(0.5)

                    actions.move_to_element(elem1).perform()
                    time.sleep(0.3)
                    actions.move_to_element(elem2).perform()
                    time.sleep(0.3)

                    # Logic chọn điểm nối theo hướng (giữ nguyên code bạn đang có)
                    from_step = None
                    to_step = None
                    match_from = re.search(r"step (\d+)", obj.lower())
                    match_to = re.search(r"step (\d+)", rel_obj.lower())
                    if match_from and match_to:
                        from_step = int(match_from.group(1))
                        to_step = int(match_to.group(1))

                    if from_step is not None and to_step is not None and from_step > to_step:
                        log(f"TRƯỜNG HỢP ĐẶC BIỆT: step {from_step} → {to_step} (ngược chiều) → nối trái-trái")
                        start_x_offset = -size1['width'] / 2 + 2
                        start_y_offset = 0
                        end_x_offset = -size2['width'] / 2 - 4
                        end_y_offset = 0
                    else:
                        if abs(delta_y) > abs(delta_x):
                            if delta_y > 0:
                                start_x_offset = 0
                                start_y_offset = size1['height'] / 2 - 2
                                end_x_offset = 0
                                end_y_offset = -size2['height'] / 2 + 2
                            else:
                                start_x_offset = 0
                                start_y_offset = -size1['height'] / 2 + 2
                                end_x_offset = 0
                                end_y_offset = size2['height'] / 2 - 2
                        else:
                            if delta_x > 0:
                                start_x_offset = size1['width'] / 2 - 2
                                start_y_offset = 0
                                end_x_offset = -size2['width'] / 2 + 2
                                end_y_offset = 0
                            else:
                                start_x_offset = -size1['width'] / 2 + 2
                                start_y_offset = 0
                                end_x_offset = size2['width'] / 2 - 2
                                end_y_offset = 0

                    actions.move_to_element_with_offset(elem1, start_x_offset, start_y_offset) \
                        .click_and_hold() \
                        .move_to_element_with_offset(elem2, end_x_offset, end_y_offset) \
                        .release() \
                        .perform()

                    log("Kết nối thành công bằng locator + offset (fallback)")

                time.sleep(0.8)
                wait_for_page_load(driver)
            return False
        except Exception as e:
            log(f"❌ Lỗi execute Python action '{action}': {e}")
            raise 

    def _increment_locator_index(self, step_index, locator_type='object'):
        if step_index in self.current_locator_index:
            if locator_type in self.current_locator_index[step_index]:
                self.current_locator_index[step_index][locator_type] += 1
                return True
        return False

    def _has_more_fallback_locators(self, step_index, locator_type='object'):
        if step_index not in self.fallback_locators:
            return False
        if locator_type not in self.fallback_locators[step_index]:
            return False

        locators = self.fallback_locators[step_index][locator_type]
        current_idx = self.current_locator_index[step_index].get(locator_type, 0)

        return current_idx + 1 < len(locators)

    def generate_script_with_steps(self, url: str, steps: list) -> tuple[str, list[str]]:
        driver = setup_chrome_driver(use_existing=True)
        all_lines = [
            "import org.openqa.selenium.*;",
            "import org.openqa.selenium.interactions.Actions;",
            "import java.util.Set;",
            "import java.util.ArrayList;",
            "",
            "public class GeneratedTest {",
            "    public static void main(String[] args) {",
            "        WebDriver driver = new ChromeDriver();",
            "        Actions actions = new Actions(driver);",
            ""
        ]
        step_codes = []

        previous_new_selectors = None  

        created_elements = {}    
        step_created_elements = {} # {step_num: selector}
        created_connectors = {}  # {(from_step, to_step): selector}

        container_selector = None
        data_initial = None
        initial_snapshot_taken = False
        steps_created_elements_in_order = []

        total_start_time = time.time()
        step_times = []

        try:
            # CHỤP ẢNH TRƯỚC KHI CHẠY (STEP 0)
            log("Bắt đầu chụp ảnh màn hình ban đầu (step 0)...")
            capture_screenshot_with_coords(driver)

            for i, step in enumerate(steps):
                current_step = i + 1
                step_start_time = time.time()
                log(f"\n=== XỬ LÝ STEP {current_step}: {step} ===")

                if step.action.lower() == "open":
                    log(f"⏭️ Bỏ qua step {current_step}: đang sử dụng Chrome hiện tại")
                    continue

                max_retries = 10
                retry_attempt = 0
                success = False
                step_code = ""
                action = ""
                object_locator = ""
                related_locator = ""
                val = ""
                obj = ""
                rel_obj = ""
                obj_type = "xpath"
                rel_type = "xpath"
                new_tab_opened = False

                step_info = {'step_num': current_step}
                self.steps_info.append(step_info)

                while retry_attempt < max_retries and not success:
                    try:
                        if retry_attempt > 0:
                            log(f"\n🔄 RETRY {retry_attempt} cho STEP {current_step}")
                            if step.object:
                                self._increment_locator_index(i, 'object')
                            if step.related_object:
                                self._increment_locator_index(i, 'related')

                        # Sinh code cho step
                        step_code, action, object_locator, related_locator, val, obj, rel_obj, obj_type, rel_type = \
                            self.generate_code_for_step(
                                url, step, driver,
                                step_created_elements=step_created_elements,
                                created_connectors=created_connectors,
                                step_index=i,
                                retry_attempt=retry_attempt
                            )
                        
                        # 🆕 KIỂM TRA VÀ LẤY TỌA ĐỘ NẾU CẦN
                        use_obj_coords = False
                        obj_coords = None
                        use_rel_coords = False
                        rel_coords = None

                        # Kiểm tra object
                        if re.search(r"element created in step (\d+)", obj.lower()):
                            match = re.search(r"step (\d+)", obj.lower())
                            if match:
                                ref_step = int(match.group(1))
                                if ref_step in self.step_coordinates:
                                    use_obj_coords = True
                                    obj_coords = self.step_coordinates[ref_step]
                                    log(f"✅ Sử dụng tọa độ {obj_coords} từ step {ref_step} cho object")
                        
                        # Kiểm tra related object
                        if re.search(r"element created in step (\d+)", rel_obj.lower()):
                            match = re.search(r"step (\d+)", rel_obj.lower())
                            if match:
                                ref_step = int(match.group(1))
                                if ref_step in self.step_coordinates:
                                    use_rel_coords = True
                                    rel_coords = self.step_coordinates[ref_step]
                                    log(f"✅ Sử dụng tọa độ {rel_coords} từ step {ref_step} cho related")

                        step_info['action'] = action.lower()

                        if action.lower() in ['connect', 'link']:
                            from_match = re.search(r"step (\d+)", step.object.lower()) if step.object else None
                            to_match = re.search(r"step (\d+)", step.related_object.lower()) if step.related_object else None
                            if from_match and to_match:
                                step_info['from_step'] = int(from_match.group(1))
                                step_info['to_step'] = int(to_match.group(1))

                        log(f"🔹 Thực thi action '{action}'...")
                        new_tab_opened = self.execute_python_action(
                            driver, action, object_locator, related_locator, val, obj, rel_obj, obj_type, rel_type,
                            use_object_coords=use_obj_coords, object_coords=obj_coords, use_related_coords=use_rel_coords, related_coords=rel_coords
                        )
                        success = True
                        log(f"✔ Step {current_step} thành công!")

                        # CHỤP ẢNH SAU KHI STEP THÀNH CÔNG
                        screenshot_metadata = capture_screenshot_with_coords(driver, current_step)

                        # === XỬ LÝ ĐẶC BIỆT: Nếu step này là "click" vào ảnh (có URL ảnh) ===
                        if action.lower() == "click" and obj and obj.strip().startswith("http"):
                            image_url = obj.strip()
                            log(f"Phát hiện click vào ảnh: {image_url}")
                            log("Kiểm tra hình dạng phần tử được click...")

                            shape_type = check_element(image_url)
                            log(f"Kết quả nhận diện hình dạng: {shape_type}")

                            if shape_type in ["diamond", "rect_para", "ellipse"]:
                                log(f"Đây là hình {shape_type} → Tạo difference mask + lấy tọa độ...")

                                # Đường dẫn 2 ảnh trước và sau
                                prev_img = os.path.join("screenshots", f"screenshot_step_{current_step-1}.png")
                                curr_img = os.path.join("screenshots", f"screenshot_step_{current_step}.png")
                                diff_img = os.path.join("detect_img", f"diff_{current_step-1}_{current_step}.png")

                                if os.path.exists(prev_img) and os.path.exists(curr_img):
                                    mask = create_difference_mask(
                                        img1_path=prev_img,
                                        img2_path=curr_img,
                                        X=current_step-1,
                                        Y=current_step,
                                        output_folder="detect_img"
                                    )

                                    if mask is not None and os.path.exists(diff_img):
                                        log(f"Tìm tọa độ trung tâm/giao điểm của shape trong diff image...")
                                        coords = check_canvas(diff_img, shape_type, output_folder="detect_img")

                                        if coords:
                                            x_img, y_img = coords
    
                                            # Áp dụng scale từ metadata ảnh trước đó
                                            scale_x = screenshot_metadata['scale_x']
                                            scale_y = screenshot_metadata['scale_y']
                                            
                                            # Chuẩn hóa về tọa độ viewport
                                            x_viewport = int(x_img * scale_x)
                                            y_viewport = int(y_img * scale_y)
                                            
                                            # Lưu tọa độ ĐÃ CHUẨN vào step_coordinates
                                            self.step_coordinates[current_step] = (x_viewport, y_viewport)
                                            
                                            log(f"ĐÃ CHUẨN HÓA tọa độ step {current_step}:")
                                            log(f"   Trong ảnh: ({x_img}, {y_img}) → Viewport: ({x_viewport}, {y_viewport})")
                                            log(f"   Scale: {scale_x:.3f}x{scale_y:.3f}")
                                        else:
                                            log(f"Không tìm thấy tọa độ cho step {current_step}")
                                    else:
                                        log("Không tạo được diff mask → bỏ qua tọa độ")
                                else:
                                    log("Thiếu ảnh trước/sau để so sánh")
                            else:
                                log(f"Hình dạng '{shape_type}' hoặc unknown → không lấy tọa độ")

                    except Exception as e:
                        log(f"❌ Lỗi ở retry {retry_attempt}: {e}")

                        has_more_object = self._has_more_fallback_locators(i, 'object') if obj else True
                        has_more_related = self._has_more_fallback_locators(i, 'related') if rel_obj else True

                        if not (has_more_object or has_more_related):
                            log(f"⚠️ Hết locator để thử cho step {current_step}")
                            break

                        retry_attempt += 1

            
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                step_times.append(step_duration)

                status = "THÀNH CÔNG" if success else "THẤT BẠI"
                print(f"Bước {current_step}: {status} | Thời gian: {step_duration:.2f}s", file=sys.stderr)

                if new_tab_opened and action == "click":
                    self.tab_index += 1
                    tab_var = f"tab{self.tab_index}"
                    step_code += f'\nArrayList<String> {tab_var} = new ArrayList<String>(driver.getWindowHandles());\n'
                    step_code += f'driver.switchTo().window({tab_var}.get({self.tab_index+1}));\n'

                step_codes.append(step_code.strip())
                step_lines = ["        " + line for line in step_code.split("\n") if line.strip()]
                all_lines.extend(step_lines)
                all_lines.append("")

                if new_tab_opened and action != "click":
                    self.tab_index += 1
                    tab_var = f"tab{self.tab_index}"
                    all_lines.append(f'        ArrayList<String> {tab_var} = new ArrayList<String>(driver.getWindowHandles());')
                    all_lines.append(f'        driver.switchTo().window({tab_var}.get({self.tab_index+1}));')
                    all_lines.append("")

                # ===== SNAPSHOT BAN ĐẦU =====
                if not initial_snapshot_taken and action.lower() == "open":
                    log("📀 Lấy snapshot DOM ban đầu...")
                    time.sleep(3)
                    data_initial = detect_new_g.get_elements_in_container(driver, container_selector)
                    if 'error' not in data_initial:
                        container_selector = data_initial.get('containerSelector')
                        initial_snapshot_taken = True
                        log(f"✔ Snapshot DOM có {data_initial['totalElements']} phần tử <g>")
                    else:
                        log(f"❌ Snapshot lỗi: {data_initial['error']}")
                    log(f"✔ Hoàn thành step {current_step}")
                    continue

                # ===== CẬP NHẬT MAPPING SAU MỖI ACTION =====
                if initial_snapshot_taken and current_step > 1 and action.lower() in ['click', 'connect', 'link', 'fill', 'enter']:
                    log(f"🔍 Kiểm tra DOM sau action {action}...")
                    time.sleep(1)
                    data_current = detect_new_g.get_elements_in_container(driver, container_selector)

                    if 'error' not in data_current and data_initial:
                        if hasattr(detect_new_g, 'find_new_elements_by_steps'):
                            classified, error = detect_new_g.find_new_elements_by_steps(
                                data_initial,
                                data_current,
                                self.steps_info,
                                created_steps=steps_created_elements_in_order,
                                previous_new_selectors=previous_new_selectors
                            )
                            if classified:
                                step_created_elements = classified.get('elements', step_created_elements)
                                created_connectors = classified.get('connectors', created_connectors)
                                log(f"🔍 Elements: {step_created_elements}")
                                log(f"🔍 Connectors: {created_connectors}")

                                initial_selectors = {el['cssSelector'] for el in data_initial['elements']}
                                current_selectors_list = [el['cssSelector'] for el in data_current['elements']]
                                new_selectors = [s for s in current_selectors_list if s not in initial_selectors]
                                new_count = len(new_selectors)
                                previous_new_count = len(steps_created_elements_in_order)

                                if new_count > previous_new_count:
                                    steps_created_elements_in_order.append(current_step)
                                    log(f"✔ Step {current_step} đã tạo phần tử mới! ({new_count - previous_new_count} element)")
                                    log("🔄 Cập nhật mapping element...")

                                    created_elements.clear()
                                    for idx, step_num in enumerate(steps_created_elements_in_order):
                                        if idx < len(new_selectors):
                                            created_elements[step_num] = new_selectors[idx]
                                            log(f"   Step {step_num} → {new_selectors[idx]}")
                                        else:
                                            log(f"   ⚠️ Step {step_num} → Không đủ phần tử để map")

                                    log(f"🔍 Mapping hiện tại: {created_elements}")

                                else:
                                    log(f"Step {current_step} không tạo phần tử mới.")
                                    created_elements.clear()
                                    for idx, step_num in enumerate(steps_created_elements_in_order):
                                        if idx < len(new_selectors):
                                            created_elements[step_num] = new_selectors[idx]
                                    log(f"🔍 Mapping cập nhật: {created_elements}")

                                previous_new_selectors = new_selectors
                                log(f"Previous new selectors: {previous_new_selectors}")

                            elif error:
                                log(f"❌ Lỗi từ find_new_elements_by_steps: {error}")
                                continue

                        else:
                            log("⚠️ Hàm find_new_elements_by_steps không tồn tại trong detect_new_g")
                            initial_selectors = {el['cssSelector'] for el in data_initial['elements']}
                            current_selectors_list = [el['cssSelector'] for el in data_current['elements']]
                            new_selectors = [s for s in current_selectors_list if s not in initial_selectors]
                            new_count = len(new_selectors)
                            previous_new_count = len(steps_created_elements_in_order)

                            if new_count > previous_new_count:
                                steps_created_elements_in_order.append(current_step)
                                log(f"✔ Step {current_step} đã tạo phần tử mới! ({new_count - previous_new_count} element)")
                                log("🔄 Cập nhật mapping element...")

                                created_elements.clear()
                                for idx, step_num in enumerate(steps_created_elements_in_order):
                                    if idx < len(new_selectors):
                                        created_elements[step_num] = new_selectors[idx]
                                        log(f"   Step {step_num} → {new_selectors[idx]}")
                                    else:
                                        log(f"   ⚠️ Step {step_num} → Không đủ phần tử để map")

                                log(f"🔍 Mapping hiện tại: {created_elements}")
                            else:
                                log(f"Step {current_step} không tạo phần tử mới.")
                                created_elements.clear()
                                for idx, step_num in enumerate(steps_created_elements_in_order):
                                    if idx < len(new_selectors):
                                        created_elements[step_num] = new_selectors[idx]
                                log(f"🔍 Mapping cập nhật: {created_elements}")

                                previous_new_selectors = new_selectors
                                log(f"Previous new selectors: {previous_new_selectors}")

                log(f"✔ Hoàn thành step {current_step}")

        finally:
            all_lines.append("        driver.quit();")
            all_lines.append("    }")
            all_lines.append("}")
            if driver:
                driver.quit()
                log("🛑 Driver đã được đóng")

        total_duration = sum(step_times)
        print(f"\nTỔNG THỜI GIAN THỰC THI: {total_duration:.2f}s", file=sys.stderr)
        print(f"Số bước: {len(steps)}", file=sys.stderr)
        for idx, t in enumerate(step_times, 1):
            print(f"  Bướcc {idx}: {t:.2f}s", file=sys.stderr)

        full_script = "\n".join(all_lines)
        return full_script, step_codes


if __name__ == "__main__":
    log("No valid JSON input, running default mode")
    from step_parser import StepParser
    parser = StepParser()
    url = "https://nhandan.vn/"
    test_steps = [
        'Click on [http://localhost:8123/uploads/stepImg/objectImg/objectImg__160__24__20251116.png]',
        'Move the element created in step 1 up',
        'Press ESC',
        'Click on [http://localhost:8123/uploads/stepImg/objectImg/objectImg__159__24__20251116.png]',
        'Connect the element created in step 1 to the element created in step 4',
        'Delete the element created in step 1'
        # 'Click on [http://localhost:8123/uploads/stepImg/objectImg/objectImg__150__22__20251113.png]',
        # 'Click on [http://localhost:8123/uploads/stepImg/objectImg/objectImg__157__24__20251116.png]',
        # 'Click on [http://localhost:8123/uploads/stepImg/objectImg/objectImg__159__24__20251116.png]',
        # 'Click on [http://localhost:8123/uploads/stepImg/objectImg/objectImg__160__24__20251116.png]',
      



        

    ]

    steps = []
    for s in test_steps:
        step = parser.process_step(s)
        if step:
            steps.append(step)
    gen = Generator()
    script = gen.generate_script_with_steps(url, steps)
    
    # log("\n====== Sinh Script Java ======\n")
    # print(script)

    # Ghi script Java ra file
    output_file = "GeneratedTest.java"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(script[0])  # script[0] là full_script

    log(f"\nSinh script Java thành công!")
    log(f"Đã lưu vào file: {output_file}")

    