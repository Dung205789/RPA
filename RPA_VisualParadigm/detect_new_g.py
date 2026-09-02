import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, JavascriptException

def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def find_divs_containing_svg(driver):
    """Tìm tất cả các thẻ div hiển thị trên giao diện chứa SVG"""
    script = """
    const svgs = document.querySelectorAll('svg');
    const result = [];
    
    svgs.forEach((svg, index) => {
        const svgRect = svg.getBoundingClientRect();
        const svgStyle = window.getComputedStyle(svg);
        const svgVisible = svgStyle.display !== 'none' && 
                          svgStyle.visibility !== 'hidden' &&
                          svgRect.width > 0 && 
                          svgRect.height > 0;
        
        if (!svgVisible) return;
        
        const parent = svg.parentElement;
        if (parent && parent.tagName === 'DIV') {
            const rect = parent.getBoundingClientRect();
            const computed = window.getComputedStyle(parent);
            
            const divVisible = computed.display !== 'none' && 
                              computed.visibility !== 'hidden' &&
                              rect.width > 0 && 
                              rect.height > 0;
            
            if (divVisible) {
                result.push({
                    index: index,
                    id: parent.id || '',
                    className: parent.className || '',
                    display: computed.display,
                    visibility: computed.visibility,
                    width: rect.width,
                    height: rect.height,
                    top: rect.top,
                    left: rect.left,
                    selector: parent.id ? '#' + parent.id : 
                             (parent.className ? '.' + parent.className.trim().split(/\\s+/).join('.') : ''),
                    outerHTML: parent.outerHTML.substring(0, 200)
                });
            }
        }
    });
    
    return result;
    """

    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        divs_info = driver.execute_script(script)

        large_divs = [d for d in divs_info if d['width'] > 100 and d['height'] > 100]
        large_divs.sort(key=lambda x: x['width'] * x['height'], reverse=True)

        return {
            'all_divs': divs_info,
            'large_divs': large_divs,
            'main_canvas': large_divs[0] if large_divs else None
        }
    except (TimeoutException, JavascriptException) as e:
        log(f"Lỗi khi tìm div chứa SVG: {e}")
        return {'all_divs': [], 'large_divs': [], 'main_canvas': None}

def get_elements_in_container(driver, container_selector=None):
    """Lấy tất cả phần tử <g> có style visibility: visible trong container, loại bỏ thẻ ẩn và thẻ chứa văn bản"""
    if container_selector is None:
        log("Đang tự động tìm container chứa SVG...")
        svg_containers = find_divs_containing_svg(driver)

        if not svg_containers['main_canvas']:
            return {'error': 'Không tìm thấy container chứa SVG phù hợp'}

        main_canvas = svg_containers['main_canvas']

        if main_canvas['id']:
            container_selector = f"#{main_canvas['id']}"
        elif main_canvas['className']:
            first_class = main_canvas['className'].split()[0]
            container_selector = f".{first_class}"
        else:
            return {'error': 'Không thể tạo selector cho container'}

        log(f"Đã tìm thấy container: {container_selector}")

    script = f"""
    function getCSSSelector(element, root) {{
        const path = [];
        let current = element;
        
        while (current && current !== root && current.nodeType === Node.ELEMENT_NODE) {{
            let selector = current.nodeName.toLowerCase();
            
            if (current.id) {{
                selector = '#' + current.id;
                path.unshift(selector);
                break;
            }}
            
            if (current.className && typeof current.className === 'string') {{
                const classes = current.className.trim().split(/\\s+/).filter(c => c).join('.');
                if (classes) selector += '.' + classes;
            }}
            
            if (current.parentNode && current.parentNode !== root) {{
                const siblings = Array.from(current.parentNode.children).filter(
                    e => e.nodeName === current.nodeName
                );
                
                if (siblings.length > 1) {{
                    const index = siblings.indexOf(current) + 1;
                    selector += ':nth-child(' + index + ')';
                }}
            }}
            
            path.unshift(selector);
            current = current.parentNode;
        }}
        
        return '{container_selector} ' + path.join(' > ');
    }}
    
    const container = document.querySelector('{container_selector}');
    if (!container) {{
        return {{error: 'Không tìm thấy container: {container_selector}'}};
    }}
    
    const elements = Array.from(container.querySelectorAll('g')).filter(
        el => {{
            // Kiểm tra visibility: visible (giữ nguyên logic cũ)
            const style = el.style.visibility === 'visible' || 
                          (el.getAttribute('style') && el.getAttribute('style').includes('visibility: visible'));
            
            // Kiểm tra thẻ ẩn thêm (display none hoặc visibility hidden)
            const computed = window.getComputedStyle(el);
            const isVisible = computed.display !== 'none' && computed.visibility !== 'hidden';
            
            // Kiểm tra chứa văn bản (text content lồng sâu)
            const hasText = el.textContent.trim().length > 0;
            
            // Giữ <g> nếu visible và KHÔNG chứa text
            return style && isVisible && !hasText;
        }}
    );
    
    return {{
        containerFound: true,
        containerSelector: '{container_selector}',
        totalElements: elements.length,
        elements: elements.map(el => {{
            return {{
                tagName: el.tagName,
                id: el.id || '',
                className: typeof el.className === 'string' ? el.className : '',
                cssSelector: getCSSSelector(el, container)
            }};
        }})
    }};
    """

    try:
        result = driver.execute_script(script)
        return result
    except JavascriptException as e:
        log(f"Lỗi khi lấy phần tử <g>: {e}")
        return {'error': f'Lỗi JavaScript: {str(e)}'}

