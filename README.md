## Tagger News

The purpose of continuing this project was an idea that I had over a year before.
However lacking the ML / text analysis skills it was left for another day. After finding out
about the [tagger news project](http://varianceexplained.org/programming/tagger-news/) (from HN funnily enough) I felt I could pursue the idea.
##### The Idea
*Wouldn't it be great to know more about the person you are chatting with on HN like their background / motiviation.*

Also: 
 *Is this person a sockpuppet? A shill? Or an apologist?*

One way to do that is to look at their comment history and articles they post / like commenting on.

And this was a good project to practice my python...
### Setup
##### Setup the environment
```
git clone https://github.com/dchecks/taggernews.git
cd taggernews
mkvirtualenv taggernews
ln -s ~/.virtualenvs/taggernews/bin/activate ./activate
echo export SECRET_KEY="PICK A SECRET KEY" >> /location/of/your/.virtualenvs/taggernews/bin/activate
echo export DEBUG=True >> /location/of/your/.virtualenvs/taggernews/bin/activate
```
For some reason a 500 will be thrown on the admin page if you don't enable debug 

##### Dependencies
```
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```
If requirements install fails due to psycopg2 (on centos7) try:
```
sudo yum install python-devel postgresql-devel
```
Credit: https://stackoverflow.com/questions/5420789/how-to-install-psycopg2-with-pip-on-python

##### MySQL
The server setup is now using mysql, a simple schema creation script can be found in the 'creates' file in the root directory.
If you want you can still use sqlite, just change the connection string in the settings.py file.

Either way settings.py will need updated with your server address, password etc. under
```
DATABASES = {...
```

##### Start the server
```
python manage.py runserver
open http://localhost:8000
```
You should now see a tagger news clone start up with no data.

For the admin interface:
```
open http://localhost:8000/admin
```

###Data Gathering and Analysis
##### Create a model
Now to create an LDA model (Latent Dirichlet Allocation)
In analyze_hn run:
```
python tagger/model_topics.py
```
This will provide you with a dictionary and gensim files.


##### Prediction
Plug these into the predictor by editing the dictionary and lda field.

```
python tagger/predict_topics.py
```

The predictor will need to load in the training data on the first run. 
This is about 15k requests and so will take a long time. The bulk of this time is 
retrieving all of the article text from the supervised_topics.csv.

This is slow due to a python bug with OSX.
It prevents multiprocess parsing of the supervised_topics list which is needed for initial model building.
If you're running it on a proper *nix try setting
```
THREAD_COUNT = (some number respective to your cores)
```
In refresh_top_articles.py (just don't abuse the hn api too much)

Once parsing of the training data is done it will create 2 prediction models, under ml_models/predictions. 
These will be used when tagging. The tagger is smart enough to pick the latest
model in the folder.


##### Tagging
Using the training set you can now put the machine to work. If you run it at
this stage the tagger will only re-tag the articles from the supervised_topics.csv
```
python manage.py tag_articles
```
Or, to run indefinitely, (sleeping while it's out of work)
```
python tagger/management/commands/tag_articles.py
```

##### Importing
To import data run the commands:
```
python manage.py refresh_top_articles
```
This will start the parser, getting the top articles and saving them to the db.
You can then run the tagging step again to tag these articles. Once this is complete
you should be able to see a reasonably accurate front page of hn with tags.

### User Tagging
To tag all the users, (and sleep when done as above)
```
python tagger/tag_user.py
```
To tag a list of users, provide the user names as cmd line arguements.

This is a reasonably intense thing to do. Each comment that a user makes 
is currently tied back to the orignal article that it was on (via a recursive call chain to the api),
the article is then parsed and put in the list to be tagged.

The first time a user is queried for their tags it won't work. Tagging is too
slow due to the amount of web fetching that needs to happen.

The front page submitters will be pre-fetched when refresh top is run.

##### In action
To view the tags, hover over a username on the website. If the user has been parsed you
will see their favourite topics. Otherwise check back a few minutes later after the tagging is complete.
