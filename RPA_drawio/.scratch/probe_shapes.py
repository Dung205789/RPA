import sys, time, json, re, os
sys.path.insert(0, ".")
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from lockguard import acquire_or_exit
acquire_or_exit("probe_shapes")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

import rpa_env, palette_matcher, drawio_ops, cell_tracker

opts = Options()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:9333")
driver = webdriver.Chrome(options=opts)

LOCAL_URL = "http://localhost:8080/?lang=en&splash=0"
rpa_env.open_clean_drawio(driver, url=LOCAL_URL, log=lambda *a: None)

def click_text(text):
    return driver.execute_script("""
    const want = arguments[0];
    const cands = Array.from(document.querySelectorAll('*')).filter(e => {
      if (e.children.length > 0) return false;
      if ((e.textContent||'').trim() !== want) return false;
      if (e.offsetParent === null) return false;
      const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    });
    return cands[0] || null;
    """, text)

def read_model_xml():
    el = click_text("Extras")
    ActionChains(driver).move_to_element(el).click().perform()
    time.sleep(0.5)
    ed = click_text("Edit Diagram...")
    ActionChains(driver).move_to_element(ed).click().perform()
    time.sleep(0.6)
    xml = driver.execute_script("const t=document.querySelector('.geDialog textarea'); return t?t.value:null;")
    cancel = driver.execute_script("""
    const btns = Array.from(document.querySelectorAll('.geDialog button')).filter(b=>b.offsetParent!==null);
    return btns.find(b => /cancel/i.test(b.textContent)) || null;
    """)
    if cancel:
        ActionChains(driver).move_to_element(cancel).click().perform()
        time.sleep(0.3)
    return xml

results = {}
for shape in ["rectangle", "rounded rectangle", "ellipse", "diamond",
              "parallelogram", "hexagon", "trapezoid", "document", "cylinder"]:
    icon_path = shape_icon = None
    fname = {"rectangle":"rectangle.png","rounded rectangle":"rectangle.png","ellipse":"ellipse.png",
             "diamond":"diamond.png","parallelogram":"parallelogram.png","hexagon":"hexagon.png",
             "trapezoid":"trapezoid.png","document":"document.png","cylinder":"cylinder.png"}[shape]
    obj = str((__import__("pathlib").Path("shape_icons") / fname).resolve())
    match = palette_matcher.find_icon(driver, obj, log=lambda *a: None)
    if not match.get("ok"):
        results[shape] = {"error": match.get("reason")}
        continue
    cand = match["ranked"][0]
    known = drawio_ops.known_cells(driver)
    if cand["palette"]:
        drawio_ops.click_palette_entry(driver, cand["element"], view_origin=None)
    else:
        ActionChains(driver).move_to_element(cand["element"]).click().perform()
        time.sleep(1.0)
    created = len(drawio_ops.known_cells(driver)) > len(known)
    if not created:
        results[shape] = {"error": "no cell created", "candidate_tag": cand["tag"]}
        continue
    xml = read_model_xml()
    # last mxCell with a style= attribute
    styles = re.findall(r'<mxCell[^>]*style="([^"]*)"[^>]*vertex="1"', xml)
    results[shape] = {"style": styles[-1] if styles else None, "icon_used": fname}
    # clean canvas between shapes for isolation
    rpa_env.clear_canvas(driver)

print(json.dumps(results, indent=2))
driver.quit()
