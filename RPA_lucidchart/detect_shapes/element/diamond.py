import cv2
import numpy as np

def is_diamond_shape(approx):
    """
    Kiểm tra xem contour có phải là hình thoi không
    - Phải có 4 đỉnh
    - 2 đường chéo phải vuông góc với nhau
    - 2 đường chéo phải cắt nhau tại trung điểm
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
    horizontal_threshold = 10  # pixels
    
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
    if cos_angle < 0.3:  # Cho phép sai số
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
            if std_dev < 0.2:  # Các cạnh gần bằng nhau
                return True
    
    return False

def has_diamond(img):
    """
    Kiểm tra xem ảnh có chứa hình thoi không.

    Args:
        img (numpy.ndarray): Ảnh đầu vào (đã được đọc bằng cv2)

    Returns:
        bool: True nếu phát hiện hình thoi, False nếu không
    """
    if img is None:
        return False
    
    # Chuyển sang ảnh xám
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Phát hiện cạnh
    edges = cv2.Canny(gray, 50, 150)
    
    # Tìm contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        # Lọc các contour quá nhỏ
        area = cv2.contourArea(contour)
        if area < 100:  # Bỏ qua các hình quá nhỏ
            continue
        
        # Xấp xỉ contour thành đa giác
        epsilon = 0.04 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Kiểm tra có phải hình thoi không
        if is_diamond_shape(approx):
            return True
    
    return False

if __name__ == "__main__":
    # Ví dụ sử dụng
    image_path = "path/to/your/image.png"  # Thay bằng đường dẫn ảnh của bạn
    img = cv2.imread(image_path)
    if has_diamond(img):
        print("✅ Ảnh chứa hình thoi!")
    else:
        print("❌ Ảnh không chứa hình thoi!")