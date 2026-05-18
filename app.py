import os
import time
import json
import traceback
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Log:
    @staticmethod
    def info(msg):
        print(msg)

    @staticmethod
    def warning(msg):
        print(msg)

    @staticmethod
    def error(msg):
        print(msg)


log = Log()
LIVE_FILE = "live_status.json"


def update_live_file(data, path=LIVE_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def set_status(data, status, step_label):
    data["status"] = status
    data["step"] = step_label
    data["updated_at"] = datetime.utcnow().isoformat() + "Z"
    update_live_file(data)


def build_driver(headless=False):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=opts)


def safe_click(driver, element):
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


def wait_ready(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def screenshot(driver, name):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{name}_{ts}.png"
    driver.save_screenshot(path)
    return path


def step1_navigate_and_open_chat(driver, data):
    log.info("\n[1/6] Opening CoinDCX support portal...")
    set_status(data, "navigating", "step1")

    driver.get("https://support.coindcx.com/")
    wait_ready(driver, 30)
    log.info("  Page fully loaded")

    time.sleep(2)

    trigger_selectors = [
        "#spr-chat__trigger-button",
        "button[id*='spr-chat']",
        "[aria-label*='chat' i]",
        "[aria-label*='support' i]",
    ]

    last_error = None
    for attempt in range(1, 4):
        log.info(f"  Attempt {attempt}/3 to open support chat...")
        try:
            trigger = None
            for sel in trigger_selectors:
                try:
                    trigger = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                    )
                    log.info(f"    Trigger found: {sel}")
                    break
                except Exception:
                    pass

            if not trigger:
                raise Exception("No clickable chat trigger found")

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center', inline:'center'});",
                trigger,
            )
            time.sleep(0.5)
            safe_click(driver, trigger)

            WebDriverWait(driver, 8).until(
                lambda d: (
                    len(d.find_elements(By.CSS_SELECTOR, ".spr-chat__window")) > 0
                    or len(
                        d.find_elements(
                            By.CSS_SELECTOR, "[id*='spr-chat'][aria-expanded='true']"
                        )
                    )
                    > 0
                    or len(
                        d.find_elements(
                            By.CSS_SELECTOR, "iframe[src*='chat'], iframe[id*='chat']"
                        )
                    )
                    > 0
                )
            )

            log.info("  Support chat opened")
            return True

        except Exception as e:
            last_error = e
            log.warning(f"    Attempt failed: {e}")
            time.sleep(2)

    shot = screenshot(driver, "step1_chat_open_failure")
    log.error(f"  Failed to open chat: {last_error}")
    log.error(f"  Screenshot: {shot}")
    return False


def step2_wait_for_input(driver, data):
    log.info("\n[2/6] Waiting for chat input...")
    set_status(data, "waiting_input", "step2")

    input_selectors = ["textarea", "input[type='text']", "[contenteditable='true']"]

    for sel in input_selectors:
        try:
            elem = WebDriverWait(driver, 12).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, sel))
            )
            log.info(f"  Input ready: {sel}")
            return elem
        except Exception:
            pass

    shot = screenshot(driver, "step2_input_not_found")
    log.error("  Chat input not found")
    log.error(f"  Screenshot: {shot}")
    return None


def step3_send_message(driver, data, input_elem, message):
    log.info("\n[3/6] Sending message...")
    set_status(data, "sending_message", "step3")

    try:
        if input_elem.tag_name in ("input", "textarea"):
            input_elem.clear()
    except Exception:
        pass

    input_elem.send_keys(message)

    send_selectors = [
        "button[type='submit']",
        "button[aria-label*='send' i]",
        "button[id*='send' i]",
    ]

    clicked = False
    for sel in send_selectors:
        try:
            btn = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
            )
            safe_click(driver, btn)
            clicked = True
            break
        except Exception:
            pass

    if not clicked:
        input_elem.send_keys("\n")

    log.info("  Message sent")
    return True


def step4_wait_response(driver, data, timeout=45):
    log.info("\n[4/6] Waiting for support response...")
    set_status(data, "waiting_response", "step4")

    end = time.time() + timeout

    while time.time() < end:
        candidates = driver.find_elements(By.CSS_SELECTOR, ".message, .chat-message, li")
        visible_texts = [c.text.strip() for c in candidates if c.text and c.text.strip()]

        if visible_texts:
            newest = visible_texts[-1]
            log.info(f"  Latest response: {newest[:120]}")
            return newest

        time.sleep(2)

    shot = screenshot(driver, "step4_no_response")
    log.warning("  No response within timeout")
    log.warning(f"  Screenshot: {shot}")
    return ""


def step5_save_result(data, response_text):
    log.info("\n[5/6] Saving response...")
    set_status(data, "saving", "step5")

    out = {
        "status": "done" if response_text else "partial",
        "response": response_text,
        "saved_at": datetime.utcnow().isoformat() + "Z",
    }

    with open("coindcx_support_result.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    log.info("  Response saved to coindcx_support_result.json")


def step6_cleanup(driver, data):
    log.info("\n[6/6] Cleanup...")
    set_status(data, "cleanup", "step6")
    driver.quit()
    set_status(data, "completed", "done")
    log.info("  Browser closed")
    log.info("  Flow completed")


def run_support_flow(user_message, headless=False):
    data = {
        "status": "starting",
        "step": "init",
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    update_live_file(data)

    driver = None
    try:
        driver = build_driver(headless=headless)

        ok = step1_navigate_and_open_chat(driver, data)
        if not ok:
            return False

        input_elem = step2_wait_for_input(driver, data)
        if not input_elem:
            return False

        step3_send_message(driver, data, input_elem, user_message)
        response = step4_wait_response(driver, data, timeout=60)
        step5_save_result(data, response)
        return True

    except Exception as e:
        log.error(f"\nFatal error: {e}")
        log.error(traceback.format_exc())
        data["status"] = "failed"
        data["error"] = str(e)
        update_live_file(data)
        if driver:
            shot = screenshot(driver, "fatal_error")
            log.error(f"Screenshot: {shot}")
        return False

    finally:
        if driver:
            step6_cleanup(driver, data)


if __name__ == "__main__":
    message = os.getenv("SUPPORT_MESSAGE", "Hi, I need help with my CoinDCX account issue.")
    headless = os.getenv("HEADLESS", "false").lower() == "true"
    run_support_flow(message, headless=headless)
