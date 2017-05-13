## Tagger News

```
git clone http://github.com/danrobinson/taggernews.git
cd taggernews
mkvirtualenv taggernews
pip install -r requirements.txt
cd taggernews
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
open http://localhost:8000
```

For the admin interface:

```
open http://localhost:8000/admin
```