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
import hashlib


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

# Photo to send with positive review response (client can change this file)
review_photo_fp = os.path.join(sys.path[0], 'data', 'review_photo.jpg')

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
            o.add_argument('--disable-session-crashed-bubble')
            o.add_experimental_option('excludeSwitches', ['enable-automation'])
            prefs = {"profile.exit_type": "Normal", "profile.exited_cleanly": True}
            o.add_experimental_option('prefs', prefs)

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

    def dismiss_restore_dialog(self):
        """Dismiss Chrome's 'Restore pages?' dialog if it appears."""
        try:
            # Try to dismiss via JavaScript - the dialog is a Chrome infobar
            self.web_browser.execute_script("""
                var buttons = document.querySelectorAll('button');
                buttons.forEach(function(btn) {
                    var text = btn.innerText.toLowerCase();
                    if (text.includes('restore') || text.includes('cancel') || text.includes('no') || text.includes('close')) {
                        btn.click();
                    }
                });
            """)
        except:
            pass
        try:
            # Also try keyboard shortcut to dismiss Chrome infobars
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(self.web_browser).send_keys(Keys.ESCAPE).perform()
        except:
            pass

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


def download_wa_image(img_element, save_path, max_retries=3):
    """Download an image from WhatsApp Web blob URL using JS fetch + base64.
    Retries up to max_retries times on failure."""
    for attempt in range(1, max_retries + 1):
        try:
            # Check that the element still has a valid blob src
            src = img_element.get_attribute('src') or ''
            if not src.startswith('blob:'):
                print(f'    attempt {attempt}: img src is not a blob ({src[:50]}), skipping')
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
                    print(f'    attempt {attempt}: downloaded data too small ({len(raw)} bytes), might be thumbnail. Retrying...')
                    time.sleep(3)
                    continue
                with open(save_path, 'wb') as f:
                    f.write(raw)
                print(f'  [OK] photo downloaded ({len(raw)} bytes): {save_path}')
                return True
            else:
                print(f'    attempt {attempt}: [FAIL] download error: {base64_data}')
                time.sleep(3)
        except Exception as e:
            print(f'    attempt {attempt}: [FAIL] exception: {e}')
            time.sleep(3)

    print(f'  [FAIL] all {max_retries} download attempts failed for {save_path}')
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

        # Get all messages - we'll process all including our own photos
        # Deduplication is handled by processed_ids.json (msg_id tracking)
        incoming_messages = []
        for m in messages:
            try:
                incoming_messages.append(m)
            except Exception as e_filter:
                # If there's an error adding message, skip it
                continue

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
        reprocess = '--reprocess' in sys.argv
        processed_ids = []
        if reprocess:
            print('  [--reprocess] Ignoring processed IDs, will re-scan all messages.')
        elif os.path.exists(processed_ids_fp):
            try:
                with open(processed_ids_fp, 'r', encoding='utf-8') as f:
                    processed_ids = json.load(f)
            except:
                pass

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
                if parsed:
                    # Add msg_id and original caption for feedback tracking
                    parsed['msg_id'] = msg_id
                    parsed['caption'] = msg_text.strip()  # Store original caption
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

                print(f'\n  [MSG {idx}] Found matching target: {parsed["date"]} {parsed["times"]} {"/".join(parsed["salas"])}')

                # 2. Check for image - try multiple strategies to find it
                img_elements = msg.find_elements(By.CSS_SELECTOR, "img[src*='blob:']")

                if not img_elements:
                    # Strategy A: Look for download button (image not auto-downloaded)
                    dl_icons = msg.find_elements(By.CSS_SELECTOR,
                        "span[data-icon='download'], span[data-icon='arrow-down'], span[data-icon='media-download']")
                    if dl_icons:
                        print('  -> Found download button. Clicking to download media...')
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
                            # RE-FETCH the message element since DOM may have changed
                            try:
                                msg = wb.web_browser.find_element(By.CSS_SELECTOR, f"div[data-id='{msg_id}']")
                            except:
                                pass
                            img_elements = msg.find_elements(By.CSS_SELECTOR, "img[src*='blob:']")
                            if img_elements:
                                print(f'  -> Image appeared after {(wait_round+1)*2}s wait')
                                break
                    else:
                        # Strategy B: Click the message itself to trigger load
                        print('  -> No download icon. Trying to click the message body...')
                        try:
                            msg.click()
                        except:
                            pass
                        time.sleep(8)
                        try:
                            msg = wb.web_browser.find_element(By.CSS_SELECTOR, f"div[data-id='{msg_id}']")
                        except:
                            pass
                        img_elements = msg.find_elements(By.CSS_SELECTOR, "img[src*='blob:']")

                if not img_elements:
                    print('  -> [WARN] Could not find image blob after all strategies, will retry next cycle')
                    continue

                # Unique filename: use index + hash of msg_id to avoid collisions
                timestamp_clean = re.sub(r'[^\w]', '_', msg_timestamp)[:30]
                id_hash = hashlib.md5(msg_id.encode()).hexdigest()[:8]
                photo_filename = f"photo_{timestamp_clean}_{id_hash}.jpg"
                photo_path = os.path.join(downloaded_photos_dir, photo_filename)

                download_success = False

                # Download directly from this message's blob (no viewer needed).
                # Each message element has its own blob URL with its specific image.
                try:
                    msg = wb.web_browser.find_element(By.CSS_SELECTOR, f"div[data-id='{msg_id}']")
                    msg_imgs = msg.find_elements(By.CSS_SELECTOR, "img[src*='blob:']")
                except:
                    msg_imgs = img_elements

                if msg_imgs:
                    # Log the blob src to verify each message has a different one
                    try:
                        blob_src = msg_imgs[0].get_attribute('src')
                        print(f'  -> Downloading from message blob: {blob_src[:60]}...')
                    except:
                        print(f'  -> Downloading from message blob...')
                    for img_el in msg_imgs:
                        download_success = download_wa_image(img_el, photo_path)
                        if download_success:
                            break

                if download_success:
                    parsed['photo_path'] = photo_path
                    parsed['msg_timestamp'] = msg_timestamp
                    photo_entries.append(parsed)
                    print(f'  -> photo entry downloaded successfully!')
                    new_processed.add(msg_id)
                else:
                    print(f'  -> [WARN] ALL download strategies failed. Will retry next cycle.')

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
                            wb.web_browser.execute_script("arguments[0].focus(); arguments[0].click();", chat_input)
                            time.sleep(0.5)
                            ActionChains(wb.web_browser).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                            time.sleep(1)
                            ActionChains(wb.web_browser).send_keys(Keys.ENTER).perform()
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

        if len(photo_entries) == 0:
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


