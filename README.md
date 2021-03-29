# Сласти от всех напастей

Мой первый REST-сервис. Даёт курьерам работу, а покупателям - сладости.

## Запуск сервиса

Для работы сервиса необходимо установить MongoDB ([инструкция для разных платформ](https://docs.mongodb.com/manual/administration/install-community/)). 

0. Убедитесь, что MongoDB запущена и запущена успешно.
1. Поставьте необходимые зависимости:
```
pip install -r requirements.txt
```
2. Запустите на адресе 0.0.0.0:8080, находясь в папке проекта
```
python index.py
```
Или командой:
```
gunicorn -w 4 -b 0.0.0.0:8080 index:app
```

Готово, сласти уже в пути!

*Сервис был написан в качестве вступительного задания для [школы бэкенд-разработки Yandex](https://academy.yandex.ru/schools/backend?utm_source=yandex&utm_medium=email&utm_campaign=sendr-444809).*
