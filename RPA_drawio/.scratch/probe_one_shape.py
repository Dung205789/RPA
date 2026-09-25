import sys, time, json, re, os
sys.path.insert(0, ".")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import rpa_env, palette_matcher, drawio_ops

shape = sys.argv[1]
fname = {"rectangle":"rectangle.png","rounded rectangle":"rectangle.png","ellipse":"ellipse.png",
         "diamond":"diamond.png","parallelogram":"parallelogram.png","hexagon":"hexagon.png",
         "trapezoid":"trapezoid.png","document":"document.png","cylinder":"cylinder.png"}[shape]

opts = Options(); opts.add_experimental_option("debuggerAddress", "127.0.0.1:9333")
driver = webdriver.Chrome(options=opts)
driver.execute_script("document.querySelectorAll('.geDialog button,.mxWindow button').forEach(b=>{if(/cancel/i.test(b.textContent)&&b.offsetParent!==null)b.click();});")
rpa_env.clear_canvas(driver)

obj = str((__import__("pathlib").Path("shape_icons") / fname).resolve())
match = palette_matcher.find_icon(driver, obj, log=lambda *a: None)
out = {"shape": shape, "icon": fname}
if not match.get("ok"):
    out["error"] = match.get("reason")
else:
    cand = match["ranked"][0]
    known = drawio_ops.known_cells(driver)
    if cand["palette"]:
        drawio_ops.click_palette_entry(driver, cand["element"], view_origin=None)
    else:
        ActionChains(driver).move_to_element(cand["element"]).click().perform()
        time.sleep(1.0)
    created = len(drawio_ops.known_cells(driver)) > len(known)
    if not created:
        out["error"] = "no cell created"
    else:
        def click_text(t):
            return driver.execute_script("""
            const want=arguments[0];
            const c=Array.from(document.querySelectorAll('*')).filter(e=>{
              if(e.children.length>0) return false;
              if((e.textContent||'').trim()!==want) return false;
              if(e.offsetParent===null) return false;
              const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;
            }); return c[0]||null;""", t)
        el = click_text("Extras")
        ActionChains(driver).move_to_element(el).click().perform(); time.sleep(0.5)
        ed = click_text("Edit Diagram...")
        ActionChains(driver).move_to_element(ed).click().perform(); time.sleep(0.6)
        xml = driver.execute_script("const t=document.querySelector('.geDialog textarea'); return t?t.value:null;")
        cancel = driver.execute_script("""
        const btns=Array.from(document.querySelectorAll('.geDialog button')).filter(b=>b.offsetParent!==null);
        return btns.find(b=>/cancel/i.test(b.textContent))||null;""")
        if cancel:
            ActionChains(driver).move_to_element(cancel).click().perform()
        styles = re.findall(r'<mxCell[^>]*style="([^"]*)"[^>]*vertex="1"', xml or "")
        out["style"] = styles[-1] if styles else None
        out["xml"] = xml

out_path = os.path.join(".scratch", "style_%s.json" % shape.replace(" ", "_"))
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(json.dumps({k:v for k,v in out.items() if k!="xml"}, ensure_ascii=False))
driver.quit()
