import datetime
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import re
import calendar
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import os
import sys
from os.path import getsize
from webdriver_manager.chrome import ChromeDriverManager
import pickle
import pyautogui
import base64
import urllib.request


# variables.
days_to_check_for_booking = 4
send_messages_to_clients_one_day_before = 0

p1_to_p6_image_path = os.path.join(sys.path[0], 'data', 'p1_to_p6.jpg')
p7_image_path = os.path.join(sys.path[0], 'data', 'p7.jpg')

client_message_template_path = os.path.join(sys.path[0], 'data', 'client_message_template.txt')
p7_client_message_template_path = os.path.join(sys.path[0], 'data', 'client_message_template p7.txt')

sent_messages_fp = os.path.join(sys.path[0], 'data', 'sent_messages.txt')
colleagues_messages_data_fp = os.path.join(sys.path[0], 'data', 'colleagues_messages.txt')
places = {
    "P1": "4e",
    "P2": "Csi",
    "P3": "9p",
    "P4": "Maf",
    "P5": "Tri1",
    "P6": "Tri2"
}
group_link = 'https://web.whatsapp.com/accept?code=EaRWSABnq5NGXLvSKyA4v8&utm_campaign=wa_chat_v2'
first_time_done_fp = os.path.join(sys.path[0], 'data', 'ftd')
log_fp = os.path.join(sys.path[0], 'data', 'logs.txt')
dates_file_path = os.path.join(sys.path[0], 'data', 'dates.json')

# --- NEW MODULE CONFIG ---
photo_group_config_fp = os.path.join(sys.path[0], 'data', 'photo_group_config.txt')
if not os.path.exists(photo_group_config_fp):
    os.makedirs(os.path.dirname(photo_group_config_fp), exist_ok=True)
    with open(photo_group_config_fp, 'w', encoding='utf-8') as f:
        f.write("Parapark Fotos 2026\nhttps://chat.whatsapp.com/J9kambMiqGYGg4GULS4LiM?mode=gi_t")

with open(photo_group_config_fp, 'r', encoding='utf-8') as f:
    config_lines = [L.strip() for L in f.readlines() if L.strip()]
    photo_group_name = config_lines[0] if len(config_lines) > 0 else 'Parapark Fotos 2026'
    photo_group_link = config_lines[1] if len(config_lines) > 1 else 'https://chat.whatsapp.com/J9kambMiqGYGg4GULS4LiM?mode=gi_t'

openrouter_api_key_fp = os.path.join(sys.path[0], 'data', 'openrouter_api_key.txt')
if not os.path.exists(openrouter_api_key_fp):
    with open(openrouter_api_key_fp, 'w', encoding='utf-8') as f:
        f.write('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')
with open(openrouter_api_key_fp, 'r', encoding='utf-8') as f:
    openrouter_api_key = f.read().strip()

google_maps_review_link = 'https://g.page/r/CRIIJJreA48cEAo/review'

pending_replies_fp = os.path.join(sys.path[0], 'data', 'pending_replies.json')
last_group_message_fp = os.path.join(sys.path[0], 'data', 'last_group_message.txt')
downloaded_photos_dir = os.path.join(sys.path[0], 'data', 'downloaded_photos')
photo_sent_messages_fp = os.path.join(sys.path[0], 'data', 'photo_sent_messages.txt')

# Caption sala -> Turitop place codes
sala_to_places = {
    '4e': ['P1'],
    'csi': ['P2'],
    'maf': ['P4'],
    'tri': ['P5', 'P6'],
}

# Templates in editable .txt files (just open and edit the text)
photo_thank_you_template_fp = os.path.join(sys.path[0], 'data', 'photo_thank_you_template.txt')
positive_review_template_fp = os.path.join(sys.path[0], 'data', 'positive_review_template.txt')
negative_review_template_fp = os.path.join(sys.path[0], 'data', 'negative_review_template.txt')
bad_caption_ids_fp = os.path.join(sys.path[0], 'data', 'bad_caption_replied_ids.json')
failed_sends_fp = os.path.join(sys.path[0], 'data', 'failed_photo_sends.json')

os.system("title " + os.path.basename(__file__))


# ============================================================
# HELPER: Cache for bad caption replies and failed sends
# ============================================================
def _load_json_set(filepath):
    """Load a JSON list from file, return as set."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except:
            pass
    return set()


def _save_json_set(filepath, data_set):
    """Save a set as JSON list to file (keep last 500)."""
    items = list(data_set)[-500:]
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(items, f)


def _track_failed_send(send_id):
    """Track a failed send so we don't retry it endlessly."""
    failed = _load_json_set(failed_sends_fp)
    failed.add(send_id)
    _save_json_set(failed_sends_fp, failed)


def _is_failed_send(send_id):
    """Check if this send previously failed."""
    failed = _load_json_set(failed_sends_fp)
    return send_id in failed


class Browser:
    def __init__(self):
        self.waiting_time = 180  # will become half.
        self.debug = False
        try:
            o = Options()
            
            # Autodetect the user's Desktop folder dynamically (works for 'AI', 'Turitop', etc.)
            desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            cache_path = os.path.join(desktop_path, 'browser_cache')
            o.add_argument(f'--user-data-dir={cache_path}')
            
            o.add_argument('--log-level=3')

            for attempt in range(3):
                try:
                    self.driver_path = ChromeDriverManager().install()
                    break
                except Exception as e2:
                    self.driver_path = ''
                    self.show_error(e2)
                    time.sleep(10)
            if self.driver_path == '':
                print("failed to get drivers from web.")
                sys.exit(1)

            # self.driver_path = os.path.join(sys.path[0], 'chromedriver.exe')
            self.driver_path = os.path.join(os.path.dirname(self.driver_path), 'chromedriver.exe')

            s = Service(executable_path=self.driver_path)

            self.web_browser = webdriver.Chrome(service=s, options=o)
            self.web_browser.set_window_size(width=1100, height=850)
        except Exception as e:
            print(str(e))
            sys.exit(1)

    def save_cookies(self, cookie_name):
        try:
            pickle.dump(self.web_browser.get_cookies(), open(os.path.join(sys.path[0], f"{cookie_name}.pkl"), "wb"))
            print("cookies saved.")
            return True
        except Exception as error_func:
            self.show_error(error_func)
            print('warning: cookies saving failed.')
            return False

    def load_cookies(self, cookie_name):
        try:
            cookies_fp = os.path.join(sys.path[0], f"{cookie_name}.pkl")
            if os.path.exists(cookies_fp):
                cookies = pickle.load(open(cookies_fp, "rb"))
                for cookie in cookies:
                    self.web_browser.add_cookie(cookie)
                print('cookies loaded.')
                return True
            else:
                print('no cookies file found.', cookie_name)
        except Exception as error_func:
            self.show_error(error_func)
            print("failed to load cookies.")
            return False

    def css_click(self, element):
        for count in range(0, self.waiting_time, 1):
            try:
                self.web_browser.find_element(By.CSS_SELECTOR, element).click()
                return True
            except Exception as e:
                # self.show_error(e)
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
                # self.show_error(e)
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
                    # self.show_error(e2)
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
                    # self.show_error(e2)
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

    def elem_wait(self, element):
        for count in range(0, self.waiting_time, 1):
            try:
                ele = self.web_browser.find_elements(By.CSS_SELECTOR, element)
                if len(ele) > 0:
                    return True
                else:
                    time.sleep(0.5)
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

    def send_keys(self, element, keys, full=False, clear=False):
        for count in range(0, self.waiting_time, 1):
            if "Enlace incorrecto. Cierra la venta y vuelve a intentarlo con un enlace diferente." in wb.web_browser.page_source or "El número de teléfono compartido a través de la dirección URL es inválido" in wb.web_browser.page_source or "El número de teléfono compartido a través de la dirección URL no es válido" in wb.web_browser.page_source:
                print('invalid chat link/number.')
                return
            try:
                ele = self.web_browser.find_element(By.CSS_SELECTOR, element)
                if full:
                    if clear:
                        ele.clear()
                    ele.send_keys(keys)
                else:
                    ele.clear()
                    for key_pack in keys.split("\n"):
                        ele.send_keys(key_pack)
                        ActionChains(wb.web_browser).key_down(Keys.ALT).perform()
                        ActionChains(wb.web_browser).send_keys(Keys.ENTER).perform()
                        ActionChains(wb.web_browser).key_up(Keys.ALT).perform()

                return True
            except Exception as e:
                # self.show_error(e)
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
            msg = datetime.datetime.now().strftime('%D %T') + str(error) + str(error.__traceback__.tb_lineno)
            print(msg)
            if not (os.path.exists(log_fp)):
                with open(log_fp, 'w') as f:
                    f.write(msg + '\n\n')
            else:
                with open(log_fp, 'a') as f:
                    f.write(msg + '\n\n')
            if (int(getsize(log_fp)) / 1000) / 1000 > 1:
                os.remove(log_fp)


