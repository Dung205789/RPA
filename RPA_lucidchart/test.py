from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json

# Kết nối với Chrome đang chạy remote debugging port 9222
chrome_options = Options()
chrome_options.debugger_address = "127.0.0.1:9222"

driver = webdriver.Chrome(options=chrome_options)

# Hàm tạo XPath đầy đủ của một element
def get_full_xpath(element):
    """Trả về XPath tuyệt đối của phần tử"""
    script = """
    function getPathTo(element) {
        if (element.id !== '')
            return 'id("' + element.id + '")';
        if (element === document.body)
            return element.tagName.toLowerCase();

        var ix = 0;
        var siblings = element.parentNode.childNodes;
        for (var i = 0; i < siblings.length; i++) {
            var sibling = siblings[i];
            if (sibling === element)
                return getPathTo(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
            if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                ix++;
        }
    }
    return getPathTo(arguments[0]);
    """
    return driver.execute_script(script, element)

# Hàm in thông tin phần tử khi click
def print_element_info(event):
    element = event['target']
    
    # Lấy thông tin kích thước và vị trí
    size = element.size
    location = element.location
    tag_name = element.tag_name
    try:
        element_id = element.get_attribute("id")
    except:
        element_id = ""
    try:
        class_name = element.get_attribute("class")
    except:
        class_name = ""
    
    xpath = get_full_xpath(element)

    print("\n" + "="*60)
    print(f"ĐÃ CLICK VÀO PHẦN TỬ:")
    print(f"Tag       : {tag_name}")
    print(f"ID        : {element_id}")
    print(f"Class     : {class_name}")
    print(f"Width     : {size['width']} px")
    print(f"Height    : {size['height']} px")
    print(f"Vị trí X  : {location['x']}")
    print(f"Vị trí Y  : {location['y']}")
    print(f"XPath     : {xpath}")
    print("="*60 + "\n")

# Script JavaScript để bắt mọi click trên trang và gửi thông tin về Python
js_inject = """
(function() {
    if (window.__clickListenerInjected) return;
    window.__clickListenerInjected = true;

    document.addEventListener('click', function(e) {
        e.preventDefault();  // Nếu không muốn ngăn hành vi click, bỏ dòng này
        window.__lastClickedElement = e.target;

        // Gửi thông tin element về Python qua console.log dạng JSON đặc biệt
        console.log('%c__ELEMENT_INFO__', 'font-size:0;', JSON.stringify({
            tagName: e.target.tagName,
            id: e.target.id,
            className: e.target.className,
            clientRect: e.target.getBoundingClientRect()
        }));
    }, true);
})();
"""

print("Đang kết nối tới Chrome và inject script bắt click...")
driver.execute_script(js_inject)

print("Đã sẵn sàng! Hãy click thử vào bất kỳ phần tử nào trên trang web.")
print("Thông tin sẽ được in ra ngay tại đây.\n")

# Vòng lặp liên tục kiểm tra console log từ Chrome
last_log = ""
while True:
    try:
        for entry in driver.get_log('browser'):
            message = entry['message']
            if "__ELEMENT_INFO__" in message:
                # Lấy phần JSON sau %c__ELEMENT_INFO__
                json_part = message.split("__ELEMENT_INFO__", 1)[1]
                json_part = json_part.split(";", 1)[1].strip()
                data = json.loads(json_part)

                # Lấy lại element thật từ trang web (vì console.log không trả về element trực tiếp)
                # Ta sẽ tìm element gần nhất có cùng đặc điểm
                # Cách đơn giản: dùng document.elementFromPoint
                js_find = f"""
                (function() {{
                    var el = document.elementFromPoint({data['clientRect']['x'] + 5}, {data['clientRect']['y'] + 5});
                    return el;
                }})()
                """
                element = driver.execute_script(js_find)
                if element:
                    print_element_info({'target': element})
        
        time.sleep(0.2)  # Không chiếm quá nhiều CPU
    except KeyboardInterrupt:
        print("\nDừng chương trình.")
        break
    except Exception as e:
        # Có thể Chrome bị ngắt kết nối
        print("Lỗi:", e)
        time.sleep(1)

driver.quit()