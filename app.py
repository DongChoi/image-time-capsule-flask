from ast import parse
from multiprocessing.sharedctypes import Value
import os
from flask import Flask, jsonify, render_template, request, flash, redirect, session, g, send_file, url_for
from unicodedata import name
from sqlalchemy.exc import IntegrityError
from sqlalchemy import null
from werkzeug.utils import secure_filename
from PIL import ImageFilter
import PIL.Image
from PIL.ExifTags import TAGS
import requests
from io import BytesIO
# from dotenv import load_dotenv
from models import db, connect_db, Capsule, Image, User
# load_dotenv()
import boto3
import uuid
from botocore.exceptions import ClientError
from flask_cors import CORS
import jwt
import schedule
import time
import datetime
import threading
from flask import Flask
from flask_mail import Mail, Message
import yagmail


CURR_USER_KEY = "curr_user"

app = Flask(__name__)
mail = Mail(app)

CORS(app)

### S3 Keys
app.config['ACCESS_KEY'] = os.environ['ACCESS_KEY']
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
SECRETT_KEY = "SHH ITS A SECRET! HAHAHAHA"
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


# @app.before_request
# def add_user_to_g():
#     """If we're logged in, add curr user to Flask global."""

#     if CURR_USER_KEY in session:
#         g.user = User.query.get(session[CURR_USER_KEY])

#     else:
#         g.user = None


# def do_login(user):
#     """Log in user."""
#     session[CURR_USER_KEY] = user.username


# def do_logout():
#     """Logout user."""

#     if CURR_USER_KEY in session:
#         del session[CURR_USER_KEY]

# @app.route('/', methods=["GET"])
# def displayHome():
#     all_images = Photos.query.all()
#     if all_images: #[{img}]
#         output = serialize(all_images)
#         # images = [image.serialize() for image in all_images]
#         return jsonify(output)
#     else:
#         return jsonify({"error": "no images yet.."})

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
    print("attempting to save user data to database")
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    try:
        user = User.signup(
            username=request.json["username"],
            password=request.json["password"],
            email=request.json["email"],

        )
        db.session.commit()
        print("user successfully committed to db")
    except IntegrityError as e:
                return {"error": "Sorry, the username is already taken"}
    token = jwt.encode({
                        "username": user.username,
                        "capsules": []},
                        SECRETT_KEY)
    print("attempting to convert data into JWT TOKEN", token)
    return jsonify(token)
    # 
    # 
    # {"user": {
    #                 "username": user.username,
    #                 "token" : user.token,
    #                 "capsules_info": {"capsules": user.capsules}
    #                 }}

#TODO: make auth into something like this
# router.post("/token", async function (req, res, next) {
#   const validator = jsonschema.validate(req.body, userAuthSchema);
#   if (!validator.valid) {
#     const errs = validator.errors.map(e => e.stack);
#     throw new BadRequestError(errs);
#   }

#   const { username, password } = req.body;
#   const user = await User.authenticate(username, password);
#   const token = createToken(user);
#   return res.json({ token });
# });

PREFIX = "Bearer "


# TODO: make sure you have it raise errors.
def check_bearer_token(header):
    '''authenticates user'''
    if not header.startswith(PREFIX):
        return False
    return header[len(PREFIX):]

def decode_token_get_user(token):
    payload = jwt.decode(token, SECRETT_KEY, algorithms=["HS256"])
    if payload:
        return payload
    else:
        raise ValueError("INVALID TOKEN!")
###TODO: make it so its <users>/capsules to match the header to the user route!!! ###
@app.route("/capsules", methods=["POST"])
def createCapsule():
    """creates capsule for the user"""
    auth_header = request.headers["Authorization"]
    token = check_bearer_token(auth_header)
    #returns {username: "user", title, message, date}
    if token:
        name = request.json["name"]
        message = request.json["message"]
        return_date = request.json["date"]
        user_payload = decode_token_get_user(token)
        user = User.query.filter_by(username =user_payload["username"]).one()
        user_id = user.id
        capsule = Capsule(name=name, message=message, return_date = return_date, user_id=user_id)
        db.session.add(capsule)
        db.session.commit()
        capsules = [Capsule.serialize(capsule) for capsule in user.capsules]
        token = jwt.encode({"username": user.username, "capsules": capsules}, SECRETT_KEY)
        return {"token": token, "capsule_id": capsule.id} 

# @app.route("/capsules/<int:capsule_id>/images", methods=["POST"])
# def bindImagesToCapsule(capsule_id):
#     """adds images to capsule"""
#     breakpoint()
#     print("printing request.json from images add", request)

#     # TODO: do some auth logic
#     #....
#     #then if capsule_id.user_id == user.id(from token),
#     #start creating urls from aws and attachiing them into DB
#     #return capsule_id.images.length
#     auth_header = request.headers["Authorization"]
#     token = check_bearer_token(auth_header)
#     if token:
#         return "SUccessful"
        

#TODO: make a function that will run everyday at 12:00 am