def send_message_to_client(booking_data):
    try:
        send_message = True
        if booking_data['wa_link'] == '':
            return

        while 1:
            # dummy loop to make decision.

            # checking if we need to send message right now.
            cdo = datetime.datetime.now()
            cd = cdo.day
            if send_messages_to_clients_one_day_before == 1:
                pd = int(booking_data['booking_day']) - 1
                if pd == 0:
                    cm_max_day = calendar.monthrange(cdo.year, cdo.month)[1]
                    if cd != cm_max_day:
                        send_message = False
                        break
                else:
                    if cd != pd:
                        send_message = False
                        break

            else:
                if cd != int(booking_data['booking_day']):
                    send_message = False
                    break

            # checking if we are out of active hours.
            if cdo.hour < 10 or cdo.hour > 21:
                send_message = False
                break

            if not (os.path.exists(sent_messages_fp)):
                with open(sent_messages_fp, 'w') as f:
                    f.write('')

            with open(sent_messages_fp, 'r') as f:
                message_id = booking_data['booking_date'] + booking_data['wa_link']
                if message_id in f.read():
                    send_message = False
                    break

            break

        if send_message:
            # send message to this number here.
            print(f'sending message to link: {booking_data["wa_link"]}')

            bp = booking_data['booking_place'].lower().strip()
            if 'p7' in bp:
                template_path = p7_client_message_template_path
            else:
                template_path = client_message_template_path

            with open(template_path, 'r', encoding='utf-8') as f:
                message_template = f.read().strip()

            if bp in ['#p1', '#p2', '#p3']:
                image = p1_to_p6_image_path
                map_link = 'https://g.co/kgs/XXKVVs'
            elif bp in ['#p4', '#p5', '#p6']:
                image = p1_to_p6_image_path
                map_link = 'https://g.co/kgs/q79HZy'
            else:
                image = p7_image_path
                map_link = "https://maps.app.goo.gl/ptJ1yjY2x4tJuCre8?g_st=iwb"

            if 'p1' in bp:
                booking_en = '4th element '
                booking_sp = 'Cuarto elemento '

            elif 'p2' in bp:
                booking_en = 'C.S.I investigation '
                booking_sp = 'C.S.I investigación '

            elif 'p4' in bp:
                booking_en = 'Italian Mafia'
                booking_sp = 'Mafia italiana'

            elif 'p5' in bp:
                booking_en = 'Bermuda Triangle 2'
                booking_sp = 'Triángulo de las Bermudas 2'

            elif 'p6' in bp:
                booking_en = 'Bermuda Triangle 1'
                booking_sp = 'Triángulo de las Bermudas 1'

            else:
                booking_en = ''
                booking_sp = ''

            message = message_template.replace("{booking_time}", booking_data['booking_time'])
            message = message.replace('{goolge_maps_link}', map_link)
            message = message.replace('{name_service}', booking_sp)
            message = message.replace('{name_service_en}', booking_en)

            link___ = booking_data['wa_link'].replace("%20", "").lower().replace("api.", "web.")
            wb.get(link___)
            time.sleep(6)
            if not ("Enlace incorrecto. Cierra la venta y vuelve a intentarlo con un enlace diferente." in wb.web_browser.page_source) and not ("El número de teléfono compartido a través de la dirección URL es inválido" in wb.web_browser.page_source) and not("El número de teléfono compartido a través de la dirección URL no es válido" in wb.web_browser.page_source) and not("no está en WhatsApp" in wb.web_browser.page_source):
                # wb.get("https://api.whatsapp.com/send/?phone=+923427382557")
                # wb.css_click("#action-button")
                # wb.x_click('//*[contains(text(), "usar WhatsApp Web")] | //*[contains(text(), "use WhatsApp Web")] | //*[contains(text(), "Continue to WhatsApp Web")]')
                wb.send_keys("div[title='Escribe un mensaje'],div[aria-label='Escribe un mensaje'],div[aria-placeholder='Escribe un mensaje']", message)

                if not ("El número de teléfono compartido a través de la dirección URL es inválido" in wb.web_browser.page_source) and not("El número de teléfono compartido a través de la dirección URL no es válido" in wb.web_browser.page_source):
                    time.sleep(3)
                    wb.css_click("button[aria-label=Enviar],span[data-icon='plus-rounded']")
                    time.sleep(3)
                    wb.x_click("//span[text()='Fotos y videos']//ancestor::li | //div[@aria-label='Fotos y videos']")
                    wb.elem_wait("input[type=file][accept*=video]")
                    time.sleep(5)
                    # wb.js_click("div[title='Adjuntar'], button[title='Adjuntar']")
                    wb.send_keys("input[type=file][accept*=video]", image, full=True)
                    time.sleep(10)
                    try:
                        pyautogui.getWindowsWithTitle("Open")[0].activate()
                        time.sleep(1)
                        pyautogui.press('esc')
                    except:
                        print("open dialog close failed.")

                    time.sleep(5)
                    res1 = wb.css_click("div[aria-label=Enviar]")
                    time.sleep(5)

                    print("sending message:", res1)
                    if wb.elem_wait('div.message-out'):
                        print('message sent.')
                        time.sleep(15)
                    else:
                        print('message NOT sent.', booking_data['wa_link'])
                else:
                    print("chat url is not valid.")
            else:
                print('invalid whatsapp link')

            # saving to record to avoid sending again.
            with open(sent_messages_fp, 'a') as f:
                message_id = booking_data['booking_date'] + booking_data['wa_link']
                f.write(message_id + '\n')

    except Exception as error_inner1:
        print('outer.', str(error_inner1), str(error_inner1.__traceback__.tb_lineno))


