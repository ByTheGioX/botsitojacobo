import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

o = Options()
o.add_argument('--no-sandbox')
o.add_argument('--disable-gpu')
o.add_argument('--user-data-dir=C:\\Users\\AI\\Desktop\\browser_cache')

raw = ChromeDriverManager().install()
driver_path = os.path.join(os.path.dirname(raw), 'chromedriver.exe')
print("Driver webdriver_manager:", driver_path)

s = Service(executable_path=driver_path)
print("Probando con el driver de webdriver_manager...")
try:
    b = webdriver.Chrome(service=s, options=o)
    print(">>> EXITO con webdriver_manager")
    b.quit()
    print(">>> cerro limpio")
except Exception as e:
    print(">>> FALLO:", str(e)[:400])