@app.route('/login', methods=["POST"])
def login():
    """Handle user login."""
    user = User.authenticate(request.json["username"],
                        request.json["password"])
    if user:
        print(user)
        capsules = [Capsule.serialize(capsule) for capsule in user.capsules]
        token = jwt.encode({
                    "username": user.username,
                    "capsules": capsules},
                    SECRETT_KEY)
        return jsonify({"token" : token})
    else:
        return jsonify({"error" : "Invalid username or password"})


#TODO:: TODO: return correct capsule stuff so we can correctly update the token and setstate for capsules!
@app.route("/capsules/<int:capsule_id>/images", methods=["POST"])
def addImage(capsule_id):
 # dataflow: client -img-> form -img-> server -img-> s3, server -data-> db

    #take file from client/browser
    #send image to s3
    #send metadata to metadata table
    #send image name & url to images table
    #slugify filenames
    for image_file in request.files.getlist("file"):
        if image_file.filename ==("/\.(jpg|JPG|jpeg|JPEG|png|PNG|gif|GIF)$/"):
            return jsonify("OH NO")
        
        # file_with_original_name = secure_filename(image_file.filename)


        #Standardizes filenames
        file_name = str(uuid.uuid1()) + image_file.filename
        image_url = f'https://s3.us-west-1.amazonaws.com/image-time-capsule/{file_name}'
        print("successfully created filename and image url")
        # image.thumbnail(size)

        # ext = image.format.lower()

        print(f"sending to s3, image file : {image_file}, file_name:  {file_name}")
        response = send_to_s3(image_file, file_name)


        #posts to databse
        photo = Image(image_key=f'{file_name}',capsule_id=capsule_id ,image_url=image_url)
        db.session.add(photo)


    # parseMetadata(image, file_name)
    db.session.commit()
    # res_image = Photos.query.filter_by(image_key=file_name).first()

    # res_serialized = serialize([res_image])

    # if os.path.exists(f'./static/downloads/{file_name}.{ext}'):
    #     os.remove(f'./static/downloads/{file_name}.{ext}')

    # if os.path.exists(f'./static/downloads/{file_with_original_name}'):
    #     os.remove(f'./static/downloads/{file_with_original_name}')


    return "jsonify(res_serialized[0])"

""" Connect to S3 Service """

client_s3 = boto3.client(
    's3',
    'us-west-1',
    aws_access_key_id=app.config['ACCESS_KEY'],
    aws_secret_access_key=app.config['SECRET_KEY']
)



def get_object_from_aws(file_name):
    try:
        url = client_s3.generate_presigned_url('get_object',
                                Params={
                                    'Bucket': 'image-time-capsule',
                                    'Key': file_name,
                                },                                  
                                ExpiresIn=86400)
    except Exception as e:
        print(e)
    return url


    
"""check daily for capsule dates that match today's date"""



def return_capsules():
    print("running return capsules")

    # Create a date with time instance
    datetimeInstance = datetime.datetime.today()
    print("got the datetimeInstance on line 332:", datetimeInstance)
    # Extract the date only from date time instance
    dateInstance = datetimeInstance.date()
    print("got the dateInstance on line 335:", dateInstance)
    capsules = Capsule.get_capsules_due_today(dateInstance)
    print("got the capsules", capsules)
    for capsule in capsules:
        print("looping capsules heres what the capsules looks like :", capsules)
        file_names_for_this_capsule = Image.get_file_names_from_capsule_id(capsule.id)
        # BUG: This is none
        urls = []
        for file_name in file_names_for_this_capsule:
            urls.append(get_object_from_aws(file_name))
        send_emails(urls)
        print("sent urls")
        

def send_emails(urls, user_email="dongandrewchoi@gmail.com"):


    user = os.environ['PROGRAM_EMAIL']
    app_password = os.environ['PROGRAM_EMAIL_PASSWORD'] # a token for gmail
    to = user_email

    subject = 'Message from imagetimecapsule2022'
    #content = [body text, attachments, attachments] with each item, there will be a line break
    content = ["lets get this bread", "and this one too"]


    with yagmail.SMTP(user, app_password) as yag:
        yag.send(to, subject, content)
        print('Sent email successfully')


print("YOU DEF GOT HERE~!")

schedule.every().day.at("17:11").do(return_capsules)
while 1:
    schedule.run_pending()
    time.sleep(1)




# #TODO: move thesde back to helper file

def send_to_bucket(path, name, bucket="image-time-capsule"):
    """upload image to s3 bucket
    args( file path, file name, default bucket)
    """

    try:
        print("uploading file...")
        client_s3.upload_file(path, bucket, name)

        #client_s3.upload_fileobj(image.read(), bucket_name, "TESTINGG!!!")

    except ClientError as err:
        print("CLIENTERROR: ",err)

    except Exception as err:
        print("EXCEPTION: ",err)


def send_to_s3(file, location):
    """ Accepts file and app and uploads to aws s3. """
    print("filename -------------",file)
    try:
        client_s3.put_object(
            Body=file,
            Bucket="image-time-capsule",
            Key=location,
            ContentType= file.mimetype
            )
    except Exception as e:
        print("Exception caught while put_object*******************", e)
        return e
    return "{}{}".format(location, str(file.filename))


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