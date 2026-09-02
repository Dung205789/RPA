import cv2
import numpy as np
import requests
from io import BytesIO
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from detect_shapes.element.diamond import has_diamond
from detect_shapes.element.ellipse import has_ellipse
from detect_shapes.element.rect_para import has_rectangle_or_parallelogram

def check_element(image_url):
    """
    Kiểm tra hình dạng trong ảnh từ URL và trả về loại hình dạng.

    Args:
        image_url (str): URL của ảnh 

    Returns:
        str: Loại hình dạng ('diamond', 'ellipse', 'rect_para', 'unknown')
    """
    try:
        # Tải ảnh từ URL
        response = requests.get(image_url)
        if response.status_code != 200:
            return "unknown"

        # Chuyển nội dung ảnh thành numpy array
        img_array = np.frombuffer(response.content, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            return "unknown"

        # Kiểm tra từng loại hình dạng
        if has_diamond(img):
            return "diamond"
        elif has_rectangle_or_parallelogram(img):
            return "rect_para"
        elif has_ellipse(img):
            return "ellipse"
        else:
            return "unknown"

    except Exception as e:
        print(f"Lỗi khi xử lý ảnh từ URL {image_url}: {str(e)}")
        return "unknown"

if __name__ == "__main__":
    # Ví dụ sử dụng
    test_url = "http://localhost:8123/uploads/stepImg/objectImg/objectImg__160__24__20251116.png"
    result = check_element(test_url)
    print(f"Kết quả: {result}")