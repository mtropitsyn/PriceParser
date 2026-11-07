import sqlite3
from database import get_connection
from price_utils import parse_price
import time
from typing import Optional, Dict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


def log_parsing(url: str, status: str, price: float, shop: str = 'vodoparad.ru', message: str = '') -> None:
    """
    Записывает результат парсинга в таблицу parsing_log.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO parsing_log (product_url, status, price, shop_name, message, parsed_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        ''', (url, status, price, shop, message or 'OK'))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка записи в лог: {e}")
    finally:
        if conn is not None:
            conn.close()


def get_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Создаёт и возвращает настроенный Chrome-драйвер.
    """
    options = Options()

    if headless:
        options.add_argument('--headless=new')

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Реалистичный User-Agent
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    )

    try:
        driver = webdriver.Chrome(options=options)
        # Дополнительная защита от детекта
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => false});")
        return driver
    except WebDriverException as e:
        print(f"Ошибка запуска ChromeDriver: {e}")
        raise


def parse_product(url: str, timeout: int = 15) -> Optional[Dict[str, object]]:
    """
    Парсит страницу товара на vodoparad.ru и возвращает словарь с данными.
    Возвращает None при ошибке.
    """
    driver = None
    try:
        driver = get_driver(headless=True)
        driver.get(url)

        wait = WebDriverWait(driver, timeout)

        # --- Поиск цены: несколько стратегий ---
        price = 0.0
        price_selectors = [
            "p.price-new",                    # Основная текущая цена
            "span.price-new",                 # Альтернатива
            "[class*='price-new']",           # Частичный класс
            "span.price",                     # Старый вариант
            "[data-price]",                   # Атрибут data-price
            "meta[property='product:price:amount']"  # OpenGraph мета-тег (резерв)
        ]

        price_elem = None
        for selector in price_selectors:
            try:
                if selector.startswith("meta"):
                    price_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    price_text = price_elem.get_attribute("content")
                else:
                    price_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    price_text = price_elem.text.strip()

                if price_text:
                    # Учитываем десятичный разделитель в цене
                    parsed_price = parse_price(price_text)
                    if parsed_price is not None:
                        price = parsed_price
                        break
            except TimeoutException:
                continue  # Пробуем следующий селектор

        # --- Название товара ---
        try:
            name_elem = driver.find_element(By.TAG_NAME, "h1")
            name = name_elem.text.strip()[:200]
        except:
            # Резерв: из title страницы
            name = driver.title.split('|')[0].strip()[:200] if '|' in driver.title else driver.title[:200]

        if not name:
            name = 'Неизвестно'

        # --- Логирование и возврат ---
        status = 'success' if price > 0 else 'warning' if price == 0 else 'error'
        log_parsing(url, status, price, 'vodoparad.ru',
                    'OK' if status == 'success' else 'Цена не найдена' if price == 0 else 'Ошибка парсинга')

        return {
            'name': name,
            'price': price,
            'url': url
        }

    except TimeoutException:
        log_parsing(url, 'error', 0, 'vodoparad.ru', 'Таймаут загрузки элемента (цена не появилась)')
        return None
    except Exception as e:
        log_parsing(url, 'error', 0, 'vodoparad.ru', f'Неизвестная ошибка: {str(e)}')
        return None
    finally:
        if driver:
            driver.quit()

