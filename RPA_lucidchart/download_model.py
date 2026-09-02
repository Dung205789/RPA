# "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selenium\ChromeProfile"
import stanza
from sentence_transformers import SentenceTransformer
import easyocr
import os
import logging

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hàm tạo thư mục nếu chưa tồn tại
def ensure_directory(directory):
    try:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Đã tạo hoặc sử dụng thư mục: {directory}")
    except Exception as e:
        logger.error(f"Lỗi khi tạo thư mục {directory}: {e}")
        raise

# Tải model tiếng Anh cho stanza
model_dir = os.path.join("src", "main", "resources", "models", "stanza")
ensure_directory(model_dir)
try:
    logger.info("Đang tải mô hình stanza tiếng Anh...")
    stanza.download("en", model_dir=model_dir)
    logger.info("Tải mô hình stanza thành công.")
except Exception as e:
    logger.error(f"Lỗi khi tải mô hình stanza: {e}")
    raise

# Tải mô hình SentenceTransformer
sentence_transformer_dir = os.path.join("src", "main", "resources", "models", "sentence_transformers", "paraphrase-multilingual-MiniLM-L12-v2")
ensure_directory(sentence_transformer_dir)
try:
    logger.info("Đang tải mô hình SentenceTransformer...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    model.save(sentence_transformer_dir)
    logger.info("Tải và lưu mô hình SentenceTransformer thành công.")
except Exception as e:
    logger.error(f"Lỗi khi tải mô hình SentenceTransformer: {e}")
    raise

# # Tải mô hình EasyOCR
# easyocr_model_dir = os.path.join("src", "main", "resources", "models", "easyocr")
# ensure_directory(easyocr_model_dir)
# try:
#     logger.info("Đang khởi tạo EasyOCR reader...")
#     languages = ['vi', 'en']
#     reader = easyocr.Reader(
#         lang_list=languages,
#         gpu=False,
#         model_storage_directory=easyocr_model_dir,
#         download_enabled=True,
#         verbose=True
#     )
#     logger.info("Khởi tạo EasyOCR reader thành công.")
# except Exception as e:
#     logger.error(f"Lỗi khi khởi tạo EasyOCR reader: {e}")
#     raise