def send_message_to_group(all_booking_data):
    try:
        cdo = datetime.datetime.now()
        if cdo.hour == 9:
            current_date_string = cdo.strftime('%D')
            if not os.path.exists(dates_file_path):
                json.dump(obj=[], fp=open(dates_file_path, 'w', encoding='utf-8'), indent=1)
            all_dates = json.load(open(dates_file_path, 'r', encoding='utf-8'))
            if not (current_date_string in all_dates):
                print('flushing record on new day.')
                os.remove(colleagues_messages_data_fp)
                all_dates.append(current_date_string)
                json.dump(obj=all_dates, fp=open(dates_file_path, 'w', encoding='utf-8'), indent=1)

        if not (os.path.exists(colleagues_messages_data_fp)):
            with open(colleagues_messages_data_fp, 'w') as f:
                f.write('[]')

        if cdo.hour in [23, 0, 1, 2, 3, 4, 5, 6, 7, 8]:
            return

        # generating messages
        current_bookings = []
        for bd in all_booking_data:
            if bd['payment_status'].upper().strip() == 'PAGADO':
                ps = 'PAGADO'
            else:
                ps = ''

            if 'familia' in bd['family_or_child_text'].lower():
                foc = '*familia*'

            elif 'family' in bd['family_or_child_text'].lower():
                foc = "*family*"

            elif "niño" in bd['family_or_child_text'].lower() or "si" in bd['family_or_child_text'].lower():
                foc = '*niño*'

            elif "kid" in bd['family_or_child_text'].lower():
                foc = "*kids*"

            elif "años" in bd['family_or_child_text'].lower() or "year" in bd['family_or_child_text'].lower():
                foc = "*" + bd['family_or_child_text'].lower() + '*'

            elif "adults" in bd['family_or_child_text'].lower():
                foc = '*adults*'

            elif "adultos" in bd['family_or_child_text'].lower():
                foc = '*adultos*'

            else:
                foc = 'no'

            if bd['notes'] == '':
                notes_ = ''
            else:
                notes_ = f'({bd["notes"]})'

            if '10' in bd['experience']:
                exp = '*' + bd['experience'] + '*'
            else:
                exp = bd['experience']

            if exp != '':
                exp = 'Ex(' + exp + ')'

            if 'p7' in bd['booking_place'].lower():
                continue

            place__ = places[bd['booking_place'].upper().replace("#", "")]

            current_bookings.append(
                f"{bd['booking_day_name']} {bd['booking_day']} {bd['booking_month']}###{bd['booking_time']} "
                f"{place__} {exp} ({foc}) {ps} {notes_}"
            )

        new_bookings = []
        cancelled_bookings = []
        old_bookings = json.load(open(colleagues_messages_data_fp, 'r'))

        # getting new bookings
        for booking in current_bookings:
            if not (booking in old_bookings):
                new_bookings.append(booking)

        # getting cancelled booking
        for booking in old_bookings:
            if not (booking in current_bookings):
                cancelled_bookings.append(booking)

        if cdo.hour == 0:
            print("it is late night. so, only removing bookings from previous day.")
            if len(cancelled_bookings) > 0:
                for cb_ in cancelled_bookings:
                    while cb_ in old_bookings:
                        old_bookings.remove(cb_)
                json.dump(obj=old_bookings, fp=open(colleagues_messages_data_fp, 'w'), indent=1)

            return

        print(f'current bookings: {len(current_bookings)} '
              f'old bookings: {len(old_bookings)} '
              f'cancelled bookings: {len(cancelled_bookings)}')

        if len(new_bookings) > 0 or len(cancelled_bookings) > 0:
            messages_set = {}

            for booking in current_bookings:
                booking_comps = booking.split('###')
                booking_date_title = booking_comps[0]
                booking_text = booking_comps[1]

                if booking in new_bookings:
                    message = "*NEW* " + booking_text
                else:
                    message = booking_text

                message = message.strip()
                if booking_date_title in messages_set:
                    messages_set[booking_date_title].append(message)
                else:
                    messages_set[booking_date_title] = []
                    messages_set[booking_date_title].append(message)

            for booking in cancelled_bookings:
                if int(cdo.hour) == 0:
                    continue

                booking_comps = booking.split('###')
                booking_date_title = booking_comps[0]
                message = "*cancel* " + booking_comps[1]

                message = message.strip()
                if booking_date_title in messages_set:
                    messages_set[booking_date_title].append(message)
                else:
                    messages_set[booking_date_title] = []
                    messages_set[booking_date_title].append(message)

            # sending message to group here.
            if int(cdo.hour) != 0 or len(new_bookings) > 0:
                wb.get(group_link)
                # wb.get("https://api.whatsapp.com/send/?phone=923427382557")
                wb.css_click_with_timer("#action-button", 40)
                wb.x_click_with_timer('//*[contains(text(), "usar WhatsApp Web")] | //*[contains(text(), "use WhatsApp Web")] | //*[contains(text(), "Continue to WhatsApp Web")]', 20)

                for message_tuple in sorted(messages_set.items(), key=lambda y: int(y[0].split(' ')[1])):
                    message_date = message_tuple[0].strip() + '\n\n'
                    cb = []
                    nb = []
                    for ind, msg in enumerate(message_tuple[1]):
                        if '*NEW*' in msg:
                            nm = msg.replace('*NEW*', '').strip()
                            message_tuple[1][ind] = nm
                            nb.append(nm)

                        if '*cancel*' in msg:
                            nm = msg.replace('*cancel*', '').strip()
                            message_tuple[1][ind] = nm
                            cb.append(nm)

                    nmt = sorted(message_tuple[1])
                    for ind, each_ in enumerate(nmt):
                        if each_ in nb:
                            nmt[ind] = '*NEW* ' + each_
                        if each_ in cb:
                            nmt[ind] = '*cancel* ' + each_

                    message = '\n'.join(nmt).strip()
                    final_message = message_date + message
                    if not ("NEW" in final_message) and not ("cancel" in final_message):
                        continue

                    if "*NEW* 16:00" in final_message:
                        final_message = final_message.replace('*NEW* 16:00', "\n*NEW* 16:00", 1)
                    elif "16:00" in final_message:
                        final_message = final_message.replace('16:00', "\n16:00", 1)

                    wb.send_keys("div[title='Escribe un mensaje'],div[aria-label='Escribe un mensaje'],div[aria-placeholder='Escribe un mensaje']", final_message)
                    if wb.js_click("span[data-icon='wds-ic-send-filled'],span[data-testid=send],span[data-icon=send],button[aria-label='Enviar'],div[aria-label='Enviar']"):
                        time.sleep(3)

                    time.sleep(7)

                time.sleep(15)
                if not (os.path.exists(first_time_done_fp)):
                    with open(first_time_done_fp, 'w') as f:
                        f.write('done.')

            # saving sent message to avoid sending again.
            json.dump(obj=current_bookings, fp=open(colleagues_messages_data_fp, 'w'), indent=1)

    except Exception as error_inner1:
        print('outer.', str(error_inner1), str(error_inner1.__traceback__.tb_lineno))


# ============================================================
# MODULE 1 — Scrape Photo Group
# ============================================================

def parse_photo_caption(caption_text):
    """Parse caption like '14/3 17:30 csi' or '14/3 17:30/40 csi' or '14/3 17:30 csi/maf'.
    Returns dict with date, times[], salas[] or None if invalid."""
    caption_text = caption_text.lower().strip()
    # Format: dd/m HH:MM[/mm] sala[/sala2/sala3...]
    match = re.search(
        r'(\d{1,2}/\d{1,2})\s+(\d{1,2}:\d{2})(?:/(\d{2}))?\s+((?:4e|csi|maf|tri)(?:/(?:4e|csi|maf|tri))*)',
        caption_text
    )
    if not match:
        return None

    date_str = match.group(1)   # "14/3"
    time1 = match.group(2)      # "17:30"
    time2_min = match.group(3)  # "40" or None
    salas = match.group(4).split('/')  # ["csi"] or ["csi", "maf"]

    times = [time1]
    if time2_min:
        hour = time1.split(':')[0]
        times.append(f"{hour}:{time2_min}")

    return {'date': date_str, 'times': times, 'salas': salas}


