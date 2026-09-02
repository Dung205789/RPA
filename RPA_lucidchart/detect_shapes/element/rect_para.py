import cv2
import numpy as np

def is_rectangle_or_parallelogram(approx):
    """
    Kiểm tra xem contour có phải là hình chữ nhật hoặc hình bình hành không
    
    Điều kiện:
    - Phải có 4 đỉnh
    - 1 trong 2 cặp cạnh đối diện phải nằm ngang (so với trục X)
    - 2 cặp cạnh đối diện đôi một song song
    - Nếu có 1 góc vuông → HÌNH CHỮ NHẬT
    - Nếu không có góc vuông → HÌNH BÌNH HÀNH
    
    Returns:
        'rectangle' nếu là hình chữ nhật
        'parallelogram' nếu là hình bình hành
        None nếu không phải cả hai
    """
    if len(approx) != 4:
        return None
    
    # Lấy 4 đỉnh
    pts = approx.reshape(4, 2).astype(float)
    
    # ===== KIỂM TRA CÓ ÍT NHẤT 1 CẶP CẠNH ĐỐI DIỆN NẰM NGANG =====
    edges = []
    for i in range(4):
        next_i = (i + 1) % 4
        edge_vector = pts[next_i] - pts[i]
        edges.append(edge_vector)
    
    # Ngưỡng để coi là "nằm ngang" (độ chênh lệch Y nhỏ)
    horizontal_threshold = 10  # pixels
    
    # Kiểm tra các cặp cạnh đối diện
    has_horizontal_pair = False
    for i in range(4):
        opposite_i = (i + 2) % 4  # Cạnh đối diện
        
        # Cạnh nằm ngang = độ chênh lệch Y giữa 2 đầu mút < ngưỡng
        edge_i_horizontal = abs(edges[i][1]) < horizontal_threshold
        edge_opposite_horizontal = abs(edges[opposite_i][1]) < horizontal_threshold
        
        # Nếu cả 2 cạnh đối diện đều nằm ngang
        if edge_i_horizontal and edge_opposite_horizontal:
            has_horizontal_pair = True
            break
    
    if not has_horizontal_pair:
        return None  # Không thỏa điều kiện có cặp cạnh nằm ngang
    
    # ===== KIỂM TRA 2 CẶP CẠNH ĐỐI DIỆN SONG SONG =====
    # Cặp 1: cạnh 0 và cạnh 2 (đối diện)
    # Cặp 2: cạnh 1 và cạnh 3 (đối diện)
    
    parallel_threshold = 0.01  # Ngưỡng cho độ song song (cos góc giữa 2 vector)
    
    # Kiểm tra cặp 1 (cạnh 0 và cạnh 2)
    edge0 = edges[0]
    edge2 = edges[2]
    
    # Chuẩn hóa vector
    edge0_norm = edge0 / (np.linalg.norm(edge0) + 1e-10)
    edge2_norm = edge2 / (np.linalg.norm(edge2) + 1e-10)
    
    # Tính cos góc (tích vô hướng của 2 vector đã chuẩn hóa)
    # Song song nghĩa là cos = ±1 (góc 0° hoặc 180°)
    cos_pair1 = abs(np.dot(edge0_norm, edge2_norm))
    
    # Kiểm tra cặp 2 (cạnh 1 và cạnh 3)
    edge1 = edges[1]
    edge3 = edges[3]
    
    edge1_norm = edge1 / (np.linalg.norm(edge1) + 1e-10)
    edge3_norm = edge3 / (np.linalg.norm(edge3) + 1e-10)
    
    cos_pair2 = abs(np.dot(edge1_norm, edge3_norm))
    
    # Cả 2 cặp đều phải song song (cos gần 1)
    if cos_pair1 < (1 - parallel_threshold) or cos_pair2 < (1 - parallel_threshold):
        return None  # Không song song
    
    # ===== KIỂM TRA GÓC VUÔNG =====
    # Tính 4 góc tại 4 đỉnh
    angles = []
    for i in range(4):
        prev_i = (i - 1) % 4
        next_i = (i + 1) % 4
        
        # Vector từ đỉnh hiện tại đến đỉnh trước và sau
        v1 = pts[prev_i] - pts[i]
        v2 = pts[next_i] - pts[i]
        
        # Chuẩn hóa
        v1_norm = v1 / (np.linalg.norm(v1) + 1e-10)
        v2_norm = v2 / (np.linalg.norm(v2) + 1e-10)
        
        # Tính cos góc
        cos_angle = np.dot(v1_norm, v2_norm)
        
        # Chuyển sang độ
        angle = np.arccos(np.clip(cos_angle, -1, 1)) * 180 / np.pi
        angles.append(angle)
    
    # Kiểm tra có ít nhất 1 góc vuông (90° ± 10°)
    right_angle_threshold = 10  # độ
    has_right_angle = any(abs(angle - 90) < right_angle_threshold for angle in angles)
    
    if has_right_angle:
        return 'rectangle'
    else:
        return 'parallelogram'


def has_rectangle_or_parallelogram(image):
    """
    Kiểm tra xem ảnh có chứa hình chữ nhật hoặc hình bình hành hay không.
    
    Args:
        image: Ảnh đầu vào (numpy array, định dạng BGR từ OpenCV)
    
    Returns:
        bool: True nếu ảnh chứa ít nhất một hình chữ nhật hoặc hình bình hành, False nếu không
    """
    if image is None:
        return False
    
    # Chuyển sang ảnh xám
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Phát hiện cạnh
    edges = cv2.Canny(gray, 50, 150)
    
    # Tìm contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        # Lọc các contour quá nhỏ
        area = cv2.contourArea(contour)
        if area < 100:
            continue
        
        # Xấp xỉ contour
        epsilon = 0.04 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Kiểm tra hình dạng
        if is_rectangle_or_parallelogram(approx):
            return True
    
    return False

if __name__ == "__main__":
    # Ví dụ sử dụng
    image_path = "path/to/your/image.png"  # Thay bằng đường dẫn ảnh của bạn
    img = cv2.imread(image_path)
    if has_rectangle_or_parallelogram(img):
        print("✅ Ảnh chứa hình chữ nhật hoặc hình bình hành!")
    else:
        print("❌ Ảnh không chứa hình chữ nhật hoặc hình bình hành!")