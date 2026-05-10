# 📱 Phone Hunter BETA-1.0

> Автономный OSINT-инструмент для поиска информации по номеру телефона.
> Полностью локально. Без API-ключей. Без регистраций.

---

## 🎯 Возможности

| Модуль | Описание |
|--------|----------|
| 📡 **HLR** | Город, регион, федеральный округ, часовой пояс |
| 📋 **Validator** | Валидация номера, страна, оператор |
| 👤 **Social** | Поиск в VK, OK, Telegram, Instagram |
| 💬 **Messengers** | Проверка Telegram, WhatsApp, Viber, Signal |
| 🔓 **Leaks** | Поиск в утечках (HaveIBeenPwned, LeakCheck, PSBDMP) |
| 🕵️ **Fraud** | Жалобы на мошенничество, спам, коллекторов |
| 📱 **Line Type** | Тип линии: частная / корпоративная / массовая активация |
| 🔄 **Port** | Переносился ли номер между операторами |
| 🌍 **Geo** | Геоанализ по DEF-коду и HLR |
| 🕶️ **Darknet** | Поиск на даркнет-форумах |

---

## 🚀 Быстрый старт

### Требования

- **Python 3.10+**
- **Windows 10/11** (или Linux/Mac)
- **Браузер** (Firefox рекомендуется)

### Установка

```bash
# 1. Клонируй репозиторий
git clone https://github.com/VERNIDOV/phone-hunter.git
cd phone-hunter

# 2. Установи зависимости
cd backend
pip install -r requirements.txt

# 3. Запусти сервер
python main.py