def download_wa_image(img_element, save_path, max_retries=3):
    """Download an image from WhatsApp Web blob URL using JS fetch + base64.
    Retries up to max_retries times on failure."""
    for attempt in range(1, max_retries + 1):
        try:
            # Check that the element still has a valid blob src
            src = img_element.get_attribute('src') or ''
            if not src.startswith('blob:'):
                print(f'  attempt {attempt}: img src is not a blob ({src[:50]}), skipping')
                time.sleep(2)
                continue

            base64_data = wb.web_browser.execute_async_script("""
                var callback = arguments[arguments.length - 1];
                var imgEl = arguments[0];
                fetch(imgEl.src)
                    .then(function(r) { return r.blob(); })
                    .then(function(blob) {
                        var reader = new FileReader();
                        reader.onloadend = function() { callback(reader.result); };
                        reader.readAsDataURL(blob);
                    })
                    .catch(function(err) { callback('ERROR:' + err.toString()); });
            """, img_element)

            if base64_data and not str(base64_data).startswith('ERROR:'):
                if ',' in base64_data:
                    base64_data = base64_data.split(',')[1]
                raw = base64.b64decode(base64_data)
                # Verify we got actual image data (at least 5KB to avoid thumbnails)
                if len(raw) < 5000:
                    print(f'  attempt {attempt}: downloaded data too small ({len(raw)} bytes), might be thumbnail. Retrying...')
                    time.sleep(3)
                    continue
                with open(save_path, 'wb') as f:
                    f.write(raw)
                print(f'photo downloaded ({len(raw)} bytes): {save_path}')
                return True
            else:
                print(f'  attempt {attempt}: failed to download image: {base64_data}')
                time.sleep(3)
        except Exception as e:
            print(f'  attempt {attempt}: error downloading image: {e}')
            time.sleep(3)

    print(f'all {max_retries} download attempts failed for {save_path}')
    return False


def scrape_photo_group():
    """Scrape the photo group for new messages with photos and captions."""
    photo_entries = []
    try:
        print('--- Module 1: Scraping photo group ---')

        # Use a list of processed IDs to avoid processing old messages
        processed_ids_fp = os.path.join(sys.path[0], 'data', 'processed_photo_ids.json')
        processed_ids = []
        if os.path.exists(processed_ids_fp):
            try:
                with open(processed_ids_fp, 'r', encoding='utf-8') as f:
                    processed_ids = json.load(f)
            except:
                pass

        print(f'  Searching for group: "{photo_group_name}"')

        # Click search box
        search_clicked = wb.css_click_with_timer("div[contenteditable='true'][data-tab='3']", 15)
        if not search_clicked:
            search_clicked = wb.css_click_with_timer("div[role='textbox'][data-tab='3']", 10)
        if not search_clicked:
            search_clicked = wb.x_click_with_timer("//div[@data-tab='3']", 10)
        time.sleep(2)

        # Type group name
        search_box = wb.web_browser.find_element(By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='3']")
        search_box.clear()
        search_box.send_keys(photo_group_name)
        time.sleep(3)

        # Click on the group result
        group_clicked = wb.x_click_with_timer(f"//span[@title='{photo_group_name}']", 15)
        if not group_clicked:
            print('  [ERROR] Could not find group in search results!')
            return photo_entries

        time.sleep(10)

        # Scroll up to load more messages (load enough history to catch all photos)
        try:
            chat_pane = None
            for pane_sel in ["div[role='application']", "div.copyable-area div[tabindex]", "div._ajyl"]:
                try:
                    chat_pane = wb.web_browser.find_element(By.CSS_SELECTOR, pane_sel)
                    break
                except:
                    continue
            if chat_pane:
                for _ in range(8):
                    wb.web_browser.execute_script("arguments[0].scrollTop = 0;", chat_pane)
                    time.sleep(2)
                # Scroll back down to load all messages in view
                wb.web_browser.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", chat_pane)
                time.sleep(3)
        except:
            pass

        os.makedirs(downloaded_photos_dir, exist_ok=True)

        # Use robust selectors to find messages
        msg_containers = wb.web_browser.find_elements(By.CSS_SELECTOR, "div[data-id]")
        messages = msg_containers if msg_containers else wb.web_browser.find_elements(By.CSS_SELECTOR, "div.message-in")

        incoming_messages = []
        for m in messages:
            try:
                data_id = m.get_attribute('data-id') or ''
                if 'true' in data_id: continue
                incoming_messages.append(m)
            except:
                incoming_messages.append(m)

        print(f'found {len(incoming_messages)} messages in photo group.')

        found_new = False
        new_processed = set()

        for idx, msg in enumerate(incoming_messages):
            try:
                # 0. Get unique message ID
                msg_id = msg.get_attribute('data-id') or f"unknown_{idx}"
                if msg_id in processed_ids or msg_id in new_processed:
                    continue

                copyable_els = msg.find_elements(By.CSS_SELECTOR, "[data-pre-plain-text]")
                if not copyable_els:
                    try:
                        parent = msg.find_element(By.XPATH, "./..")
                        copyable_els = parent.find_elements(By.CSS_SELECTOR, "[data-pre-plain-text]")
                    except:
                        pass

                if copyable_els:
                    pre_text = copyable_els[0].get_attribute("data-pre-plain-text").strip()
                    msg_timestamp = pre_text
                else:
                    msg_timestamp = f"msg_{idx}"

                msg_text = msg.get_attribute('innerText') or msg.text or ''

                # 1. Parse caption directly from entire message text block
                parsed = parse_photo_caption(msg_text)
                if not parsed:
                    # Check if this message has a photo (image with bad/missing caption)
                    has_image = bool(msg.find_elements(By.CSS_SELECTOR, "img[src*='blob:']"))
                    if not has_image:
                        has_image = bool(msg.find_elements(By.CSS_SELECTOR, "span[data-icon='download'], span[data-icon='arrow-down']"))

                    if has_image:
                        bad_caption_replied = _load_json_set(bad_caption_ids_fp)
                        if msg_id not in bad_caption_replied:
                            print(f'  Photo with BAD nomenclature detected! Replying...')
                            try:
                                ActionChains(wb.web_browser).context_click(msg).perform()
                                time.sleep(1)
                                reply_clicked = wb.css_click_with_timer(
                                    "div[aria-label='Responder'], div[aria-label='Reply'], li[data-animate-dropdown-item='true']:first-child",
                                    5
                                )
                                if reply_clicked:
                                    time.sleep(1)
                                    reply_text = (
                                        "⚠️ Esta foto no tiene el formato correcto.\n"
                                        "Por favor reenvíala con el formato:\n\n"
                                        "📝 *dia/mes hora sala*\n"
                                        "Ejemplo: 24/3 19:10 csi\n"
                                        "Varias salas: 24/3 19:10 csi/tri\n"
                                        "Salas válidas: 4e, csi, maf, tri"
                                    )
                                    import pyperclip
                                    pyperclip.copy(reply_text)
                                    time.sleep(0.5)
                                    chat_input = wb.web_browser.find_element(
                                        By.CSS_SELECTOR, "footer div[contenteditable='true']"
                                    )
                                    chat_input.click()
                                    time.sleep(0.5)
                                    chat_input.send_keys(Keys.CONTROL, 'v')
                                    time.sleep(1)
                                    chat_input.send_keys(Keys.ENTER)
                                    time.sleep(2)
                                    print(f'  -> Replied with format instructions.')
                                else:
                                    print(f'  -> Could not open reply menu.')
                                    ActionChains(wb.web_browser).send_keys(Keys.ESCAPE).perform()
                                    time.sleep(0.5)
                            except Exception as reply_err:
                                print(f'  -> Error replying to bad caption: {reply_err}')
                                try:
                                    ActionChains(wb.web_browser).send_keys(Keys.ESCAPE).perform()
                                except:
                                    pass

                            bad_caption_replied.add(msg_id)
                            _save_json_set(bad_caption_ids_fp, bad_caption_replied)

                    new_processed.add(msg_id)
                    continue
                    
                found_new = True

                print(f'mapped caption: {parsed["date"]} {parsed["times"]} {"/".join(parsed["salas"])}')
                
                # 2. Check for image - try multiple strategies to find it
                img_elements = msg.find_elements(By.CSS_SELECTOR, "img[src*='blob:']")

                if not img_elements:
                    # Strategy A: Look for download button (image not auto-downloaded)
                    dl_icons = msg.find_elements(By.CSS_SELECTOR,
                        "span[data-icon='download'], span[data-icon='arrow-down'], span[data-icon='media-download']")
                    if dl_icons:
                        print(f'  clicking download button for message...')
                        for dl_icon in dl_icons:
                            try:
                                wb.web_browser.execute_script("arguments[0].scrollIntoView(true);", dl_icon)
                                time.sleep(0.5)
                                try:
                                    dl_icon.find_element(By.XPATH, "..").click()
                                except:
                                    dl_icon.click()
                                break
                            except:
                                continue
                        # Wait longer for download to complete (images can be large)
                        for wait_round in range(15):
                            time.sleep(2)
                            img_elements = msg.find_elements(By.CSS_SELECTOR, "img[src*='blob:']")
                            if img_elements:
                                print(f'  image appeared after {(wait_round+1)*2}s wait')
                                break
                    else:
                        # Strategy B: Click the message itself to trigger load
                        try:
                            msg.click()
                        except:
                            pass
                        time.sleep(8)
                        img_elements = msg.find_elements(By.CSS_SELECTOR, "img[src*='blob:']")

                if not img_elements:
                    print(f'  could not find image blob after all strategies, will retry next cycle')
                    continue

                timestamp_clean = re.sub(r'[^\w]', '_', msg_timestamp)[:30]
                photo_filename = f"photo_{timestamp_clean}.jpg"
                photo_path = os.path.join(downloaded_photos_dir, photo_filename)

                download_success = False

                # Strategy 1: Open image viewer for full-size image
                for viewer_attempt in range(2):
                    try:
                        wb.web_browser.execute_script("arguments[0].scrollIntoView(true);", img_elements[0])
                        time.sleep(1)
                        wb.web_browser.execute_script("arguments[0].click();", img_elements[0])
                        time.sleep(5)

                        # Look for the full-size image in viewer (it's usually the last blob img)
                        viewer_imgs = wb.web_browser.find_elements(By.CSS_SELECTOR, "img[src*='blob:']")
                        # Filter to find viewer images (usually larger/different from chat thumbnails)
                        if len(viewer_imgs) > len(img_elements):
                            # New blob images appeared = viewer opened
                            download_success = download_wa_image(viewer_imgs[-1], photo_path)

                        if not download_success and viewer_imgs:
                            # Try each blob image from last to first (last is usually the viewer)
                            for vi in reversed(viewer_imgs):
                                download_success = download_wa_image(vi, photo_path, max_retries=1)
                                if download_success:
                                    break

                        # Close viewer
                        wb.css_click_with_timer("span[data-icon='x'], span[data-icon='x-viewer'], span[data-icon='back']", 5)
                        time.sleep(2)

                        if download_success:
                            break
                    except Exception as viewer_err:
                        print(f'  viewer attempt {viewer_attempt+1} error: {viewer_err}')
                        try:
                            wb.css_click_with_timer("span[data-icon='x'], span[data-icon='x-viewer']", 5)
                            time.sleep(1)
                        except:
                            pass

                # Strategy 2: If viewer failed, download directly from thumbnail blob
                if not download_success:
                    print(f'  viewer download failed, trying direct thumbnail download...')
                    for img_el in img_elements:
                        download_success = download_wa_image(img_el, photo_path)
                        if download_success:
                            break

                if download_success:
                    parsed['photo_path'] = photo_path
                    parsed['msg_timestamp'] = msg_timestamp
                    photo_entries.append(parsed)
                    print(f'photo entry downloaded: {parsed["date"]} {parsed["times"]} {"/".join(parsed["salas"])}')
                    new_processed.add(msg_id)
                else:
                    print(f'  ALL download strategies failed for this photo. Will retry next cycle.')

            except Exception as e_msg:
                print(f'error processing message: {e_msg}')
                try:
                    wb.css_click_with_timer("span[data-icon='x'], span[data-icon='x-viewer']", 5)
                except:
                    pass
                continue

        # Save updated processed IDs
        if new_processed:
            processed_ids.extend(list(new_processed))
            processed_ids = processed_ids[-500:]
            with open(processed_ids_fp, 'w', encoding='utf-8') as f:
                json.dump(processed_ids, f)
            print('updated processed message IDs.')

        if not found_new:
            print('no new messages in photo group.')

        print(f'--- Module 1 complete: {len(photo_entries)} photo entries found ---')

    except Exception as e:
        print(f'error in scrape_photo_group: {e}')

    return photo_entries


