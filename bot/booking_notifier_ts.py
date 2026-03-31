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
group_link = 'https://chat.whatsapp.com/EaRWSABnq5NGXLvSKyA4v8'
first_time_done_fp = os.path.join(sys.path[0], 'data', 'ftd')
log_fp = os.path.join(sys.path[0], 'data', 'logs.txt')
dates_file_path = os.path.join(sys.path[0], 'data', 'dates.json')


os.system("title " + os.path.basename(__file__))


class Browser:
    def __init__(self):
        self.waiting_time = 180  # will become half.
        self.debug = False
        try:
            o = Options()
            o.add_argument('--user-data-dir=' + os.path.join(os.environ.get('USERPROFILE', 'C:/Users/Turitop'), 'Desktop', 'booking_bot_profile'))
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
            if "El número de teléfono compartido a través de la dirección URL es inválido" in wb.web_browser.page_source:
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
            if not(os.path.exists(log_fp)):
                with open(log_fp, 'w') as f:
                    f.write(msg + '\n\n')
            else:
                with open(log_fp, 'a') as f:
                    f.write(msg + '\n\n')
            if (int(getsize(log_fp))/1000)/1000 > 1:
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

            if not(os.path.exists(sent_messages_fp)):
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
            if not("Enlace incorrecto. Cierra la venta y vuelve a intentarlo con un enlace diferente." in wb.web_browser.page_source) and not("El número de teléfono compartido a través de la dirección URL es inválido" in wb.web_browser.page_source) and not("El número de teléfono compartido a través de la dirección URL no es válido" in wb.web_browser.page_source):
                # wb.get("https://api.whatsapp.com/send/?phone=+923427382557")
                # wb.css_click("#action-button")
                # wb.x_click('//a[contains(text(), "usar WhatsApp Web")]')
                wb.send_keys("div[title='Escribe un mensaje'],div[aria-label='Escribe un mensaje'],div[aria-placeholder='Escribe un mensaje']", message)

                if not("El número de teléfono compartido a través de la dirección URL es inválido" in wb.web_browser.page_source):
                    time.sleep(3)
                    wb.css_click("button[aria-label=Enviar]")
                    time.sleep(3)
                    wb.js_click("div[title='Adjuntar'], button[title='Adjuntar']")
                    time.sleep(3)
                    wb.send_keys("input[type=file][accept*=video]", image, full=True)
                    time.sleep(4)
                    res = wb.css_click("div[aria-label=Enviar]")
                    print("sending message:", res)
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
            if not(current_date_string in all_dates):
                print('flushing record on new day.')
                os.remove(colleagues_messages_data_fp)
                all_dates.append(current_date_string)
                json.dump(obj=all_dates, fp=open(dates_file_path, 'w', encoding='utf-8'), indent=1)

        if not(os.path.exists(colleagues_messages_data_fp)):
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
            elif "niño" in bd['family_or_child_text'].lower() or "si" in bd['family_or_child_text'].lower():
                foc = '*si*'
            elif "años" in bd['family_or_child_text'].lower():
                foc = "*" + bd['family_or_child_text'].lower() + '*'
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
            if not(booking in old_bookings):
                new_bookings.append(booking)

        # getting cancelled booking
        for booking in old_bookings:
            if not(booking in current_bookings):
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
                wb.css_click_with_timer("#action-button", 60)
                wb.x_click('//*[contains(text(), "usar WhatsApp Web")]')

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
                    if not("NEW" in final_message) and not("cancel" in final_message):
                        continue

                    if "*NEW* 16:00" in final_message:
                        final_message = final_message.replace('*NEW* 16:00', "\n*NEW* 16:00", 1)
                    elif "16:00" in final_message:
                        final_message = final_message.replace('16:00', "\n16:00", 1)

                    wb.send_keys("div[title='Escribe un mensaje'],div[aria-label='Escribe un mensaje'],div[aria-placeholder='Escribe un mensaje']", final_message)
                    if wb.js_click("span[data-testid=send],span[data-icon=send],button[aria-label='Enviar'],div[aria-label='Enviar']"):
                        wb.save_cookies('whatsapp')
                        time.sleep(3)

                    time.sleep(7)

                time.sleep(15)
                if not(os.path.exists(first_time_done_fp)):
                    with open(first_time_done_fp, 'w') as f:
                        f.write('done.')

            # saving sent message to avoid sending again.
            json.dump(obj=current_bookings, fp=open(colleagues_messages_data_fp, 'w'), indent=1)

    except Exception as error_inner1:
        print('outer.', str(error_inner1), str(error_inner1.__traceback__.tb_lineno))


time.sleep(10)
print("starting.")
wb = None
try:
    print('starting browser.')
    wb = Browser()
    print('logging in to site.')
    wb.get("https://app.turitop.com/admin/company/P271/bookings")
    if "admin/login/es/" in wb.web_browser.current_url:
        input("we are logged out. please login and press enter to resume.")

    print(f'getting all bookings detail in next {days_to_check_for_booking} days.')
    starting_date_obj = datetime.datetime.now()
    valid_days = []
    for day_count in range(0, days_to_check_for_booking+1, 1):
        valid_days.append(
            datetime.datetime.fromtimestamp(time.time()+(86400*day_count)).day
        )

    ending_date_obj = datetime.datetime.fromtimestamp(time.time()+(86400*days_to_check_for_booking))
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
            pass

        if invalid_selection:
            print('could not select the correct data. quitting.')
            wb.web_browser.quit()
            time.sleep(3)
            exit()

        bookings_on_page = wb.web_browser.find_elements(By.CSS_SELECTOR, "tr.bookings-history-row:not([class*='deleted'])")
        if len(bookings_on_page) == 0:
            break

        for each in bookings_on_page:
            try:
                booking_day = wb.get_text("div.format-day-of-month-number", each)
                if not(int(booking_day) in valid_days):
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
                if not(d in all_bookings):
                    all_bookings.append(d)

            except Exception as error_inner:
                wb.show_error(error_inner)

    print(f'found {len(all_bookings)} bookings in this date range.')

    print("sending messages to client.")
    wb.get("https://web.whatsapp.com")
    wb.load_cookies('whatsapp')
    time.sleep(7)

    for each_booking in sorted(all_bookings, key=lambda y: y['booking_time']):
        send_message_to_client(each_booking)

    """for each_booking in all_bookings:
        send_message_to_client(each_booking)"""

    print("sending messages to colleagues group.")
    send_message_to_group(all_bookings)

    wb.web_browser.quit()

except Exception as error_outer:
    print('outer.', str(error_outer), str(error_outer.__traceback__.tb_lineno))
    if wb is not None:
        wb.web_browser.quit()
