import sys, json
sys.path.insert(0, ".")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import rpa_env, palette_matcher

opts = Options(); opts.add_experimental_option("debuggerAddress", "127.0.0.1:9333")
driver = webdriver.Chrome(options=opts)
driver.execute_script("document.querySelectorAll('.geDialog button,.mxWindow button').forEach(b=>{if(/cancel/i.test(b.textContent)&&b.offsetParent!==null)b.click();});")
rpa_env.clear_canvas(driver)

obj = str((__import__("pathlib").Path("shape_icons") / "rectangle.png").resolve())
match = palette_matcher.find_icon(driver, obj, log=print)
print("ok:", match.get("ok"))
for i, c in enumerate(match.get("ranked", [])[:6]):
    print(i, {k: c[k] for k in ("score", "tag", "palette", "title") if k in c})
driver.quit()
