# Foodrgam

«Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.


### Установка и запуск


Выполнить клонирование
```bash
git clone git@github.com: yandex-praktikum/foodgram.git
```
Перейти в папку с проектом
```
cd foodgram
```
Создать виртуальное окружение:
   Команда для Windows: -
```
python -m venv venv
```
Команда для Linux и macOS: - 
```
python3 -m venv venv
```
Активировать виртуальное окружение:`
   Команда для Windows: -
```
source venv/Scripts/activate
```
Для Linux и macOS: -
```
source venv/bin/activate
```
Обновить пакетный менеджер:
   Для Windows: -
```
python -m pip install --upgrade pip
```
Для Linux и macOS: -
```
python3 -m pip install --upgrade pip
```
Установить модули из файла requirementst.txt:`
```
pip install -r requirements.txt
```
Запустить приложение
```
python manage.py runserver
```

Далее создать файл .env в корне проекта:
```
DB_NAME=postgres # имя БД
POSTGRES_USER=postgres # логин для подключения к БД
POSTGRES_PASSWORD=postgres # пароль для подключения к БД
DB_HOST=db # название сервиса
DB_PORT=5432 # порт для подключения к БД
```


### Запуск проекта при помощи Docker:

В директории с файлом docker-compose.yml, выполнить команды.

```
docker compose exec backend python manage.py makemigrations
```
```
docker compose exec backend python manage.py migrate
```
```
docker compose exec backend python manage.py load_ingredients
```
```
docker compose exec backend python manage.py load_tags
```
```
docker compose exec backend python manage.py createsuperuser
```

Копируем статику для админки Django

```
docker compose exec backend python manage.py collectstatic
```
И статику для бэкенда
```
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/ 
```

Foodgram доступен по адресу https://fooding.hopto.org
