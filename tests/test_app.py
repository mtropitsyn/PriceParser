import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'PriceParser'))

import database
from app import app
from price_utils import parse_price


class PriceParsingTests(unittest.TestCase):
    def test_russian_and_metadata_prices(self):
        cases = {
            '1 299,90 ₽': 1299.90,
            '1\u00a0299,90 руб.': 1299.90,
            '1\u202f299,90 ₽': 1299.90,
            '1299.90': 1299.90,
            '1299,9': 1299.9,
            '12 345 ₽': 12345,
            '0': 0,
            'Цена: 499,50 руб.': 499.50,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(expected, parse_price(text))

    def test_missing_or_invalid_prices(self):
        for text in ['', 'Цена по запросу', '-1299', '1299.999', '1.299,90']:
            with self.subTest(text=text):
                self.assertIsNone(parse_price(text))


class ProductRoutesTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db_path = Path(self.directory.name) / 'prices.db'
        self.database_patch = patch.object(database, 'DATABASE_PATH', self.db_path)
        self.database_patch.start()
        self.addCleanup(self.database_patch.stop)
        database.init_database()
        self.client = app.test_client()
        self.url = 'https://www.vodoparad.ru/product/example'

    def add_product(self, price=1299.90):
        with patch('app.parse_product', return_value={'name': 'Тестовый товар', 'price': price}):
            return self.client.post('/add_product', data={'url': self.url})

    def test_home_and_empty_lists(self):
        self.assertEqual(200, self.client.get('/').status_code)
        self.assertEqual([], self.client.get('/get_products').get_json())
        self.assertEqual([], self.client.get('/get_logs').get_json())

    def test_add_duplicate_update_and_delete(self):
        self.assertTrue(self.add_product().get_json()['success'])
        products = self.client.get('/get_products').get_json()
        self.assertEqual(1, len(products))
        self.assertEqual(1299.90, products[0]['price'])
        self.assertFalse(self.add_product().get_json()['success'])
        product_id = products[0]['id']
        with patch('app.parse_product', return_value={'name': 'Тестовый товар', 'price': 1199.50}):
            self.assertTrue(self.client.post(f'/update_product/{product_id}').get_json()['success'])
        with closing(sqlite3.connect(self.db_path)) as conn:
            self.assertEqual(2, conn.execute('SELECT COUNT(*) FROM prices').fetchone()[0])
        self.assertTrue(self.client.post(f'/delete_product/{product_id}').get_json()['success'])
        self.assertEqual([], self.client.get('/get_products').get_json())
        with closing(sqlite3.connect(self.db_path)) as conn:
            self.assertEqual(0, conn.execute('SELECT COUNT(*) FROM prices').fetchone()[0])

    def test_invalid_url_does_not_parse(self):
        with patch('app.parse_product') as parser:
            response = self.client.post('/add_product', data={'url': 'not-a-url'}).get_json()
            self.assertFalse(response['success'])
            parser.assert_not_called()

    def test_failed_update_keeps_the_previous_price(self):
        self.add_product()
        product_id = self.client.get('/get_products').get_json()[0]['id']
        with patch('app.parse_product', return_value=None):
            self.assertFalse(self.client.post(f'/update_product/{product_id}').get_json()['success'])
        self.assertEqual(1299.90, self.client.get('/get_products').get_json()[0]['price'])

    def test_batch_parsing_with_no_products(self):
        with patch('app.parse_product') as parser:
            self.assertTrue(self.client.post('/run_parser').get_json()['success'])
            parser.assert_not_called()

    def test_log_uses_the_same_database(self):
        from parser import log_parsing
        log_parsing(self.url, 'success', 1299.90)
        logs = self.client.get('/get_logs').get_json()
        self.assertEqual(1, len(logs))
        self.assertEqual(1299.90, logs[0]['price'])


if __name__ == '__main__':
    unittest.main()
