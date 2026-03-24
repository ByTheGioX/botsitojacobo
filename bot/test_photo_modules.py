"""
Script de prueba SOLO para los módulos de fotos.
Abre WhatsApp Web, scrapea el grupo de fotos, hace match con Turitop,
envía fotos a clientes, y chequea respuestas pendientes.

Uso: python test_photo_modules.py
"""
import datetime
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import re
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import os
import sys
from webdriver_manager.chrome import ChromeDriverManager
import base64
import urllib.request
import pyautogui
import pyperclip
import subprocess


# ============================================================
# CONFIG
# ============================================================
# --- Read Photo Group Config ---
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
log_fp = os.path.join(sys.path[0], 'data', 'logs.txt')

photo_thank_you_template_fp = os.path.join(sys.path[0], 'data', 'photo_thank_you_template.txt')
positive_review_template_fp = os.path.join(sys.path[0], 'data', 'positive_review_template.txt')
negative_review_template_fp = os.path.join(sys.path[0], 'data', 'negative_review_template.txt')
bad_caption_ids_fp = os.path.join(sys.path[0], 'data', 'bad_caption_replied_ids.json')
failed_sends_fp = os.path.join(sys.path[0], 'data', 'failed_photo_sends.json')

sala_to_places = {
    '4e': ['P1'],
    'csi': ['P2'],
    'maf': ['P4'],
    'tri': ['P5', 'P6'],
}

os.system("title Test Photo Modules")


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


# ============================================================
# BROWSER CLASS (copia simplificada)
# ============================================================
class Browser:
    def __init__(self):
        self.waiting_time = 60
        self.debug = True
        try:
            o = Options()
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
                    print(f'driver download error: {e2}')
                    time.sleep(10)
            if self.driver_path == '':
                print("failed to get drivers from web.")
                sys.exit(1)

            self.driver_path = os.path.join(os.path.dirname(self.driver_path), 'chromedriver.exe')
            s = Service(executable_path=self.driver_path)
            self.web_browser = webdriver.Chrome(service=s, options=o)
            self.web_browser.set_window_size(width=1100, height=850)
        except Exception as e:
            print(str(e))
            sys.exit(1)

    def css_click(self, element):
        for count in range(0, self.waiting_time, 1):
            try:
                self.web_browser.find_element(By.CSS_SELECTOR, element).click()
                return True
            except:
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
            except:
                time.sleep(0.5)
        return ''

    def x_click(self, element):
        for count in range(0, self.waiting_time, 1):
            try:
                self.web_browser.find_element(By.XPATH, element).click()
                return True
            except:
                time.sleep(0.5)
        return False

    def css_click_with_timer(self, element, timer):
        for count in range(0, timer, 1):
            try:
                self.web_browser.find_element(By.CSS_SELECTOR, element).click()
                return True
            except:
                try:
                    elem = self.web_browser.find_element(By.CSS_SELECTOR, element)
                    self.web_browser.execute_script('arguments[0].click()', elem)
                    return True
                except:
                    time.sleep(0)
                time.sleep(0.5)
        return False

    def x_click_with_timer(self, element, timer):
        for count in range(0, timer, 1):
            try:
                self.web_browser.find_element(By.XPATH, element).click()
                return True
            except:
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

    def send_keys(self, element, keys, full=False, clear=False):
        for count in range(0, self.waiting_time, 1):
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
                        ActionChains(self.web_browser).key_down(Keys.ALT).perform()
                        ActionChains(self.web_browser).send_keys(Keys.ENTER).perform()
                        ActionChains(self.web_browser).key_up(Keys.ALT).perform()
                return True
            except:
                time.sleep(0.5)
        return False

    def get(self, url):
        for try_ in range(0, 3, 1):
            try:
                self.web_browser.get(url)
                return True
            except Exception as e:
                print(f'get error: {e}')
                time.sleep(0.5)
        return False


# ============================================================
# MODULE 1 — Scrape Photo Group
# ============================================================

