import cv2
import numpy as np

def is_ellipse_shape(contour):
    """
    Kiểm tra xem contour có phải là hình ellipse không
    - Cần ít nhất 5 điểm để fit ellipse
    - Kiểm tra độ phù hợp giữa contour và ellipse
    - Kiểm tra tỷ lệ trục để loại bỏ hình quá méo
    """
    if len(contour) < 5:
        return False, None
    
    try:
        # Fit ellipse vào contour
        ellipse = cv2.fitEllipse(contour)
        (x, y), (MA, ma), goc = ellipse
        
        # Kiểm tra kích thước hợp lý
        if MA < 20 or ma < 20:
            return False, None
        
        # Kiểm tra tỷ lệ trục (loại bỏ ellipse quá méo)
        ty_le = MA / ma if ma > 0 else 0
        if ty_le > 5:  # Quá méo, có thể là đoạn thẳng
            return False, None
        
        # Tính diện tích của ellipse lý thuyết
        dien_tich_ellipse = np.pi * (MA / 2) * (ma / 2)
        
        # Tính diện tích của contour thực tế
        dien_tich_contour = cv2.contourArea(contour)
        
        # Kiểm tra độ phù hợp (diện tích contour ~ diện tích ellipse)
        if dien_tich_contour > 0:
            ty_le_dien_tich = dien_tich_ellipse / dien_tich_contour
            # Cho phép sai số 20-30%
            if 0.7 < ty_le_dien_tich < 1.3:
                return True, ellipse
        
        return False, None
        
    except:
        return False, None

def has_ellipse(image):
    """
    Kiểm tra xem ảnh có chứa hình ellipse hay không.
    
    Args:
        image: Ảnh đầu vào (numpy array, định dạng BGR từ OpenCV)
    
    Returns:
        bool: True nếu ảnh chứa ít nhất một hình ellipse, False nếu không
    """
    if image is None:
        return False
    
    # Chuyển sang ảnh xám
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Làm mờ để giảm nhiễu
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Phát hiện cạnh
    edges = cv2.Canny(blurred, 50, 150)
    
    # Tìm contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        # Lọc các contour quá nhỏ
        area = cv2.contourArea(contour)
        if area < 100:
            continue
        
        # Kiểm tra có phải ellipse không
        if is_ellipse_shape(contour):
            return True
    
    return False

if __name__ == "__main__":
    # Ví dụ sử dụng
    image_path = "path/to/your/image.png"  # Thay bằng đường dẫn ảnh của bạn
    img = cv2.imread(image_path)
    if has_ellipse(img):
        print("✅ Ảnh chứa hình ellipse!")
    else:
        print("❌ Ảnh không chứa hình ellipse!")