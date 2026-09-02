import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from detect_shapes.canvas.diamond import detect_diamond
from detect_shapes.canvas.ellipse import detect_ellipse
from detect_shapes.canvas.rect_para import detect_rect_para

def check_canvas(image_path, shape_type, output_folder="detect_img"):
    """
    Phát hiện hình dạng lớn nhất trong ảnh dựa trên loại hình được chỉ định.
    
    Args:
        image_path (str): Đường dẫn đến ảnh đầu vào
        shape_type (str): Loại hình ('diamond', 'ellipse', 'rect_para')
        output_folder (str): Folder để lưu ảnh kết quả (mặc định: detect_img)
    
    Returns:
        tuple: Tọa độ (x, y) của giao điểm đường chéo (diamond, rect_para) hoặc trung tâm (ellipse),
               hoặc None nếu không tìm thấy
    """
    shape_type = shape_type.lower()
    valid_shapes = ['diamond', 'ellipse', 'rect_para']
    
    if shape_type not in valid_shapes:
        print(f"❌ Loại hình không hợp lệ: {shape_type}. Chọn một trong: {valid_shapes}")
        return None
    
    if not os.path.exists(image_path):
        print(f"❌ Không tìm thấy file: {image_path}")
        return None
    
    print(f"🔍 Đang kiểm tra hình {shape_type} trong ảnh: {image_path}")
    
    if shape_type == 'diamond':
        return detect_diamond(image_path, output_folder)
    elif shape_type == 'ellipse':
        return detect_ellipse(image_path, output_folder)
    elif shape_type == 'rect_para':
        return detect_rect_para(image_path, output_folder)

if __name__ == "__main__":
    # Ví dụ sử dụng
    image_path = "detect_img/diff_3_4.png"
    shape_type = "rect_para"  # Có thể thay bằng 'ellipse' hoặc 'rect_para'
    
    coordinates = check_canvas(image_path, shape_type)
    if coordinates:
        print(f"📍 Tọa độ {'giao điểm đường chéo' if shape_type in ['diamond', 'rect_para'] else 'trung tâm'}: {coordinates}")