def parse_photo_caption(caption_text):
    caption_text = caption_text.lower().strip()
    # Use search instead of match to find the pattern anywhere in the text block
    # Format: dd/m HH:MM[/mm] sala[/sala2/sala3...]
    match = re.search(
        r'(\d{1,2}/\d{1,2})\s+(\d{1,2}:\d{2})(?:/(\d{2}))?\s+((?:4e|csi|maf|tri)(?:/(?:4e|csi|maf|tri))*)',
        caption_text
    )
    if not match:
        return None

    date_str = match.group(1)
    time1 = match.group(2)
    time2_min = match.group(3)
    salas = match.group(4).split('/')

    times = [time1]
    if time2_min:
        hour = time1.split(':')[0]
        times.append(f"{hour}:{time2_min}")

    return {'date': date_str, 'times': times, 'salas': salas}


def download_wa_image(img_element, save_path):
    try:
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

        if base64_data and not base64_data.startswith('ERROR:'):
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
            with open(save_path, 'wb') as f:
                f.write(base64.b64decode(base64_data))
            print(f'  [OK] photo downloaded: {save_path}')
            return True
        else:
            print(f'  [FAIL] download error: {base64_data}')
            return False
    except Exception as e:
        print(f'  [FAIL] exception: {e}')
        return False