def delete_message_from_group(msg_id):
    """Navigate to photo group and delete a specific message ('Eliminar para mí').
    This prevents re-sending on bot restart."""
    try:
        print(f'  -> Deleting message {msg_id[:30]}... from group')

        # Search and open the photo group
        search_box = wb.web_browser.find_element(By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='3']")
        wb.web_browser.execute_script("arguments[0].focus(); arguments[0].click();", search_box)
        time.sleep(1)
        search_box.clear()
        pyperclip.copy(photo_group_name)
        ActionChains(wb.web_browser).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(3)

        # Click on the group
        group_found = False
        for sel in [
            f"span[title='{photo_group_name}']",
            f"span[title*='{photo_group_name.split()[0]}']"
        ]:
            try:
                group_el = wb.web_browser.find_element(By.CSS_SELECTOR, sel)
                wb.web_browser.execute_script("arguments[0].click();", group_el)
                group_found = True
                break
            except:
                continue

        if not group_found:
            print(f'  -> [WARN] Could not find group to delete message.')
            return False

        time.sleep(4)

        # Find the message by data-id
        try:
            msg_el = wb.web_browser.find_element(By.CSS_SELECTOR, f"div[data-id='{msg_id}']")
        except:
            print(f'  -> Message not found in group (may already be deleted).')
            return True  # Not an error - message is gone

        # Hover over the message to reveal the dropdown arrow
        ActionChains(wb.web_browser).move_to_element(msg_el).perform()
        time.sleep(1)

        # Click the dropdown arrow (context menu trigger)
        down_arrow = None
        for arrow_sel in [
            "span[data-icon='down-context']",
            "span[data-icon='menu']",
            "span[data-icon='down']",
            "div[role='button'][aria-label*='menú']",
            "div[role='button'][aria-label*='Menu']",
        ]:
            try:
                down_arrow = msg_el.find_element(By.CSS_SELECTOR, arrow_sel)
                break
            except:
                continue

        if not down_arrow:
            # Try finding it in the general area after hover
            for arrow_sel in ["span[data-icon='down-context']", "span[data-icon='menu']"]:
                try:
                    down_arrow = wb.web_browser.find_element(By.CSS_SELECTOR, arrow_sel)
                    break
                except:
                    continue

        if not down_arrow:
            print(f'  -> [WARN] Could not find dropdown arrow for message.')
            return False

        wb.web_browser.execute_script("arguments[0].click();", down_arrow)
        time.sleep(1)

        # Click "Eliminar" / "Delete" in the context menu
        delete_clicked = False
        menu_items = wb.web_browser.find_elements(By.CSS_SELECTOR, "div[role='application'] li, div[tabindex='-1'] div[role='button']")
        for item in menu_items:
            item_text = (item.get_attribute('innerText') or '').strip().lower()
            if 'eliminar' in item_text or 'delete' in item_text or 'borrar' in item_text:
                wb.web_browser.execute_script("arguments[0].click();", item)
                delete_clicked = True
                break

        if not delete_clicked:
            # Fallback: try aria-label on list items
            for sel in ["li[data-animate-dropdown-item]", "div[role='listitem']"]:
                try:
                    items = wb.web_browser.find_elements(By.CSS_SELECTOR, sel)
                    for item in items:
                        txt = (item.get_attribute('innerText') or '').lower()
                        if 'eliminar' in txt or 'delete' in txt:
                            wb.web_browser.execute_script("arguments[0].click();", item)
                            delete_clicked = True
                            break
                except:
                    continue
                if delete_clicked:
                    break

        if not delete_clicked:
            print(f'  -> [WARN] Could not find "Eliminar" option in menu.')
            ActionChains(wb.web_browser).send_keys(Keys.ESCAPE).perform()
            return False

        time.sleep(2)

        # Click "Eliminar para mí" / "Delete for me" in the confirmation dialog
        confirm_clicked = False
        for btn_sel in ["button", "div[role='button']"]:
            try:
                buttons = wb.web_browser.find_elements(By.CSS_SELECTOR, btn_sel)
                for btn in buttons:
                    btn_text = (btn.get_attribute('innerText') or '').strip().lower()
                    if 'para mí' in btn_text or 'for me' in btn_text or 'eliminar para' in btn_text:
                        wb.web_browser.execute_script("arguments[0].click();", btn)
                        confirm_clicked = True
                        break
                if confirm_clicked:
                    break
            except:
                continue

        if not confirm_clicked:
            print(f'  -> [WARN] Could not confirm "Eliminar para mí".')
            ActionChains(wb.web_browser).send_keys(Keys.ESCAPE).perform()
            return False

        time.sleep(2)
        print(f'  -> [OK] Message deleted from group!')
        return True

    except Exception as e:
        print(f'  -> [ERROR] delete_message_from_group: {e}')
        try:
            ActionChains(wb.web_browser).send_keys(Keys.ESCAPE).perform()
        except:
            pass
        return False


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
          try:
            date_str = entry['date']
            salas = entry['salas']
            photo_path = entry['photo_path']
            sala_label = '/'.join(salas)
            day_num = date_str.split('/')[0]
            bookings = bookings_by_date.get(date_str, [])

            # Track wa_links we've already sent THIS photo to, to avoid duplicates
            # (e.g., maf/csi 16:00/10 where both bookings belong to the same customer)
            sent_wa_links_this_photo = set()
            entry_all_sends_ok = True  # Track if all sends for this entry succeeded

            # Match each time to its corresponding sala.
            # Caption "16:00/10 maf/csi" means: 16:00→maf, 16:10→csi
            # If there's only 1 time but multiple salas, send to all matching bookings.
            # If times and salas are paired (same count), each time matches its sala.
            times = entry['times']

            for time_idx, t in enumerate(times):
                msg_id = entry.get('msg_id')  # Get msg_id for feedback tracking

                # Determine which places to search for this specific time
                if len(times) == len(salas) and len(times) > 1:
                    # Paired: time[i] corresponds to sala[i]
                    specific_sala = salas[time_idx]
                    time_target_places = sala_to_places.get(specific_sala, [])
                    print(f'\n  Matching: date={date_str} time={t} sala={specific_sala} (paired)')
                else:
                    # Single time or mismatch: use all salas
                    time_target_places = []
                    for s in salas:
                        time_target_places.extend(sala_to_places.get(s, []))
                    print(f'\n  Matching: date={date_str} time={t} salas={sala_label}')

                matched_booking = None
                for b in bookings:
                    b_place = b['booking_place'].upper().replace('#', '')
                    if (b['booking_time'].strip() == t.strip() and
                            b['booking_day'].strip() == day_num.strip() and
                            any(p.upper() in b_place for p in time_target_places)):
                        matched_booking = b
                        break

                # Fallback: if paired match failed, try the other salas in the caption
                # This handles cases where the caption has the salas in wrong order
                # e.g. caption "16:00/10 csi/maf" but Turitop has 16:00→maf, 16:10→csi
                if not matched_booking and len(times) == len(salas) and len(times) > 1:
                    fallback_places = []
                    for s in salas:
                        fallback_places.extend(sala_to_places.get(s, []))
                    # Remove the places we already tried
                    fallback_places = [p for p in fallback_places if p not in time_target_places]
                    if fallback_places:
                        for b in bookings:
                            b_place = b['booking_place'].upper().replace('#', '')
                            if (b['booking_time'].strip() == t.strip() and
                                    b['booking_day'].strip() == day_num.strip() and
                                    any(p.upper() in b_place for p in fallback_places)):
                                matched_booking = b
                                print(f'  -> [FALLBACK] Matched via swapped sala order for time={t}')
                                break

                if not matched_booking:
                    print(f'  -> No matching booking found.')
                    continue

                if not matched_booking.get('wa_link'):
                    print('  -> Booking found but no WhatsApp link.')
                    continue

                # Skip if we already sent this same photo to this wa_link
                wa_link_normalized = matched_booking['wa_link'].strip().lower()
                if wa_link_normalized in sent_wa_links_this_photo:
                    print(f'  -> Already sent this photo to {matched_booking["wa_link"]}, skipping duplicate.')
                    continue

                sent_id = f"{date_str}_{t}_{sala_label}_{matched_booking['wa_link']}"

                with open(photo_sent_messages_fp, 'r') as f:
                    if sent_id in f.read():
                        print('  -> Already sent, skipping.')
                        continue

                # Note: we no longer permanently skip failed sends.
                # Each cycle gets a fresh chance to send.

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

                send_success = False
                for send_attempt in range(1, 3):  # Try up to 2 times
                    try:
                        # 1. Copy image to Windows clipboard via PowerShell FIRST
                        print(f"  -> Send attempt {send_attempt}: Copying image to OS clipboard...")
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

                        # 3. Click chat input to ensure it's focused (use JS to avoid intercept)
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
                                wb.web_browser.execute_script("arguments[0].focus(); arguments[0].click();", chat_input)
                                break
                            except:
                                continue

                        if not chat_input:
                            print("  [WARN] Could not find chat input, trying active element...")

                        time.sleep(1)

                        # 4. Paste image into WhatsApp chat
                        print("  -> Pasting image into WhatsApp...")
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
                                print(f"    paste try {paste_try+1} failed: {paste_err}")
                                time.sleep(1)
                                try:
                                    ActionChains(wb.web_browser).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                                    paste_ok = True
                                    break
                                except:
                                    time.sleep(2)

                        if not paste_ok:
                            print("  -> All paste attempts failed, retrying send...")
                            continue

                    except Exception as paste_e:
                        print(f'  [ERROR] Failed to paste image (attempt {send_attempt}): {paste_e}')
                        try:
                            ActionChains(wb.web_browser).send_keys(Keys.ESCAPE).perform()
                            time.sleep(1)
                        except:
                            pass
                        continue

                    # --- Send photo WITHOUT caption, then send text separately ---
                    # Wait for image preview overlay
                    print("  -> Waiting for image preview overlay...")
                    preview_found = False
                    preview_indicators = [
                        "span[data-icon='pencil']",
                        "span[data-icon='crop']",
                        "span[data-icon='scissors']",
                        "span[data-icon='text']",
                        "span[data-icon='sticker']",
                        "span[data-icon='wds-ic-send-filled']",
                        "div[aria-placeholder*='Añade']",
                        "div[aria-placeholder*='Add a caption']",
                    ]
                    for wait_i in range(15):
                        time.sleep(2)
                        # Check duplicate 'Escribe un mensaje' inputs (2+ = preview open)
                        try:
                            escribe_inputs = wb.web_browser.find_elements(By.CSS_SELECTOR, "div[aria-placeholder*='Escribe un mensaje']")
                            if len(escribe_inputs) >= 2:
                                preview_found = True
                                print(f"  -> Preview detected via duplicate inputs ({len(escribe_inputs)}) after {(wait_i+1)*2}s")
                                break
                        except:
                            pass
                        for sel in preview_indicators:
                            try:
                                if wb.web_browser.find_elements(By.CSS_SELECTOR, sel):
                                    preview_found = True
                                    print(f"  -> Preview detected via '{sel}' after {(wait_i+1)*2}s")
                                    break
                            except:
                                continue
                        if preview_found:
                            break

                    if not preview_found:
                        print(f"  -> Image preview did not appear (attempt {send_attempt}), retrying...")
                        try:
                            ActionChains(wb.web_browser).send_keys(Keys.ESCAPE).perform()
                            time.sleep(2)
                        except:
                            pass
                        continue

                    # Step A: Send the photo (no caption) by clicking the send button in preview
                    print("  -> Sending photo without caption...")
                    photo_sent = False
                    for send_sel in ["span[data-icon='send']", "span[data-icon='wds-ic-send-filled']", "div[aria-label='Enviar']"]:
                        try:
                            send_btn = wb.web_browser.find_element(By.CSS_SELECTOR, send_sel)
                            wb.web_browser.execute_script("arguments[0].click();", send_btn)
                            photo_sent = True
                            print(f"  -> Photo send clicked via '{send_sel}'")
                            break
                        except:
                            continue

                    if not photo_sent:
                        print(f"  -> Could not click send button (attempt {send_attempt}), retrying...")
                        try:
                            ActionChains(wb.web_browser).send_keys(Keys.ESCAPE).perform()
                            time.sleep(2)
                        except:
                            pass
                        continue

                    # Wait for photo to actually send (preview closes, message appears)
                    time.sleep(5)

                    # Step B: Now send the thank-you text as a separate message
                    print("  -> Sending thank-you text as separate message...")
                    text_sent = False
                    # Find the chat input box
                    chat_input_2 = None
                    for selector in [
                        "footer div[contenteditable='true']",
                        "div[contenteditable='true'][data-tab]",
                        "div[title='Escribe un mensaje aquí']",
                        "div[title='Escribe un mensaje']",
                        "div[title='Type a message']",
                        "div[aria-placeholder='Escribe un mensaje']"
                    ]:
                        try:
                            chat_input_2 = wb.web_browser.find_element(By.CSS_SELECTOR, selector)
                            break
                        except:
                            continue

                    if chat_input_2:
                        pyperclip.copy(photo_thank_you_msg)
                        time.sleep(0.5)
                        wb.web_browser.execute_script("arguments[0].focus(); arguments[0].click();", chat_input_2)
                        time.sleep(0.5)
                        ActionChains(wb.web_browser).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                        time.sleep(2)
                        # Press Enter to send the text message
                        ActionChains(wb.web_browser).send_keys(Keys.ENTER).perform()
                        time.sleep(3)
                        text_sent = True
                        print("  -> Text message sent!")
                    else:
                        print("  -> [WARN] Could not find chat input for text message")

                    # Verify message was sent
                    for check_i in range(10):
                        out_msgs = wb.web_browser.find_elements(By.CSS_SELECTOR, 'div.message-out')
                        if out_msgs:
                            send_success = True
                            break
                        time.sleep(2)

                    if send_success:
                        print('  -> [OK] Photo + text sent successfully!')
                        time.sleep(3)
                        break
                    else:
                        print(f'  -> Messages NOT confirmed as sent (attempt {send_attempt})')
                        try:
                            ActionChains(wb.web_browser).send_keys(Keys.ESCAPE).perform()
                            time.sleep(2)
                        except:
                            pass

                if send_success:
                    sent_wa_links_this_photo.add(wa_link_normalized)
                    with open(photo_sent_messages_fp, 'a') as f:
                        f.write(sent_id + '\n')

                    pending.append({
                        'wa_link': matched_booking['wa_link'],
                        'timestamp_sent': datetime.datetime.now().isoformat(),
                        'booking_code': f"{date_str}_{t}_{sala_label}",
                        'booking_date': matched_booking.get('booking_date', ''),
                        'booking_day': matched_booking.get('booking_day', ''),
                        'booking_time': matched_booking.get('booking_time', ''),
                        'booking_place': matched_booking.get('booking_place', ''),
                    })
                else:
                    print(f'  -> [WARN] Photo send FAILED after all attempts. Will retry next cycle.')
                    entry_all_sends_ok = False

            # After processing all times for this entry: delete from group if all sends succeeded
            if entry_all_sends_ok and sent_wa_links_this_photo:
                msg_id_to_delete = entry.get('msg_id')
                if msg_id_to_delete:
                    print(f'\n  All sends OK for this photo. Deleting from group...')
                    delete_message_from_group(msg_id_to_delete)
          except Exception as entry_err:
            print(f'  -> [ERROR] Failed processing entry: {entry_err}')
            print(f'     Continuing with next entry...')
            try:
                ActionChains(wb.web_browser).send_keys(Keys.ESCAPE).perform()
                time.sleep(2)
            except:
                pass
        json.dump(pending, open(pending_replies_fp, 'w'), indent=2)
        print(f'\n========== MODULE 2 DONE: {len(pending)} pending replies ==========')

    except Exception as e:
        print(f'  [ERROR] match_and_send_photos: {e}, line: {e.__traceback__.tb_lineno}')


