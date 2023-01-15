from builtins import breakpoint
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Integer
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt


bcrypt = Bcrypt()
db = SQLAlchemy()

class Image(db.Model):
    """Store Image key & url"""

    __tablename__ = 'images'
    #TODO: if filename is identical, add a uuid or add a prefix or suffix
    image_key = db.Column(
        db.Text,
        nullable=False,
        primary_key = True,
        unique=True
    )

    capsule_id = db.Column(
        db.Integer,
        db.ForeignKey("capsules.id", ondelete="CASCADE"),
        nullable=False,
    )

    image_url = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    capsule = db.relationship("Capsule", backref="images")

    
    def __repr__(self):
        return f"<Image #{self.image_key}: {self.capsule_id}, {self.image_url}>"

    @classmethod
    def get_file_names_from_capsule_id(cls, cap_id):
        images = cls.query.filter_by(capsule_id=cap_id).all()
        image_keys = [image.image_key for image in images]
        return image_keys



    # @classmethod
    # def add_image(self, key, url):
    #     """adds image to database"""
    #     image = Images(
    #         image_key=key,
    #         image_url=url,
    #     )
    #     db.session.add(image)
    #     return image
    
    # def serialize(self):
    #     """Serialize number fact dicts to a dict of number fact info."""

    #     return {
    #         "imageKey": self.image_key,
    #         "imageUrl": self.image_url,
    #     }



class Capsule(db.Model):
    """Hold Capsule Data connecting user <-> images"""

    __tablename__ = 'capsules'

    id = db.Column(
        db.Integer,
        nullable=False,
        primary_key=True,
        autoincrement=True,
        unique=True
    )
    
    name = db.Column(
        db.Text,
        nullable=False,
    )

    message = db.Column(
        db.Text,
        nullable=True
    )

    return_date = db.Column(
        db.Date,
        nullable=False,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )


    user = db.relationship("User", backref="capsules")


    @classmethod
    def get_capsules_due_today(cls, today="2022-12-03"):
        capsules = cls.query.filter_by(return_date=today).all()
        return capsules


    def serialize(self):
        """Serialize number fact dicts to a dict of number fact info."""



        return {
            "id": self.id,
            "name": self.name,
            "message": self.message,
            "return_date": str(self.return_date),
            "user_id": self.user_id
        }









    # #optional TODO: to make it more complicated, we can do metadata_1, metadata_2



class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
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



    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(cls, username, email, password):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')
        print("hashed pwd", hashed_pwd)
        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
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
        print(user)
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




