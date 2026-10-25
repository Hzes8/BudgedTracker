
from api.index import app
from api.extensions import db
from api import models

with app.app_context():
    db.create_all()
    print("Pembuatan tabel selesai.")
