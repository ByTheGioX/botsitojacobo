from selenium import webdriver
from selenium.webdriver.chrome.options import Options
o = Options()
o.add_argument('--user-data-dir=C:\\Users\\AI\\Desktop\\bcache6')
o.add_argument('--no-sandbox')
o.add_argument('--disable-gpu')
o.add_experimental_option('excludeSwitches', ['enable-automation'])
print("Test 6 = solo excludeSwitches")
try:
    b = webdriver.Chrome(options=o)
    print(">>> EXITO (excludeSwitches OK)")
    b.quit()
except Exception as e:
    print(">>> FALLO (excludeSwitches es el culpable):", str(e)[:200])
