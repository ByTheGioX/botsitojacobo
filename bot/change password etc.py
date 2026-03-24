import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import re
import os
import sys
from webdriver_manager.chrome import ChromeDriverManager


# variables.
days_to_check_for_booking = 4
send_messages_to_clients_one_day_before = 0
p1_p2_p3_image_path = os.path.join(sys.path[0], 'data', 'p1 p2 p3.png')
p4_p5_image_path = os.path.join(sys.path[0], 'data', 'p4 p5.png')
client_message_template_path = os.path.join(sys.path[0], 'data', 'client_message_template.txt')
sent_messages_fp = os.path.join(sys.path[0], 'data', 'sent_messages.txt')
colleagues_messages_data_fp = os.path.join(sys.path[0], 'data', 'colleagues_messages.txt')
places = {
    "P1": "4e",
    "P2": "Csi",
    "P3": "9p",
    "P4": "Maf",
    "P5": "Tri"
}
group_link = 'https://chat.whatsapp.com/GbPVBIcdqEd9v6EzW4u2Lk'
first_time_done_fp = os.path.join(sys.path[0], 'data', 'ftd')


os.system("title " + os.path.basename(__file__))


class Browser:
    def __init__(self):
        self.waiting_time = 180  # will become half.
        self.debug = True
        try:
            o = Options()
            o.add_argument(r'--user-data-dir=C:/Users/Turitop/Desktop/browser_cache')
            o.add_argument('--log-level=3')

            self.driver_path = ChromeDriverManager().install()
            self.driver_path = os.path.join(os.path.dirname(self.driver_path), 'chromedriver.exe')


            s = Service(executable_path=self.driver_path)
            
            self.web_browser = webdriver.Chrome(service=s, options=o)
            self.web_browser.set_window_size(width=1100, height=850)
        except Exception as e:
            print(str(e))
            input("try to get new drivers if an update is released. \npress enter to exit...")
            sys.exit('')

    def css_click(self, element):
        for count in range(0, self.waiting_time, 1):
            try:
                self.web_browser.find_element(By.CSS_SELECTOR, element).click()
                return True
            except Exception as e:
                self.show_error(e)
                time.sleep(0.5)
        return False

    @staticmethod
    def re_get_text(re_pattern, raw_text):
        try:
            return re.findall(re_pattern, raw_text)[0].strip()
        except:
            return ''

    def get_text(self, element, parent_element=None):
        for count in range(0, 3, 1):
            try:
                if type(element) == str:
                    if parent_element is None:
                        t = self.web_browser.find_element(By.CSS_SELECTOR, element).get_attribute('innerText').strip()
                    else:
                        t = parent_element.find_element(By.CSS_SELECTOR, element).get_attribute('innerText').strip()
                else:
                    t = element.get_attribute('innerText').strip()
                return t
            except Exception as e:
                self.show_error(e)
                time.sleep(0.5)
        return ''

    def get_attr(self, element, attr, parent_element=None):
        for count in range(0, 3, 1):
            try:
                if type(element) == str:
                    if parent_element is None:
                        t = self.web_browser.find_element(By.CSS_SELECTOR, element).get_attribute(attr).strip()
                    else:
                        t = parent_element.find_element(By.CSS_SELECTOR, element).get_attribute(attr).strip()
                else:
                    t = element.get_attribute(attr).strip()
                return t
            except Exception as e:
                self.show_error(e)
                time.sleep(0.5)
        return ''

    def x_click(self, element):
        for count in range(0, self.waiting_time, 1):
            try:
                self.web_browser.find_element(By.XPATH, element).click()
                return True
            except Exception as e:
                self.show_error(e)
                time.sleep(0.5)
        return False

    def css_click_with_timer(self, element, timer):
        for count in range(0, timer, 1):
            try:
                self.web_browser.find_element(By.CSS_SELECTOR, element).click()
                return True
            except Exception as e:
                self.show_error(e)
                try:
                    elem = self.web_browser.find_element(By.CSS_SELECTOR, element)
                    self.web_browser.execute_script('arguments[0].click()', elem)
                    return True
                except Exception as e2:
                    self.show_error(e2)
                    time.sleep(0)
                time.sleep(0.5)
        return False

    def x_click_with_timer(self, element, timer):
        for count in range(0, timer, 1):
            try:
                self.web_browser.find_element(By.XPATH, element).click()
                return True
            except Exception as e:
                self.show_error(e)
                try:
                    elem = self.web_browser.find_element(By.CSS_SELECTOR, element)
                    self.web_browser.execute_script('arguments[0].click()', elem)
                    return True
                except Exception as e2:
                    self.show_error(e2)
                    time.sleep(0)
                time.sleep(0.5)
        return False

    def js_click(self, element):
        for count in range(0, self.waiting_time, 1):
            try:
                ele = self.web_browser.find_element(By.CSS_SELECTOR, element)
                self.web_browser.execute_script('arguments[0].click()', ele)
                return True
            except:
                time.sleep(0.5)
        return False

    def obj_click(self, obj):
        for count in range(0, self.waiting_time, 1):
            try:
                obj.click()
                return True
            except Exception as e:
                self.show_error(e)
                time.sleep(0.5)
        return False

    def obj_js_click(self, obj):
        for count in range(0, self.waiting_time, 1):
            try:
                self.web_browser.execute_script('arguments[0].click()', obj)
                return True
            except Exception as e:
                self.show_error(e)
                time.sleep(0.5)
        return False

    def text_wait(self, text):
        for count in range(0, self.waiting_time, 1):
            try:
                if text in self.web_browser.page_source:
                    return True
                else:
                    time.sleep(0.5)
            except Exception as e:
                self.show_error(e)
                time.sleep(0.5)
        return False

    def send_keys(self, element, keys, full=False):
        for count in range(0, self.waiting_time, 1):
            try:
                ele = self.web_browser.find_element(By.CSS_SELECTOR, element)
                if full:
                    ele.send_keys(keys)
                else:
                    ele.clear()
                    for key_pack in keys.split("\n"):
                        ele.send_keys(key_pack)

                return True
            except Exception as e:
                self.show_error(e)
                time.sleep(0.5)
        return False

    def get(self, url):
        for try_ in range(0, 3, 1):
            try:
                self.web_browser.get(url)
                return True
            except Exception as e:
                self.show_error(e)
                time.sleep(0.5)
        return False

    def show_error(self, error):
        if self.debug:
            print(str(error))
            print("Line:", str(error.__traceback__.tb_lineno))


wb = Browser()
wb.get("https://app.turitop.com/admin/company/P271/bookings")
breakpoint()

