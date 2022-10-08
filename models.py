from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Integer
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import bcrypt

db = SQLAlchemy()

class Images(db.Model):
    """Store Image key & url"""

    __tablename__ = 'images'

    image_key = db.Column(
        db.Text,
        nullable=False,
        primary_key = True
    )

    image_url = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )


    def __repr__(self):
        return f"<Image #{self.id}: {self.image_key}, {self.image_url}>"

    @classmethod
    def add_image(self, key, url):
        """adds image to database"""
        image = Images(
            image_key=key,
            image_url=url,
        )
        db.session.add(image)
        return image
    
    def serialize(self):
        """Serialize number fact dicts to a dict of number fact info."""

        return {
            "imageKey": self.image_key,
            "imageUrl": self.image_url,
        }



class Capsules(db.Model):
    """Hold Capsule Data connecting user <-> images"""

    __tablename__ = 'capsules'

    id = db.Column(
        db.Integer,
        nullable=False,
        primary_key=True
    )

    capsule_return_date = db.Column(
        db.Text,
        nullable=False,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    def serialize(self):
        """Serialize number fact dicts to a dict of number fact info."""

        return {
            "exifField": self.image_type,
            "exifValue": self.image_value
        }









    # #optional TODO: to make it more complicated, we can do metadata_1, metadata_2



class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    # image_url = db.Column(
    #     db.Text,
    #     default="/static/images/default-pic.png",
    # )



    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(cls, username, email, password, image_url):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False





def connect_db(app):
    """Connect this database to provided Flask app.
    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)




