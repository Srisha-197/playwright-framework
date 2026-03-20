from core.driver import get_driver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

driver = get_driver()
time.sleep(3)

updates_tab = driver.find_element(AppiumBy.XPATH, "//android.widget.FrameLayout[@content-desc='Updates']")
updates_tab.click()
time.sleep(3)
with open("updates_source.xml", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

print("Updates page source saved!")
driver.quit()