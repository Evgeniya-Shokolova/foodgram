# Проект Foodrgam

[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646?style=flat-square&logo=Django)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/-Django%20REST%20Framework-464646?style=flat-square&logo=Django%20REST%20Framework)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-464646?style=flat-square&logo=PostgreSQL)](https://www.postgresql.org/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat-square&logo=NGINX)](https://nginx.org/ru/)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat-square&logo=gunicorn)](https://gunicorn.org/)
[![docker](https://img.shields.io/badge/-Docker-464646?style=flat-square&logo=docker)](https://www.docker.com/)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat-square&logo=GitHub%20actions)](https://github.com/features/actions)

«Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

Все сервисы и страницы проекта должны быть доступны для пользователей в соответствии с их правами. 
### Авторизованные пользователи
могут подписаться и отписаться на странице автора, есть возможность добавить рецепт в список избранного и удалить его оттуда, добавить рецепт в список покупок и удалить его оттуда, выгрузить файл с перечнем и количеством необходимых ингредиентов для рецептов из «Списка покупок». 
Доступна страница «Создать рецепт»: опубликовать свой рецепт, отредактировать и сохранить изменения в своём рецепте, удалить свой рецепт.
### Для неавторизованных пользователей 
доступна главная страница, страница отдельного рецепта, страница любого пользователя, работает форма входа и регистрации.


## Установка и запуск проекта

### Выполняем клонирование

```bash
git clone git@github.com: yandex-praktikum/foodgram.git
```
Переходим в папку с проектом
```bash
cd foodgram
```

### Установка Docker

Скачиваем установочный файл Docker Desktop. Будет установлена программа для управления контейнерами (докер-демон) и докер-клиенты — графический интерфейс и интерфейс командной строки. 
Дополнительно к Docker устанавливаем утилиту Docker Compose:
```bash
sudo apt install docker-compose-plugin
```
Проверяем, что Docker работает:
```bash
sudo systemctl status docker
```

### Упаковка проекта в Docker-образ

Docker должен быть запущен. Открываем терминал, переходим в соответсвующую директорию backend/, frontend/, nginx/ проекта Foodgram и выполняем сборку образа:
```bash
docker build -t food_backend . 
```
```bash
docker build -t food_frontend .
```
```bash
docker build -t food_nginx .
```
Выполняем команду аутентификации:
```bash
docker login
```
Пушим образы на Docker Hub:
```bash
docker push username/food_backend:latest
```
```bash
docker push username/food_frontend:latest 
```

### Загрузка образов на Docker Hub
Собираем образы:
```bash
docker build -t username/food_backend:latest backend/
```
```bash
docker build -t username/food_frontend:latest frontend/
```

## База данных и переменные окружения

### Создаём файл .env в корне проекта. 
Добавляем в файл переменные и их значения:
```bash
POSTGRES_USER=django_user(имя пользователя БД )
POSTGRES_PASSWORD=mysecretpassword(пароль пользователя БД)
POSTGRES_DB=django(название базы данных )
DB_HOST=db(адрес, по которому Django будет соединяться с базой данных.)
DB_PORT=5432(порт, по которому Django будет обращаться к базе данных.)
```
### Создаём контейнер ```db``` и запускаем его в отдельном терминале:
```bash
docker exec -it db psql -U django_user -d django 
```
### Применяем миграции:
```bash
docker compose exec backend python manage.py migrate
```
### Создаём файл ```docker-compose.yml``` в корне проекта.
Все контейнеры, описанные в docker-compose.yml, будут запущены при выполнении команды:
```bash
docker compose up
```

### Для перезапуска Docker Compose:
```bash
docker compose stop && docker compose up --build 
```
### Копируем статику для админки Django

```bash
docker compose exec backend python manage.py collectstatic
```
### И статику для бэкенда
```bash
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/ 
```
### Загружаем список ингредиентов:
```bash
docker compose exec backend python manage.py load_ingredients
```
### Загружаем теги:
```bash
docker compose exec backend python manage.py load_tags
```
### Создаём админку:
```bash
docker compose exec backend python manage.py createsuperuser
```

## Публикация проекта на сервере.
### Устанавливаем Docker Compose на сервер:
```bash
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin 
```
### Запускаем Docker Compose в режиме демона:
```bash
sudo docker compose -f docker-compose.production.yml up -d
```

## Workflow
Секретные данные можно спрятать на платформе GitHub Actions, в специальном хранилище. 
Перейдите в настройки репозитория — **`Settings`**, выберите на панели слева **`Secrets and Variables`** → **`Actions`**, нажмите **`New repository secret`**

- ```DOCKER_USERNAME``` - имя пользователя в DockerHub
- ```DOCKER_PASSWORD``` - пароль пользователя в DockerHub
- ```HOST``` - адрес сервера
- ```USER``` - пользователь
- ```SSH_KEY``` - приватный ssh ключ
- ```PASSPHRASE``` - пароль для ssh-ключа
- ```HOST``` - db
- ```TELEGRAM_TO``` - id своего телеграм-аккаунта (можно узнать у @userinfobot, команда /start)
- ```TELEGRAM_TOKEN``` - токен бота (получить токен можно у @BotFather, /token, имя бота)

## Сохраняем, коммитим и пушим изменения на GitHub
```bash
git add .
```
```bash
git commit -m "Comment"
```
```bash
git push
```

## Набор доступных эндпоинтов:
```api/users/``` - получение информации о пользователе и регистрация новых пользователей. (GET, POST).
```api/recipes/``` - Получение списка с рецептами и публикация рецептов (GET, POST).
```api/tags/``` - Получение списка тегов (GET).
```api/ingredients/``` - Получение списка ингредиентов (GET).


### Проект доступен по адресу 
**```https://fooding.hopto.org```**
### Автор
[Евгения Шоколова](https://github.com/Evgeniya-Shokolova/foodgram)