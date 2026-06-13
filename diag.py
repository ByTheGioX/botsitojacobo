import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

print("Selenium version:", selenium.__version__)

o = Options()
o.add_argument('--no-sandbox')
o.add_argument('--disable-gpu')

try:
    s = Service(service_args=['--verbose'], log_output='cdlog.txt')
except TypeError:
    s = Service(service_args=['--verbose'], log_path='cdlog.txt')

print("Lanzando Chrome con driver automatico de Selenium...")
try:
    b = webdriver.Chrome(service=s, options=o)
    print(">>> EXITO: Chrome arranco correctamente")
    b.quit()
    print(">>> EXITO: cerro limpio")
except Exception as e:
    print(">>> FALLO:", str(e)[:400])

print("---- Revisa cdlog.txt para el detalle ----")
