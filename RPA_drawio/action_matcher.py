#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
action_matcher.py - Mapping action không hợp lệ sang action được hỗ trợ
Sử dụng Sentence Transformer để tính độ tương đồng cosine
"""

import os
import sys
import numpy as np
from sentence_transformers import SentenceTransformer, util
import warnings

# Tắt warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

# Cache model toàn cục
_cached_model = None
_model_loaded = False

def log(*args, **kwargs):
    """Log ra stderr"""
    print(*args, file=sys.stderr, **kwargs)

def get_sentence_model():
    """Load model một lần duy nhất và cache lại (giống by_text.py)"""
    global _cached_model, _model_loaded

    if _cached_model is None:
        # Lấy đường dẫn tuyệt đối của file hiện tại
        current_file = os.path.abspath(__file__)
        
        # Tìm project root bằng cách tìm thư mục chứa "src"
        current_dir = os.path.dirname(current_file)
        
        # Đi lên đến khi tìm thấy thư mục "src" hoặc đến root
        while current_dir and current_dir != os.path.dirname(current_dir):
            if "src" in os.listdir(current_dir):
                project_root = current_dir
                break
            current_dir = os.path.dirname(current_dir)
        else:
            # Fallback: Nếu không tìm thấy, dùng đường dẫn tương đối
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))

        model_path = os.path.join(project_root, "src", "main", "resources", "models",
                                  "sentence_transformers", "paraphrase-multilingual-MiniLM-L12-v2")

        if not os.path.exists(model_path):
            log(f"❌ Lỗi: Mô hình không tồn tại tại {model_path}")
            log(f"💡 Hãy chạy: python src/main/python/auto_test_generator_DOM/download_model.py")
            return None

        try:
            _cached_model = SentenceTransformer(model_path)
            if not _model_loaded:
                log("✅ Action Matcher Model đã được load vào cache")
                _model_loaded = True
        except Exception as e:
            log(f"❌ Lỗi khi tải mô hình: {str(e)}")
            return None

    return _cached_model


class ActionMatcher:
    """
    Class để map action không hợp lệ sang action được hỗ trợ
    """
    
    # Danh sách các action được hỗ trợ và các biến thể/từ đồng nghĩa
    SUPPORTED_ACTIONS = {
        'open': [
            'open', 'launch', 'start', 'navigate', 'go to', 'visit', 
            'access', 'browse', 'load page', 'open url'
        ],
        'click': [
            'click', 'press', 'tap', 'select', 'choose', 'hit',
            'click on', 'press on', 'tap on', 'clicking'
        ],
        'double click': [
            'double click', 'doubleclick', 'double-click', 'double tap',
            'double press', 'doubleclicking', 'double clicking'
        ],
        'fill': [
            'fill', 'enter', 'type', 'input', 'write', 'insert',
            'fill in', 'enter text', 'type in', 'key in', 'typing'
        ],
        'press': [
            'press', 'press key', 'hit key', 'keyboard', 'key press',
            'press button', 'push key', 'strike key'
        ],
        'move': [
            'move', 'drag', 'shift', 'reposition', 'relocate',
            'move to', 'drag to', 'position', 'place'
        ],
        'extend': [
            'extend', 'expand', 'enlarge', 'scale up', 'increase size',
            'make bigger', 'grow', 'stretch', 'resize larger'
        ],
        'shrink': [
            'shrink', 'reduce', 'scale down', 'decrease size', 'make smaller',
            'compress', 'minimize', 'contract', 'resize smaller'
        ],
        'delete': [
            'delete', 'remove', 'erase', 'clear', 'eliminate',
            'discard', 'drop', 'get rid of', 'take away'
        ],
        'connect': [
            'connect', 'link', 'join', 'attach', 'associate',
            'relate', 'tie', 'bind', 'couple', 'connect to'
        ]
    }

    def __init__(self, threshold=0.5):
        """
        Khởi tạo ActionMatcher
        
        Args:
            threshold: Ngưỡng tối thiểu cho độ tương đồng (default: 0.5)
        """
        self.threshold = threshold
        self.model = get_sentence_model()
        
        if self.model is None:
            log("⚠️ Không load được model, ActionMatcher sẽ sử dụng fallback matching")
            self.use_fallback = True
        else:
            self.use_fallback = False
            self._prepare_embeddings()

    def _prepare_embeddings(self):
        """
        Tạo embeddings cho tất cả các action và biến thể của chúng
        """
        if self.use_fallback:
            return

        self.action_texts = []
        self.action_labels = []
        
        for action, variants in self.SUPPORTED_ACTIONS.items():
            for variant in variants:
                self.action_texts.append(variant)
                self.action_labels.append(action)
        
        try:
            log(f"🔄 Đang tạo embeddings cho {len(self.action_texts)} action variants...")
            self.action_embeddings = self.model.encode(self.action_texts, convert_to_tensor=True)
            log("✅ Embeddings đã được tạo xong")
        except Exception as e:
            log(f"❌ Lỗi khi tạo embeddings: {e}")
            self.use_fallback = True

    def _fallback_match(self, action_text):
        """
        Phương pháp fallback: so sánh string đơn giản
        """
        action_lower = action_text.lower().strip()
        
        # Kiểm tra exact match trước
        for action, variants in self.SUPPORTED_ACTIONS.items():
            if action_lower in [v.lower() for v in variants]:
                return action, 1.0
        
        # Kiểm tra substring match
        best_match = None
        best_score = 0
        
        for action, variants in self.SUPPORTED_ACTIONS.items():
            for variant in variants:
                variant_lower = variant.lower()
                # Tính điểm dựa trên số từ trùng khớp
                action_words = set(action_lower.split())
                variant_words = set(variant_lower.split())
                
                if action_words and variant_words:
                    common_words = action_words & variant_words
                    score = len(common_words) / max(len(action_words), len(variant_words))
                    
                    if score > best_score:
                        best_score = score
                        best_match = action
        
        if best_match and best_score >= self.threshold:
            return best_match, best_score
        
        return None, 0

    def match_action(self, action_text):
        """
        Tìm action được hỗ trợ gần nhất với action_text
        LUÔN TRẢ VỀ ACTION KEY (không phải variant)
        
        Args:
            action_text: Action text cần match
            
        Returns:
            tuple: (matched_action, confidence_score)
                   hoặc (None, 0) nếu không tìm thấy match phù hợp
        """
        if not action_text or not action_text.strip():
            return None, 0
        
        action_text = action_text.strip().lower()
        
        # ⭐ Kiểm tra xem action đã là KEY hợp lệ chưa
        if action_text in self.SUPPORTED_ACTIONS:
            return action_text, 1.0
        
        # Sử dụng fallback nếu không có model
        if self.use_fallback:
            return self._fallback_match(action_text)
        
        try:
            # Tạo embedding cho action cần match
            query_embedding = self.model.encode(action_text, convert_to_tensor=True)
            
            # Tính cosine similarity với tất cả action variants
            similarities = util.cos_sim(query_embedding, self.action_embeddings)[0]
            
            # Lấy top match
            top_idx = similarities.argmax().item()
            top_score = similarities[top_idx].item()
            
            if top_score >= self.threshold:
                # ⭐ TRẢ VỀ ACTION KEY (từ action_labels)
                matched_action = self.action_labels[top_idx]
                log(f"🎯 Matched '{action_text}' -> '{matched_action}' (score: {top_score:.3f})")
                return matched_action, top_score
            else:
                log(f"⚠️ Không tìm thấy match phù hợp cho '{action_text}' (best score: {top_score:.3f})")
                return None, top_score
                
        except Exception as e:
            log(f"❌ Lỗi khi matching action: {e}")
            return self._fallback_match(action_text)

    def is_valid_action(self, action_text):
        """
        Kiểm tra xem action có hợp lệ (nằm trong danh sách supported CHÍNH THỨC) không
        CHỈ CHECK TRONG KEY, KHÔNG CHECK TRONG VARIANTS
        
        Args:
            action_text: Action text cần kiểm tra
            
        Returns:
            bool: True nếu action hợp lệ (là key trong SUPPORTED_ACTIONS), False nếu không
        """
        action_lower = action_text.lower().strip()
        
        # ⭐ CHỈ KIỂM TRA TRONG KEYS, KHÔNG KIỂM TRA TRONG VARIANTS
        return action_lower in self.SUPPORTED_ACTIONS

    def get_all_supported_actions(self):
        """
        Trả về danh sách tất cả các action được hỗ trợ
        
        Returns:
            list: Danh sách các action chính (không bao gồm variants)
        """
        return list(self.SUPPORTED_ACTIONS.keys())


# Singleton instance để tái sử dụng
_action_matcher_instance = None

def get_action_matcher(threshold=0.5):
    """
    Lấy hoặc tạo ActionMatcher instance (singleton pattern)
    
    Args:
        threshold: Ngưỡng tối thiểu cho độ tương đồng
        
    Returns:
        ActionMatcher instance
    """
    global _action_matcher_instance
    
    if _action_matcher_instance is None:
        _action_matcher_instance = ActionMatcher(threshold=threshold)
    
    return _action_matcher_instance


# Test function
if __name__ == "__main__":
    matcher = get_action_matcher(threshold=0.5)
    
    # Test cases
    test_actions = [
        "click",           # valid
        "double click",    # valid
        "tap",            # should map to click
        "navigate",       # should map to open
        "type",           # should map to fill
        "expand",         # should map to extend
        "reduce",         # should map to shrink
        "erase",          # should map to delete
        "join",           # should map to connect
        "unknown_action", # should return None
    ]
    
    print("\n=== Testing Action Matcher ===\n")
    for action in test_actions:
        matched, score = matcher.match_action(action)
        status = "✅" if matched else "❌"
        print(f"{status} '{action}' -> '{matched}' (score: {score:.3f})")