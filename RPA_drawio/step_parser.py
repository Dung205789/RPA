#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import stanza
import sys
import io
import os

# ⭐ IMPORT ACTION MATCHER
try:
    from action_matcher import get_action_matcher
    ACTION_MATCHER_AVAILABLE = True
except ImportError:
    ACTION_MATCHER_AVAILABLE = False
    print("⚠️ Warning: action_matcher not available, action correction disabled", file=sys.stderr)

# Ép stdout/stderr dùng UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Helper: log ra stderr
def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class Step:
    def __init__(self, action, object_val, related_object="", value=""):
        self.action = action
        self.object = object_val
        self.related_object = related_object
        self.value = value

    def __repr__(self):
        return (f"Step(action='{self.action}', "
                f"object='{self.object}', "
                f"related_object='{self.related_object}', "
                f"value='{self.value}')")

class StepParser:
    URL_PATTERN = re.compile(r"https?://[\w\-]+(\.[\w\-]+)+[/#?]?.*$")
    IMAGE_PATTERN = re.compile(r"\[(.*?)\]")
    STOP_WORDS = {"the", "a", "an", "of"}
    MENU_KEYWORDS = {"save", "open", "new", "close", "file", "edit", "view"}

    # ⭐ Danh sách action CHÍNH THỨC - Chỉ những action này mới được trả về
    SUPPORTED_ACTIONS = {
        'open', 'click', 'double click', 'fill', 'enter', 
        'press', 'move', 'extend', 'scale up', 'shrink', 
        'scale down', 'delete', 'remove', 'connect', 'link'
    }
    
    # ⭐ Mapping từ đồng nghĩa sang action chuẩn
    ACTION_ALIASES = {
        # Synonyms của open
        'launch': 'open', 'start': 'open', 'navigate': 'open', 
        'visit': 'open', 'browse': 'open', 'access': 'open',
        # Synonyms của click
        'tap': 'click', 'select': 'click', 'choose': 'click', 'hit': 'click',
        # Synonyms của fill/enter
        'type': 'fill', 'input': 'fill', 'write': 'fill', 
        'insert': 'fill', 'typing': 'fill',
        # Synonyms của move
        'drag': 'move', 'shift': 'move', 'reposition': 'move', 
        'relocate': 'move', 'position': 'move',
        # Synonyms của extend
        'expand': 'extend', 'enlarge': 'extend', 'grow': 'extend', 
        'stretch': 'extend',
        # Synonyms của shrink
        'reduce': 'shrink', 'compress': 'shrink', 'minimize': 'shrink', 
        'contract': 'shrink',
        # Synonyms của delete/remove
        'erase': 'delete', 'clear': 'delete', 'eliminate': 'delete', 
        'discard': 'delete',
        # Synonyms của connect/link
        'join': 'connect', 'attach': 'connect', 'associate': 'connect', 
        'relate': 'connect', 'tie': 'connect',
    }

    ACTION_KEYWORDS = {
        # Original keywords
        "open", "press", "click", "fill", "enter", "clicking",
        "move", "drag", "position",
        "scale",
        "connect", "link",
        "delete", "remove",
        "doubleclick", "double_click", "doubleclicking",
        "extend", "shrink",
        # ⭐ THÊM: Các từ đồng nghĩa để StepParser có thể detect
        "launch", "start", "navigate", "visit", "browse", "access",
        "tap", "select", "choose", "hit",
        "type", "input", "write", "insert", "typing",
        "shift", "reposition", "relocate",
        "expand", "enlarge", "grow", "stretch",
        "reduce", "compress", "minimize", "contract",
        "erase", "clear", "eliminate", "discard",
        "join", "attach", "associate", "relate", "tie"
    }

    DIRECTION_WORDS = {
        "left", "right", "top", "bottom", "up", "down", "center", "middle"
    }

    LOCATION_PREPOSITIONS = {"at", "in", "on", "near", "beside", "above", "below", "under", "from"}

    def __init__(self, action_matching_threshold=0.5):
        """
        Khởi tạo StepParser
        
        Args:
            action_matching_threshold: Ngưỡng tối thiểu cho action matching (0.0 - 1.0)
        """
        # Đường dẫn đến thư mục mô hình Stanza trong src/main/resources/models/stanza
        # (Sửa 2026-09-02: dòng gốc hard-code "C:\Users\HP\OneDrive\Desktop\BE\..." — đường
        # dẫn tuyệt đối trên máy tác giả gốc, không tồn tại trên máy khác. Đổi sang tương đối
        # theo cwd, khớp quy ước download_model.py/action_matcher.py đã dùng.)
        model_dir = os.path.join("src", "main", "resources", "models", "stanza")
        log(f"Đang tải mô hình Stanza từ thư mục: {model_dir}...")
        if not os.path.exists(model_dir):
            raise FileNotFoundError(f"Thư mục mô hình Stanza không tồn tại tại {model_dir}. Vui lòng tải bằng lệnh: python -m stanza.resources.common download en --dir src/main/resources/models/stanza")
        # Sử dụng mô hình cục bộ và tắt tải tài nguyên động
        self.pipeline = stanza.Pipeline('en', processors='tokenize,pos', dir=model_dir, download_method=None)
        log("Mô hình đã sẵn sàng.")
        
        # ⭐ Khởi tạo Action Matcher
        self.action_matcher = None
        self.action_matching_enabled = False
        
        if ACTION_MATCHER_AVAILABLE:
            try:
                self.action_matcher = get_action_matcher(threshold=action_matching_threshold)
                self.action_matching_enabled = True
                log(f"✅ Action Matching được kích hoạt (threshold: {action_matching_threshold})")
            except Exception as e:
                log(f"⚠️ Không thể khởi tạo Action Matcher: {e}")

    def _is_key_press(self, word):
        return word.lower() in ["enter", "esc", "tab", "space"]

    def _is_preposition(self, word):
        return word.lower() in ["into", "on", "at", "by", "in", "with", "of", "to"]

    def _is_location_preposition(self, words, doc, j):
        """
        Kiểm tra xem từ tại vị trí j có phải là giới từ vị trí THỰC SỰ không
        Bằng cách kiểm tra từ tiếp theo
        """
        word_lower = words[j].lower()

        # Nếu không phải giới từ vị trí thì return False
        if word_lower not in self.LOCATION_PREPOSITIONS:
            return False

        # Nếu là từ cuối cùng thì không phải giới từ vị trí
        if j + 1 >= len(words):
            return False

        next_word = words[j + 1].lower()
        next_pos = doc.sentences[0].words[j + 1].xpos if j + 1 < len(doc.sentences[0].words) else ""

        tag_map = {"text button", "button", "input", "textbox", "password", "checkbox", "radio", "link", "a", "image", "img", "label", "dropdown", "select", "textarea", "submit"}

        # Nếu từ tiếp theo hoặc thể từ loại của nó thuộc tag_map, không phải giới từ chỉ vị trí
        if next_word in tag_map or next_pos in tag_map:
            return False

        # Giới từ vị trí thực sự nếu từ tiếp theo là:
        # 1. Từ chỉ hướng (left, right, top, bottom...)
        if next_word in self.DIRECTION_WORDS:
            return True

        # 2. Từ chỉ định (the, this, that)
        if next_word in ["the", "this", "that"]:
            return True

        # 3. Số (tọa độ)
        if next_word.replace(",", "").replace(".", "").replace("-", "").isdigit():
            return True

        # 4. POS tag là số (CD = Cardinal number)
        if next_pos.startswith("CD"):
            return True

        # 5. Giới từ khác (vd: "in at")
        if next_word in self.LOCATION_PREPOSITIONS:
            return True

        # 6. Danh từ hoặc cụm danh từ (NN, NNS) - để xử lý trường hợp như "at the top bar"
        if next_pos.startswith("NN") or next_pos.startswith("NNS"):
            return True

        # Các trường hợp khác: không phải giới từ vị trí
        return False

    def _extract_text_from_original(self, original_text, start_idx, end_idx, words):
        """
        Trích xuất chuỗi gốc từ text ban đầu dựa trên chỉ số từ
        """
        if start_idx >= len(words) or end_idx > len(words):
            return ""

        # Tìm vị trí ký tự trong chuỗi gốc
        pattern = r'\s+'.join(re.escape(words[i]) for i in range(start_idx, end_idx))
        match = re.search(pattern, original_text, re.IGNORECASE)

        if match:
            return match.group(0)

        # Fallback: nối các từ với khoảng trắng
        return " ".join(words[start_idx:end_idx])

    def _correct_action(self, action):
        """
        ⭐ PHƯƠNG THỨC MỚI: Sửa action không hợp lệ sang action được hỗ trợ
        LUÔN LUÔN trả về action nằm trong SUPPORTED_ACTIONS
        
        Args:
            action: Action cần kiểm tra/sửa
            
        Returns:
            tuple: (corrected_action, was_corrected, confidence)
        """
        if not action or not action.strip():
            return action, False, 0.0
        
        action_lower = action.lower().strip()
        
        # ⭐ BƯỚC 1: Kiểm tra xem đã là action chuẩn chưa
        if action_lower in self.SUPPORTED_ACTIONS:
            return action_lower, False, 1.0
        
        # ⭐ BƯỚC 2: Check trong ACTION_ALIASES (mapping nhanh)
        if action_lower in self.ACTION_ALIASES:
            mapped_action = self.ACTION_ALIASES[action_lower]
            log(f"🔧 Action được map: '{action}' -> '{mapped_action}' (alias)")
            return mapped_action, True, 1.0
        
        # ⭐ BƯỚC 3: Sử dụng Action Matcher để tìm action gần nhất
        if not self.action_matching_enabled or self.action_matcher is None:
            # Fallback: Không có ActionMatcher, thử tìm trong aliases
            log(f"⚠️ Action Matcher không khả dụng, không thể map '{action}'")
            # Trả về action gốc nhưng đánh dấu là failed
            return action, False, 0.0
        
        # Sử dụng Action Matcher để tìm action gần nhất
        matched_action, confidence = self.action_matcher.match_action(action)
        
        if matched_action and matched_action in self.SUPPORTED_ACTIONS:
            log(f"🔧 Action được sửa: '{action}' -> '{matched_action}' (confidence: {confidence:.3f})")
            return matched_action, True, confidence
        else:
            log(f"⚠️ Không tìm thấy action phù hợp cho '{action}'")
            log(f"⚠️ Action KHÔNG HỢP LỆ - Generator sẽ không xử lý được!")
            # Trả về action gốc nhưng cảnh báo
            return action, False, confidence

    def process_step(self, step_text):
        original_text = step_text  # Lưu lại text gốc
        image_matches = self.IMAGE_PATTERN.findall(step_text)
        cleaned_text = self.IMAGE_PATTERN.sub("", step_text)

        doc = self.pipeline(cleaned_text)

        current_action = []
        object_start_idx = None
        object_end_idx = None
        related_start_idx = None
        related_end_idx = None
        current_value = []

        action_detected = False
        in_quotes = False
        url_detected = False
        in_related_part = False
        after_preposition = False

        if not doc.sentences:
            # fallback: nếu chỉ có ảnh thì coi là click vào ảnh
            if image_matches:
                return Step("click", image_matches[0], "", "")
            return None

        words = [w.text for w in doc.sentences[0].words]
        i = 0
        while i < len(words):
            word = words[i]
            lower_word = word.lower()

            # Phát hiện cụm "element created in step + số"
            if (i <= len(words)-4 and
                    lower_word == "element" and
                    words[i+1].lower() == "created" and
                    words[i+2].lower() == "in" and
                    words[i+3].lower() == "step" and
                    i+4 < len(words) and words[i+4].isdigit()):
                if in_related_part:
                    if related_start_idx is None:
                        related_start_idx = i
                    related_end_idx = i + 5
                else:
                    if object_start_idx is None:
                        object_start_idx = i
                    object_end_idx = i + 5
                i += 5
                continue

            # phát hiện "double click"
            if i < len(words)-1 and lower_word == "double" and words[i+1].lower() == "click":
                current_action.append("double click")
                action_detected = True
                i += 2
                continue

            # phát hiện "scale up/down"
            if i < len(words)-1 and lower_word == "scale" and words[i+1].lower() in ["up", "down"]:
                current_action.append(f"scale {words[i+1].lower()}")
                action_detected = True
                i += 2
                continue

            # phát hiện "move + direction"
            if lower_word == "move":
                if i < len(words)-1 and words[i+1].lower() in self.DIRECTION_WORDS:
                    current_action.append("move")
                    current_value.append(words[i+1].lower())
                    action_detected = True
                    i += 2
                    continue
                elif i < len(words)-2 and words[i+2].lower() in self.DIRECTION_WORDS:
                    current_action.append("move")
                    if object_start_idx is None:
                        object_start_idx = i + 1
                    object_end_idx = i + 2
                    current_value.append(words[i+2].lower())
                    action_detected = True
                    i += 3
                    continue

            # phát hiện "direction + edge"
            if i < len(words)-1 and lower_word in self.DIRECTION_WORDS and words[i+1].lower() == "edge":
                current_value.append(lower_word)
                i += 2
                continue

            # Phát hiện từ khóa hướng ở bất kỳ vị trí nào sau hành động
            if action_detected and lower_word in self.DIRECTION_WORDS:
                current_value.append(lower_word)
                i += 1
                continue

            # phát hiện URL
            if self.URL_PATTERN.match(word):
                current_value.append(word)
                url_detected = True
                i += 1
                continue

            # phát hiện text trong dấu nháy kép
            if word == "\"":
                in_quotes = not in_quotes
                i += 1
                continue
            if in_quotes:
                current_value.append(word)
                i += 1
                continue

            # phát hiện action chính
            if not action_detected and lower_word in self.ACTION_KEYWORDS:
                current_action.append(lower_word)
                action_detected = True
                i += 1
                continue

            # phím tắt (Enter, Esc…)
            if action_detected and self._is_key_press(word):
                current_value.append(word)
                i += 1
                continue

            # bắt đầu related object sau "to"
            if action_detected and lower_word == "to":
                in_related_part = True
                i += 1
                continue

            # xử lý preposition
            if action_detected and self._is_preposition(word):
                if object_end_idx is not None and self._is_location_preposition(words, doc, i):
                    # Đã có object, và đây là giới từ vị trí → skip phần còn lại
                    i = len(words)
                    continue
                else:
                    after_preposition = True
                    i += 1
                    continue

            # Xử lý object / related object
            if after_preposition:
                if " ".join(current_action).lower() == "click":
                    # Đánh dấu vị trí bắt đầu object
                    if object_start_idx is None:
                        object_start_idx = i

                    # Tìm vị trí kết thúc (trước giới từ vị trí hoặc hành động khác)
                    j = i
                    while j < len(words):
                        if self._is_location_preposition(words, doc, j) or words[j].lower() in self.ACTION_KEYWORDS:
                            break
                        j += 1

                    object_end_idx = j
                    i = j
                    after_preposition = False
                    continue

                # Đặc biệt: "Save as"
                if i < len(words)-1 and lower_word == "save" and words[i+1].lower() == "as":
                    if object_start_idx is None:
                        object_start_idx = i
                    object_end_idx = i + 2
                    i += 2
                    after_preposition = False
                    continue
                elif lower_word not in self.STOP_WORDS:
                    if object_start_idx is None:
                        object_start_idx = i
                    object_end_idx = i + 1
                    after_preposition = False
                    i += 1
                    continue

            token = doc.sentences[0].words[i]
            pos_tag = token.xpos

            if action_detected and not url_detected and \
                    (pos_tag.startswith("NN") or pos_tag in ["NNP", "VB", "PRP$", "DT", "JJ"] or lower_word == "in"):
                if lower_word not in self.STOP_WORDS:
                    if in_related_part:
                        if lower_word in self.DIRECTION_WORDS:
                            current_value.append(word)
                        else:
                            if related_start_idx is None:
                                related_start_idx = i
                            related_end_idx = i + 1
                    else:
                        if object_start_idx is None:
                            object_start_idx = i
                        object_end_idx = i + 1
            i += 1

        # Trích xuất object và related object từ text gốc
        final_object = ""
        final_related = ""

        if object_start_idx is not None and object_end_idx is not None:
            final_object = self._extract_text_from_original(cleaned_text, object_start_idx, object_end_idx, words)

        if related_start_idx is not None and related_end_idx is not None:
            final_related = self._extract_text_from_original(cleaned_text, related_start_idx, related_end_idx, words)

        # Gán ảnh vào object / related object nếu có
        if image_matches:
            if len(image_matches) == 1:
                if in_related_part:
                    final_related = image_matches[0]
                else:
                    final_object = image_matches[0]
            elif len(image_matches) >= 2:
                final_object = image_matches[0]
                final_related = image_matches[1]

        # Kết quả cuối
        final_action = " ".join(current_action)
        final_value = " ".join(current_value)

        if action_detected:
            # ⭐ SỬA ACTION NẾU KHÔNG HỢP LỆ
            corrected_action, was_corrected, confidence = self._correct_action(final_action)
            
            if was_corrected:
                log(f"📝 Step parsed: '{step_text}'")
                log(f"   Original action: '{final_action}' -> Corrected: '{corrected_action}' (confidence: {confidence:.3f})")
            
            return Step(corrected_action, final_object.strip(), final_related.strip(), final_value)
        return None