def scrape_photo_group():
    photo_entries = []
    try:
        print('--- Module 1: Scraping photo group ---')

        # Navigate to group by searching its name in WhatsApp
        print(f'  Searching for group: "{photo_group_name}"')

        # Click search box
        search_clicked = wb.css_click_with_timer(
            "div[contenteditable='true'][data-tab='3']", 15
        )
        if not search_clicked:
            # Try alternative search selectors
            search_clicked = wb.css_click_with_timer(
                "div[role='textbox'][data-tab='3']", 10
            )
        if not search_clicked:
            search_clicked = wb.x_click_with_timer(
                "//div[@data-tab='3']", 10
            )
        print(f'  Search box clicked: {search_clicked}')
        time.sleep(2)

        # Type group name - Try multiple selectors for robustness
        search_box = None
        selectors_to_try = [
            ("div[contenteditable='true'][data-tab='3']", By.CSS_SELECTOR),
            ("div[role='textbox'][data-tab='3']", By.CSS_SELECTOR),
            ("//input[@type='text']", By.XPATH),
            ("input[type='text']", By.CSS_SELECTOR),
        ]

        for selector, by_type in selectors_to_try:
            try:
                search_box = wb.web_browser.find_element(by_type, selector)
                if search_box:
                    break
            except:
                continue

        if not search_box:
            print('  [ERROR] Could not find search box element!')
            return photo_entries

        try:
            search_box.clear()
        except:
            pass
        search_box.send_keys(photo_group_name)
        time.sleep(3)

        # Click on the group result
        group_clicked = wb.x_click_with_timer(
            f"//span[@title='{photo_group_name}']", 15
        )
        print(f'  Group clicked: {group_clicked}')
        if not group_clicked:
            print('  [ERROR] Could not find group in search results!')
            return photo_entries

        print('  Waiting for chat to load...')
        time.sleep(10)

        # Scroll up to load more messages
        try:
            chat_pane = wb.web_browser.find_element(
                By.CSS_SELECTOR, "div[role='application'], div.copyable-area div[tabindex]"
            )
            for _ in range(3):
                wb.web_browser.execute_script(
                    "arguments[0].scrollTop = 0;", chat_pane
                )
                time.sleep(2)
        except:
            print('  (could not scroll up, continuing with visible messages)')

        os.makedirs(downloaded_photos_dir, exist_ok=True)

        # --- DEBUG: Try multiple selectors to find messages ---
        selectors_to_try = [
            ("div.message-in", "Standard message-in"),
            ("div[class*='message-in']", "Partial class message-in"),
            ("div[data-id]", "Messages by data-id"),
            ("div.copyable-text", "Copyable text divs"),
            ("div[data-pre-plain-text]", "Pre-plain-text divs"),
            ("div[class*='_amjw']", "WhatsApp internal class"),
        ]

        print('\n  --- DEBUG: Testing CSS selectors ---')
        for selector, desc in selectors_to_try:
            try:
                found = wb.web_browser.find_elements(By.CSS_SELECTOR, selector)
                print(f'    {desc} ({selector}): {len(found)} elements')
            except Exception as e_sel:
                print(f'    {desc} ({selector}): ERROR - {e_sel}')

        # Also dump a sample of the actual HTML to understand structure
        print('\n  --- DEBUG: Looking for messages with images ---')
        all_imgs = wb.web_browser.find_elements(By.CSS_SELECTOR, "img[src*='blob:']")
        print(f'    Total blob images on page: {len(all_imgs)}')

        # Try to find message containers by looking for data-id attribute
        msg_containers = wb.web_browser.find_elements(By.CSS_SELECTOR, "div[data-id]")
        print(f'    Message containers (div[data-id]): {len(msg_containers)}')

        # Use div[data-id] as the primary selector since it's more stable
        messages = msg_containers
        if not messages:
            # Fallback: try message-in
            messages = wb.web_browser.find_elements(By.CSS_SELECTOR, "div.message-in")

        # Filter to only incoming messages (not our own)
        incoming_messages = []
        for m in messages:
            try:
                data_id = m.get_attribute('data-id') or ''
                classes = m.get_attribute('class') or ''
                # In WhatsApp, incoming messages have 'false' in data-id or 'message-in' in class
                if 'true' in data_id:
                    continue  # Skip our own messages (data-id contains 'true' for outgoing)
                incoming_messages.append(m)
            except:
                incoming_messages.append(m)

        print(f'\n  Found {len(incoming_messages)} incoming messages.')

        if len(incoming_messages) == 0:
            # Extra debug: print page title and URL
            print(f'  Current URL: {wb.web_browser.current_url}')
            print(f'  Page title: {wb.web_browser.title}')
            # Print a snippet of body text
            try:
                body_text = wb.web_browser.find_element(By.TAG_NAME, 'body').text[:500]
                print(f'  Body text preview: {body_text[:200]}...')
            except:
                print('  (could not retrieve body text preview)')

        # Use a list of processed IDs instead of a broken string timestamp comparison
        processed_ids_fp = os.path.join(sys.path[0], 'data', 'processed_photo_ids.json')
        processed_ids = []
        if os.path.exists(processed_ids_fp):
            try:
                with open(processed_ids_fp, 'r', encoding='utf-8') as f:
                    processed_ids = json.load(f)
            except:
                pass

        found_new = False
        new_processed = set()

        # Collect bad caption message IDs to reply AFTER processing all good photos
        # (replying in the group refreshes the DOM and makes other elements stale)
        bad_caption_msg_ids = []

        for idx, msg in enumerate(incoming_messages):
            try:
                # 0. Get unique message ID
                msg_id = msg.get_attribute('data-id') or f"unknown_{idx}"
                if msg_id in processed_ids or msg_id in new_processed:
                    continue

                # Get timestamp for filename only
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

                # 1. Parse caption FIRST. This acts as our primary filter.
                parsed = parse_photo_caption(msg_text)
                if not parsed:
                    # Check if this message has a photo (image with bad/missing caption)
                    has_image = bool(msg.find_elements(By.CSS_SELECTOR, "img[src*='blob:']"))
                    if not has_image:
                        has_image = bool(msg.find_elements(By.CSS_SELECTOR, "span[data-icon='download'], span[data-icon='arrow-down']"))

                    if has_image:
                        # Defer reply to after all good photos are processed
                        bad_caption_replied = _load_json_set(bad_caption_ids_fp)
                        if msg_id not in bad_caption_replied:
                            bad_caption_msg_ids.append(msg_id)
                            print(f'\n  [MSG {idx}] Photo with BAD nomenclature detected (will reply later).')

                    new_processed.add(msg_id)
                    continue

                found_new = True
                print(f'\n  [MSG {idx}] Found matching target: {parsed["date"]} {parsed["times"]} {"/".join(parsed["salas"])}')

                # 2. Check for image blob
                img_elements = msg.find_elements(By.CSS_SELECTOR, "img[src*='blob:']")
                
                # If no blob, it might be pending download (e.g. shows "468 kB")
                if not img_elements:
                    print('  -> Image blob not found. It might be pending download.')
                    dl_icons = msg.find_elements(By.CSS_SELECTOR, "span[data-icon='download'], span[data-icon='arrow-down']")
                    if dl_icons:
                        print('  -> Found download button. Clicking to download media...')
                        try:
                            # Sometimes the icon is not directly clickable, click its parent
                            parent_btn = dl_icons[0].find_element(By.XPATH, "..")
                            parent_btn.click()
                        except:
                            dl_icons[0].click()
                    else:
                        print('  -> No download icon. Trying to click the message body...')
                        try:
                            msg.click()
                        except:
                            pass
                    
                    # Wait for download to finish
                    time.sleep(6)
                    img_elements = msg.find_elements(By.CSS_SELECTOR, "img[src*='blob:']")

                if not img_elements:
                    print('  -> [ERROR] Still no image blob found after attempting download. Skipping.')
                    continue

                timestamp_clean = re.sub(r'[^\w]', '_', msg_timestamp)[:30]
                photo_filename = f"photo_{timestamp_clean}.jpg"
                photo_path = os.path.join(downloaded_photos_dir, photo_filename)

                print(f'  -> Opening media viewer to save photo...')
                # Scroll to image and use JavaScript click to avoid "element click intercepted" error
                try:
                    wb.web_browser.execute_script("arguments[0].scrollIntoView(true);", img_elements[0])
                    time.sleep(1)
                    wb.web_browser.execute_script("arguments[0].click();", img_elements[0])
                except:
                    # Fallback to regular click
                    img_elements[0].click()
                time.sleep(4)

                viewer_imgs = wb.web_browser.find_elements(
                    By.CSS_SELECTOR, "img[src*='blob:']"
                )
                if viewer_imgs:
                    download_success = download_wa_image(viewer_imgs[-1], photo_path)
                else:
                    download_success = download_wa_image(img_elements[0], photo_path)

                wb.css_click_with_timer(
                    "span[data-icon='x'], span[data-icon='x-viewer']", 10
                )
                time.sleep(2)

                if download_success:
                    parsed['photo_path'] = photo_path
                    parsed['msg_timestamp'] = msg_timestamp
                    photo_entries.append(parsed)
                    print(f'  -> photo entry downloaded successfully!')
                    # Successfully processed complete photo entry
                    new_processed.add(msg_id)
                else:
                    print(f'  -> Failed to download image.')

            except Exception as e_msg:
                print(f'error processing message: {e_msg}')
                try:
                    wb.css_click_with_timer(
                        "span[data-icon='x'], span[data-icon='x-viewer']", 5
                    )
                except:
                    pass
                continue

        # Now handle deferred bad caption replies (after all good photos are processed)
        if bad_caption_msg_ids:
            print(f'\n--- Processing {len(bad_caption_msg_ids)} deferred bad caption replies ---')
            # Refresh messages to get current state
            time.sleep(2)
            incoming_messages = wb.web_browser.find_elements(By.CSS_SELECTOR, "div[data-id]")

            for msg_id in bad_caption_msg_ids:
                try:
                    # Find the message by data-id
                    msg_element = None
                    for msg in incoming_messages:
                        try:
                            if msg.get_attribute('data-id') == msg_id:
                                msg_element = msg
                                break
                        except:
                            pass

                    if not msg_element:
                        print(f'  [WARN] Message {msg_id} not found in current list, skipping reply.')
                        continue

                    print(f'  -> Replying to bad caption message: {msg_id}')
                    try:
                        # Long-press / right-click the message to reply
                        ActionChains(wb.web_browser).context_click(msg_element).perform()
                        time.sleep(1)
                        # Click "Responder" / "Reply" option
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
                            pyperclip.copy(reply_text)
                            time.sleep(0.5)
                            # Find the chat input and paste
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

                    # Track that we already replied to this message
                    bad_caption_replied = _load_json_set(bad_caption_ids_fp)
                    bad_caption_replied.add(msg_id)
                    _save_json_set(bad_caption_ids_fp, bad_caption_replied)

                except Exception as e_bad_caption:
                    print(f'  [ERROR] processing bad caption reply: {e_bad_caption}')

        # Save updated processed IDs
        if new_processed:
            processed_ids.extend(list(new_processed))
            # Keep only the last 500 to avoid massive files
            processed_ids = processed_ids[-500:]
            with open(processed_ids_fp, 'w', encoding='utf-8') as f:
                json.dump(processed_ids, f)
            print('  -> updated processed message IDs.')

        if not found_new:
            print('  No new messages found.')
        print(f'\n========== MODULE 1 DONE: {len(photo_entries)} photo entries ==========')

    except Exception as e:
        print(f'  [ERROR] scrape_photo_group: {e}, line: {e.__traceback__.tb_lineno}')

    return photo_entries


