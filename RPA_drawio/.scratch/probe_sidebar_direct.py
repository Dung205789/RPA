import sys, time, json, re
sys.path.insert(0, ".")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import rpa_env

opts = Options(); opts.add_experimental_option("debuggerAddress", "127.0.0.1:9333")
driver = webdriver.Chrome(options=opts)
driver.execute_script("document.querySelectorAll('.geDialog button,.mxWindow button').forEach(b=>{if(/cancel/i.test(b.textContent)&&b.offsetParent!==null)b.click();});")
rpa_env.clear_canvas(driver)

# Read the sidebar's first N items' title/tooltip attributes directly, no image matching
items = driver.execute_script("""
return Array.from(document.querySelectorAll('.geSidebarContainer a.geItem')).slice(0, 6).map((el, i) => ({
  index: i, title: el.getAttribute('title'), style: el.getAttribute('style') ? 'has-style-attr' : null
}));
""")
print("first 6 sidebar items:", json.dumps(items, ensure_ascii=False))

# click exactly the item whose title is "Rectangle" (exact, case-sensitive as draw.io renders it)
el = driver.execute_script("""
const items = Array.from(document.querySelectorAll('.geSidebarContainer a.geItem'));
return items.find(e => e.getAttribute('title') === 'Rectangle') || null;
""")
print("found exact 'Rectangle' item:", el)
if el:
    ActionChains(driver).move_to_element(el).click().perform()
    time.sleep(1.0)

def click_text(t):
    return driver.execute_script("""
    const want=arguments[0];
    const c=Array.from(document.querySelectorAll('*')).filter(e=>{
      if(e.children.length>0) return false;
      if((e.textContent||'').trim()!==want) return false;
      if(e.offsetParent===null) return false;
      const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;
    }); return c[0]||null;""", t)
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
print("XML:", xml)
driver.quit()
