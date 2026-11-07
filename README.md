# PriceParser

Парсер цен с сайта vodoparad.ru.
Можно добавить ссылки на товары, обновить цены и посмотреть результат в браузере.

Стек: Python, Flask, Selenium, SQLite.

## Что умеет

- Получать название и цену товара.
- Обновлять один товар или весь список.
- Сохранять историю цен и журнал обновлений в SQLite.
- Удалять товары из списка.

## Запуск

Нужны Python 3.13 и Google Chrome. Из корня репозитория:

```bash
python -m venv .venv
```

Активировать окружение в PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

В Linux и macOS — `source .venv/bin/activate`.
После этого:

```bash
python -m pip install -r requirements.txt
python PriceParser/app.py
```

Открыть http://localhost:5000. База `PriceParser/prices.db` создаётся сама.
При первом запуске парсера Selenium может скачать ChromeDriver.

## Тесты

```bash
python -m unittest discover -s tests -v
```

Тесты проверяют разбор цен и работу с товарами во временной базе. К магазину они не обращаются.

Парсер работает с одним сайтом, цены обновляются вручную. Если разметка магазина изменится, селекторы придётся поправить.