# ============================================================
# MODULE 2 — Match with Turitop & Send Photo to Client
# ============================================================

def scrape_turitop_for_date(target_day, target_month):
    bookings = []
    try:
        year = datetime.datetime.now().year
        target_date = f"{int(target_day):02d}-{int(target_month):02d}-{year}"
        print(f'  Scraping Turitop for date: {target_date}')

        wb.web_browser.execute_script("window.open('')")
        wb.web_browser.switch_to.window(wb.web_browser.window_handles[-1])

        wb.get("https://app.turitop.com/admin/company/P271/bookings")
        time.sleep(5)

        if "admin/login/es/" in wb.web_browser.current_url:
            print("  [WARN] Turitop logged out! Skipping.")
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
            wb.get(f"https://app.turitop.com/admin/company/P271/bookings/list/page/{booking_page}")
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
                    print(f'  [ERROR] row: {e_inner}')

        print(f'  Found {len(bookings)} bookings for {target_date}')

        wb.web_browser.close()
        wb.web_browser.switch_to.window(wb.web_browser.window_handles[0])

    except Exception as e:
        print(f'  [ERROR] scrape_turitop: {e}, line: {e.__traceback__.tb_lineno}')
        try:
            if len(wb.web_browser.window_handles) > 1:
                wb.web_browser.close()
                wb.web_browser.switch_to.window(wb.web_browser.window_handles[0])
        except:
            pass

    return bookings