def classify_new_elements(new_selectors, steps_info, created_steps=None):
    """
    Phân loại các element mới thành:
    - Element thông thường (từ click)
    - Connector (từ connect/link)

    Args:
        new_selectors: List các CSS selector mới
        steps_info: List các dict chứa thông tin step
                    [{'step_num': 2, 'action': 'click'},
                     {'step_num': 4, 'action': 'connect', 'from_step': 2, 'to_step': 3}, ...]
        created_steps: List các step_num đã tạo phần tử mới

    Returns:
        dict: {
            'elements': {step_num: selector},
            'connectors': {(from_step, to_step): selector}
        }
    """
    result = {
        'elements': {},
        'connectors': {}
    }

    if created_steps is None:
        created_steps = []

    # Đếm số element và connector cần tạo
    element_steps = [s for s in steps_info if s['action'] in ['click', 'double click'] and s['step_num'] in created_steps]
    
    # Thêm current_step (step cuối cùng) nếu action là click/double click và chưa tồn tại
    if steps_info:
        current = steps_info[-1]
        if current['action'] in ['click', 'double click'] and current['step_num'] not in created_steps:
            element_steps.append(current)
    
    connector_steps = [s for s in steps_info if s['action'] in ['connect', 'link']]

    log(f"📊 Cần tạo: {len(element_steps)} elements, {len(connector_steps)} connectors")
    log(f"📊 Có sẵn: {len(new_selectors)} selectors mới")

    # ===== LOGIC MỚI: Elements trước, Connectors sau =====
    
    selector_idx = 0

    # BƯỚC 1: Gán tất cả elements trước (theo thứ tự step_num tăng dần)
    element_steps_sorted = sorted(element_steps, key=lambda x: x['step_num'])
    
    for elem_step in element_steps_sorted:
        step_num = elem_step['step_num']
        if selector_idx < len(new_selectors):
            result['elements'][step_num] = new_selectors[selector_idx]
            log(f"   📦 element created in step {step_num} -> {new_selectors[selector_idx]}")
            selector_idx += 1

    # BƯỚC 2: Gán tất cả connectors sau (theo thứ tự xuất hiện trong steps_info)
    for conn in connector_steps:
        if selector_idx < len(new_selectors):
            result['connectors'][(conn['from_step'], conn['to_step'])] = new_selectors[selector_idx]
            log(f"   🔗 connector_from_step{conn['from_step']}_to_step{conn['to_step']} -> {new_selectors[selector_idx]}")
            selector_idx += 1

    if selector_idx < len(new_selectors):
        log(f"⚠️  Còn {len(new_selectors) - selector_idx} selectors chưa được gán")

    return result

def find_new_elements_by_steps(data_initial, data_current, steps_info, created_steps=None, previous_new_selectors=None):
    """
    So sánh DOM ban đầu với DOM hiện tại và tạo mapping

    Args:
        data_initial: DOM snapshot ban đầu
        data_current: DOM snapshot hiện tại
        steps_info: List thông tin các step đã tạo element/connector
        created_steps: List các step_num đã tạo phần tử mới
        previous_new_selectors: List các CSS selector mới từ bước trước đó (nếu có)

    Returns:
        tuple: (classified_result, error)
    """
    if 'error' in data_initial or 'error' in data_current:
        error_msg = data_initial.get('error') or data_current.get('error')
        return None, error_msg

    initial_selectors = {el['cssSelector'] for el in data_initial['elements']}
    current_selectors_list = [el['cssSelector'] for el in data_current['elements']]

    new_selectors = [s for s in current_selectors_list if s not in initial_selectors]

    if not new_selectors:
        return None, "Không tìm thấy phần tử mới nào"

    # Sửa mới: So sánh với previous_new_selectors nếu có
    if previous_new_selectors and set(new_selectors) == set(previous_new_selectors):
        return None, "Không có phần tử mới (trùng với bước trước)"

    log(f"✅ Tìm thấy {len(new_selectors)} phần tử mới trong DOM")

    # Phân loại element và connector
    classified = classify_new_elements(new_selectors, steps_info, created_steps=created_steps)

    return classified, None