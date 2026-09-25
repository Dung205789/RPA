import sys, time, json
sys.path.insert(0, ".")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import rpa_env

opts = Options(); opts.add_experimental_option("debuggerAddress", "127.0.0.1:9333")
driver = webdriver.Chrome(options=opts)
driver.execute_script("document.querySelectorAll('.geDialog button,.mxWindow button').forEach(b=>{if(/cancel/i.test(b.textContent)&&b.offsetParent!==null)b.click();});")
rpa_env.clear_canvas(driver)

# check aria-label on first sidebar items
labels = driver.execute_script("""
return Array.from(document.querySelectorAll('.geSidebarContainer a.geItem')).slice(0, 8).map((el,i) => ({
  index: i,
  aria: el.getAttribute('aria-label'),
  imgTitle: (el.querySelector('img')||{}).title,
  innerTitle: el.title,
}));
""")
print("sidebar item labels:", json.dumps(labels, ensure_ascii=False))

# use the search box
box = driver.find_element("css selector", "input.geSearchOverride, input[placeholder*='search' i]")
print("search box tag:", box.tag_name)
box.click()
box.send_keys("rectangle")
time.sleep(1.0)
results = driver.execute_script("""
return Array.from(document.querySelectorAll('.geSidebarContainer a.geItem')).map((el,i) => ({
  index: i, aria: el.getAttribute('aria-label')
}));
""")
print("search 'rectangle' results:", json.dumps(results, ensure_ascii=False))
driver.quit()