def match_and_send_photos(photo_entries):
    try:
        print('\n========== MODULE 2: Matching photos with bookings ==========')

        if not os.path.exists(photo_sent_messages_fp):
            with open(photo_sent_messages_fp, 'w') as f:
                f.write('')

        dates_to_scrape = set()
        for entry in photo_entries:
            dates_to_scrape.add(entry['date'])

        bookings_by_date = {}
        for date_str in dates_to_scrape:
            parts = date_str.split('/')
            day, month = parts[0], parts[1]
            bookings_by_date[date_str] = scrape_turitop_for_date(day, month)
            time.sleep(3)

        wb.web_browser.switch_to.window(wb.web_browser.window_handles[0])

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
                print(f'\n  Matching: date={date_str} time={t} salas={sala_label}')

                matched_booking = None
                for b in bookings:
                    b_place = b['booking_place'].upper().replace('#', '')
                    if (b['booking_time'].strip() == t.strip() and
                            b['booking_day'].strip() == day_num.strip() and
                            any(p.upper() in b_place for p in target_places)):
                        matched_booking = b
                        break

                if not matched_booking:
                    print(f'  -> No matching booking found.')
                    continue

                if not matched_booking.get('wa_link'):
                    print('  -> Booking found but no WhatsApp link.')
                    continue

                sent_id = f"{date_str}_{t}_{sala_label}_{matched_booking['wa_link']}"

                with open(photo_sent_messages_fp, 'r') as f:
                    if sent_id in f.read():
                        print('  -> Already sent, skipping.')
                        continue

                # Check if this send previously failed (avoid retry loop)
                if _is_failed_send(sent_id):
                    print('  -> Previously failed send, skipping to avoid loop.')
                    continue

                print(f'  -> Sending photo to: {matched_booking["wa_link"]}')
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
                    print('  -> Invalid WhatsApp link.')
                    continue

                with open(photo_thank_you_template_fp, 'r', encoding='utf-8') as f:
                    photo_thank_you_msg = f.read().strip()

                try:
                    # 1. Copy image to Windows clipboard via PowerShell FIRST (before focusing browser)
                    print("  -> Copying image to OS clipboard...")
                    photo_ps_path = os.path.abspath(photo_path).replace("\\", "/")
                    ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile('{photo_ps_path}')
