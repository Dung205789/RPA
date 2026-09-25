import sys, time, json, re
sys.path.insert(0, ".")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import rpa_env

opts = Options(); opts.add_experimental_option("debuggerAddress", "127.0.0.1:9333")
driver = webdriver.Chrome(options=opts)
driver.execute_script("document.querySelectorAll('.geDialog button,.mxWindow button').forEach(b=>{if(/cancel/i.test(b.textContent)&&b.offsetParent!==null)b.click();});")
rpa_env.clear_canvas(driver)

box = driver.find_element("css selector", "input.geSearchOverride, input[placeholder*='search' i]")
box.click()
box.send_keys("rectangle")
box.send_keys(Keys.ENTER)
time.sleep(1.2)
n = driver.execute_script("return document.querySelectorAll('.geSidebarContainer a.geItem').length;")
print("results count:", n)

def click_text(t):
    return driver.execute_script("""
    const want=arguments[0];
    const c=Array.from(document.querySelectorAll('*')).filter(e=>{
      if(e.children.length>0) return false;
      if((e.textContent||'').trim()!==want) return false;
      if(e.offsetParent===null) return false;
      const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;
    }); return c[0]||null;""", t)

def read_xml():
    ex = click_text("Extras")
    ActionChains(driver).move_to_element(ex).click().perform(); time.sleep(0.5)
    ed = click_text("Edit Diagram...")
    ActionChains(driver).move_to_element(ed).click().perform(); time.sleep(0.6)
    xml = driver.execute_script("const t=document.querySelector('.geDialog textarea'); return t?t.value:null;")
    cancel = driver.execute_script("""
    const btns=Array.from(document.querySelectorAll('.geDialog button')).filter(b=>b.offsetParent!==null);
    return btns.find(b=>/cancel/i.test(b.textContent))||null;""")
    if cancel:
        ActionChains(driver).move_to_element(cancel).click().perform()
        time.sleep(0.3)
    return xml

results = []
for idx in range(min(4, n)):
    item = driver.execute_script("return document.querySelectorAll('.geSidebarContainer a.geItem')[arguments[0]];", idx)
    ActionChains(driver).move_to_element(item).click().perform()
    time.sleep(0.8)
    xml = read_xml()
    styles = re.findall(r'<mxCell[^>]*style="([^"]*)"[^>]*vertex="1"', xml or "")
    results.append({"result_index": idx, "style": styles[-1] if styles else None})
    rpa_env.clear_canvas(driver)

print(json.dumps(results, indent=2))
driver.quit()
