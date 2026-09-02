import cv2
import numpy as np
import os

def create_difference_mask(img1_path, img2_path, X, Y, output_folder="detect_img"):
    # Kiểm tra file
    if not os.path.exists(img1_path) or not os.path.exists(img2_path):
        print("❌ File không tồn tại")
        return None
    
    # Đọc ảnh
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)
    if img1 is None or img2 is None:
        print("❌ Không thể đọc ảnh")
        return None
    
    # Resize nếu khác kích thước
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    
    # Chuyển sang ảnh xám
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # Tính khác biệt mới mà ảnh 2 có
    diff = cv2.subtract(gray1, gray2)
    
    # Ngưỡng Otsu → tạo mask khác nhau
    _, diff_mask = cv2.threshold(diff, 90, 255, cv2.THRESH_BINARY_INV)
    
    # Tạo thư mục detect_img nếu chưa tồn tại
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Tạo tên file mask động với X và Y
    mask_filename = f"diff_{X}_{Y}.png"
    mask_path = os.path.join(output_folder, mask_filename)
    
    # Lưu mask
    cv2.imwrite(mask_path, diff_mask)
    print("Đã lưu mask tại:", mask_path)
    return diff_mask

if __name__ == "__main__":
    img1_path = r"D:\otherBE\screenshots\screenshot_step_0.png"
    img2_path = r"D:\otherBE\screenshots\screenshot_step_5.png"
    X = 68  # Ví dụ số X do người dùng truyền vào
    Y = 69  # Ví dụ số Y do người dùng truyền vào
    create_difference_mask(img1_path, img2_path, X, Y)