# ============================================================
# MODULE 2 — Match with Turitop & Send Photo to Client
# ============================================================

def scrape_turitop_for_date(target_day, target_month):
    """Scrape Turitop bookings for a specific date. Returns list of booking dicts."""
    bookings = []
    try:
        year = datetime.datetime.now().year
        target_date = f"{int(target_day):02d}-{int(target_month):02d}-{year}"
        print(f'scraping turitop for date: {target_date}')

        # Open new tab for Turitop
        wb.web_browser.execute_script("window.open('')")
        wb.web_browser.switch_to.window(wb.web_browser.window_handles[-1])

        wb.get("https://app.turitop.com/admin/company/P271/bookings")
        time.sleep(5)

        if "admin/login/es/" in wb.web_browser.current_url:
            print("turitop logged out, skipping photo matching this cycle.")
            wb.web_browser.close()
            wb.web_browser.switch_to.window(wb.web_browser.window_handles[0])
            return bookings

        wb.send_keys("#filter_event_date_from", target_date, full=True, clear=True)
        wb.send_keys("#filter_event_date_to", target_date, full=True, clear=True)
        time.sleep(2)
        wb.js_click("button[type=submit][name=action]")
        time.sleep(3)

        for booking_page in range(1, 5):
            wb.send_keys("#filter_event_date_from", target_date, full=True, clear=True)
            wb.send_keys("#filter_event_date_to", target_date, full=True, clear=True)
            time.sleep(1)
            wb.js_click("button[type=submit][name=action]")
            time.sleep(3)
            wb.get(
                f"https://app.turitop.com/admin/company/P271/bookings/list/page/{booking_page}"
            )
            time.sleep(5)

            rows = wb.web_browser.find_elements(
                By.CSS_SELECTOR, "tr.bookings-history-row:not([class*='deleted'])"
            )
            if len(rows) == 0:
                break

            for each in rows:
                try:
                    booking_day = wb.get_text("div.format-day-of-month-number", each)
                    booking_time = wb.get_text("div.format-time-short", each)
                    booking_place = wb.get_text("span.bookings-product-name", each)
                    wa_link = wb.get_attr("a.whatsapp-button", "href", each)
                    booking_month = wb.get_text("div.format-month-name-short", each)
                    booking_year = wb.get_text("div.format-year-long", each)
                    booking_date = f'{booking_day} {booking_month} {booking_year}'

                    d = {
                        "booking_time": booking_time,
                        "booking_day": booking_day,
                        "booking_place": booking_place,
                        "wa_link": wa_link,
                        "booking_date": booking_date,
                    }
                    if d not in bookings:
                        bookings.append(d)
                except Exception as e_inner:
                    print(f'error scraping booking row: {e_inner}')

        print(f'found {len(bookings)} bookings for {target_date}')

        # Close Turitop tab, return to WA
        wb.web_browser.close()
        wb.web_browser.switch_to.window(wb.web_browser.window_handles[0])

    except Exception as e:
        print(f'error in scrape_turitop_for_date: {e}, line: {e.__traceback__.tb_lineno}')
        try:
            if len(wb.web_browser.window_handles) > 1:
                wb.web_browser.close()
                wb.web_browser.switch_to.window(wb.web_browser.window_handles[0])
        except:
            pass

    return bookings


