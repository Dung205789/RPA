import cv2
import numpy as np
import os
import sys

def log(*args, **kwargs):
    """In log ra stderr"""
    print(*args, file=sys.stderr, **kwargs)

def match_images_with_sift(screenshot_path, template_path, output_path="img_test/matched_result.png", min_matches=8):
    """
    Tìm và đánh dấu phần khớp giữa template và screenshot bằng SIFT/ORB
    
    Args:
        screenshot_path: Đường dẫn ảnh screenshot đầy đủ
        template_path: Đường dẫn ảnh template cần tìm
        output_path: Đường dẫn lưu ảnh kết quả đã đánh dấu
        min_matches: Số lượng matches tối thiểu để xác định tìm thấy (mặc định: 8)
    
    Returns:
        dict: {
            'success': bool,
            'num_matches': int,
            'bounding_box': tuple (x, y, width, height) hoặc None,
            'center': tuple (x, y) hoặc None,
            'output_path': str
        }
    """
    
    # Kiểm tra file tồn tại
    if not os.path.exists(screenshot_path):
        log(f"❌ Không tìm thấy file: {screenshot_path}")
        return {'success': False, 'num_matches': 0, 'bounding_box': None, 'center': None, 'output_path': None}
    
    if not os.path.exists(template_path):
        log(f"❌ Không tìm thấy file: {template_path}")
        return {'success': False, 'num_matches': 0, 'bounding_box': None, 'center': None, 'output_path': None}
    
    # Đọc ảnh
    log("📖 Đọc ảnh...")
    img_screenshot = cv2.imread(screenshot_path)
    img_template = cv2.imread(template_path)
    
    if img_screenshot is None:
        log(f"❌ Không đọc được ảnh screenshot: {screenshot_path}")
        return {'success': False, 'num_matches': 0, 'bounding_box': None, 'center': None, 'output_path': None}
    
    if img_template is None:
        log(f"❌ Không đọc được ảnh template: {template_path}")
        return {'success': False, 'num_matches': 0, 'bounding_box': None, 'center': None, 'output_path': None}
    
    log(f"   Screenshot: {img_screenshot.shape[1]}x{img_screenshot.shape[0]}")
    log(f"   Template: {img_template.shape[1]}x{img_template.shape[0]}")
    
    # Chuyển sang ảnh xám
    img_gray = cv2.cvtColor(img_screenshot, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(img_template, cv2.COLOR_BGR2GRAY)
    
    # Thử dùng SIFT trước, nếu không được thì dùng ORB
    log("🔍 Khởi tạo detector...")
    try:
        detector = cv2.SIFT_create(nfeatures=0)
        method = "SIFT"
        log("   ✓ Sử dụng SIFT")
    except Exception as e:
        log(f"   ⚠️ SIFT không khả dụng: {e}")
        detector = cv2.ORB_create(nfeatures=0)
        method = "ORB"
        log("   ✓ Sử dụng ORB")
    
    # Phát hiện keypoints và descriptors
    log("🔎 Phát hiện đặc trưng...")
    kp1, des1 = detector.detectAndCompute(template_gray, None)
    kp2, des2 = detector.detectAndCompute(img_gray, None)
    
    if des1 is None or des2 is None:
        log(f"❌ {method} không tìm thấy đặc trưng")
        return {'success': False, 'num_matches': 0, 'bounding_box': None, 'center': None, 'output_path': None}
    
    log(f"   Template keypoints: {len(kp1)}")
    log(f"   Screenshot keypoints: {len(kp2)}")
    
    # Matching
    log("🔗 Matching descriptors...")
    if method == "SIFT":
        # FLANN matcher cho SIFT
        index_params = dict(algorithm=1, trees=5)
        search_params = dict(checks=100)
        matcher = cv2.FlannBasedMatcher(index_params, search_params)
    else:
        # BFMatcher cho ORB
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    
    try:
        matches = matcher.knnMatch(des1, des2, k=2)
    except Exception as e:
        log(f"❌ Lỗi khi matching: {e}")
        return {'success': False, 'num_matches': 0, 'bounding_box': None, 'center': None, 'output_path': None}
    
    # Lọc matches tốt bằng Lowe's ratio test
    log("✂️ Lọc matches tốt (Lowe's ratio test)...")
    good_matches = []
    for match_pair in matches:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < 0.8 * n.distance:
                good_matches.append(m)
    
    log(f"   ✓ Số matches tốt: {len(good_matches)}/{len(matches)}")
    
    # Kiểm tra đủ matches không
    if len(good_matches) < min_matches:
        log(f"❌ Không đủ matches (cần ít nhất {min_matches})")
        return {'success': False, 'num_matches': len(good_matches), 'bounding_box': None, 'center': None, 'output_path': None}
    
    # Tìm homography
    log("📐 Tính toán Homography...")
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    
    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    
    if M is None:
        log("❌ Không tính được Homography matrix")
        return {'success': False, 'num_matches': len(good_matches), 'bounding_box': None, 'center': None, 'output_path': None}
    
    # Tính số inliers
    inliers = np.sum(mask)
    log(f"   ✓ Inliers: {inliers}/{len(good_matches)}")
    
    # Tìm vị trí template trong screenshot
    h, w = template_gray.shape
    pts = np.float32([[0, 0], [0, h], [w, h], [w, 0]]).reshape(-1, 1, 2)
    dst = cv2.perspectiveTransform(pts, M)
    
    # Vẽ kết quả
    log("🎨 Vẽ kết quả...")
    img_result = img_screenshot.copy()
    
    # Vẽ polygon bao quanh vùng tìm thấy (màu xanh lá)
    img_result = cv2.polylines(img_result, [np.int32(dst)], True, (0, 255, 0), 3)
    
    # Tính bounding box và center
    x, y, w_box, h_box = cv2.boundingRect(np.int32(dst))
    center_x = x + w_box // 2
    center_y = y + h_box // 2
    
    # Vẽ bounding box (màu vàng)
    cv2.rectangle(img_result, (x, y), (x + w_box, y + h_box), (0, 255, 255), 2)
    
    # Vẽ center point (màu đỏ)
    cv2.circle(img_result, (center_x, center_y), 8, (0, 0, 255), -1)
    cv2.circle(img_result, (center_x, center_y), 12, (0, 0, 255), 2)
    
    # Vẽ text thông tin
    info_text = f"{method}: {len(good_matches)} matches ({inliers} inliers)"
    cv2.putText(img_result, info_text, (x, y - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Vẽ tọa độ center
    coord_text = f"Center: ({center_x}, {center_y})"
    cv2.putText(img_result, coord_text, (x, y + h_box + 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    # Lưu ảnh kết quả
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, img_result)
    log(f"💾 Đã lưu kết quả: {output_path}")
    
    # Tạo ảnh matches để debug (optional)
    debug_path = output_path.replace('.png', '_matches.png')
    img_matches = cv2.drawMatches(img_template, kp1, img_screenshot, kp2, 
                                   good_matches[:50], None, 
                                   flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    cv2.imwrite(debug_path, img_matches)
    log(f"💾 Đã lưu debug matches: {debug_path}")
    
    result = {
        'success': True,
        'method': method,
        'num_matches': len(good_matches),
        'num_inliers': int(inliers),
        'bounding_box': (x, y, w_box, h_box),
        'center': (center_x, center_y),
        'output_path': output_path,
        'debug_path': debug_path
    }
    
    log("\n" + "="*60)
    log("✅ KẾT QUẢ THÀNH CÔNG")
    log(f"   Phương pháp: {method}")
    log(f"   Số matches: {len(good_matches)} ({inliers} inliers)")
    log(f"   Bounding box: x={x}, y={y}, w={w_box}, h={h_box}")
    log(f"   Center: ({center_x}, {center_y})")
    log("="*60)
    
    return result


if __name__ == "__main__":
    # Đường dẫn mặc định
    screenshot_path = "img_test/screenshot.png"
    template_path = "img_test/template2.png"
    output_path = "img_test/matched_result.png"
    
    # Cho phép truyền tham số từ command line
    if len(sys.argv) > 1:
        screenshot_path = sys.argv[1]
    if len(sys.argv) > 2:
        template_path = sys.argv[2]
    if len(sys.argv) > 3:
        output_path = sys.argv[3]
    
    print(f"\n🚀 BẮT ĐẦU MATCHING")
    print(f"   Screenshot: {screenshot_path}")
    print(f"   Template: {template_path}")
    print(f"   Output: {output_path}\n")
    
    # Thực hiện matching
    result = match_images_with_sift(screenshot_path, template_path, output_path)
    
    # In kết quả
    if result['success']:
        print(f"\n✅ Tìm thấy template trong screenshot!")
        print(f"   Tọa độ center: {result['center']}")
        print(f"   Kích thước vùng tìm thấy: {result['bounding_box'][2]}x{result['bounding_box'][3]}")
        print(f"   Đã lưu kết quả tại: {result['output_path']}")
        sys.exit(0)
    else:
        print(f"\n❌ Không tìm thấy template trong screenshot")
        print(f"   Số matches: {result['num_matches']}")
        sys.exit(1)