if __name__ == "__main__":
    processor = StepParser()
    
    # Test cases với action không hợp lệ
    test_cases = [
        "click the button",           # valid action → click
        "tap the login button",       # invalid → should map to "click"
        "navigate to https://google.com",  # invalid → should map to "open"
        "type username in textbox",   # invalid → should map to "fill"
        "expand the window",          # invalid → should map to "extend"
        "erase the text",            # invalid → should map to "delete"
        "join node1 to node2",       # invalid → should map to "connect"
    ]
    
    expected_actions = ["click", "click", "open", "fill", "extend", "delete", "connect"]
    
    print("\n" + "="*60)
    print("TESTING STEP PARSER WITH ACTION MATCHING")
    print("="*60 + "\n")
    
    passed = 0
    failed = 0
    
    for i, (test_input, expected) in enumerate(zip(test_cases, expected_actions), 1):
        print(f"\n[Test {i}] Input: {test_input}")
        print(f"Expected action: {expected}")
        print("-" * 60)
        
        step = processor.process_step(test_input)
        if step:
            actual = step.action
            status = "✅ PASS" if actual == expected else "❌ FAIL"
            
            if actual == expected:
                passed += 1
            else:
                failed += 1
            
            print(f"{status}")
            print(f"   Action        : {step.action} {'✓' if actual == expected else '✗ (expected: ' + expected + ')'}")
            print(f"   Object        : {step.object}")
            print(f"   Related Object: {step.related_object}")
            print(f"   Value         : {step.value}")
        else:
            print("❌ FAIL - Không phát hiện được hành động trong câu này.")
            failed += 1
    
    print("\n" + "="*60)
    print(f"TEST SUMMARY: {passed}/{len(test_cases)} passed, {failed}/{len(test_cases)} failed")
    print("="*60)
    
    # Interactive mode
    print("\n" + "="*60)
    print("INTERACTIVE MODE")
    print("="*60)
    print("\nSupported actions:")
    for action in sorted(processor.SUPPORTED_ACTIONS):
        print(f"  - {action}")
    print("")
    
    while True:
        user_input = input("\nNhập câu lệnh test (hoặc gõ 'exit' để thoát): ").strip()
        if user_input.lower() == "exit":
            print("Kết thúc chương trình.")
            break

        step = processor.process_step(user_input)
        if step:
            is_valid = step.action in processor.SUPPORTED_ACTIONS
            status = "✅" if is_valid else "⚠️"
            print(f"{status} Action        : {step.action}{' (VALID)' if is_valid else ' (INVALID - NOT SUPPORTED)'}")
            print(f"   Object        : {step.object}")
            print(f"   Related Object: {step.related_object}")
            print(f"   Value         : {step.value}")
        else:
            print("❌ Không phát hiện được hành động trong câu này.")