def match_and_send_photos(photo_entries):
    """Match photo entries with Turitop bookings and send photos to clients."""
    try:
        print('--- Module 2: Matching photos with bookings ---')

        if not os.path.exists(photo_sent_messages_fp):
            with open(photo_sent_messages_fp, 'w') as f:
                f.write('')

        # Collect unique dates and scrape Turitop for each
        dates_to_scrape = set()
        for entry in photo_entries:
            dates_to_scrape.add(entry['date'])

        bookings_by_date = {}
        for date_str in dates_to_scrape:
            parts = date_str.split('/')
            day, month = parts[0], parts[1]
            bookings_by_date[date_str] = scrape_turitop_for_date(day, month)
            time.sleep(3)

        # Ensure we are on WA tab
        wb.web_browser.switch_to.window(wb.web_browser.window_handles[0])

        # Load pending replies
        if not os.path.exists(pending_replies_fp):
            json.dump([], open(pending_replies_fp, 'w'), indent=2)
        pending = json.load(open(pending_replies_fp, 'r'))

        for entry in photo_entries:
            date_str = entry['date']
            salas = entry['salas']
            photo_path = entry['photo_path']
            target_places = []
            for s in salas:
                target_places.extend(sala_to_places.get(s, []))
            sala_label = '/'.join(salas)
            day_num = date_str.split('/')[0]
            bookings = bookings_by_date.get(date_str, [])

            for t in entry['times']:
                print(f'matching: date={date_str} time={t} salas={sala_label}')

                matched_booking = None
                for b in bookings:
                    b_place = b['booking_place'].upper().replace('#', '')
                    if (b['booking_time'].strip() == t.strip() and
                            b['booking_day'].strip() == day_num.strip() and
                            any(p.upper() in b_place for p in target_places)):
                        matched_booking = b
                        break

                if not matched_booking:
                    print(f'no matching booking for {date_str} {t} {sala_label}')
                    continue

                if not matched_booking.get('wa_link'):
                    print('booking found but no WhatsApp link.')
                    continue

                # Check if already sent
                sent_id = f"{date_str}_{t}_{sala_label}_{matched_booking['wa_link']}"

                with open(photo_sent_messages_fp, 'r') as f:
                    if sent_id in f.read():
                        print('photo already sent for this booking, skipping.')
                        continue

                # Note: we no longer permanently skip failed sends.
                # Each cycle gets a fresh chance to send.

                # Send photo + message to client
                print(f'sending photo to client: {matched_booking["wa_link"]}')
                link = matched_booking['wa_link'].replace("%20", "").lower().replace("api.", "web.")
                wb.get(link)
                time.sleep(6)

                invalid_markers = [
                    "Enlace incorrecto",
                    "El número de teléfono compartido a través de la dirección URL es inválido",
                    "El número de teléfono compartido a través de la dirección URL no es válido",
                    "no está en WhatsApp"
                ]
                if any(m in wb.web_browser.page_source for m in invalid_markers):
                    print('invalid whatsapp link for client.')
                    continue

                # Load thank-you template from file
                with open(photo_thank_you_template_fp, 'r', encoding='utf-8') as f:
                    photo_thank_you_msg = f.read().strip()

                send_success = False
                for send_attempt in range(1, 3):  # Try up to 2 times
                    try:
                        import subprocess
                        import pyperclip
                        from selenium.webdriver.common.keys import Keys

                        # 1. Copy image to Windows clipboard via PowerShell FIRST (before focusing browser)
                        print(f"  send attempt {send_attempt}: copying image to OS clipboard...")
                        photo_ps_path = os.path.abspath(photo_path).replace("\\", "/")
                        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile('{photo_ps_path}')