# ============================================================
# MODULE 2B — Photo Audit (Review Image Descriptions)
# ============================================================

def audit_photo_descriptions(photo_entries):
    """
    Audita las imágenes descargadas:
    - Verifica si tienen descripción
    - Valida la nomenclatura
    - Reporta problemas
    """
    try:
        print('\n========== MODULE 2B: Auditing photo descriptions ==========')

        if not photo_entries:
            print('  No photos to audit.')
            return

        audit_results = {
            "total": len(photo_entries),
            "ok": [],
            "no_description": [],
            "bad_nomenclature": []
        }

        for idx, entry in enumerate(photo_entries, 1):
            caption = entry.get('caption', '').strip()
            photo_path = entry.get('photo_path', '?')
            date_str = entry.get('date', '?')
            times = entry.get('times', [])
            salas = entry.get('salas', [])

            print(f'\n  [{idx}] {photo_path}')

            # Check 1: Has description?
            if not caption:
                print(f'      ❌ Sin descripción')
                audit_results["no_description"].append({
                    "photo": photo_path,
                    "date": date_str,
                    "times": times,
                    "salas": salas,
                    "issue": "Imagen sin descripción"
                })
                continue

            # Check 2: Valid nomenclature?
            parsed = parse_photo_caption(caption)
            if not parsed:
                print(f'      ❌ Nomenclatura inválida: "{caption}"')
                print(f'         Debe reenviarse con: DD/MM HH:MM sala')
                audit_results["bad_nomenclature"].append({
                    "photo": photo_path,
                    "caption": caption,
                    "issue": "Nomenclatura inválida - Debe reenviar con: DD/MM HH:MM sala"
                })
                continue

            # Check 3: Image file exists?
            if not os.path.exists(photo_path):
                print(f'      ⚠️  Archivo no encontrado')
                audit_results["no_description"].append({
                    "photo": photo_path,
                    "issue": "Archivo de imagen no encontrado"
                })
                continue

            # All good!
            print(f'      ✅ OK - {caption}')
            audit_results["ok"].append({
                "photo": os.path.basename(photo_path),
                "caption": caption,
                "date": date_str,
                "times": times,
                "salas": salas
            })

        # Print summary
        print(f'\n  ═══════════════════════════════════════════════════')
        print(f'  RESUMEN:')
        print(f'    ✅ Válidas:               {len(audit_results["ok"])}')
        print(f'    ❌ Sin descripción:      {len(audit_results["no_description"])}')
        print(f'    ❌ Nomenclatura inválida: {len(audit_results["bad_nomenclature"])}')
        print(f'  ═══════════════════════════════════════════════════')

        # Save audit results
        audit_fp = os.path.join(sys.path[0], 'data', 'photo_audit_results.json')
        with open(audit_fp, 'w') as f:
            json.dump(audit_results, f, indent=2, ensure_ascii=False)
        print(f'  Reporte guardado en: {audit_fp}')

        print(f'\n========== MODULE 2B DONE ==========')

    except Exception as e:
        print(f'  [ERROR] audit_photo_descriptions: {e}, line: {e.__traceback__.tb_lineno}')


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
    """Returns list of negative review entries (with booking info) for Module 5."""
    negative_reviews = []
    try:
        print('\n========== MODULE 3: Checking pending replies ==========')

        if not os.path.exists(pending_replies_fp):
            print('  No pending replies file.')
            return negative_reviews

        pending = json.load(open(pending_replies_fp, 'r'))
        if len(pending) == 0:
            print('  No pending replies.')
            return negative_reviews

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
                    print('  -> POSITIVE! Sending review photo + link.')
                    with open(positive_review_template_fp, 'r', encoding='utf-8') as f:
                        review_msg = f.read().strip()

                    try:
                        # Step 1: Send review photo if it exists
                        if os.path.exists(review_photo_fp):
                            print('  -> Copying review photo to clipboard...')
                            photo_ps_path = os.path.abspath(review_photo_fp).replace("\\", "/")
                            ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile('{photo_ps_path}')
