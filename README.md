# Supermarket Together — Save Editor v1.1

Простой редактор сейвов **Supermarket Together**.  
Меняете **Funds** → жмёте **«Применить к игре»** → открываете магазин.

---

## Важно (чтобы сработало)

1. **Закройте игру**
2. **Выключите Steam Cloud** для этой игры  
   (Свойства → Общие → снять «Хранить в облаке Steam»)
3. Открывайте **`StoreFile0.es3` / `StoreFile1.es3`**  
   **НЕ** файлы из папки `backups` и **НЕ** `*_EDITED.es3`
4. Жмите зелёную кнопку **«Применить к игре»**
5. Запустите игру и зайдите в **тот же** слот — сразу смотрите деньги

Папка `backups` создаётся редактором сама — это запасные копии, игра их не читает.

---

## Игра / путь

- Steam: [Supermarket Together](https://store.steampowered.com/app/2709570/)
- Сейвы: `%USERPROFILE%\AppData\LocalLow\DDTNL\Supermarket Together\`
- Файлы: `StoreFile0.es3`, `StoreFile1.es3`, …

---

## Установка

1. Python 3.11+ (Add to PATH)
2. ZIP с ветки `main`
3. Дважды кликнуть **`start.bat`**

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## Тесты

```bat
python -m samples.sample_save_data
python -m unittest tests.test_save_handler -v
```
