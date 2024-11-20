# Foodrgam

«Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.


`Выполнить клонирование`
```bash
git clone git@github.com: yandex-praktikum/api_yamdb.git
```
`Перейти в папку с проектом` 
```bash
cd api_yamdb
```
`Создать виртуальное окружение:`
   Команда для Windows: -
```bash
python -m venv venv
```
Команда для Linux и macOS: - 
```bash
python3 -m venv venv
```
Активировать виртуальное окружение:`
   Команда для Windows: -
```bash
source venv/Scripts/activate
```
Для Linux и macOS: -
```bash
source venv/bin/activate
```
`Обновить пакетный менеджер:`
   Для Windows: -
```bash
python -m pip install --upgrade pip
```
Для Linux и macOS: -
```bash
python3 -m pip install --upgrade pip
```
Установить модули из файла requirementst.txt:`
```bash
pip install -r requirements.txt
```
`Запустить приложение`
```bash
python manage.py runserver
```

### В основной директории проекта, где лежит файл docker-compose.yml, выполнить команду:
```
docker compose up -build
```
В той же директории с файлом docker-compose.yml, но уже в новом терминале git, выполнить команды.
Также эти команды можно выполнить в декстопном приложении Docker, провалиться в контейнер backend,
войти в раздел exec и в консоль ввести команды.
```
docker compose exec backend python manage.py makemigrations
```
docker compose exec backend python manage.py migrate
```
docker compose exec backend python manage.py load_ingredients
```
```
docker compose exec backend python manage.py load_tags
```
Последняя команда загружает в бд подготовленный набор необходимых данных(ингредиенты и тэги)
Дополнительно можно создать суперпользователя, для доступа к админ-панели сайта, командой:
```
docker compose exec backend python manage.py createsuperuser
```
Также необходимо скопировать статику для админки Django
```
docker compose exec backend python manage.py collectstatic
```
И скопировать статику в volume static для бэкенда
```
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/ 
```

После Foodgram станет доступен по адресу http://localhost 

Список доступных API-эндпоинтов доступен по ссылке http://localhost/api/redoc/

