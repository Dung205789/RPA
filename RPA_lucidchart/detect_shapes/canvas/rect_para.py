# File: detect_shapes/element/rectangle.py
import cv2
import numpy as np
import os

def preprocess_image(img):
    """Tiền xử lý ảnh - Tăng cường cạnh mạnh"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Tăng tương phản
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Khử nhiễu
    denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
    
    # Làm sắc nét
    kernel_sharpen = np.array([[-1,-1,-1], [-1, 9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(denoised, -1, kernel_sharpen)
    
    # Adaptive threshold
    thresh = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # Làm liền các đường bị đứt
    kernel = np.ones((3, 3), np.uint8)
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=3)
    dilated = cv2.dilate(closed, kernel, iterations=2)
    
    # Phát hiện cạnh
    edges = cv2.Canny(dilated, 20, 80)
    
    # Nối các cạnh bị đứt theo nhiều hướng
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 1))
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 7))
    kernel_d = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_h, iterations=1)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_v, iterations=1)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_d, iterations=2)
    edges = cv2.dilate(edges, kernel, iterations=1)
    
    return edges

def is_rectangle_or_parallelogram(approx):
    """
    Kiểm tra hình chữ nhật hoặc hình bình hành
    
    Returns: 'rectangle', 'parallelogram', hoặc None
    """
    if len(approx) != 4:
        return None
    
    pts = approx.reshape(4, 2).astype(float)
    
    # Tính các cạnh
    edges = []
    edge_lengths = []
    for i in range(4):
        next_i = (i + 1) % 4
        edge_vector = pts[next_i] - pts[i]
        edge_length = np.linalg.norm(edge_vector)
        edges.append(edge_vector)
        edge_lengths.append(edge_length)
    
    # Lọc hình có cạnh quá ngắn
    if min(edge_lengths) < 10:
        return None
    
    # Kiểm tra 2 cặp cạnh đối diện song song
    edge0_norm = edges[0] / (edge_lengths[0] + 1e-10)
    edge2_norm = edges[2] / (edge_lengths[2] + 1e-10)
    cos_pair1 = abs(np.dot(edge0_norm, edge2_norm))
    
    edge1_norm = edges[1] / (edge_lengths[1] + 1e-10)
    edge3_norm = edges[3] / (edge_lengths[3] + 1e-10)
    cos_pair2 = abs(np.dot(edge1_norm, edge3_norm))
    
    if cos_pair1 < 0.95 or cos_pair2 < 0.95:  # Không song song
        return None
    
    # Kiểm tra độ dài cặp cạnh đối diện
    length_ratio_1 = abs(edge_lengths[0] - edge_lengths[2]) / max(edge_lengths[0], edge_lengths[2])
    length_ratio_2 = abs(edge_lengths[1] - edge_lengths[3]) / max(edge_lengths[1], edge_lengths[3])
    
    if length_ratio_1 > 0.3 or length_ratio_2 > 0.3:
        return None
    
    # Tính góc để phân biệt chữ nhật và bình hành
    angles = []
    for i in range(4):
        prev_i = (i - 1) % 4
        next_i = (i + 1) % 4
        
        v1 = pts[prev_i] - pts[i]
        v2 = pts[next_i] - pts[i]
        
        v1_norm = v1 / (np.linalg.norm(v1) + 1e-10)
        v2_norm = v2 / (np.linalg.norm(v2) + 1e-10)
        
        cos_angle = np.dot(v1_norm, v2_norm)
        angle = np.arccos(np.clip(cos_angle, -1, 1)) * 180 / np.pi
        angles.append(angle)
    
    # Có ít nhất 2 góc vuông → hình chữ nhật
    right_angle_count = sum(1 for angle in angles if abs(angle - 90) < 15)
    
    if right_angle_count >= 2:
        return 'rectangle'
    else:
        # Kiểm tra góc đối diện bằng nhau → hình bình hành
        angle_diff_1 = abs(angles[0] - angles[2])
        angle_diff_2 = abs(angles[1] - angles[3])
        
        if angle_diff_1 < 20 and angle_diff_2 < 20:
            return 'parallelogram'
    
    return None

def find_diagonals_intersection(approx):
    """
    Tính giao điểm của hai đường chéo của hình chữ nhật hoặc hình bình hành
    - Đường chéo 1: nối đỉnh 0 và 2
    - Đường chéo 2: nối đỉnh 1 và 3
    """
    pts = approx.reshape(4, 2).astype(float)
    # Đường chéo 1: (x0, y0) -> (x2, y2)
    p0, p2 = pts[0], pts[2]
    # Đường chéo 2: (x1, y1) -> (x3, y3)
    p1, p3 = pts[1], pts[3]
    
    # Phương trình đường thẳng: ax + by = c
    # Đường chéo 1: (y2 - y0)x - (x2 - x0)y = x0y2 - x2y0
    a1 = p2[1] - p0[1]
    b1 = p0[0] - p2[0]
    c1 = p0[0] * p2[1] - p2[0] * p0[1]
    
    # Đường chéo 2: (y3 - y1)x - (x3 - x1)y = x1y3 - x3y1
    a2 = p3[1] - p1[1]
    b2 = p1[0] - p3[0]
    c2 = p1[0] * p3[1] - p3[0] * p1[1]
    
    # Tính định thức
    det = a1 * b2 - a2 * b1
    if abs(det) < 1e-10:  # Hai đường song song hoặc trùng nhau
        return None
    
    # Tính giao điểm
    x = (b2 * c1 - b1 * c2) / det
    y = (a1 * c2 - a2 * c1) / det
    
    return (int(x), int(y))

def detect_rect_para(image_path, output_folder="detect_img"):
    """
    Phát hiện hình chữ nhật hoặc hình bình hành lớn nhất trong ảnh và trả về tọa độ giao điểm của hai đường chéo.
    Lưu ảnh kết quả với giao điểm đánh dấu bằng chấm đỏ vào folder detect_img.

    Args:
        image_path (str): Đường dẫn đến ảnh đầu vào
        output_folder (str): Folder để lưu ảnh kết quả (mặc định: detect_img)

    Returns:
        tuple: (x, y) tọa độ giao điểm của hai đường chéo của hình lớn nhất, hoặc None nếu không tìm thấy
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
    
    # Tiền xử lý
    edges = preprocess_image(img)
    
    # Tìm contours
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    # Tìm shape lớn nhất
    largest_shape = None
    largest_area = 0
    largest_intersection = None
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 500:  # Diện tích tối thiểu
            continue
        
        perimeter = cv2.arcLength(contour, True)
        epsilon = 0.04 * perimeter  # Sử dụng epsilon cố định để đơn giản
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        shape_type = is_rectangle_or_parallelogram(approx)
        
        if shape_type and area > largest_area:
            largest_shape = approx
            largest_area = area
            # Tính giao điểm của hai đường chéo
            intersection = find_diagonals_intersection(approx)
            if intersection:
                largest_intersection = intersection
    
    # Xử lý kết quả
    if largest_shape is not None and largest_intersection is not None:
        # Vẽ shape lớn nhất
        cv2.drawContours(output, [largest_shape], -1, (0, 255, 0), 1)
        # Vẽ giao điểm bằng chấm đỏ
        cv2.circle(output, largest_intersection, 2, (0, 0, 255), -1)
        
        # Lưu ảnh kết quả
        output_path = os.path.join(output_folder, "rec_para_detected.png")
        cv2.imwrite(output_path, output)
        print(f"✅ Phát hiện {'hình chữ nhật' if shape_type == 'rectangle' else 'hình bình hành'} lớn nhất! Tọa độ giao điểm đường chéo: {largest_intersection}")
        print(f"📸 Đã lưu ảnh kết quả tại: {output_path}")
        
        return largest_intersection
    else:
        print("❌ Không phát hiện thấy hình chữ nhật hoặc hình bình hành trong ảnh!")
        return None

if __name__ == "__main__":
    # Ví dụ sử dụng
    image_path = r"C:\Users\HP\OneDrive\Desktop\test_templatematching\img_test\hbh_pro_lc.png"
    intersection = detect_rect_para(image_path)
    if intersection:
        print(f"Tọa độ giao điểm đường chéo hình lớn nhất: {intersection}")