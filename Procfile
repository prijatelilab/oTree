web: gunicorn prijateli_tree.app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --host=0.0.0.0 --port=${PORT:-5000}
release: alembic --config=./prijateli_tree/migrations/alembic.ini upgrade head