[System.Windows.Forms.Clipboard]::SetImage($img)
$img.Dispose()
"""
                            subprocess.run(["powershell", "-STA", "-command", ps_script], check=True, timeout=30)
                            wb.web_browser.switch_to.window(wb.web_browser.current_window_handle)
                            time.sleep(2)

                            # Find chat input and paste image
                            chat_input = None
                            for selector in [
                                "footer div[contenteditable='true']",
                                "div[contenteditable='true'][data-tab]",
                                "div[aria-placeholder='Escribe un mensaje']"
                            ]:
                                try:
                                    chat_input = wb.web_browser.find_element(By.CSS_SELECTOR, selector)
                                    wb.web_browser.execute_script("arguments[0].focus(); arguments[0].click();", chat_input)
                                    break
                                except:
                                    continue
                            time.sleep(1)

                            print('  -> Pasting review photo...')
                            if chat_input:
                                chat_input.send_keys(Keys.CONTROL, 'v')
                            else:
                                ActionChains(wb.web_browser).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                            time.sleep(3)

                            # Wait for preview and click send (no caption)
                            preview_found = False
                            for wait_i in range(15):
                                time.sleep(2)
                                try:
                                    escribe_inputs = wb.web_browser.find_elements(By.CSS_SELECTOR, "div[aria-placeholder*='Escribe un mensaje']")
                                    if len(escribe_inputs) >= 2:
                                        preview_found = True
                                        break
                                except:
                                    pass
                                for sel in ["span[data-icon='wds-ic-send-filled']", "span[data-icon='pencil']", "span[data-icon='crop']"]:
                                    try:
                                        if wb.web_browser.find_elements(By.CSS_SELECTOR, sel):
                                            preview_found = True
                                            break
                                    except:
                                        continue
                                if preview_found:
                                    break

                            if preview_found:
                                for send_sel in ["span[data-icon='send']", "span[data-icon='wds-ic-send-filled']", "div[aria-label='Enviar']"]:
                                    try:
                                        send_btn = wb.web_browser.find_element(By.CSS_SELECTOR, send_sel)
                                        wb.web_browser.execute_script("arguments[0].click();", send_btn)
                                        print('  -> Review photo sent!')
                                        break
                                    except:
                                        continue
                                time.sleep(5)
                            else:
                                print('  -> [WARN] Preview not detected for review photo, skipping photo.')
                                try:
                                    ActionChains(wb.web_browser).send_keys(Keys.ESCAPE).perform()
                                    time.sleep(2)
                                except:
                                    pass
                        else:
                            print(f'  -> [WARN] Review photo not found at {review_photo_fp}, sending text only.')

                        # Step 2: Send the review text message
                        print('  -> Sending review text...')
                        chat_input_2 = None
                        for selector in [
                            "footer div[contenteditable='true']",
                            "div[contenteditable='true'][data-tab]",
                            "div[aria-placeholder='Escribe un mensaje']"
                        ]:
                            try:
                                chat_input_2 = wb.web_browser.find_element(By.CSS_SELECTOR, selector)
                                break
                            except:
                                continue

                        if chat_input_2:
                            wb.web_browser.execute_script("arguments[0].focus(); arguments[0].click();", chat_input_2)
                            time.sleep(0.5)
                            pyperclip.copy(review_msg)
                            ActionChains(wb.web_browser).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                            time.sleep(1)
                            ActionChains(wb.web_browser).send_keys(Keys.ENTER).perform()
                            time.sleep(3)
                            print('  -> Review text sent!')
                        else:
                            print('  -> [ERROR] Could not find chat input for review text.')
                            updated_pending.append(entry)
                            continue
                    except Exception as ex:
                        print(f'  [ERROR] Failed to send positive review: {ex}')
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
                        wb.web_browser.execute_script("arguments[0].focus(); arguments[0].click();", chat_input)
                        time.sleep(0.5)

                        pyperclip.copy(neg_msg)
                        ActionChains(wb.web_browser).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                        time.sleep(1)
                        ActionChains(wb.web_browser).send_keys(Keys.ENTER).perform()
                        time.sleep(3)
                        print('  Negative response sent.')
                        # Accumulate for Module 5 (dequeue review email in Turitop)
                        negative_reviews.append(entry)
                        print(f'  -> Added to negative reviews queue for Turitop dequeue.')
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
        if negative_reviews:
            print(f'  -> {len(negative_reviews)} negative reviews queued for Turitop dequeue.')
        return negative_reviews

    except Exception as e:
        print(f'  [ERROR] check_pending_replies: {e}, line: {e.__traceback__.tb_lineno}')
        return negative_reviews


# ============================================================
# MODULE 5 — Dequeue Turitop review emails for negative reviews
# ============================================================

def dequeue_negative_review_emails(negative_entries):
    """For each negative review, go to Turitop, find the booking,
    click 'Acciones del Email' and select 'Desencolar el email de solicitud de opinión automática'."""
    try:
        print(f'\n========== MODULE 5: Dequeuing {len(negative_entries)} review emails ==========')

        if not negative_entries:
            print('  No negative reviews to process.')
            print('========== MODULE 5 DONE ==========')
            return

        # Open Turitop in a new tab
        wb.web_browser.execute_script("window.open('')")
        wb.web_browser.switch_to.window(wb.web_browser.window_handles[-1])
        wb.get("https://app.turitop.com/admin/company/P271/bookings")
        time.sleep(5)

        if "admin/login/es/" in wb.web_browser.current_url:
            print("  [WARN] Turitop logged out! Cannot dequeue emails.")
            wb.web_browser.close()
            wb.web_browser.switch_to.window(wb.web_browser.window_handles[0])
            return

        for entry in negative_entries:
            try:
                booking_code = entry.get('booking_code', '')
                booking_date_str = entry.get('booking_date', '')  # e.g. "26 Mar 2026"
                booking_day = entry.get('booking_day', '')
                booking_time = entry.get('booking_time', '')
                booking_place = entry.get('booking_place', '')

                print(f'\n  Processing: {booking_code} (day={booking_day} time={booking_time} place={booking_place})')

                # Parse the date to get day/month for Turitop filter
                # booking_code format: "26/3_17:30_4e"
                parts = booking_code.split('_')
                if len(parts) >= 1:
                    date_parts = parts[0].split('/')
                    if len(date_parts) == 2:
                        day = date_parts[0]
                        month = date_parts[1]
                    else:
                        print(f'  -> Cannot parse date from booking_code: {booking_code}')
                        continue
                else:
                    print(f'  -> Invalid booking_code format: {booking_code}')
                    continue

                year = datetime.datetime.now().year
                target_date = f"{int(day):02d}-{int(month):02d}-{year}"

                # Navigate to bookings and filter by date
                wb.get("https://app.turitop.com/admin/company/P271/bookings")
                time.sleep(5)

                wb.send_keys("#filter_event_date_from", target_date, full=True, clear=True)
                wb.send_keys("#filter_event_date_to", target_date, full=True, clear=True)
                time.sleep(2)
                wb.js_click("button[type=submit][name=action]")
                time.sleep(5)

                # Find the correct booking row by matching day, time and place
                rows = wb.web_browser.find_elements(
                    By.CSS_SELECTOR, "tr.bookings-history-row:not([class*='deleted'])"
                )

                target_row = None
                for row in rows:
                    try:
                        row_day = wb.get_text("div.format-day-of-month-number", row)
                        row_time = wb.get_text("div.format-time-short", row)
                        row_place = wb.get_text("span.bookings-product-name", row)

                        # Match by time (most specific) and optionally by place
                        if row_time.strip() == booking_time.strip() and row_day.strip() == day.strip():
                            # If we have place info, also verify it
                            if booking_place:
                                if booking_place.upper().replace('#', '') in row_place.upper().replace('#', ''):
                                    target_row = row
                                    break
                            else:
                                target_row = row
                                break
                    except:
                        continue

                if not target_row:
                    print(f'  -> Booking row not found in Turitop.')
                    continue

                print(f'  -> Found booking row. Clicking "Acciones del Email"...')

                # Find and click the "Acciones del Email" button (wrench/tool icon)
                email_action_btn = None
                try:
                    # The email actions button - try common icon selectors in the row
                    for btn_sel in [
                        "a[title*='Acciones']",
                        "a[title*='acciones']",
                        "a[title*='Email']",
                        "a[title*='email']",
                        "a.btn-email-actions",
                        "a[onclick*='emailAction']",
                        "a[onclick*='email_action']",
                    ]:
                        try:
                            email_action_btn = target_row.find_element(By.CSS_SELECTOR, btn_sel)
                            break
                        except:
                            continue

                    # Fallback: try all action buttons/links in the row
                    if not email_action_btn:
                        action_links = target_row.find_elements(By.CSS_SELECTOR, "a.btn, a[role='button'], td a")
                        for link in action_links:
                            title = (link.get_attribute('title') or '').lower()
                            onclick = (link.get_attribute('onclick') or '').lower()
                            icon = ''
                            try:
                                icon_el = link.find_element(By.CSS_SELECTOR, "i, span")
                                icon = (icon_el.get_attribute('class') or '').lower()
                            except:
                                pass
                            if ('email' in title or 'email' in onclick or
                                'wrench' in icon or 'tool' in icon or 'cog' in icon or
                                'acciones' in title):
                                email_action_btn = link
                                break

                except Exception as btn_err:
                    print(f'  -> Error finding email action button: {btn_err}')

                if not email_action_btn:
                    print(f'  -> [WARN] Could not find "Acciones del Email" button.')
                    continue

                wb.web_browser.execute_script("arguments[0].click();", email_action_btn)
                print(f'  -> Waiting 10s for email actions menu...')
                time.sleep(10)

                # Now look for the dropdown/select with "Desencolar" option
                dequeue_clicked = False

                # Try 1: It might be a <select> dropdown with "Escoge una acción"
                try:
                    select_el = wb.web_browser.find_element(By.CSS_SELECTOR, "select")
                    from selenium.webdriver.support.ui import Select
                    select_obj = Select(select_el)
                    for option in select_obj.options:
                        opt_text = (option.get_attribute('innerText') or '').strip().lower()
                        if 'desencolar' in opt_text:
                            select_obj.select_by_visible_text(option.get_attribute('innerText').strip())
                            dequeue_clicked = True
                            print(f'  -> Selected "Desencolar" option from dropdown.')
                            break
                except:
                    pass

                # Try 2: Click on list items / links if it's a menu
                if not dequeue_clicked:
                    try:
                        menu_items = wb.web_browser.find_elements(By.CSS_SELECTOR, "a, li, div[role='option'], option")
                        for item in menu_items:
                            item_text = (item.get_attribute('innerText') or '').strip().lower()
                            if 'desencolar' in item_text:
                                wb.web_browser.execute_script("arguments[0].click();", item)
                                dequeue_clicked = True
                                print(f'  -> Clicked "Desencolar" option.')
                                break
                    except:
                        pass

                if dequeue_clicked:
                    time.sleep(3)
                    # Check for confirmation dialog and accept
                    try:
                        alert = wb.web_browser.switch_to.alert
                        alert.accept()
                        print(f'  -> Confirmation alert accepted.')
                    except:
                        pass
                    # Also try clicking any confirm/ok buttons
                    for confirm_sel in ["button.btn-primary", "button.btn-success", "input[type='submit']", "button[type='submit']"]:
                        try:
                            confirm_btn = wb.web_browser.find_element(By.CSS_SELECTOR, confirm_sel)
                            wb.web_browser.execute_script("arguments[0].click();", confirm_btn)
                            break
                        except:
                            continue
                    time.sleep(3)
                    print(f'  -> [OK] Review email dequeued for {booking_code}!')
                else:
                    print(f'  -> [WARN] Could not find "Desencolar" option.')
                    # Close any open dialog
                    try:
                        for close_sel in ["button.btn-danger", "a.close", "button[data-dismiss]"]:
                            try:
                                close_btn = wb.web_browser.find_element(By.CSS_SELECTOR, close_sel)
                                wb.web_browser.execute_script("arguments[0].click();", close_btn)
                                break
                            except:
                                continue
                    except:
                        pass

            except Exception as e_entry:
                print(f'  [ERROR] Processing negative entry: {e_entry}, line: {e_entry.__traceback__.tb_lineno}')

        # Close Turitop tab
        try:
            wb.web_browser.close()
            wb.web_browser.switch_to.window(wb.web_browser.window_handles[0])
        except:
            pass

        print(f'\n========== MODULE 5 DONE ==========')

    except Exception as e:
        print(f'  [ERROR] dequeue_negative_review_emails: {e}, line: {e.__traceback__.tb_lineno}')
        try:
            if len(wb.web_browser.window_handles) > 1:
                wb.web_browser.close()
                wb.web_browser.switch_to.window(wb.web_browser.window_handles[0])
        except:
            pass


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
# Dismiss Chrome's "Restore pages?" dialog if present
time.sleep(2)
wb.dismiss_restore_dialog()
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

# Module 2B: Audit photo descriptions
if photo_entries:
    audit_photo_descriptions(photo_entries)

# Module 3: Check pending replies
negative_reviews = check_pending_replies() or []

# Module 5: Dequeue review emails for negative reviews
if negative_reviews:
    dequeue_negative_review_emails(negative_reviews)
else:
    print("\nNo negative reviews — skipping Module 5.")

print("\n" + "=" * 60)
print("  ALL DONE! Press Enter to close browser and exit.")
print("=" * 60)
input()
wb.web_browser.quit()
