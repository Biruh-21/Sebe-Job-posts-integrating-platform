# Et Jobs

\#1 Job search site in Ethiopia

It is all-in-one job search site in Ethiopia which aggregates job posts from multiple sources and present in one place. This enables users to search and view muliple jobs matching their preference at one place.

## How to use

- Create Virtual environment and activate it
```
python3 -m venv venv
```
```
source venv/bin/activate (Linux or MacOS)
```
```
.\venv\Scripts\activate (Windows)
```

- Clone this  repo
```
git clone https://github.com/balewgize/et_jobs.git
```

- Install required packages
```
pip install -r requirements.txt
```

## Provide credentials in .env file
- Create a file named .env inside et_jobs folder (the project root dir)

- Provide credentials in key=value format without qoutes as follows

- First, to generate scret key for your project run the following commands

```
django-admin shell
```
```
from django.core.management.utils import get_random_secret_key
```
```
get_random_secret_key()
```
- Assign the output (without quotes) to SECRET_KEY in .env 

- Finally, provide email credentials to enable email verification during sign up

```
DB_NAME=name
DB_USER=user
DB_PASS=password

# Django credentials
SECRET_KEY=your django project secret key
DEBUG=True

# Email credentials
EMAIL_USER=email address
EMAIL_PASS=eamil password
```

<strong>Note: </strong> If you are using Gmail, you need to create 
<a href="https://myaccount.google.com/apppasswords">Google App Password </a> that
will be used as in place of email password

## Apply migrations
```
python manage.py migrate
```

## Create super user and start the server
```
python manage.py createsuperuser
```

- Login to admin site and add few post categories
(Post categories are managed by the admin only, writers can only select)

```
python manage.py runserver
```

Enjoy the website :)
