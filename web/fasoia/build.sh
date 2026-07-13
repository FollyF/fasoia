#|/usr/bin/env bash

set -o errexit

pip install -r requirements.txt
python -m spacy download fr_core_news_sm
python manage.py collectstatic --noinput   
python manage.py migrate