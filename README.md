# Supermarket Together — Save Editor

Простой редактор сейвов **Supermarket Together** (Steam, бесплатно).  
Меняете **Funds (деньги)** — в магазине сразу видно, сработало или нет.

---

## Игра

- Steam: [Supermarket Together](https://store.steampowered.com/app/2709570/)
- Сейвы: `%USERPROFILE%\AppData\LocalLow\DDTNL\Supermarket Together\`
- Файлы: `StoreFile0.es3`, `StoreFile1.es3`, … (+ `DayN` — бэкапы в игре)

Формат: **Easy Save 3** (AES). Редактор сам расшифровывает и шифрует обратно.

---

## Как пользоваться (3 шага)

1. **Закройте игру** (и лучше временно отключите Steam Cloud для этой игры).
2. Запустите редактор (`start.bat`) → **Открыть сейв** / **Быстрый слот 0**  
   → поставьте деньги (например `1000000`) → **Сохранить**.
3. Скопируйте `*_EDITED.es3` поверх нужного `StoreFileN.es3`  
   **или** нажмите **Сохранить поверх исходного сейва**.

Запустите игру и откройте магазин — деньги должны обновиться.

Если Steam вернул старый файл: загрузите **Day-бэкап** из меню игры  
(тот день, который вы правили) или отключите Cloud.

---

## Установка редактора

1. Python 3.11+ (галочка **Add to PATH**)
2. Скачать ZIP репозитория (`main`)
3. Дважды кликнуть **`start.bat`**

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## Что можно править

| Поле | Что это |
|------|---------|
| **Funds** | Деньги магазина (главное) |
| Franchise Points | Очки франшизы |
| Franchise Exp | Опыт франшизы |
| Last Awarded Level | Уровень (как в гайдах) |

Перед каждой записью создаётся копия в папке `backups` рядом с сейвом.

---

## Тесты

```bat
python -m samples.sample_save_data
python -m unittest tests.test_save_handler -v
```
