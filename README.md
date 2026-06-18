# AI Car Detail — ИИ-помощник по техобслуживанию авто

**Десктопное приложение на Python с интеграцией DeepSeek AI**

Приложение анализирует данные автомобиля и дает персонализированные рекомендации по техническому обслуживанию с использованием нейросети DeepSeek.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

## 📸 Скриншот

![Скриншот приложения](screenshots/screenshot.png)

## Основные возможности

- Ввод данных автомобиля (марка, год, тип двигателя, общий пробег, среднегодовой пробег)
- Расчёт рекомендаций по 13+ узлам авто
- Использование **DeepSeek AI** для глубокого анализа
- Потоковый вывод ответов нейросети
- Удобный интерфейс на Tkinter

## Как запустить

```bash
git clone https://github.com/Bobidze/AI_Car_Detail.git
cd AI_Car_Detail

# Установка зависимостей
pip install -r requirements.txt

# Запуск
python car_maintenance.py
```

## Настройка DeepSeek API

1. Получите API-ключ на [platform.deepseek.com](https://platform.deepseek.com)
2. В приложении вставьте ключ в поле **API ключ**
3. Нажмите **«Сохранить ключ»**

Ключ сохраняется локально в `config.json` ( файл игнорится Git-om ).

## Технологии

- Python 3.10+
- Tkinter ( встроен в Python)
- DeepSeek API

## Лицензия

MIT License

---

*Developed with ❤️ by Nikita Tarasiuk*