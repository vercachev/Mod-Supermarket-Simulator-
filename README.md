# Bitburner — Save Editor

Внешний редактор **экспортированных** сохранений игры **Bitburner** (бесплатно в Steam).  
Ничего не ставит в папку игры — только правит файл, который вы сами экспортировали.

---

## Зачем так (важно!)

В Bitburner сейв **не лежит** простым файлом в AppData.  
Нужен цикл:

1. В игре: **Options → Export save / Export game**
2. Открыть полученный файл (`.json` или `.json.gz`) в этом редакторе
3. Изменить → **Сохранить файл**
4. В игре: **Options → Import save** → выбрать файл

---

## Быстрый старт

1. Установите **Python 3.11+** с https://www.python.org/downloads/  
   (галочка Add to PATH / через Install Manager поставьте CPython)
2. Скачайте Bitburner в Steam (лёгкая бесплатная игра)
3. Скачайте этот проект (ZIP с `main`)
4. Дважды кликните **`start.bat`**
5. В Bitburner сделайте **Export save**
6. В редакторе **Открыть экспорт** → правьте → **Сохранить файл**
7. В Bitburner сделайте **Import save**

---

## Что можно менять

| Вкладка | Поля |
|---------|------|
| 💰 Деньги | `money` |
| 🧠 Навыки | hacking, strength, defense, dexterity, agility, charisma, intelligence |
| 🛰️ Прогресс | BitNode, эксплойт `EditSaveFile` |
| 🔧 Прочее | бэкапы + сырой JSON |

Перед каждым сохранением создаётся бэкап в папке `backups` рядом с файлом.

---

## Установка из консоли (если bat не сработал)

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## Сборка .exe

```bat
build.bat
```

Результат: `dist\BitburnerSaveEditor.exe`

---

## Тесты / демо-сейв

```bat
python -m samples.sample_save_data
python -m unittest tests.test_save_handler -v
```

Файлы появятся в `samples/`.

---

## Если что-то не так

| Проблема | Решение |
|----------|---------|
| `python` не найден | Переустановить Python с PATH |
| «Не удалось прочитать сейв» | Нужен именно **Export** из Bitburner, не случайный файл |
| После Import ничего не изменилось | Убедитесь, что импортировали **тот же** сохранённый файл |
| Хочу откатить | Вкладка **Прочее** → восстановить бэкап |

---

## Отказ от ответственности

Проект не связан с разработчиками Bitburner. Правка сейвов — на ваш риск; бэкап делается автоматически.
