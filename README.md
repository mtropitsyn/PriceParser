# PriceParser

Локальный трекер цен товаров **vodoparad.ru** с веб-интерфейсом.
Приложение открывает страницу товара через Selenium, сохраняет цену в SQLite и показывает журнал обновлений.

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-43B02A?logo=selenium&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
[![Tests](https://github.com/mtropitsyn/PriceParser/actions/workflows/tests.yml/badge.svg)](https://github.com/mtropitsyn/PriceParser/actions/workflows/tests.yml)

## Возможности

- Добавление и удаление отслеживаемых товаров.
- Получение названия и цены со страницы товара.
- Обновление одного товара или всего списка вручную.
- Хранение истории цен и журнала парсинга в SQLite.
- Отображение последней цены и статуса обновлений в браузере.

## Требования

- Python 3.13 — версия, используемая в CI.
- Установленный Google Chrome для получения страниц товаров.
- Интернет: Selenium Manager может загрузить совместимый ChromeDriver при первом парсинге.

## Быстрый запуск

```bash
git clone https://github.com/mtropitsyn/PriceParser.git
cd PriceParser
python -m venv .venv
```

Активируйте окружение:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
```

Установите зависимости и запустите приложение:

```bash
python -m pip install -r requirements.txt
python PriceParser/app.py
```

Откройте **http://localhost:5000**, добавьте ссылку на товар vodoparad.ru и дождитесь обновления.
База `PriceParser/prices.db` создаётся автоматически и не хранится в репозитории.
При необходимости задайте путь к другой базе переменной окружения `PRICEPARSER_DB` до запуска.

## Проверки

```bash
python -m unittest discover -s tests -v
```

Проверки используют временную SQLite-базу и подменяют обращение к магазину. Chrome и доступ к сайту для них не нужны.
GitHub Actions запускает этот же набор проверок.

## Устройство проекта

```text
PriceParser/
├── app.py                # Flask-маршруты и операции с товарами
├── database.py           # Единая схема и подключения SQLite
├── parser.py             # Получение страниц через Selenium
├── price_utils.py        # Разбор целых и дробных цен
└── templates/index.html  # Веб-интерфейс
tests/                    # Проверки цен и маршрутов
requirements.txt          # Версии зависимостей
```

## Ограничения

Парсер настроен на разметку одного магазина: изменение страницы или ограничения доступа могут потребовать обновления селекторов.
Обновления запускаются вручную и выполняются последовательно в HTTP-запросе; большой список может обрабатываться долго.
Интерфейс показывает последнюю цену, история сохраняется в базе. Приложение предназначено для локального использования и запускается на `127.0.0.1`.
