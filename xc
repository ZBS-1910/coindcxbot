log.info("\n[1/6] Opening CoinDCX support portal...")

data["status"] = "navigating"
update_live_file(data)

driver.get("https://support.coindcx.com/")

# Wait for full page load
WebDriverWait(driver, 30).until(
    lambda d: d.execute_script("return document.readyState") == "complete"
)
log.info("  ✔ Page fully loaded")

# Optional: small buffer for widget bootstrap
time.sleep(2)

trigger_selectors = [
    "#spr-chat__trigger-button",
    "button[id*='spr-chat']",
    "[aria-label*='chat' i]",
    "[aria-label*='support' i]"
]

opened = False
last_error = None

for attempt in range(1, 4):
    log.info(f"  • Attempt {attempt}/3 to open support chat...")
    try:
        trigger = None
        for sel in trigger_selectors:
            try:
                trigger = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                log.info(f"    ✔ Trigger found with selector: {sel}")
                break
            except Exception:
                continue

        if not trigger:
            raise Exception("No clickable chat trigger found with known selectors")

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center', inline:'center'});",
            trigger
        )
        time.sleep(0.5)

        try:
            trigger.click()
        except Exception:
            driver.execute_script("arguments[0].click();", trigger)

        # Confirm chat opened (panel/expanded state/iframe)
        WebDriverWait(driver, 8).until(
            lambda d: (
                len(d.find_elements(By.CSS_SELECTOR, ".spr-chat__window")) > 0 or
                len(d.find_elements(By.CSS_SELECTOR, "[id*='spr-chat'][aria-expanded='true']")) > 0 or
                len(d.find_elements(By.CSS_SELECTOR, "iframe[src*='chat'], iframe[id*='chat']")) > 0
            )
        )

        opened = True
        log.info("  ✔ Support chat opened")
        break

    except Exception as e:
        last_error = e
        log.warning(f"    ⚠ Attempt {attempt} failed: {e}")
        time.sleep(2)

if not opened:
    screenshot_path = "step1_chat_open_failure.png"
    try:
        driver.save_screenshot(screenshot_path)
        log.error(f"  ❌ Failed to open chat after retries: {last_error}")
        log.error(f"  📸 Screenshot saved: {screenshot_path}")
    except Exception as ss_e:
        log.error(f"  ❌ Failed to open chat after retries: {last_error}")
        log.error(f"  ⚠ Also failed to save screenshot: {ss_e}")