import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

def sift_match_and_locate(template_path, screenshot_path):
    # 1. Kiểm tra sự tồn tại của file
    if not os.path.exists(template_path):
        print(f"Lỗi: Không tìm thấy file template tại '{template_path}'")
        return
    if not os.path.exists(screenshot_path):
        print(f"Lỗi: Không tìm thấy file screenshot tại '{screenshot_path}'")
        return

    # 2. Đọc ảnh
    # SIFT hoạt động tốt nhất trên ảnh xám (grayscale)
    img_template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    img_screenshot = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
    
    # Đọc ảnh màu để vẽ kết quả cuối cùng cho đẹp
    img_screenshot_color = cv2.imread(screenshot_path)

    if img_template is None or img_screenshot is None:
        print("Lỗi: Không thể đọc định dạng ảnh.")
        return

    # 3. Khởi tạo SIFT detector
    sift = cv2.SIFT_create()

    # Tìm Keypoints và Descriptors
    kp1, des1 = sift.detectAndCompute(img_template, None)
    kp2, des2 = sift.detectAndCompute(img_screenshot, None)

    print(f"Template: {len(kp1)} keypoints")
    print(f"Screenshot: {len(kp2)} keypoints")

    # 4. Sử dụng FLANN Matcher để khớp đặc trưng
    # FLANN nhanh hơn và hiệu quả hơn Brute-Force cho SIFT
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50) # Kiểm tra 50 lần (độ chính xác vs tốc độ)
    
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    
    # Tìm 2 điểm khớp tốt nhất cho mỗi descriptor (k=2) để áp dụng ratio test
    matches = flann.knnMatch(des1, des2, k=2)

    # 5. Lọc các điểm khớp tốt (Good Matches) theo tỷ lệ Lowe
    # Giữ lại điểm khớp nếu khoảng cách của nó nhỏ hơn 0.7 lần điểm khớp thứ nhì
    good_matches = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good_matches.append(m)

    print(f"Số lượng điểm khớp tốt (Good matches): {len(good_matches)}")

    # Quy định số lượng điểm khớp tối thiểu để coi là tìm thấy ảnh
    MIN_MATCH_COUNT = 10

    if len(good_matches) > MIN_MATCH_COUNT:
        # 6. Tìm ma trận Homography để định vị vật thể
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        # Sử dụng RANSAC để loại bỏ ngoại lai (outliers)
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        matchesMask = mask.ravel().tolist()

        # Lấy kích thước ảnh gốc
        h, w = img_template.shape
        
        # Tạo khung hình chữ nhật bao quanh ảnh gốc
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        
        # Biến đổi phối cảnh để tìm vị trí tương ứng trên ảnh screenshot
        if M is not None:
            dst = cv2.perspectiveTransform(pts, M)
            
            # Vẽ khung chữ nhật lên ảnh kết quả (Màu xanh lá, độ dày 3)
            img_result = cv2.polylines(img_screenshot_color, [np.int32(dst)], True, (0, 255, 0), 3, cv2.LINE_AA)
            print("Đã tìm thấy ảnh và vẽ khung đánh dấu!")
        else:
            print("Không thể tính toán ma trận Homography (có thể do các điểm thẳng hàng).")
            img_result = img_screenshot_color

    else:
        print(f"Không tìm thấy đủ điểm khớp tốt - Cần ít nhất {MIN_MATCH_COUNT} điểm.")
        matchesMask = None
        img_result = img_screenshot_color

    # 7. Hiển thị kết quả bằng Matplotlib
    draw_params = dict(matchColor=(0, 255, 0), # Màu xanh cho các điểm khớp đúng
                       singlePointColor=None,
                       matchesMask=matchesMask, # Chỉ vẽ inliers
                       flags=2)

    img_matches = cv2.drawMatches(img_template, kp1, img_result, kp2, good_matches, None, **draw_params)

    plt.figure(figsize=(20, 10))
    plt.imshow(cv2.cvtColor(img_matches, cv2.COLOR_BGR2RGB))
    plt.title("Ket qua nhan dien SIFT")
    plt.axis('off')
    plt.show()

if __name__ == "__main__":
    # Đường dẫn file theo yêu cầu của bạn
    # Lưu ý: Nếu chạy trên Windows, hãy đảm bảo đường dẫn chính xác
    template = os.path.join("img_test", "template2.png")
    screenshot = os.path.join("img_test", "screenshot.png")
    
    sift_match_and_locate(template, screenshot)