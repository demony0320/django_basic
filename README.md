this is docker-compose project for django implementation

basic command list

```
docker-compose run web django-admin startproject alpha .
docker-compose run web python manage.py startapp news
```

Init new db and create 'news' model
```
docker-compose run web python manage.py  migrate
docker-compose run web python manage.py makemigrations news 
```
export, migrate, check
```
docker-compose run web python manage.py sqlmigrate news 0001
docker-compose run web python manage.py  migrate
docker-compose run web python manage.py  check
```
So now, Let's play with  'python manage.py shell'
