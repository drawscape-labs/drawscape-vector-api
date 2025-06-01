web: gunicorn server:app --bind 0.0.0.0:$PORT
worker: rq worker --url $REDIS_URL high default low svg-generation 