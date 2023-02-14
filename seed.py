from app import db
from models import Photos, User, Image


db.create_all()
db.session.commit()