[System.Windows.Forms.Clipboard]::SetImage($img)
$img.Dispose()
"""
                        subprocess.run(["powershell", "-STA", "-command", ps_script], check=True, timeout=30)

                        # 2. Re-focus browser window (PowerShell stole focus)
                        wb.web_browser.switch_to.window(wb.web_browser.current_window_handle)
                        time.sleep(2)

                        # 3. Click chat input to ensure it's focused and interactable
                        chat_input = None
                        for selector in [
                            "footer div[contenteditable='true']",
                            "div[contenteditable='true'][data-tab]",
                            "div[title='Escribe un mensaje aquí']",
                            "div[title='Escribe un mensaje']",
                            "div[title='Type a message']",
                            "div[aria-placeholder='Escribe un mensaje']"
                        ]:
                            try:
                                chat_input = wb.web_browser.find_element(By.CSS_SELECTOR, selector)
                                wb.web_browser.execute_script("arguments[0].scrollIntoView(true);", chat_input)
                                time.sleep(0.5)
                                chat_input.click()
                                break
                            except:
                                continue

                        if not chat_input:
                            print("  could not find chat input, trying active element...")

                        time.sleep(1)

                        # 4. Paste image into WhatsApp chat
                        print("  pasting image into WhatsApp...")
                        paste_ok = False
                        for paste_try in range(3):
                            try:
                                if chat_input:
                                    chat_input.send_keys(Keys.CONTROL, 'v')
                                else:
                                    wb.web_browser.switch_to.active_element.send_keys(Keys.CONTROL, 'v')
                                paste_ok = True
                                break
                            except Exception as paste_err:
                                print(f"  paste try {paste_try+1} failed: {paste_err}")
                                time.sleep(1)
                                try:
                                    ActionChains(wb.web_browser).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                                    paste_ok = True
                                    break
                                except:
                                    time.sleep(2)

                        if not paste_ok:
                            print("  all paste attempts failed, retrying send...")
                            continue

                    except Exception as e:
                        print(f'  error pasting image (attempt {send_attempt}): {e}')
                        continue

                    print("  waiting for image preview overlay...")
                    # Wait longer and check if preview actually appeared
                    # Detect by editing toolbar icons OR caption input variants
                    preview_found = False
                    for wait_i in range(15):
                        time.sleep(2)
                        for preview_sel in [
                            "div[aria-placeholder*='Añade']",
                            "div[aria-placeholder*='Add a caption']",
                            "div[aria-placeholder*='Escribe un mensaje']",
                            "div[title*='comentario']",
                            "span[data-icon='pencil']",
                            "span[data-icon='crop']",
                            "span[data-icon='scissors']",
                            "span[data-icon='text']",
                            "span[data-icon='sticker']",
                            "span[data-icon='emoji']",
                        ]:
                            try:
                                found = wb.web_browser.find_elements(By.CSS_SELECTOR, preview_sel)
                                if found:
                                    preview_found = True
                                    print(f"  preview detected via '{preview_sel}' after {(wait_i+1)*2}s")
                                    break
                            except:
                                continue
                        if preview_found:
                            break

                    if not preview_found:
                        print(f"  image preview did not appear (attempt {send_attempt}), retrying...")
                        # Press Escape to dismiss any partial overlay
                        try:
                            ActionChains(wb.web_browser).send_keys(Keys.ESCAPE).perform()
                            time.sleep(2)
                        except:
                            pass
                        continue

                    print("  typing caption with clipboard to preserve format...")
                    caption_box = None
                    for cap_sel in [
                        "div[aria-placeholder*='Añade']",
                        "div[aria-placeholder*='Add a caption']",
                        "div[aria-placeholder*='Escribe un mensaje']",
                        "div[title*='comentario']",
                    ]:
                        try:
                            caption_box = wb.web_browser.find_element(By.CSS_SELECTOR, cap_sel)
                            caption_box.click()
                            print(f"  caption box found via '{cap_sel}'")
                            break
                        except:
                            continue
                    if not caption_box:
                        print("  could not find specific caption box, falling back to active element")
                        caption_box = wb.web_browser.switch_to.active_element

                    pyperclip.copy(photo_thank_you_msg)
                    time.sleep(1)
                    caption_box.send_keys(Keys.CONTROL, 'v')

                    time.sleep(3)

                    res = wb.css_click("div[aria-label=Enviar],span[data-icon='send'],span[data-icon='wds-ic-send-filled']")
                    time.sleep(5)

                    print(f"  sending photo result: {res}")
                    # Wait for the message to appear as sent
                    for check_i in range(10):
                        out_msgs = wb.web_browser.find_elements(By.CSS_SELECTOR, 'div.message-out')
                        if out_msgs:
                            send_success = True
                            break
                        time.sleep(2)

                    if send_success:
                        print('  photo with caption sent to client!')
                        time.sleep(5)
                        break
                    else:
                        print(f'  photo NOT confirmed as sent (attempt {send_attempt})')
                        # Press Escape and retry
                        try:
                            ActionChains(wb.web_browser).send_keys(Keys.ESCAPE).perform()
                            time.sleep(2)
                        except:
                            pass

                if send_success:
                    # Record as sent
                    with open(photo_sent_messages_fp, 'a') as f:
                        f.write(sent_id + '\n')

                    # Add to pending replies
                    pending.append({
                        'wa_link': matched_booking['wa_link'],
                        'timestamp_sent': datetime.datetime.now().isoformat(),
                        'booking_code': f"{date_str}_{t}_{sala_label}",
                        'booking_date': matched_booking.get('booking_date', '')
                    })
                else:
                    print(f'  photo send FAILED after all attempts for {sent_id}. Will retry next cycle.')

        # Save pending replies
        json.dump(pending, open(pending_replies_fp, 'w'), indent=2)
        print(f'--- Module 2 complete: {len(pending)} pending replies ---')

    except Exception as e:
        print(f'error in match_and_send_photos: {e}, line: {e.__traceback__.tb_lineno}')


# ============================================================
# MODULE 3 — AI Response Classification
# ============================================================

def classify_reply_with_ai(reply_text):
    """Send reply text to OpenRouter GPT-4o mini for POSITIVO/NEGATIVO/NEUTRAL."""
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = json.dumps({
            "model": "openai/gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Classify the following customer reply about their escape room "
                        "experience as exactly one word: POSITIVO, NEGATIVO, or NEUTRAL. "
                        "Reply with only that one word."
                    )
                },
                {"role": "user", "content": reply_text}
            ],
            "max_tokens": 10,
            "temperature": 0
        }).encode('utf-8')

        req = urllib.request.Request(url, data=payload, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', f'Bearer {openrouter_api_key}')

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            classification = result['choices'][0]['message']['content'].strip().upper()
            print(f'AI classification: {classification}')

            if 'POSITIVO' in classification or 'POSITIVE' in classification:
                return 'POSITIVO'
            elif 'NEGATIVO' in classification or 'NEGATIVE' in classification:
                return 'NEGATIVO'
            else:
                return 'NEUTRAL'

    except Exception as e:
        print(f'error calling OpenRouter API: {e}')
        return 'NEUTRAL'


def check_pending_replies():
    """Check pending replies for client responses and classify with AI."""
    try:
        print('--- Module 3: Checking pending replies ---')

        if not os.path.exists(pending_replies_fp):
            print('no pending replies file.')
            return

        pending = json.load(open(pending_replies_fp, 'r'))
        if len(pending) == 0:
            print('no pending replies.')
            return

        updated_pending = []
        now = datetime.datetime.now()

        for entry in pending:
            try:
                sent_time = datetime.datetime.fromisoformat(entry['timestamp_sent'])
                hours_elapsed = (now - sent_time).total_seconds() / 3600

                if hours_elapsed > 24:
                    print(f'pending reply expired (>24h): {entry["booking_code"]}')
                    continue  # discard

                # Navigate to client chat
                link = entry['wa_link'].replace("%20", "").lower().replace("api.", "web.")
                wb.get(link)
                time.sleep(6)

                invalid_markers = [
                    "Enlace incorrecto",
                    "El número de teléfono compartido a través de la dirección URL es inválido",
                    "El número de teléfono compartido a través de la dirección URL no es válido",
                    "no está en WhatsApp"
                ]
                if any(m in wb.web_browser.page_source for m in invalid_markers):
                    print('invalid chat link, removing from pending.')
                    continue

                time.sleep(3)

                # Check if last message in chat is incoming (client replied)
                all_msgs = wb.web_browser.find_elements(
                    By.CSS_SELECTOR, "div.message-in, div.message-out"
                )
                if len(all_msgs) == 0:
                    updated_pending.append(entry)
                    continue

                last_msg = all_msgs[-1]
                msg_classes = last_msg.get_attribute('class') or ''
                if 'message-in' not in msg_classes:
                    print(f'no reply yet from client: {entry["booking_code"]}')
                    updated_pending.append(entry)
                    continue

                # Intentar extraer el texto real del mensaje (no metadata/timestamps)
                reply_text = ''
                try:
                    span = last_msg.find_element(
                        By.CSS_SELECTOR,
                        "span.selectable-text, span[class*='selectable-text'], div[class*='copyable-text'] span"
                    )
                    reply_text = (span.get_attribute('innerText') or span.text or '').strip()
                except Exception:
                    pass
                if not reply_text:
                    reply_text = wb.get_text(last_msg)

                if not reply_text or reply_text.strip() == '':
                    print('empty reply, keeping in pending.')
                    updated_pending.append(entry)
                    continue

                print(f'client reply: {reply_text[:100]}')

                # Classify with AI
                classification = classify_reply_with_ai(reply_text)

                import pyperclip
                from selenium.webdriver.common.keys import Keys

                if classification == 'POSITIVO':
                    print('positive reply! sending review link.')
                    with open(positive_review_template_fp, 'r', encoding='utf-8') as f:
                        review_msg = f.read().strip()

                    try:
                        chat_input = wb.web_browser.find_element(
                            By.CSS_SELECTOR, "footer div[contenteditable='true']"
                        )
                        chat_input.click()
                        time.sleep(0.5)

                        pyperclip.copy(review_msg)
                        chat_input.send_keys(Keys.CONTROL, 'v')
                        time.sleep(1)
                        chat_input.send_keys(Keys.ENTER)
                        time.sleep(3)
                        print('review link sent.')
                    except Exception as ex:
                        print(f'error sending positive review msg: {ex}')
                        updated_pending.append(entry)
                        continue

                elif classification == 'NEGATIVO':
                    print('negative reply, sending empathy message.')
                    with open(negative_review_template_fp, 'r', encoding='utf-8') as f:
                        neg_msg = f.read().strip()

                    try:
                        chat_input = wb.web_browser.find_element(
                            By.CSS_SELECTOR, "footer div[contenteditable='true']"
                        )
                        chat_input.click()
                        time.sleep(0.5)

                        pyperclip.copy(neg_msg)
                        chat_input.send_keys(Keys.CONTROL, 'v')
                        time.sleep(1)
                        chat_input.send_keys(Keys.ENTER)
                        time.sleep(3)
                        print('negative response sent.')
                    except Exception as ex:
                        print(f'error sending negative empathy msg: {ex}')
                        updated_pending.append(entry)
                        continue

                else:
                    print('neutral reply, not sending anything.')

                # Processed — do not add to updated_pending

            except Exception as e_entry:
                print(f'error processing pending: {e_entry}, line: {e_entry.__traceback__.tb_lineno}')
                updated_pending.append(entry)  # keep on error

        # Save updated pending
        json.dump(updated_pending, open(pending_replies_fp, 'w'), indent=2)
        print(f'--- Module 3 complete: {len(updated_pending)} still pending ---')

    except Exception as e:
        print(f'error in check_pending_replies: {e}, line: {e.__traceback__.tb_lineno}')


# ============================================================
# MODULE 4 — Daily Cleanup
# ============================================================

def daily_cleanup():
    """Delete old photos (>24h) and expired pending replies."""
    try:
        print('--- Module 4: Daily cleanup ---')
        now = datetime.datetime.now()

        # Clean old photos
        if os.path.exists(downloaded_photos_dir):
            for photo_file in os.listdir(downloaded_photos_dir):
                fp = os.path.join(downloaded_photos_dir, photo_file)
                if os.path.isfile(fp):
                    file_age_hours = (time.time() - os.path.getmtime(fp)) / 3600
                    if file_age_hours > 24:
                        os.remove(fp)
                        print(f'cleaned up old photo: {photo_file}')

        # Clean expired pending replies
        if os.path.exists(pending_replies_fp):
            pending = json.load(open(pending_replies_fp, 'r'))
            updated = []
            for entry in pending:
                try:
                    sent_time = datetime.datetime.fromisoformat(entry['timestamp_sent'])
                    hours_elapsed = (now - sent_time).total_seconds() / 3600
                    if hours_elapsed <= 24:
                        updated.append(entry)
                    else:
                        print(f'removing expired pending: {entry["booking_code"]}')
                except:
                    pass  # remove invalid entries

            if len(updated) != len(pending):
                json.dump(updated, open(pending_replies_fp, 'w'), indent=2)
                print(f'cleaned {len(pending) - len(updated)} expired pending replies.')

        # Clear failed sends so they get retried each day
        if os.path.exists(failed_sends_fp):
            try:
                os.remove(failed_sends_fp)
                print('cleared failed sends tracking (fresh retry).')
            except:
                pass

        print('--- Module 4 complete ---')

    except Exception as e:
        print(f'error in daily_cleanup: {e}, line: {e.__traceback__.tb_lineno}')


time.sleep(10)
print('starting browser.')
wb = Browser()
while 1:
    try:
        while 1:
            wb.web_browser.switch_to.window(wb.web_browser.window_handles[0])
            if len(wb.web_browser.window_handles) > 1:
                wb.web_browser.switch_to.window(wb.web_browser.window_handles[1])
                wb.web_browser.close()
            else:
                break
        wb.web_browser.switch_to.window(wb.web_browser.window_handles[0])
        if not("whatsapp.com" in wb.web_browser.current_url):
            wb.get("https://web.whatsapp.com")
            time.sleep(100)
        else:
            wb.web_browser.refresh()
            time.sleep(100)


        wb.web_browser.execute_script("window.open('')")
        wb.web_browser.switch_to.window(wb.web_browser.window_handles[1])

        
        print('logging in to site.')
        wb.get("https://app.turitop.com/admin/company/P271/bookings")
        if "admin/login/es/" in wb.web_browser.current_url:
            input("we are logged out. please login and press enter to resume.")

        print(f'getting all bookings detail in next {days_to_check_for_booking} days.')
        starting_date_obj = datetime.datetime.now()
        valid_days = []
        for day_count in range(0, days_to_check_for_booking + 1, 1):
            valid_days.append(
                datetime.datetime.fromtimestamp(time.time() + (86400 * day_count)).day
            )

        ending_date_obj = datetime.datetime.fromtimestamp(time.time() + (86400 * days_to_check_for_booking))
        starting_date = starting_date_obj.strftime('%d-%m-%Y')
        ending_date = ending_date_obj.strftime('%d-%m-%Y')

        wb.send_keys("#filter_event_date_from", starting_date, full=True, clear=True)
        wb.send_keys("#filter_event_date_to", ending_date, full=True, clear=True)
        time.sleep(2)
        wb.js_click("button[type=submit][name=action]")
        time.sleep(3)

        print('scraping bookings detail.')
        all_bookings = []
        for booking_page in range(1, 11, 1):
            wb.send_keys("#filter_event_date_from", starting_date, full=True, clear=True)
            wb.send_keys("#filter_event_date_to", ending_date, full=True, clear=True)
            time.sleep(1)
            wb.js_click("button[type=submit][name=action]")
            time.sleep(3)
            wb.get(f"https://app.turitop.com/admin/company/P271/bookings/list/page/{booking_page}")
            time.sleep(5)
            invalid_selection = False
            try:
                for retries in range(5):
                    total_records = int(re.findall(r'\((\d+) en total\)', wb.web_browser.page_source)[0].strip())
                    print('total records:', total_records)
                    if total_records > 300:
                        print('invalid selections. resetting...')
                        invalid_selection = True
                        wb.send_keys("#filter_event_date_from", starting_date, full=True)
                        wb.send_keys("#filter_event_date_to", ending_date, full=True)
                        wb.js_click("button[type=submit][name=action]")
                        time.sleep(5)
                        wb.get(f"https://app.turitop.com/admin/company/P271/bookings/list/page/{booking_page}")
                        time.sleep(10)
                    else:
                        invalid_selection = False
                        break
            except:
                print('could not found the total records.')
                invalid_selection = False

            if invalid_selection:
                print('could not select the correct data. quitting.')
                break

            bookings_on_page = wb.web_browser.find_elements(By.CSS_SELECTOR, "tr.bookings-history-row:not([class*='deleted'])")
            if len(bookings_on_page) == 0:
                break

            for each in bookings_on_page:
                try:
                    booking_day = wb.get_text("div.format-day-of-month-number", each)
                    if not (int(booking_day) in valid_days):
                        print("invalid booking found:", booking_day)
                        continue

                    booking_time = wb.get_text("div.format-time-short", each)
                    booking_day_name = wb.get_text("div.format-day-of-week-name-short", each).replace('(', '').replace(')', '').strip()
                    booking_month = wb.get_text("div.format-month-name-short", each)
                    booking_year = wb.get_text("div.format-year-long", each)
                    booking_date = f'{booking_day} {booking_month} {booking_year}'
                    booking_place = wb.get_text("span.bookings-product-name", each)

                    booking_base_text = each.get_attribute('innerText').strip()
                    experience = wb.re_get_text(r'#1:(.*?),', booking_base_text)
                    family_or_child_text = wb.re_get_text(r'#3:(.*?),', booking_base_text)
                    booking_payment_status = wb.get_text("div.bookings-history-payment-status", each)
                    notes = wb.re_get_text(r'Notas\n\n(.*?)\n\t', booking_base_text)
                    wa_link = wb.get_attr("a.whatsapp-button", "href", each)

                    d = {
                        "booking_time": booking_time,
                        "booking_day": booking_day,
                        "booking_day_name": booking_day_name,
                        "booking_month": booking_month,
                        "booking_year": booking_year,
                        "booking_date": booking_date,
                        "booking_place": booking_place,
                        "experience": experience,
                        "family_or_child_text": family_or_child_text,
                        "payment_status": booking_payment_status,
                        "notes": notes,
                        "wa_link": wa_link
                    }
                    if not (d in all_bookings):
                        all_bookings.append(d)

                except Exception as error_inner:
                    wb.show_error(error_inner)

        print(f'found {len(all_bookings)} bookings in this date range.')
        wb.web_browser.close()
        wb.web_browser.switch_to.window(wb.web_browser.window_handles[0])

        print("sending messages to client.")
        time.sleep(7)

        for each_booking in sorted(all_bookings, key=lambda y: y['booking_time']):
            send_message_to_client(each_booking)

        print("sending messages to colleagues group.")
        send_message_to_group(all_bookings)

        # --- NEW MODULES ---
        # Module 4: Daily cleanup (run first to keep system light)
        daily_cleanup()

        # Module 1: Scrape photo group for new photos with captions
        photo_entries = scrape_photo_group()

        # Module 2: Match photos to Turitop bookings and send to clients
        if photo_entries:
            match_and_send_photos(photo_entries)

        # Module 3: Check pending replies and classify with AI
        check_pending_replies()

    except Exception as error_outer:
        print('outer.', str(error_outer), str(error_outer.__traceback__.tb_lineno))
        try:
            wb.web_browser.quit()
        except Exception as error:
            print(error, error_outer.__traceback__.tb_lineno)
        print('starting browser again.')
        wb = Browser()

    print("waiting for 15 minutes...")
    time.sleep(900)
