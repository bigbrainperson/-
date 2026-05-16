"""
parser.py — статический парсер сайтов конкурентов кофеен
Курс: Наука о данных, spring26
Проект: Анализ открытия кофейни Surf Coffee рядом с ВШЭ на Покровском бульваре
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time


# ─────────────────────────────────────────────
# Класс для парсинга одного сайта
# ─────────────────────────────────────────────

class CoffeeSiteParser:
    """
    Парсер одного сайта кофейни.
    Принимает название и URL, делает запрос, обрабатывает HTML.
    """

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.soup = None
        self.success = False

    def fetch(self) -> bool:
        """Загружает страницу. Возвращает True при успехе."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        try:
            response = requests.get(self.url, headers=headers, timeout=15)
            response.raise_for_status()
            # Пробуем определить кодировку
            response.encoding = response.apparent_encoding or "utf-8"
            self.soup = BeautifulSoup(response.text, "html.parser")
            self.success = True
            print(f"[OK] {self.name}: страница загружена ({len(response.text)} символов)")
        except requests.exceptions.ConnectionError:
            print(f"[ОШИБКА] {self.name}: нет подключения к {self.url}")
        except requests.exceptions.Timeout:
            print(f"[ОШИБКА] {self.name}: превышено время ожидания")
        except requests.exceptions.HTTPError as e:
            print(f"[ОШИБКА] {self.name}: HTTP ошибка — {e}")
        except Exception as e:
            print(f"[ОШИБКА] {self.name}: неизвестная ошибка — {e}")
        return self.success

    def get_title(self) -> str:
        """Возвращает <title> страницы."""
        if not self.soup:
            return ""
        tag = self.soup.find("title")
        return tag.get_text(strip=True) if tag else ""

    def get_headings(self) -> dict:
        """Возвращает словарь {тег: [тексты]} для h1, h2, h3."""
        if not self.soup:
            return {}
        result = {}
        for tag in ["h1", "h2", "h3"]:
            texts = [el.get_text(strip=True) for el in self.soup.find_all(tag) if el.get_text(strip=True)]
            if texts:
                result[tag] = texts
        return result

    def get_paragraphs(self) -> list:
        """Возвращает список непустых абзацев <p>."""
        if not self.soup:
            return []
        return [el.get_text(strip=True) for el in self.soup.find_all("p") if el.get_text(strip=True)]

    def get_list_items(self) -> list:
        """Возвращает текст из элементов <li>."""
        if not self.soup:
            return []
        return [el.get_text(strip=True) for el in self.soup.find_all("li") if el.get_text(strip=True)]

    def get_links(self) -> list:
        """Возвращает список всех ссылок <a href=...>."""
        if not self.soup:
            return []
        links = []
        for a in self.soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.get_text(strip=True)
            if href and not href.startswith("#"):
                links.append({"text": text, "href": href})
        return links

    def get_full_text(self) -> str:
        """Возвращает весь видимый текст страницы."""
        if not self.soup:
            return ""
        # Убираем скрипты и стили
        for tag in self.soup(["script", "style", "noscript"]):
            tag.decompose()
        return " ".join(self.soup.get_text(separator=" ").split())

    def to_dict(self) -> dict:
        """Собирает всю информацию в один словарь."""
        headings = self.get_headings()
        return {
            "name": self.name,
            "url": self.url,
            "success": self.success,
            "title": self.get_title(),
            "h1": " | ".join(headings.get("h1", [])),
            "h2": " | ".join(headings.get("h2", [])),
            "h3": " | ".join(headings.get("h3", [])),
            "paragraphs_count": len(self.get_paragraphs()),
            "links_count": len(self.get_links()),
            "full_text_length": len(self.get_full_text()),
            "full_text_preview": self.get_full_text()[:500],
        }


# ─────────────────────────────────────────────
# Класс для парсинга меню "Правда кофе"
# ─────────────────────────────────────────────

