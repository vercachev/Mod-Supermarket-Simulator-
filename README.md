# Cookie Clicker — Save Editor

Простой редактор сейвов **Cookie Clicker**.  
Одно понятное число: **сколько печенек**. Открыли игру — сразу видно, сработало или нет.

---

## Зачем эта игра

| Было (Bitburner) | Стало (Cookie Clicker) |
|------------------|-------------------------|
| Сложные суффиксы `$1.000s` | Обычное большое число печенек сверху |
| Export/Import + сравнение сейвов | Export → правка → Import |
| Непонятно, применилось ли | Сразу видно на главном экране |

---

## Где взять игру

- **Бесплатно в браузере:** https://orteil.dashnet.org/cookieclicker/  
- **Steam (платно, ~$5):** Cookie Clicker — тот же Export/Import

Редактор работает с **обоими**.

---

## Как пользоваться (3 шага)

1. В игре: **Options → Export save** (скопировать код)  
   или **Save to file**
2. Запустить редактор (`start.bat`) → **Вставить из буфера** / **Открыть файл**  
   → поставить печеньки (например `1000000000`) → **Сохранить**  
   (код копируется в буфер, файл в Downloads)
3. В игре: **Options → Import save** → Ctrl+V → Load  

Сверху должно стать огромное число печенек.

---

## Установка редактора

1. Python 3.11+ (Add to PATH)
2. Скачать ZIP этого репозитория (`main`)
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
