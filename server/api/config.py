SECRET_KEY = 'very_very_secure_and_secret'
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'db+mysql://user:password@mysql:3306/db'
UPLOAD_FOLDER = 'tmp'
LIMITER_SECONDS=20