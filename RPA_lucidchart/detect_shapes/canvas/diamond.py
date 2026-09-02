# File: detect_shapes/element/diamond.py
import cv2
import numpy as np
import os

def is_diamond_shape(approx):
    """
    Kiểm tra xem contour có phải là hình thoi không
    - Phải có 4 đỉnh
    - 2 đường chéo phải vuông góc với nhau
    - 4 cạnh có độ dài gần bằng nhau
    - KHÔNG có 2 cạnh đối diện nằm ngang (so với trục X của ảnh)
    """
    if len(approx) != 4:
        return False
    
    # Lấy 4 đỉnh
    pts = approx.reshape(4, 2)

    # ===== KIỂM TRA 2 CẠNH ĐỐI DIỆN NẰM NGANG =====
    # Tính vector của 4 cạnh
    edges = []
    for i in range(4):
        next_i = (i + 1) % 4
        edge_vector = pts[next_i] - pts[i]
        edges.append(edge_vector)
    
    # Ngưỡng để coi là "nằm ngang" (độ chênh lệch Y nhỏ)
    horizontal_threshold = 10  # pixels (tăng lên để chấp nhận sai số)
    
    # Kiểm tra từng cặp cạnh đối diện
    for i in range(4):
        opposite_i = (i + 2) % 4  # Cạnh đối diện
        
        # Cạnh nằm ngang = độ chênh lệch Y giữa 2 đầu mút < ngưỡng
        edge_i_horizontal = abs(edges[i][1]) < horizontal_threshold
        edge_opposite_horizontal = abs(edges[opposite_i][1]) < horizontal_threshold
        
        # Nếu cả 2 cạnh đối diện đều nằm ngang → LOẠI BỎ
        if edge_i_horizontal and edge_opposite_horizontal:
            return False
        
    # ===== KIỂM TRA 2 ĐƯỜNG CHÉO VUÔNG GÓC =====
    
    # Tính 2 đường chéo
    diag1 = pts[2] - pts[0]  # Đường chéo 1
    diag2 = pts[3] - pts[1]  # Đường chéo 2
    
    # Kiểm tra 2 đường chéo có vuông góc không (tích vô hướng gần 0)
    dot_product = abs(np.dot(diag1, diag2))
    diag1_length = np.linalg.norm(diag1)
    diag2_length = np.linalg.norm(diag2)
    
    # Tránh chia cho 0
    if diag1_length == 0 or diag2_length == 0:
        return False
    
    # Góc giữa 2 đường chéo (cos của góc)
    cos_angle = dot_product / (diag1_length * diag2_length)
    
    # Nếu góc gần 90 độ thì cos gần 0
    if cos_angle < 0.35:  # Cho phép sai số nhiều hơn
        # Kiểm tra 4 cạnh có độ dài gần bằng nhau không
        side1 = np.linalg.norm(pts[1] - pts[0])
        side2 = np.linalg.norm(pts[2] - pts[1])
        side3 = np.linalg.norm(pts[3] - pts[2])
        side4 = np.linalg.norm(pts[0] - pts[3])
        
        sides = [side1, side2, side3, side4]
        avg_side = np.mean(sides)
        
        # Kiểm tra độ lệch chuẩn của các cạnh
        if avg_side > 0:
            std_dev = np.std(sides) / avg_side
            if std_dev < 0.25:  # Cho phép sai số nhiều hơn
                return True
    
    return False

def detect_diamond(image_path, output_folder="detect_img"):
    """
    Phát hiện hình thoi lớn nhất trong ảnh và trả về tọa độ trung tâm.
    Lưu ảnh kết quả với trung tâm đánh dấu bằng chấm đỏ vào folder detect_img.

    Args:
        image_path (str): Đường dẫn đến ảnh đầu vào
        output_folder (str): Folder để lưu ảnh kết quả (mặc định: detect_img)

    Returns:
        tuple: (x, y) tọa độ trung tâm của hình thoi lớn nhất, hoặc None nếu không tìm thấy
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
    
    # Chuyển sang ảnh xám
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Áp dụng Gaussian Blur để giảm nhiễu
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Phát hiện cạnh với nhiều ngưỡng Canny
    edges1 = cv2.Canny(blurred, 30, 100)
    edges2 = cv2.Canny(blurred, 50, 150)
    edges3 = cv2.Canny(blurred, 70, 200)
    edges_combined = cv2.bitwise_or(edges1, cv2.bitwise_or(edges2, edges3))
    
    # Làm dày đường viền
    kernel = np.ones((4, 4), np.uint8)
    edges_dilated = cv2.dilate(edges_combined, kernel, iterations=1)
    
    # Tìm contours
    contours, _ = cv2.findContours(edges_dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    largest_diamond = None
    max_area = 0
    largest_center = None
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 700:
            continue
        
        epsilon = 0.04 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        if is_diamond_shape(approx):
            if area > max_area:
                max_area = area
                largest_diamond = approx
                # Tính trung tâm: trung bình tọa độ 4 đỉnh
                pts = approx.reshape(4, 2)
                center_x = int(np.mean(pts[:, 0]))
                center_y = int(np.mean(pts[:, 1]))
                largest_center = (center_x, center_y)
    
    # Xử lý kết quả
    if largest_diamond is not None:
        # Vẽ hình thoi lớn nhất
        cv2.drawContours(output, [largest_diamond], -1, (0, 255, 0), 1)
        # Vẽ trung tâm bằng chấm đỏ
        cv2.circle(output, largest_center, 2, (0, 0, 255), -1)
        
        # Lưu ảnh kết quả
        output_path = os.path.join(output_folder, "diamond_detected.png")
        cv2.imwrite(output_path, output)
        print(f"✅ Phát hiện hình thoi lớn nhất! Tọa độ trung tâm: {largest_center}")
        print(f"📸 Đã lưu ảnh kết quả tại: {output_path}")
        
        return largest_center
    else:
        print("❌ Không phát hiện thấy hình thoi trong ảnh!")
        return None

if __name__ == "__main__":
    # Ví dụ sử dụng
    image_path = r"C:\Users\HP\OneDrive\Desktop\test_templatematching\img_test\thoi_pro_lc.png"
    center = detect_diamond(image_path)
    if center:
        print(f"Tọa độ trung tâm hình thoi lớn nhất: {center}")