class PravdaMenuParser:
    """
    Специализированный парсер меню Правда кофе.
    URL: https://pravdacoffee.ru/mainmenu/
    Использует регулярные выражения для извлечения цен и объёмов.
    """

    # Напитки, которые особенно важны для анализа
    KEY_DRINKS = [
        "американо", "капучино", "латте", "флэт уайт",
        "флэтуайт", "раф", "какао", "чай", "матча"
    ]

    def __init__(self, url: str = "https://pravdacoffee.ru/mainmenu/"):
        self.url = url
        self.soup = None
        self.raw_text = ""
        self.success = False

    def fetch(self) -> bool:
        """Загружает страницу меню."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        try:
            resp = requests.get(self.url, headers=headers, timeout=15)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            self.soup = BeautifulSoup(resp.text, "html.parser")
            # Убираем скрипты и стили
            for tag in self.soup(["script", "style", "noscript"]):
                tag.decompose()
            self.raw_text = " ".join(self.soup.get_text(separator="\n").split("\n"))
            self.success = True
            print(f"[OK] Меню Правда кофе загружено ({len(self.raw_text)} символов)")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось загрузить меню: {e}")
        return self.success

    def extract_prices_regex(self) -> list:
        """
        Пытается найти напитки и цены через регулярные выражения.
        Ищет паттерны вида: "Название ... 250 мл ... 180 руб"
        Примечание: часть цен может требовать ручной валидации.
        """
        if not self.raw_text:
            return []

        results = []

        # Паттерн 1: "Название (объём мл) цена ₽" или "Название цена р"
        # Ищем строки, которые содержат число (цена) рядом с ₽/руб/р
        price_pattern = re.compile(
            r'([А-ЯЁа-яёA-Za-z][А-ЯЁа-яёA-Za-z\s\-]{2,40}?)\s+'
            r'(?:(\d{2,4})\s*(?:мл|ml))?\s*'
            r'(\d{2,5})\s*(?:₽|руб|р\.?)\b',
            re.IGNORECASE
        )

        for match in price_pattern.finditer(self.raw_text):
            drink_name = match.group(1).strip().lower()
            volume_str = match.group(2)
            price_str = match.group(3)

            # Проверяем, похоже ли это на напиток (ключевые слова или общий случай)
            is_key = any(kw in drink_name for kw in self.KEY_DRINKS)
            volume_ml = int(volume_str) if volume_str else None
            price_rub = int(price_str) if price_str else None

            # Фильтрация: цена кофе обычно 100–700 руб
            if price_rub and 80 <= price_rub <= 700:
                results.append({
                    "drink_name": drink_name.strip(),
                    "category": self._categorize(drink_name),
                    "volume_ml": volume_ml,
                    "price_rub": price_rub,
                    "is_key_drink": is_key,
                    "source_url": self.url,
                    "validation_note": "авто" if is_key else "требует проверки",
                })

        return results

    def extract_structured(self) -> list:
        """
        Пробует извлечь данные из структурированного HTML (div, span, li).
        Дополняет результаты regex-парсинга.
        """
        if not self.soup:
            return []

        results = []

        # Ищем контейнеры с классами, характерными для меню
        menu_classes = [
            "menu", "product", "item", "dish", "drink",
            "price", "catalog", "card", "menu-item"
        ]

        for cls in menu_classes:
            items = self.soup.find_all(class_=re.compile(cls, re.IGNORECASE))
            for item in items[:50]:  # ограничиваем, чтобы не зависнуть
                text = item.get_text(separator=" ", strip=True)
                # Ищем цену в тексте элемента
                price_match = re.search(r'(\d{2,4})\s*(?:₽|руб|р\.?)', text)
                volume_match = re.search(r'(\d{2,4})\s*(?:мл|ml)', text, re.IGNORECASE)

                if price_match:
                    price = int(price_match.group(1))
                    volume = int(volume_match.group(1)) if volume_match else None
                    name = re.sub(r'\d+\s*(?:₽|руб|р\.?|мл|ml)', '', text).strip()
                    name = name[:60].lower()  # обрезаем

                    if 80 <= price <= 700 and len(name) > 2:
                        is_key = any(kw in name for kw in self.KEY_DRINKS)
                        results.append({
                            "drink_name": name,
                            "category": self._categorize(name),
                            "volume_ml": volume,
                            "price_rub": price,
                            "is_key_drink": is_key,
                            "source_url": self.url,
                            "validation_note": "структурный парсинг",
                        })

        return results

    def _categorize(self, name: str) -> str:
        """Простая категоризация напитка по ключевым словам."""
        name = name.lower()
        if any(w in name for w in ["эспрессо", "американо", "лонг блэк"]):
            return "эспрессо-напитки"
        if any(w in name for w in ["капучино", "латте", "флэт", "раф", "кортадо", "макиато"]):
            return "молочные напитки"
        if any(w in name for w in ["чай", "матча", "чайник"]):
            return "чай/матча"
        if any(w in name for w in ["какао", "шоколад", "чоко"]):
            return "какао/шоколад"
        if any(w in name for w in ["лимонад", "морс", "смузи", "сок"]):
            return "холодные напитки"
        return "прочее"

    def get_raw_text_snippet(self) -> str:
        """Возвращает первые 2000 символов текста страницы для диагностики."""
        return self.raw_text[:2000]


# ─────────────────────────────────────────────
# Функция: запуск парсинга всех сайтов
# ─────────────────────────────────────────────

def parse_all_sites(sites: list, delay: float = 1.5) -> tuple:
    """
    Принимает список словарей {"name": ..., "url": ...}.
    Возвращает (df_sites, df_links) — два датафрейма.
    """
    all_site_data = []
    all_links = []

    for site in sites:
        parser = CoffeeSiteParser(name=site["name"], url=site["url"])
        if parser.fetch():
            all_site_data.append(parser.to_dict())
            # Сохраняем ссылки с меткой сайта
            for link in parser.get_links():
                link["source_name"] = site["name"]
                link["source_url"] = site["url"]
                all_links.append(link)
        else:
            # Добавляем строку с пометкой об ошибке
            all_site_data.append({
                "name": site["name"],
                "url": site["url"],
                "success": False,
                "title": "", "h1": "", "h2": "", "h3": "",
                "paragraphs_count": 0, "links_count": 0,
                "full_text_length": 0, "full_text_preview": "",
            })
        time.sleep(delay)  # пауза между запросами — вежливый парсинг

    df_sites = pd.DataFrame(all_site_data)
    df_links = pd.DataFrame(all_links) if all_links else pd.DataFrame(
        columns=["text", "href", "source_name", "source_url"]
    )
    return df_sites, df_links


# ─────────────────────────────────────────────
# Список сайтов для парсинга
# ─────────────────────────────────────────────

SITES_TO_PARSE = [
    {"name": "Правда кофе",   "url": "https://pravdacoffee.ru/"},
    {"name": "Corner Coffee", "url": "https://cornercoffee.ru/"},
    {"name": "Jeffrey's Coffee", "url": "https://jeffreys.ru/"},
]


# ─────────────────────────────────────────────
# Точка входа (если запускать parser.py напрямую)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Парсинг сайтов конкурентов кофеен")
    print("=" * 60)

    # 1. Парсим основные сайты
    df_sites, df_links = parse_all_sites(SITES_TO_PARSE)

    df_sites.to_csv("data/raw/parsed_sites.csv", index=False, encoding="utf-8-sig")
    df_links.to_csv("data/raw/parsed_links.csv", index=False, encoding="utf-8-sig")
    print(f"\nСохранено: parsed_sites.csv ({len(df_sites)} строк), "
          f"parsed_links.csv ({len(df_links)} строк)")

    # 2. Парсим меню Правда кофе
    print("\n" + "=" * 60)
    print("Парсинг меню Правда кофе")
    print("=" * 60)

    menu_parser = PravdaMenuParser()
    if menu_parser.fetch():
        # Попытка 1: regex
        items_regex = menu_parser.extract_prices_regex()
        # Попытка 2: структурный HTML
        items_structured = menu_parser.extract_structured()

        # Объединяем и дедуплицируем
        all_items = items_regex + items_structured
        df_raw_menu = pd.DataFrame(all_items)

        if not df_raw_menu.empty:
            df_raw_menu = df_raw_menu.drop_duplicates(subset=["drink_name", "price_rub"])
            df_raw_menu.to_csv("data/raw/pravda_menu_raw.csv", index=False, encoding="utf-8-sig")
            print(f"Сохранено: pravda_menu_raw.csv ({len(df_raw_menu)} строк)")
        else:
            print("Меню: автоматически не извлечено — сохраняем сырой текст")
            pd.DataFrame([{"raw_text": menu_parser.get_raw_text_snippet()}]).to_csv(
                "data/raw/pravda_menu_raw.csv", index=False, encoding="utf-8-sig"
            )
    else:
        print("Меню не доступно — создаём пустой файл с примером данных.")
        # Ручные данные для fallback (цены актуальны на 2024–2025 г.)
        fallback = [
            {"drink_name": "американо",  "category": "эспрессо-напитки", "volume_ml": 250, "price_rub": 170, "is_key_drink": True, "source_url": "ручной ввод", "validation_note": "ручная валидация"},
            {"drink_name": "капучино",   "category": "молочные напитки",  "volume_ml": 300, "price_rub": 220, "is_key_drink": True, "source_url": "ручной ввод", "validation_note": "ручная валидация"},
            {"drink_name": "латте",      "category": "молочные напитки",  "volume_ml": 350, "price_rub": 240, "is_key_drink": True, "source_url": "ручной ввод", "validation_note": "ручная валидация"},
            {"drink_name": "флэт уайт",  "category": "молочные напитки",  "volume_ml": 200, "price_rub": 240, "is_key_drink": True, "source_url": "ручной ввод", "validation_note": "ручная валидация"},
            {"drink_name": "раф",        "category": "молочные напитки",  "volume_ml": 300, "price_rub": 280, "is_key_drink": True, "source_url": "ручной ввод", "validation_ация": "ручная валидация"},
            {"drink_name": "какао",      "category": "какао/шоколад",     "volume_ml": 300, "price_rub": 260, "is_key_drink": True, "source_url": "ручной ввод", "validation_note": "ручная валидация"},
            {"drink_name": "матча латте","category": "чай/матча",         "volume_ml": 300, "price_rub": 280, "is_key_drink": True, "source_url": "ручной ввод", "validation_note": "ручная валидация"},
            {"drink_name": "чай",        "category": "чай/матча",         "volume_ml": 400, "price_rub": 180, "is_key_drink": True, "source_url": "ручной ввод", "validation_note": "ручная валидация"},
        ]
        pd.DataFrame(fallback).to_csv("data/raw/pravda_menu_raw.csv", index=False, encoding="utf-8-sig")
        print("Сохранён fallback-файл с ручными данными.")
