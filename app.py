from ast import parse
import os
from flask import Flask, jsonify, render_template, request, flash, redirect, session, g, send_file, url_for
from unicodedata import name
from sqlalchemy.exc import IntegrityError
from sqlalchemy import null
from werkzeug.utils import secure_filename
from PIL import Image, ImageFilter
from PIL.ExifTags import TAGS
import requests
from io import BytesIO
# from dotenv import load_dotenv
from models import db, connect_db, Capsules, Images, User
# load_dotenv()
import boto3
import uuid
from botocore.exceptions import ClientError
from flask_cors import CORS

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

cors = CORS(app, resources={r'/*': {'origins': "http://localhost:3000"}})

### S3 Keys
app.config['ACCESS_KEY'] = os.environ['ACCESS_KEY']
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

### DB Configs
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.environ['DATABASE_URL'].replace("postgres://", "postgresql://"))


connect_db(app)
db.create_all()

# routelist
# register
# login
# upload
# download
# update profile - only update emails, phone number, firstname lastname, 
# passwords never ID or username

##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/', methods=["GET"])
def displayHome():
    all_images = Photos.query.all()
    if all_images: #[{img}]
        output = serialize(all_images)
        # images = [image.serialize() for image in all_images]
        return jsonify(output)
    else:
        return jsonify({"error": "no images yet.."})

    #  images = {images: [{image object}, {image object}...]}
    #  .map(image_key, image_url <single card {redirect}>)
    #  route -> single <image card button=>onclick=gets form component ajax call state image onsubmit=>upload image, database, delete file> 
    # """Display Image from url from bucket"""
    # @app.route('/images/<filename>', methods=["GET"])
    # def displayImages(filename):

#     #downloads image url :)
#     image_url = f'https://s3.us-west-1.amazonaws.com/pix.ly/{filename}'
#     img = Image.open(requests.get(image_url, stream=True).raw)
#     img.save(f'./static/downloads/WALRUS.jpeg')


#     # image_blur = image.filter(ImageFilter.BLUR)
#     # image_blur.save(f'./static/downloads/blur-{filename}')
#     #do image manipulation here

#     return render_template("images.html", url=image_url)


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    try:
        user = User.signup(
            username=request.json["username"],
            password=request.json["password"],
            email=request.json["email"],
            image=request.json["image"] or User.image_url.default.arg,
        )
        db.session.commit()

    except IntegrityError as e:
                return {"error": "Sorry, the username is already taken"}
    do_login(user)

    return {"success": "successfully registered user"}


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    username = request.json["username"],
    password = request.json["password"]
    user = User.authenticate(request.json["username"],
                            request.json["password"])

    if user:
        do_login(user)
        flash(f"Hello, {user.username}!", "success")
        return jsonify({"user" : g.user})
    else:
        return jsonify({"error" : "Invalid username or password"})


# @app.route('/images/upload', methods=["GET","POST"])
# def addImage():
#  # dataflow: client -img-> form -img-> server -img-> s3, server -data-> db

#     #take file from client/browser
#     #send image to s3
#     #send metadata to metadata table
#     #send image name & url to images table
#     #slugify filenames

#     image_file = request.files["file"]
#     # if image_file.filename ==("/\.(jpg|JPG|jpeg|JPEG|png|PNG|gif|GIF)$/"):
#     #     return jsonify("OH NO")
#     file_with_original_name = secure_filename(image_file.filename)
#     #Standardizes filenames
#     file_name = str(uuid.uuid1())
#     image_url = f'https://s3.us-west-1.amazonaws.com/pix.ly/{file_name}'

#     image_file.save(f'./static/downloads/{file_with_original_name}')
#     image = Image.open(f'./static/downloads/{file_with_original_name}')

#     # Sets max resolution
#     size = 1200, 1200
#     image.thumbnail(size)

#     ext = image.format.lower()
#     image.save(f'./static/downloads/{file_name}.{ext}')
#     # breakpoint()
#     send_to_bucket(f'./static/downloads/{file_name}.{ext}', file_name)

#     #posts to databse
#     photo = Photos(image_key=f'{file_name}', image_url=image_url)
#     db.session.add(photo)


#     parseMetadata(image, file_name)
#     db.session.commit()
#     res_image = Photos.query.filter_by(image_key=file_name).first()

#     res_serialized = serialize([res_image])

#     if os.path.exists(f'./static/downloads/{file_name}.{ext}'):
#         os.remove(f'./static/downloads/{file_name}.{ext}')

#     if os.path.exists(f'./static/downloads/{file_with_original_name}'):
#         os.remove(f'./static/downloads/{file_with_original_name}')


#     return jsonify(res_serialized[0])




# @app.route('/images/<image>', methods=["GET", "POST"])
# def editImage(image):

#     photo = Photos.query.get_or_404(image)


#     return render_template("editingPage.html",photo=photo)



# """ Connect to S3 Service """

# client_s3 = boto3.client(
#     's3',
#     'us-west-1',
#     aws_access_key_id=app.config['ACCESS_KEY'],
#     aws_secret_access_key=app.config['SECRET_KEY']
# )


# #TODO: move thesde back to helper file

# def send_to_bucket(path, name, bucket="image-time-capsule"):
#     """upload image to s3 bucket
#     args( file path, file name, default bucket)
#     """

#     try:
#         print("uploading file...")
#         client_s3.upload_file(path, bucket, name)

#         #client_s3.upload_fileobj(image.read(), bucket_name, "TESTINGG!!!")

#     except ClientError as err:
#         print("CLIENTERROR: ",err)

#     except Exception as err:
#         print("EXCEPTION: ",err)


# """Extracts exif data from image object"""
# def parseMetadata(image, image_key):
#     exif_data = image.getexif()
#     if exif_data:
# # iterating over all EXIF data fields
#         for tag_id in exif_data:
#             # get the tag name, instead of human unreadable tag id
#             tag = TAGS.get(tag_id, tag_id)
#             data = exif_data.get(tag_id)
#             # decode bytes
#             if isinstance(data, bytes):
#                 data = data.decode()
#                 image_data =ImageData(image_key=image_key, image_type=tag,image_value=data)
#                 db.session.add(image_data)
#                 print(f"{tag:25}: {data}")
#             image_data =ImageData(image_key=image_key, image_type=tag,image_value=str(data))
#             db.session.add(image_data)
#             print(image_data)
#             #Raw exif looks like: {296: 2, 34665: 90, 274: 1, 282: 144.0, 283: 144.0, 40962: 1357, 40963: 1277, 37510: b'ASCII\x00\x00\x00Screenshot'}
#             #TODO: come back to it if we have more time for GPS

# def serialize(images):
#     output = []
#     for image in images:
#         tags = []
#         for exif in image.image_data:
#             tags.append(exif.serialize())
#         variable = {"imageKey": image.image_key,
#         "imageUrl": image.image_url,
#         "imageData": tags
#         }
#         output.append(variable)
#     return output

# # @app.route('/test', methods=["GET"])
# # def editImage():
    

# #     return send_file("./static/downloads/b0d39268-d23d-11ec-a33d-8c85902145ec.png")



# """ Connect to S3 Service """

# client_s3 = boto3.client(
#     's3',
#     'us-west-1',
#     aws_access_key_id=app.config['ACCESS_KEY'],
#     aws_secret_access_key=app.config['SECRET_KEY']
# )