from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@logger.catch
def get_driver(headless: bool) -> webdriver:
    """
    Функция инициализирует webdriver
    """
    options: Options = Options()

    if headless:
        options.add_argument("--headless")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("start-maximized")
    driver: webdriver = webdriver.Chrome(options=options)

    return driver
