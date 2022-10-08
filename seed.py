from app import db
from models import Photos, User


db.drop_all()
db.create_all()
db.session.commit()