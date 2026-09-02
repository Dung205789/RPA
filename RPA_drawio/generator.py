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
        self.fallback_locators = {}  # {step_index: {'object': [locators], 'related': [locators]}}
        self.current_locator_index = {}  # {step_index: {'object': idx, 'related': idx}}
        self.steps_info = []  # List lưu thông tin các step đã thực thi

    def _new_object_var(self):
        self.object_count += 1
        return f"object{self.object_count}"

    def _new_related_var(self):
        self.related_count += 1
        return f"relatedObject{self.related_count}"

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

        # Phát hiện xem có phải connector reference không
        is_object_connector_ref = bool(re.search(r"connector_from_step\d+_to_step\d+", obj.lower()))
        is_related_connector_ref = bool(re.search(r"connector_from_step\d+_to_step\d+", rel_obj.lower()))

        # Xác định loại locator ban đầu (sẽ update lại sau khi lấy locator thực tế)
        object_locator_type = "cssSelector" if (is_object_created or is_object_connector_ref) else "xpath"
        related_locator_type = "cssSelector" if (is_related_created or is_related_connector_ref) else "xpath"

        object_locator = "//not-found"
        related_locator = "//not-found"

        # Helper: Xác định loại selector dựa trên format string
        def detect_locator_type(locator_str):
            """
            Phát hiện loại selector dựa trên cấu trúc string
            - XPath: bắt đầu với / hoặc ( hoặc chứa //
            - CSS Selector: chứa . # : hoặc > space
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

        # TÌM OBJECT với hỗ trợ fallback
        if obj:
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

            log(f"📍 Object Locator ({object_locator_type}): {object_locator}")

        # TÌM RELATED OBJECT với hỗ trợ fallback (tương tự)
        if rel_obj:
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

            log(f"📍 Related Locator ({related_locator_type}): {related_locator}")

        # Sinh code theo action - SỬ DỤNG locator_type động
        if action == "open":
            code_lines = [f'{self.driver_var}.get("{val}");']

        elif action in ["fill", "enter"]:
            if obj:  # Nếu có object
                if is_object_created:
                    code_lines.append(
                        f'{self.actions_var}.sendKeys("{val}").perform();'
                    )
                else:
                    code_lines.append(
                        f'{self.driver_var}.findElement(By.{object_locator_type}("{object_locator}")).sendKeys("{val}");'
                    )
            else:  # Nếu không có object - focus vào element hiện tại
                code_lines.append(
                    f'WebElement textBox = {self.driver_var}.switchTo().activeElement();'
                )
                code_lines.append(
                    f'textBox.sendKeys("{val}");'
                )

        elif action == "click":
            code_lines.append(
                f'{self.driver_var}.findElement(By.{object_locator_type}("{object_locator}")).click();'
            )

        elif action == "double click":
            object_var = self._new_object_var()
            code_lines.append(
                f'WebElement {object_var} = {self.driver_var}.findElement(By.{object_locator_type}("{object_locator}"));'
            )
            code_lines.append(
                f'{self.actions_var}.doubleClick({object_var}).perform();'
            )

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
            # THÊM XỬ LÝ CÁC TRƯỜNG HỢP NỐI NHƯ python action
            # ===================================
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
                              object_locator_type="xpath", related_locator_type="xpath"):
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
                log(f"❌ Không thể đảm bảo element visible: {e}")
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
                if obj:  # Nếu có object
                    if is_object_created:
                        actions.send_keys(val).perform()
                    else:
                        elem = driver.find_element(object_by, object_locator)
                        elem.send_keys(val)
                else:  # Nếu không có object - focus vào element hiện tại
                    active_elem = driver.switch_to.active_element
                    active_elem.send_keys(val)
                wait_for_page_load(driver)
            elif action == "click":
                elem = driver.find_element(object_by, object_locator)
                ensure_element_visible(elem)  # 🆕 Scroll trước khi click
                
                # VẼ CHẤM ĐỎ TẠI VỊ TRÍ CLICK
                driver.execute_script("""
                    const elem = arguments[0];
                    const r = elem.getBoundingClientRect();
                    const dot = document.createElement('div');
                    dot.style.cssText = `
                        position: fixed;
                        left: ${r.left + r.width/2 - 5}px;
                        top: ${r.top + r.height/2 - 5}px;
                        width: 10px;
                        height: 10px;
                        background: red;
                        border-radius: 50%;
                        z-index: 999999;
                        pointer-events: none;
                    `;
                    document.body.appendChild(dot);
                    setTimeout(() => dot.remove(), 1500);
                """, elem)

                window_handles_before = len(driver.window_handles)
                elem.click()
                wait_for_page_load(driver)
                if len(driver.window_handles) > window_handles_before:
                    new_handles = driver.window_handles
                    driver.switch_to.window(new_handles[-1])
                    wait_for_page_load(driver)
                    return True

                # # 🆕 Thử nhiều phương pháp click
                # clicked = False
                # methods = [
                #     ("normal_click", lambda: elem.click()),
                #     ("js_click", lambda: driver.execute_script("arguments[0].click();", elem)),
                #     ("action_click", lambda: actions.move_to_element(elem).click().perform()),
                #     ("offset_click", lambda: actions.move_to_element(elem).move_by_offset(0, 0).click().perform())
                # ]
                
                # for method_name, click_func in methods:
                #     try:
                #         log(f"🖱️ Thử click bằng: {method_name}")
                #         click_func()
                #         clicked = True
                #         log(f"✅ Click thành công bằng: {method_name}")
                #         break
                #     except Exception as e:
                #         log(f"⚠️ {method_name} thất bại: {str(e)[:100]}")
                #         continue
                
                # if not clicked:
                #     raise Exception("Không thể click element bằng bất kỳ phương pháp nào")
                
                # wait_for_page_load(driver)
                
                # if len(driver.window_handles) > window_handles_before:
                #     new_handles = driver.window_handles
                #     driver.switch_to.window(new_handles[-1])
                #     wait_for_page_load(driver)
                #     return True



            elif action == "double click":
                elem = driver.find_element(object_by, object_locator)

                # Vẽ chấm đỏ ngay giữa phần tử
                driver.execute_script("""
                    const elem = arguments[0];
                    const r = elem.getBoundingClientRect();
                    const dot = document.createElement('div');
                    dot.style.cssText = `
                        position: fixed;
                        left: ${r.left + r.width/2 - 5}px;
                        top: ${r.top + r.height/2 - 5}px;
                        width: 10px;
                        height: 10px;
                        background: red;
                        border-radius: 50%;
                        z-index: 999999;
                        pointer-events: none;
                    `;
                    document.body.appendChild(dot);
                    setTimeout(() => dot.remove(), 1500);
                """, elem)

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
                elem = driver.find_element(object_by, object_locator)
                elem.click()
                time.sleep(0.5)
                
                # Di chuyển với Shift (mỗi lần nhảy xa hơn)
                for _ in range(15):
                    if val == "right":
                        actions.key_down(Keys.SHIFT).send_keys(Keys.ARROW_RIGHT).key_up(Keys.SHIFT).perform()
                    elif val == "left":
                        actions.key_down(Keys.SHIFT).send_keys(Keys.ARROW_LEFT).key_up(Keys.SHIFT).perform()
                for _ in range(12):
                    if val in ["up", "top"]:
                        actions.key_down(Keys.SHIFT).send_keys(Keys.ARROW_UP).key_up(Keys.SHIFT).perform()
                for _ in range(12):
                    if val in ["down", "bottom"]:
                        actions.key_down(Keys.SHIFT).send_keys(Keys.ARROW_DOWN).key_up(Keys.SHIFT).perform()
                
                wait_for_page_load(driver)
            elif action in ["extend", "scale up"]:
                elem = driver.find_element(object_by, object_locator)
                elem.click()  # Click để select element
                time.sleep(0.5)  # Wait cho element được select
                
                # Resize với Ctrl + Arrow keys
                
                if val == "right":
                    for _ in range(30):
                        actions.key_down(Keys.CONTROL).send_keys(Keys.ARROW_RIGHT).key_up(Keys.CONTROL).perform()
                elif val == "left":
                    actions.move_to_element(elem).move_by_offset(-elem.size['width'] // 2, 0).click_and_hold().move_by_offset(-50, 0).release().perform()
                elif val in ["bottom", "down"]:
                    for _ in range(30):
                        actions.key_down(Keys.CONTROL).send_keys(Keys.ARROW_DOWN).key_up(Keys.CONTROL).perform()
                elif val in ["top", "up"]:
                    actions.move_to_element(elem).move_by_offset(0, -elem.size['height'] // 2).click_and_hold().move_by_offset(0, -50).release().perform()
                
                wait_for_page_load(driver)
            elif action in ["shrink", "scale down"]:
                elem = driver.find_element(object_by, object_locator)
                elem.click()
                time.sleep(0.5)
                
                if val == "right":
                    for _ in range(30):
                        actions.key_down(Keys.CONTROL).send_keys(Keys.ARROW_LEFT).key_up(Keys.CONTROL).perform()
                elif val == "left":
                    actions.move_to_element(elem).move_by_offset(-elem.size['width'] // 2, 0).click_and_hold().move_by_offset(50, 0).release().perform()
                elif val in ["bottom", "down"]:
                    for _ in range(30):
                        actions.key_down(Keys.CONTROL).send_keys(Keys.ARROW_UP).key_up(Keys.CONTROL).perform()
                elif val in ["top", "up"]:
                        actions.move_to_element(elem).move_by_offset(0, -elem.size['height'] // 2).click_and_hold().move_by_offset(0, 50).release().perform()
                
                wait_for_page_load(driver)
            elif action in ["delete", "remove"]:
                elem = driver.find_element(object_by, object_locator)
                actions.click(elem).perform()
                actions.send_keys(Keys.DELETE).perform()
                wait_for_page_load(driver)
            # elif action in ["connect", "link"]:
            #     elem1 = driver.find_element(object_by, object_locator)
            #     elem2 = driver.find_element(related_by, related_locator)
            #     actions.move_to_element_with_offset(elem1, 0, -elem1.size['height'] // 2).click_and_hold().move_to_element_with_offset(elem2, 0, -elem2.size['height'] // 2).release().perform()
            #     wait_for_page_load(driver)
            # elif action in ["connect", "link"]:
            #     elem1 = driver.find_element(object_by, object_locator)
            #     elem2 = driver.find_element(related_by, related_locator)
                
            #     # Lấy vị trí và kích thước thực tế
            #     loc1 = elem1.location
            #     size1 = elem1.size
            #     loc2 = elem2.location
            #     size2 = elem2.size
                
            #     # Đảm bảo elements visible (scroll vào view nếu cần)
            #     driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem1)
            #     time.sleep(0.5)  # Wait cho scroll
            #     driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem2)
            #     time.sleep(0.5)
                
            #     # Hover để trigger connector points
            #     actions.move_to_element(elem1).perform()
            #     time.sleep(0.5)  # Wait cho hover effect
            #     actions.move_to_element(elem2).perform()
            #     time.sleep(0.5)

            #     # Tính toán vị trí tương đối
            #     delta_x = loc2['x'] - loc1['x']
            #     delta_y = loc2['y'] - loc1['y']
                
            #     # Xác định hướng connect dựa trên vị trí tương đối
            #     if abs(delta_y) > abs(delta_x):  # Vertical (elem2 dưới elem1)
            #         # Connect bottom of elem1 to top of elem2
            #         log("Thực hiện trường hợp 1")
            #         start_x_offset = 0  # Giữa theo x
            #         start_y_offset = size1['height'] / 2 - 1  # Bottom center, offset nhẹ để hit point
            #         end_x_offset = 0
            #         end_y_offset = -size2['height'] / 2 + 1  # Top center, offset nhẹ
                
            #     elif delta_x > 0 and delta_y > 0:
            #         # Right center elem1 → Top center elem2
            #         log("Thực hiện trường hợp 2")
            #         start_x_offset = 0
            #         start_y_offset = -size1['height'] / 2 + 1  # Top center elem1
            #         end_x_offset = 0
            #         end_y_offset = -size2['height'] / 2 + 1  # Top center elem2

            #     else:  # Horizontal (elem2 bên phải elem1)
            #         # Connect right of elem1 to left of elem2
            #         log("Thực hiện trường hợp 3")
            #         start_x_offset = size1['width'] / 2 - 1  # Right center
            #         start_y_offset = 0
            #         end_x_offset = -size2['width'] / 2 + 1  # Left center
            #         end_y_offset = 0

            #     # # Right center elem1 → Top center elem2
            #     # log("Thực hiện trường hợp 2")
            #     # start_x_offset = 0
            #     # start_y_offset = -size1['height'] / 2 + 1  # Top center elem1
            #     # end_x_offset = 0
            #     # end_y_offset = -size2['height'] / 2 + 1  # Top center elem2
                
            #     # Thực hiện drag với định dạng chính xác
            #     actions.move_to_element_with_offset(elem1, start_x_offset, start_y_offset) \
            #         .click_and_hold() \
            #         .move_to_element_with_offset(elem2, end_x_offset, end_y_offset) \
            #         .release() \
            #         .perform()
                
            #     wait_for_page_load(driver)

            # # code ổn nhưng chưa có điều kiện cho trường hợp X>Y
            # elif action in ["connect", "link"]:
            #     elem1 = driver.find_element(object_by, object_locator)
            #     elem2 = driver.find_element(related_by, related_locator)
                
            #     # Lấy vị trí và kích thước thực tế
            #     loc1 = elem1.location
            #     size1 = elem1.size
            #     loc2 = elem2.location
            #     size2 = elem2.size
                
            #     # Tính tâm của mỗi element
            #     center1_x = loc1['x'] + size1['width'] / 2
            #     center1_y = loc1['y'] + size1['height'] / 2
            #     center2_x = loc2['x'] + size2['width'] / 2
            #     center2_y = loc2['y'] + size2['height'] / 2
                
            #     # Tính delta
            #     delta_x = center2_x - center1_x
            #     delta_y = center2_y - center1_y
                
            #     # Đảm bảo elements visible
            #     driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem1)
            #     time.sleep(0.5)
            #     driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem2)
            #     time.sleep(0.5)
                
            #     # Hover để trigger connector points
            #     actions.move_to_element(elem1).perform()
            #     time.sleep(0.5)
            #     actions.move_to_element(elem2).perform()
            #     time.sleep(0.5)
                
            #     # Xác định hướng kết nối dựa trên vị trí tương đối
            #     # Nếu |delta_y| > |delta_x| => Phần tử xếp theo chiều dọc
            #     # Nếu |delta_x| > |delta_y| => Phần tử xếp theo chiều ngang

                
                
            #     if abs(delta_y) > abs(delta_x):
            #         # ✅ TRƯỜNG HỢP DỌC: Phần tử 1 nằm trên/dưới phần tử 2
            #         if delta_y > 0:
            #             # elem1 ở TRÊN, elem2 ở DƯỚI
            #             # Nối: đáy của elem1 (bottom center) → đỉnh của elem2 (top center)
            #             log("📍 Kết nối: elem1 ở TRÊN → elem2 ở DƯỚI (bottom → top)")
            #             start_x_offset = 0
            #             start_y_offset = size1['height'] / 2 - 2  # Bottom center
            #             end_x_offset = 0
            #             end_y_offset = -size2['height'] / 2 + 2  # Top center
            #         else:
            #             # elem1 ở DƯỚI, elem2 ở TRÊN
            #             # Nối: đỉnh của elem1 (top center) → đáy của elem2 (bottom center)
            #             log("📍 Kết nối: elem1 ở DƯỚI → elem2 ở TRÊN (top → bottom)")
            #             start_x_offset = 0
            #             start_y_offset = -size1['height'] / 2 + 2  # Top center
            #             end_x_offset = 0
            #             end_y_offset = size2['height'] / 2 - 2  # Bottom center
            #     else:
            #         # ✅ TRƯỜNG HỢP NGANG: Phần tử 1 nằm ngang với phần tử 2
            #         if delta_x > 0:
            #             # elem1 ở BÊN TRÁI, elem2 ở BÊN PHẢI
            #             # Nối: cạnh phải của elem1 (right center) → cạnh trái của elem2 (left center)
            #             log("📍 Kết nối: elem1 ở TRÁI → elem2 ở PHẢI (right → left)")
            #             start_x_offset = size1['width'] / 2 - 2  # Right center
            #             start_y_offset = 0
            #             end_x_offset = -size2['width'] / 2 + 2  # Left center
            #             end_y_offset = 0
            #         else:
            #             # elem1 ở BÊN PHẢI, elem2 ở BÊN TRÁI
            #             # Nối: cạnh trái của elem1 (left center) → cạnh phải của elem2 (right center)
            #             log("📍 Kết nối: elem1 ở PHẢI → elem2 ở TRÁI (left → right)")
            #             start_x_offset = -size1['width'] / 2 + 2  # Left center
            #             start_y_offset = 0
            #             end_x_offset = size2['width'] / 2 - 2  # Right center
            #             end_y_offset = 0
                
            #     # Thực hiện drag and drop với offset đã tính
            #     actions.move_to_element_with_offset(elem1, start_x_offset, start_y_offset) \
            #         .click_and_hold() \
            #         .move_to_element_with_offset(elem2, end_x_offset, end_y_offset) \
            #         .release() \
            #         .perform()
                
            #     wait_for_page_load(driver)

            elif action in ["connect", "link"]:
                elem1 = driver.find_element(object_by, object_locator)
                elem2 = driver.find_element(related_by, related_locator)
                
                # Lấy vị trí và kích thước thực tế
                loc1 = elem1.location
                size1 = elem1.size
                loc2 = elem2.location
                size2 = elem2.size
                
                # Tính tâm của mỗi element
                center1_x = loc1['x'] + size1['width'] / 2
                center1_y = loc1['y'] + size1['height'] / 2
                center2_x = loc2['x'] + size2['width'] / 2
                center2_y = loc2['y'] + size2['height'] / 2
                
                # Tính delta
                delta_x = center2_x - center1_x
                delta_y = center2_y - center1_y
                
                # Đảm bảo elements visible
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem1)
                time.sleep(0.5)
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem2)
                time.sleep(0.5)
                
                # Hover để trigger connector points
                actions.move_to_element(elem1).perform()
                time.sleep(0.5)
                actions.move_to_element(elem2).perform()
                time.sleep(0.5)
                
                # === PHÁT HIỆN STEP X và Y ===
                from_step = None
                to_step = None
                match_from = re.search(r"step (\d+)", obj.lower())
                match_to = re.search(r"step (\d+)", rel_obj.lower())
                if match_from and match_to:
                    from_step = int(match_from.group(1))
                    to_step = int(match_to.group(1))
                    log(f"Phát hiện kết nối: step {from_step} → step {to_step}")

                # === TRƯỜNG HỢP ĐẶC BIỆT: X > Y → NỐI TRÁI-TRÁI ===
                if from_step is not None and to_step is not None and from_step > to_step:
                    log(f"TRƯỜNG HỢP ĐẶC BIỆT: X ({from_step}) > Y ({to_step}) → NỐI TRÁI-TRÁI")
                    # Nối từ: cạnh trái của elem1 → cạnh trái của elem2
                    start_x_offset = -size1['width'] / 2 + 2   # Cạnh trái elem1
                    start_y_offset = 0
                    end_x_offset = -size2['width'] / 2 - 4     # Cạnh trái elem2
                    end_y_offset = 0

                # === TRƯỜNG HỢP THƯỜNG: X < Y → DÙNG LOGIC HIỆN TẠI (theo hướng) ===
                else:
                    # Logic cũ: dựa vào vị trí tương đối (trái-phải, trên-dưới)
                    if abs(delta_y) > abs(delta_x):
                        # DỌC
                        if delta_y > 0:
                            # elem1 TRÊN → elem2 DƯỚI: bottom → top
                            log("Kết nối: elem1 ở TRÊN → elem2 ở DƯỚI (bottom → top)")
                            start_x_offset = 0
                            start_y_offset = size1['height'] / 2 - 2
                            end_x_offset = 0
                            end_y_offset = -size2['height'] / 2 + 2
                        else:
                            # elem1 DƯỚI → elem2 TRÊN: top → bottom
                            log("Kết nối: elem1 ở DƯỚI → elem2 ở TRÊN (top → bottom)")
                            start_x_offset = 0
                            start_y_offset = -size1['height'] / 2 + 2
                            end_x_offset = 0
                            end_y_offset = size2['height'] / 2 - 2
                    else:
                        # NGANG
                        if delta_x > 0:
                            # elem1 TRÁI → elem2 PHẢI: right → left
                            log("Kết nối: elem1 ở TRÁI → elem2 ở PHẢI (right → left)")
                            start_x_offset = size1['width'] / 2 - 2
                            start_y_offset = 0
                            end_x_offset = -size2['width'] / 2 + 2
                            end_y_offset = 0
                        else:
                            # elem1 PHẢI → elem2 TRÁI: left → right
                            log("Kết nối: elem1 ở PHẢI → elem2 ở TRÁI (left → right)")
                            start_x_offset = -size1['width'] / 2 + 2
                            start_y_offset = 0
                            end_x_offset = size2['width'] / 2 - 2
                            end_y_offset = 0

                # === THỰC HIỆN DRAG & DROP ===
                actions.move_to_element_with_offset(elem1, start_x_offset, start_y_offset) \
                    .click_and_hold() \
                    .move_to_element_with_offset(elem2, end_x_offset, end_y_offset) \
                    .release() \
                    .perform()
                
                wait_for_page_load(driver)
            
            # chỉ có 2 trường hợp nối
            # elif action in ["connect", "link"]:
            #     elem1 = driver.find_element(object_by, object_locator)
            #     elem2 = driver.find_element(related_by, related_locator)
                
            #     # Lấy vị trí và kích thước thực tế
            #     loc1 = elem1.location
            #     size1 = elem1.size
            #     loc2 = elem2.location
            #     size2 = elem2.size
                
            #     # Tính tâm của mỗi element
            #     center1_x = loc1['x'] + size1['width'] / 2
            #     center1_y = loc1['y'] + size1['height'] / 2
            #     center2_x = loc2['x'] + size2['width'] / 2
            #     center2_y = loc2['y'] + size2['height'] / 2
                
            #     # Tính delta
            #     delta_x = center2_x - center1_x
            #     delta_y = center2_y - center1_y
                
            #     # Đảm bảo elements visible
            #     driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem1)
            #     time.sleep(0.5)
            #     driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem2)
            #     time.sleep(0.5)
                
            #     # Hover để trigger connector points
            #     actions.move_to_element(elem1).perform()
            #     time.sleep(0.5)
            #     actions.move_to_element(elem2).perform()
            #     time.sleep(0.5)
                
            #     # === PHÁT HIỆN STEP X và Y ===
            #     from_step = None
            #     to_step = None
            #     match_from = re.search(r"step (\d+)", obj.lower())
            #     match_to = re.search(r"step (\d+)", rel_obj.lower())
            #     if match_from and match_to:
            #         from_step = int(match_from.group(1))
            #         to_step = int(match_to.group(1))
            #         log(f"Phát hiện kết nối: step {from_step} → step {to_step}")

            #     # === TRƯỜNG HỢP ĐẶC BIỆT: X > Y → NỐI TRÁI-TRÁI (GIỮ LOGIC CŨ) ===
            #     if from_step is not None and to_step is not None and from_step > to_step:
            #         log(f"TRƯỜNG HỢP ĐẶC BIỆT: X ({from_step}) > Y ({to_step}) → NỐI TRÁI-TRÁI")
            #         # Nối từ: cạnh trái của elem1 → cạnh trái của elem2
            #         start_x_offset = -size1['width'] / 2 + 1   # Cạnh trái elem1
            #         start_y_offset = 0
            #         end_x_offset = -size2['width'] / 2 - 4    # Cạnh trái elem2
            #         end_y_offset = 0

            #     # === TRƯỜNG HỢP: X < Y → NỐI TRUNG TÂM CẠNH ĐÁY CỦA X TỚI TRUNG TÂM CẠNH TRÊN CỦA Y ===
            #     else:
            #         log(f"Kết nối: step {from_step} < step {to_step} → NỐI CẠNH ĐÁY X TỚI CẠNH TRÊN Y")
            #         # Nối từ: trung tâm cạnh đáy của elem1 → trung tâm cạnh trên của elem2
            #         start_x_offset = 0  # Trung tâm ngang của elem1
            #         start_y_offset = size1['height'] / 2 - 2  # Cạnh đáy elem1
            #         end_x_offset = 0  # Trung tâm ngang của elem2
            #         end_y_offset = -size2['height'] / 2 + 2  # Cạnh trên elem2

                
            #     # === THỰC HIỆN DRAG & DROP ===
            #     actions.move_to_element_with_offset(elem1, start_x_offset, start_y_offset) \
            #         .click_and_hold() \
            #         .move_to_element_with_offset(elem2, end_x_offset, end_y_offset) \
            #         .release() \
            #         .perform()
                
            #     wait_for_page_load(driver)

            return False
        except Exception as e:
            log(f"⚠️ Lỗi execute Python action '{action}': {e}")
            raise  # QUAN TRỌNG: Raise exception để trigger fallback

    def _increment_locator_index(self, step_index, locator_type='object'):
        """Tăng index của locator để thử locator tiếp theo"""
        if step_index in self.current_locator_index:
            if locator_type in self.current_locator_index[step_index]:
                self.current_locator_index[step_index][locator_type] += 1
                return True
        return False

    def _has_more_fallback_locators(self, step_index, locator_type='object'):
        """Kiểm tra xem còn locator nào để fallback không"""
        if step_index not in self.fallback_locators:
            return False
        if locator_type not in self.fallback_locators[step_index]:
            return False

        locators = self.fallback_locators[step_index][locator_type]
        current_idx = self.current_locator_index[step_index].get(locator_type, 0)

        return current_idx + 1 < len(locators)

    def generate_script_with_steps(self, url: str, steps: list) -> tuple[str, list[str]]:
        """PHIÊN BẢN HOÀN CHỈNH - HỖ TRỢ ELEMENT + CONNECTOR + FALLBACK"""
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

        previous_new_selectors = None  # Lưu selectors mới từ bước trước

        # Lưu các mapping
        created_elements = {}    
        step_created_elements = {} # {step_num: selector}
        created_connectors = {}  # {(from_step, to_step): selector}

        # Dữ liệu cho phát hiện DOM mới
        container_selector = None
        data_initial = None
        initial_snapshot_taken = False
        steps_created_elements_in_order = []

        # === BIẾN ĐO THỜI GIAN ===
        total_start_time = time.time()
        step_times = []

        try:
            for i, step in enumerate(steps):
                current_step = i + 1
                step_start_time = time.time()
                log(f"\n=== XỬ LÝ STEP {current_step}: {step} ===")

                # Khởi tạo biến cho retry
                max_retries = 5
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

                # Ghi lại thông tin step
                step_info = {'step_num': current_step}
                self.steps_info.append(step_info)

                # ===== SNAPSHOT BAN ĐẦU =====
                if not initial_snapshot_taken and (action.lower() == "open" or current_step == 1):
                    log("📸 Lấy snapshot DOM ban đầu...")
                    time.sleep(3)
                    data_initial = detect_new_g.get_elements_in_container(driver, container_selector)
                    if 'error' not in data_initial:
                        container_selector = data_initial.get('containerSelector')
                        initial_snapshot_taken = True
                        log(f"[SNAPSHOT] Snapshot DOM có {data_initial['totalElements']} phần tử <g>")
                    else:
                        log(f"[ERROR] Snapshot lỗi: {data_initial['error']}")
                    if action.lower() == "open":
                        log(f"[OK] Hoàn thành step {current_step} (open URL)")
                        continue

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

                        # Cập nhật loại hành động
                        step_info['action'] = action.lower()

                        # Nếu là connect/link → lưu from_step & to_step
                        if action.lower() in ['connect', 'link']:
                            from_match = re.search(r"step (\d+)", step.object.lower()) if step.object else None
                            to_match = re.search(r"step (\d+)", step.related_object.lower()) if step.related_object else None
                            if from_match and to_match:
                                step_info['from_step'] = int(from_match.group(1))
                                step_info['to_step'] = int(to_match.group(1))

                        # Thực thi action thật bằng Python để cập nhật DOM
                        log(f"⚙️ Thực thi action '{action}'...")
                        new_tab_opened = self.execute_python_action(
                            driver, action, object_locator, related_locator, val, obj, rel_obj, obj_type, rel_type
                        )
                        success = True
                        log(f"✅ Step {current_step} thành công!")

                    except Exception as e:
                        log(f"❌ Lỗi ở retry {retry_attempt}: {e}")

                        # Kiểm tra fallback locator
                        has_more_object = self._has_more_fallback_locators(i, 'object') if obj else True
                        has_more_related = self._has_more_fallback_locators(i, 'related') if rel_obj else True

                        if not (has_more_object or has_more_related):
                            log(f"⚠️ Hết locator để thử cho step {current_step}")
                            break

                        retry_attempt += 1

                # if not success:
                #     log(f"❌ STEP {current_step} FAILED sau {retry_attempt} lần thử!")

                # === GHI NHẬN THỜI GIAN BƯỚC ===
                step_end_time = time.time()
                step_duration = step_end_time - step_start_time
                step_times.append(step_duration)

                # === IN THỜI GIAN TỪNG BƯỚC ===
                status = "THÀNH CÔNG" if success else "THẤT BẠI"
                print(f"Bước {current_step}: {status} | Thời gian: {step_duration:.2f}s", file=sys.stderr)

                # Nếu click mở tab mới → chuyển sang tab
                if new_tab_opened and action == "click":
                    self.tab_index += 1
                    tab_var = f"tab{self.tab_index}"
                    step_code += f'\nArrayList<String> {tab_var} = new ArrayList<String>(driver.getWindowHandles());\n'
                    step_code += f'driver.switchTo().window({tab_var}.get({self.tab_index+1}));\n'

                # Lưu code
                step_codes.append(step_code.strip())
                step_lines = ["        " + line for line in step_code.split("\n") if line.strip()]
                all_lines.extend(step_lines)
                all_lines.append("")

                # Chuyển tab nếu cần (khi hành động khác click)
                if new_tab_opened and action != "click":
                    self.tab_index += 1
                    tab_var = f"tab{self.tab_index}"
                    all_lines.append(f'        ArrayList<String> {tab_var} = new ArrayList<String>(driver.getWindowHandles());')
                    all_lines.append(f'        driver.switchTo().window({tab_var}.get({self.tab_index+1}));')
                    all_lines.append("")

                # ===== CẬP NHẬT MAPPING SAU MỖI ACTION =====
                if initial_snapshot_taken and action.lower() in ['click', 'connect', 'link', 'fill', 'enter']:
                    log(f"🔍 Kiểm tra DOM sau action {action}...")
                    time.sleep(1)
                    data_current = detect_new_g.get_elements_in_container(driver, container_selector)

                    if 'error' not in data_current and data_initial:
                        # ✨ Gọi hàm phân loại nâng cao trước
                        if hasattr(detect_new_g, 'find_new_elements_by_steps'):
                            classified, error = detect_new_g.find_new_elements_by_steps(
                                data_initial,
                                data_current,
                                self.steps_info,
                                created_steps=steps_created_elements_in_order,
                                previous_new_selectors=previous_new_selectors
                            )
                            if classified:
                                # Cập nhật step_created_elements và created_connectors từ classified
                                step_created_elements = classified.get('elements', step_created_elements)
                                created_connectors = classified.get('connectors', created_connectors)
                                log(f"📋 Elements: {step_created_elements}")
                                log(f"📋 Connectors: {created_connectors}")

                                # Tính toán new_selectors để kiểm tra element mới
                                initial_selectors = {el['cssSelector'] for el in data_initial['elements']}
                                current_selectors_list = [el['cssSelector'] for el in data_current['elements']]
                                new_selectors = [s for s in current_selectors_list if s not in initial_selectors]
                                new_count = len(new_selectors)
                                previous_new_count = len(steps_created_elements_in_order)

                                # 🆕 Nếu phát hiện element mới
                                if new_count > previous_new_count:
                                    steps_created_elements_in_order.append(current_step)
                                    log(f"✅ Step {current_step} đã tạo phần tử mới! ({new_count - previous_new_count} element)")
                                    log("🔄 Cập nhật mapping element...")

                                    created_elements.clear()
                                    for idx, step_num in enumerate(steps_created_elements_in_order):
                                        if idx < len(new_selectors):
                                            created_elements[step_num] = new_selectors[idx]
                                            log(f"   Step {step_num} → {new_selectors[idx]}")
                                        else:
                                            log(f"   ⚠️ Step {step_num} → Không đủ phần tử để map")

                                    log(f"📋 Mapping hiện tại: {created_elements}")

                                # Nếu không tạo thêm phần tử mới
                                else:
                                    log(f"Step {current_step} không tạo phần tử mới.")
                                    # Vẫn cập nhật lại mapping cho chắc
                                    created_elements.clear()
                                    for idx, step_num in enumerate(steps_created_elements_in_order):
                                        if idx < len(new_selectors):
                                            created_elements[step_num] = new_selectors[idx]
                                    log(f"📋 Mapping cập nhật: {created_elements}")

                                # Cập nhật previous_new_selectors cho bước sau
                                previous_new_selectors = new_selectors
                                log(f"Previous new selectors: {previous_new_selectors}")

                            elif error:
                                log(f"⚠️ Lỗi từ find_new_elements_by_steps: {error}")
                                # Nếu có lỗi, bỏ qua logic kiểm tra new_count
                                continue

                        else:
                            log("⚠️ Hàm find_new_elements_by_steps không tồn tại trong detect_new_g")
                            # Fallback logic nếu không có find_new_elements_by_steps
                            initial_selectors = {el['cssSelector'] for el in data_initial['elements']}
                            current_selectors_list = [el['cssSelector'] for el in data_current['elements']]
                            new_selectors = [s for s in current_selectors_list if s not in initial_selectors]
                            new_count = len(new_selectors)
                            previous_new_count = len(steps_created_elements_in_order)

                            if new_count > previous_new_count:
                                steps_created_elements_in_order.append(current_step)
                                log(f"✅ Step {current_step} đã tạo phần tử mới! ({new_count - previous_new_count} element)")
                                log("🔄 Cập nhật mapping element...")

                                created_elements.clear()
                                for idx, step_num in enumerate(steps_created_elements_in_order):
                                    if idx < len(new_selectors):
                                        created_elements[step_num] = new_selectors[idx]
                                        log(f"   Step {step_num} → {new_selectors[idx]}")
                                    else:
                                        log(f"   ⚠️ Step {step_num} → Không đủ phần tử để map")

                                log(f"📋 Mapping hiện tại: {created_elements}")
                            else:
                                log(f"Step {current_step} không tạo phần tử mới.")
                                created_elements.clear()
                                for idx, step_num in enumerate(steps_created_elements_in_order):
                                    if idx < len(new_selectors):
                                        created_elements[step_num] = new_selectors[idx]
                                log(f"📋 Mapping cập nhật: {created_elements}")

                                previous_new_selectors = new_selectors
                                log(f"Previous new selectors: {previous_new_selectors}")

                log(f"✅ Hoàn thành step {current_step}")

        finally:
            all_lines.append("        driver.quit();")
            all_lines.append("    }")
            all_lines.append("}")
            if driver:
                driver.quit()
                log("🚪 Driver đã được đóng")

        # === TÍNH TỔNG THỜI GIAN ===
        total_duration = sum(step_times)
        print(f"\nTỔNG THỜI GIAN THỰC THI: {total_duration:.2f}s", file=sys.stderr)
        print(f"Số bước: {len(steps)}", file=sys.stderr)
        for idx, t in enumerate(step_times, 1):
            print(f"  Bước {idx}: {t:.2f}s", file=sys.stderr)

        full_script = "\n".join(all_lines)
        return full_script, step_codes


if __name__ == "__main__":
    log("No valid JSON input, running default mode")
    from step_parser import StepParser
    parser = StepParser()
    url = "https://nhandan.vn/"
    test_steps = [
        'Click on [http://localhost:8123/uploads/stepImg/objectImg/objectImg__153__23__20251116.png]',
        'Move the element created in step 1 up',
        'Move the element created in step 1 up',
        'Move the element created in step 1 up',
        'Click on [http://localhost:8123/uploads/stepImg/objectImg/objectImg__156__23__20251116.png]',
        'Move the element created in step 5 up',
        'Move the element created in step 5 up',
        'Click on [http://localhost:8123/uploads/stepImg/objectImg/objectImg__154__23__20251116.png]',
        'Move the element created in step 8 up',
        'Click on [http://localhost:8123/uploads/stepImg/objectImg/objectImg__155__23__20251116.png]',
        'Move the element created in step 10 left',
        'Click on [http://localhost:8123/uploads/stepImg/objectImg/objectImg__155__23__20251116.png]',
        'Move the element created in step 12 right',
        'Click on [http://localhost:8123/uploads/stepImg/objectImg/objectImg__153__23__20251116.png]',
        'Move the element created in step 14 down',
        'Double click on the element created in step 1',
        'Fill "Leave home" into the element created in step 1',
        'Double click on the element created in step 5',
        'Fill "Check timeline" into the element created in step 5',
        'Double click on the element created in step 8',
        'Fill "Before 7 am ?" into the element created in step 8',
        'Double click on the element created in step 10',
        'Fill "Take bus" into the element created in step 10',
        'Double click on the element created in step 12',
        'Fill "Take subway" into the element created in step 12',
        'Double click on the element created in step 14',
        'Fill "Reach school" into the element created in step 14',
        'Connect the element created in step 1 to the element created in step 5',
        'Connect the element created in step 5 to the element created in step 8',
        'Connect the element created in step 8 to the element created in step 10',
        'Double click on connector_from_step8_to_step10',
        'Fill "NO"',
        'Connect the element created in step 8 to the element created in step 12',
        'Double click on connector_from_step8_to_step12',
        'Fill "YES"',
        'Connect the element created in step 10 to the element created in step 14',
        'Connect the element created in step 12 to the element created in step 14',






        # http://localhost:8123/uploads/stepImg/objectImg/objectImg__153__23__20251116.png
        # http://localhost:8123/uploads/stepImg/objectImg/objectImg__154__23__20251116.png
        # http://localhost:8123/uploads/stepImg/objectImg/objectImg__155__23__20251116.png
        # http://localhost:8123/uploads/stepImg/objectImg/objectImg__156__23__20251116.png
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
    