[System.Windows.Forms.Clipboard]::SetImage($img)
$img.Dispose()
"""
                    subprocess.run(["powershell", "-STA", "-command", ps_script], check=True)

                    # 2. Re-focus browser window (PowerShell stole focus)
                    wb.web_browser.switch_to.window(wb.web_browser.current_window_handle)
                    time.sleep(1)

                    # 3. Click chat input to ensure it's focused and interactable
                    chat_input = None
                    for selector in [
                        "footer div[contenteditable='true']",
                        "div[contenteditable='true'][data-tab]",
                        "div[title='Escribe un mensaje aquí']",
                        "div[title='Type a message']"
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
                        print("  [WARN] Could not find chat input, trying active element...")

                    time.sleep(1)

                    # 4. Paste image into WhatsApp chat
                    print("  -> Pasting image into WhatsApp...")
                    try:
                        if chat_input:
                            chat_input.send_keys(Keys.CONTROL, 'v')
                        else:
                            wb.web_browser.switch_to.active_element.send_keys(Keys.CONTROL, 'v')
                    except Exception as paste_err:
                        print(f"  [WARN] First paste attempt failed: {paste_err}")
                        # Fallback: use ActionChains
                        ActionChains(wb.web_browser).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()

                except Exception as e:
                    print(f'  [ERROR] Failed to paste image: {e}')
                    # Track this as a failed send
                    failed_send_id = f"{date_str}_{t}_{sala_label}_{matched_booking['wa_link']}"
                    _track_failed_send(failed_send_id)
                    continue

                print("  -> Waiting for image preview overlay...")
                time.sleep(6) # Important to wait for the preview dialog to fully render

                # The caption box is usually auto-focused when the image preview opens.
                print("  -> Typing caption with clipboard to preserve emojis and line breaks...")
                try:
                    caption_box = wb.web_browser.find_element(
                        By.CSS_SELECTOR, 
                        "div[aria-placeholder*='Añade'], div[aria-placeholder*='Add a caption'], div[title*='comentario']"
                    )
                    caption_box.click()
                except:
                    print("  [WARN] Could not find specific caption box, falling back to active element.")
                    caption_box = wb.web_browser.switch_to.active_element

                # Copying to clipboard and sending Ctrl+V perfectly preserves emojis and multi-line formatting in WhatsApp Web
                pyperclip.copy(photo_thank_you_msg)
                time.sleep(1)
                caption_box.send_keys(Keys.CONTROL, 'v')
                
                time.sleep(3)

                res = wb.css_click("div[aria-label=Enviar],span[data-icon='send']")
                time.sleep(5)

                print(f"  -> Send result: {res}")
                if wb.elem_wait('div.message-out'):
                    print('  -> [OK] Photo with caption sent!')
                    time.sleep(10)

                    with open(photo_sent_messages_fp, 'a') as f:
                        f.write(sent_id + '\n')

                    pending.append({
                        'wa_link': matched_booking['wa_link'],
                        'timestamp_sent': datetime.datetime.now().isoformat(),
                        'booking_code': f"{date_str}_{t}_{sala_label}",
                        'booking_date': matched_booking.get('booking_date', '')
                    })
                else:
                    print('  -> [FAIL] Photo NOT sent. Tracking as failed.')
                    _track_failed_send(sent_id)

        json.dump(pending, open(pending_replies_fp, 'w'), indent=2)
        print(f'\n========== MODULE 2 DONE: {len(pending)} pending replies ==========')

    except Exception as e:
        print(f'  [ERROR] match_and_send_photos: {e}, line: {e.__traceback__.tb_lineno}')


# ============================================================
# MODULE 3 — AI Response Classification
# ============================================================

def classify_reply_with_ai(reply_text):
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
            print(f'  AI classification: {classification}')

            if 'POSITIVO' in classification or 'POSITIVE' in classification:
                return 'POSITIVO'
            elif 'NEGATIVO' in classification or 'NEGATIVE' in classification:
                return 'NEGATIVO'
            else:
                return 'NEUTRAL'

    except Exception as e:
        print(f'  [ERROR] OpenRouter API: {e}')
        return 'NEUTRAL'


def check_pending_replies():
    try:
        print('\n========== MODULE 3: Checking pending replies ==========')

        if not os.path.exists(pending_replies_fp):
            print('  No pending replies file.')
            return

        pending = json.load(open(pending_replies_fp, 'r'))
        if len(pending) == 0:
            print('  No pending replies.')
            return

        updated_pending = []
        now = datetime.datetime.now()

        for entry in pending:
            try:
                sent_time = datetime.datetime.fromisoformat(entry['timestamp_sent'])
                hours_elapsed = (now - sent_time).total_seconds() / 3600

                if hours_elapsed > 24:
                    print(f'  Expired (>24h): {entry["booking_code"]}')
                    continue

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
                    print('  Invalid chat link, removing.')
                    continue

                time.sleep(3)

                all_msgs = wb.web_browser.find_elements(
                    By.CSS_SELECTOR, "div.message-in, div.message-out"
                )
                if len(all_msgs) == 0:
                    updated_pending.append(entry)
                    continue

                last_msg = all_msgs[-1]
                msg_classes = last_msg.get_attribute('class') or ''
                if 'message-in' not in msg_classes:
                    print(f'  No reply yet: {entry["booking_code"]}')
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
                    print('  Empty reply, keeping.')
                    updated_pending.append(entry)
                    continue

                print(f'  Client reply: {reply_text[:100]}')

                classification = classify_reply_with_ai(reply_text)

                if classification == 'POSITIVO':
                    print('  -> POSITIVE! Sending review link.')
                    with open(positive_review_template_fp, 'r', encoding='utf-8') as f:
                        review_msg = f.read().strip()

                    try:
                        chat_input = wb.web_browser.find_element(
                            By.CSS_SELECTOR, "footer div[contenteditable='true']"
                        )
                        chat_input.click()
                        time.sleep(0.5)
                        
                        # Use Clipboard paste to perfectly support emojis and line breaks
                        pyperclip.copy(review_msg)
                        chat_input.send_keys(Keys.CONTROL, 'v')
                        time.sleep(1)
                        chat_input.send_keys(Keys.ENTER)
                        time.sleep(3)
                        print('  Review link sent.')
                    except Exception as ex:
                        print(f'  [ERROR] Failed to send positive review msg: {ex}')
                        updated_pending.append(entry)
                        continue

                elif classification == 'NEGATIVO':
                    print('  -> NEGATIVE. Sending empathy message.')
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
                        print('  Negative response sent.')
                    except Exception as ex:
                        print(f'  [ERROR] Failed to send negative empathy msg: {ex}')
                        updated_pending.append(entry)
                        continue

                else:
                    print('  -> NEUTRAL. Not sending anything.')

            except Exception as e_entry:
                print(f'  [ERROR] {e_entry}, line: {e_entry.__traceback__.tb_lineno}')
                updated_pending.append(entry)

        json.dump(updated_pending, open(pending_replies_fp, 'w'), indent=2)
        print(f'\n========== MODULE 3 DONE: {len(updated_pending)} still pending ==========')

    except Exception as e:
        print(f'  [ERROR] check_pending_replies: {e}, line: {e.__traceback__.tb_lineno}')


# ============================================================
# MODULE 4 — Daily Cleanup
# ============================================================

def daily_cleanup():
    try:
        print('\n========== MODULE 4: Daily cleanup ==========')
        now = datetime.datetime.now()

        if os.path.exists(downloaded_photos_dir):
            for photo_file in os.listdir(downloaded_photos_dir):
                fp = os.path.join(downloaded_photos_dir, photo_file)
                if os.path.isfile(fp):
                    file_age_hours = (time.time() - os.path.getmtime(fp)) / 3600
                    if file_age_hours > 24:
                        os.remove(fp)
                        print(f'  Cleaned: {photo_file}')

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
                        print(f'  Removed expired: {entry["booking_code"]}')
                except:
                    pass

            if len(updated) != len(pending):
                json.dump(updated, open(pending_replies_fp, 'w'), indent=2)
                print(f'  Cleaned {len(pending) - len(updated)} expired entries.')

        print('========== MODULE 4 DONE ==========')

    except Exception as e:
        print(f'  [ERROR] daily_cleanup: {e}, line: {e.__traceback__.tb_lineno}')


# ============================================================
# MAIN — Test flow
# ============================================================

print("\n" + "=" * 60)
print("  TEST PHOTO MODULES - Script independiente")
print("=" * 60)

print("\nStarting browser...")
wb = Browser()

print("Opening WhatsApp Web...")
wb.get("https://web.whatsapp.com")
print("Waiting 30s for WhatsApp to load (scan QR if needed)...")
time.sleep(30)

print("\n--- Running all photo modules ---\n")

# Module 4: Cleanup first
daily_cleanup()

# Module 1: Scrape photo group
photo_entries = scrape_photo_group()

# Module 2: Match and send
if photo_entries:
    match_and_send_photos(photo_entries)
else:
    print("\nNo photo entries to match — skipping Module 2.")

# Module 3: Check pending replies
check_pending_replies()

print("\n" + "=" * 60)
print("  ALL DONE! Press Enter to close browser and exit.")
print("=" * 60)
input()
wb.web_browser.quit()
