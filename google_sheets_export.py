"""
google_sheets_export.py — экспорт данных проекта в Google Sheets
Проект: Анализ открытия кофейни Surf Coffee рядом с ВШЭ

Закрывает тему курса: Google Sheets API.

═══════════════════════════════════════════════════════════════════
ИНСТРУКЦИЯ ПО НАСТРОЙКЕ (один раз):
═══════════════════════════════════════════════════════════════════

1. Зайти на https://console.cloud.google.com/
2. Создать новый проект (например, "surf-coffee-analysis")
3. В меню Library найти и включить:
   - Google Sheets API
   - Google Drive API
4. В меню "Credentials" → Create Credentials → Service Account
   - Имя: surf-coffee-bot
   - Роль: Editor
5. После создания: открыть service account → Keys → Add Key →
   Create new key → JSON → скачать файл
6. Сохранить файл как `credentials.json` в корне проекта
   (НЕ коммитить в git — добавить в .gitignore!)
7. Создать в Google Sheets новую таблицу, например:
   "Surf Coffee — анализ конкурентов"
8. Скопировать e-mail сервисного аккаунта из credentials.json (поле "client_email")
9. В Google Sheets: Поделиться → вставить этот e-mail → дать права "Редактор"
10. Скопировать ID таблицы из URL:
    https://docs.google.com/spreadsheets/d/<ВОТ_ЭТО_ID>/edit

УСТАНОВКА:
    pip install gspread google-auth

ЗАПУСК:
    python src/google_sheets_export.py
"""

import os
import pandas as pd

# Импорты — отдельно, чтобы код не падал, если библиотеки не установлены
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("[ВНИМАНИЕ] gspread не установлен. Запустите: pip install gspread google-auth")


# ─────────────────────────────────────────────
# Конфигурация
# ─────────────────────────────────────────────

# Путь к JSON-файлу с ключом сервисного аккаунта
CREDENTIALS_PATH = "credentials.json"

# ID таблицы (взять из URL Google Sheets)
SPREADSHEET_ID = "ВСТАВЬТЕ_СЮДА_ID_ВАШЕЙ_ТАБЛИЦЫ"

# Необходимые scopes для Sheets + Drive
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ─────────────────────────────────────────────
# Класс-обёртка над Google Sheets API
# ─────────────────────────────────────────────

class GoogleSheetsExporter:
    """
    Обёртка для удобной выгрузки нескольких pandas-таблиц
    в разные листы одной Google-таблицы.
    """

    def __init__(self, credentials_path: str, spreadsheet_id: str):
        if not GSPREAD_AVAILABLE:
            raise RuntimeError("Установите: pip install gspread google-auth")
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Не найден файл {credentials_path}. "
                f"Создайте сервисный аккаунт в Google Cloud Console."
            )
        creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)
        print(f"[OK] Подключились к таблице: {self.spreadsheet.title}")

    def upload_dataframe(self, df: pd.DataFrame, sheet_name: str):
        """Загружает pandas DataFrame в лист с указанным именем."""
        # Создаём лист, если его нет
        try:
            ws = self.spreadsheet.worksheet(sheet_name)
            ws.clear()
            print(f"  [OK] Очищен существующий лист: {sheet_name}")
        except gspread.WorksheetNotFound:
            ws = self.spreadsheet.add_worksheet(
                title=sheet_name,
                rows=max(len(df) + 10, 50),
                cols=max(len(df.columns) + 2, 10)
            )
            print(f"  [OK] Создан новый лист: {sheet_name}")

        # Преобразуем DataFrame в список списков (заголовки + данные)
        # NaN → пустая строка, чтобы Sheets не ругались
        df_clean = df.fillna("").astype(str)
        data = [df_clean.columns.tolist()] + df_clean.values.tolist()

        ws.update(data, value_input_option="USER_ENTERED")
        # Жирные заголовки
        ws.format("1:1", {"textFormat": {"bold": True}})
        print(f"  [OK] Загружено {len(df)} строк в лист «{sheet_name}»")


# ─────────────────────────────────────────────
# Главная функция выгрузки
# ─────────────────────────────────────────────

def export_all():
    """Выгружает все ключевые таблицы проекта в Google Sheets."""
    if SPREADSHEET_ID == "ВСТАВЬТЕ_СЮДА_ID_ВАШЕЙ_ТАБЛИЦЫ":
        print("=" * 60)
        print("Заполните SPREADSHEET_ID в начале этого файла!")
        print("Это ID вашей Google-таблицы (часть URL между /d/ и /edit).")
        print("=" * 60)
        return

    exporter = GoogleSheetsExporter(CREDENTIALS_PATH, SPREADSHEET_ID)

    # Список файлов для выгрузки: (путь, имя_листа)
    files_to_upload = [
        ("data/processed/competitors_processed.csv",   "Конкуренты"),
        ("data/processed/pravda_menu_processed.csv",   "Меню_Правда_кофе"),
        ("data/raw/yandex_maps_competitors.csv",       "Яндекс_Карты_рейтинги"),
        ("data/processed/survey_responses_processed.csv","Опрос_аудитории"),
        ("data/processed/financial_model.csv",         "Финансовая_модель"),
    ]

    for path, sheet_name in files_to_upload:
        if not os.path.exists(path):
            print(f"  [ПРОПУСК] Файл не найден: {path}")
            continue
        df = pd.read_csv(path)
        exporter.upload_dataframe(df, sheet_name)

    print("\n[ГОТОВО] Все таблицы выгружены в Google Sheets!")
    print(f"Откройте: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")


# ─────────────────────────────────────────────
# Тестовый режим (без реальной выгрузки)
# ─────────────────────────────────────────────

def dry_run():
    """Показывает, что будет выгружено, без реального вызова API."""
    print("=" * 60)
    print("DRY RUN — что будет выгружено в Google Sheets")
    print("=" * 60)
    files_to_upload = [
        ("data/processed/competitors_processed.csv",   "Конкуренты"),
        ("data/processed/pravda_menu_processed.csv",   "Меню_Правда_кофе"),
        ("data/raw/yandex_maps_competitors.csv",       "Яндекс_Карты_рейтинги"),
        ("data/processed/survey_responses_processed.csv","Опрос_аудитории"),
        ("data/processed/financial_model.csv",         "Финансовая_модель"),
    ]
    for path, sheet_name in files_to_upload:
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"  Лист «{sheet_name}»: {len(df)} строк, {len(df.columns)} колонок ← {path}")
        else:
            print(f"  [ПРОПУСК] {path} (не существует)")


if __name__ == "__main__":
    if not GSPREAD_AVAILABLE or not os.path.exists(CREDENTIALS_PATH):
        print("Запускаем dry run (без подключения к API)...\n")
        dry_run()
    else:
        export_all()
