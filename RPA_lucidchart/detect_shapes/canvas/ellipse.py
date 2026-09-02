import cv2
import numpy as np
import os

def is_ellipse_shape(contour, img_shape):
    """
    Kiểm tra xem contour có phải là hình ellipse không
    - Sử dụng Tỷ lệ diện tích (Ellipse lý thuyết vs. Contour thực tế) để xác nhận
    """
    if len(contour) < 5:
        return False, None
    
    try:
        ellipse = cv2.fitEllipse(contour)
        (x, y), (MA, ma), goc = ellipse
        
        if MA < ma:
            MA, ma = ma, MA
        
        if MA < 30 or ma < 30:
            return False, None
        
        ty_le = MA / ma if ma > 0 else 0
        if ty_le > 8: 
            return False, None
        
        dien_tich_ellipse = np.pi * (MA / 2) * (ma / 2)
        dien_tich_contour = cv2.contourArea(contour)
        
        if dien_tich_contour > 0:
            ty_le_dien_tich = dien_tich_ellipse / dien_tich_contour
            if 0.5 < ty_le_dien_tich < 1.5:
                return True, ellipse
        
        return False, None
        
    except:
        return False, None

def preprocess_image_for_dashed_shapes(img):
    """
    Tiền xử lý ảnh: Phân ngưỡng, Giãn nở mạnh để kết nối nét đứt/chấm tròn, sau đó chạy Canny.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    # Giãn nở (Dilation) mạnh mẽ để kết nối các nét đứt và chấm tròn
    kernel_dilate = np.ones((10, 10), np.uint8) 
    dilated = cv2.dilate(thresh, kernel_dilate, iterations=1)
    
    # Phát hiện cạnh (Canny) trên ảnh đã được nối (dilated)
    edges = cv2.Canny(dilated, 50, 150)
    
    return edges

def detect_ellipse(image_path, output_folder="detect_img"):
    """
    Phát hiện hình ellipse lớn nhất trong ảnh và trả về tọa độ trung tâm.
    Lưu ảnh kết quả với trung tâm đánh dấu bằng chấm đỏ vào folder detect_img.

    Args:
        image_path (str): Đường dẫn đến ảnh đầu vào
        output_folder (str): Folder để lưu ảnh kết quả (mặc định: detect_img)

    Returns:
        tuple: (x, y) tọa độ trung tâm của hình ellipse lớn nhất, hoặc None nếu không tìm thấy
    """
    # Kiểm tra file có tồn tại không
    if not os.path.exists(image_path):
        print(f"❌ Không tìm thấy file: {image_path}")
        return None
    
    # Đọc ảnh
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Không thể đọc ảnh: {image_path}")
        return None
    
    # Tạo folder đầu ra nếu chưa tồn tại
    os.makedirs(output_folder, exist_ok=True)
    
    # Tạo bản sao để vẽ
    output = img.copy()
    
    # Tiền xử lý và phát hiện cạnh
    edges = preprocess_image_for_dashed_shapes(img)
    
    # Tìm contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Biến lưu trữ ellipse lớn nhất
    largest_ellipse = None
    max_area = 0
    largest_center = None
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 500:  # Bỏ qua contour nhỏ
            continue
        
        # Kiểm tra có phải ellipse không
        is_ellipse, ellipse_params = is_ellipse_shape(contour, img.shape)
        
        if is_ellipse and ellipse_params is not None:
            if area > max_area:
                max_area = area
                largest_ellipse = ellipse_params
                # Tính trung tâm
                (x, y), _, _ = ellipse_params
                largest_center = (int(x), int(y))
    
    # Xử lý kết quả
    if largest_ellipse is not None:
        # Vẽ ellipse lớn nhất (màu xanh lá)
        cv2.ellipse(output, largest_ellipse, (0, 255, 0), 1)
        # Vẽ trung tâm bằng chấm đỏ
        cv2.circle(output, largest_center, 2, (0, 0, 255), -1)
        
        # Lưu ảnh kết quả
        output_path = os.path.join(output_folder, "ellipse_detected.png")
        cv2.imwrite(output_path, output)
        print(f"✅ Phát hiện hình ellipse lớn nhất! Tọa độ trung tâm: {largest_center}")
        print(f"📸 Đã lưu ảnh kết quả tại: {output_path}")
        
        return largest_center
    else:
        print("❌ Không phát hiện thấy hình ellipse trong ảnh!")
        return None

if __name__ == "__main__":
    # Ví dụ sử dụng
    image_path = r"C:\Users\HP\OneDrive\Desktop\test_templatematching\img_test\elip_pro_lc.png"
    center = detect_ellipse(image_path)
    if center:
        print(f"Tọa độ trung tâm hình ellipse lớn nhất: {center}")