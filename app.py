import os
from flask import Flask, jsonify, render_template, request, flash, redirect, session, g, send_file, url_for
from unicodedata import name
from sqlalchemy.exc import IntegrityError
from sqlalchemy import null
from models import db, connect_db, Capsule, Image, User
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
from aws import client_s3, send_files_to_aws, get_files_from_aws

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
mail = Mail(app)

CORS(app)

### S3 Keys
app.config['ACCESS_KEY'] = os.environ['ACCESS_KEY']
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
SECRETT_KEY = os.environ["SECRET_KEY_TOKEN"]
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
def create_capsule():
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


@app.route("/capsules/<int:capsule_id>/images", methods=["POST"])
def addImage(capsule_id):
    for image_file in request.files.getlist("file"):
        if image_file.filename ==("/\.(jpg|JPG|jpeg|JPEG|png|PNG|gif|GIF)$/"):
            return jsonify("OH NO")


        #Standardizes filenames
        file_name = str(uuid.uuid1()) + image_file.filename
        image_url = f'https://s3.us-west-1.amazonaws.com/image-time-capsule/{file_name}'

        print(f"sending to s3, image file : {image_file}, file_name:  {file_name}")
        response = send_files_to_aws(image_file, file_name)

        #posts to databse
        photo = Image(image_key=f'{file_name}',capsule_id=capsule_id ,image_url=image_url)
        db.session.add(photo)

    db.session.commit()
    return "jsonify(res_serialized[0])"




    
"""check daily for capsule dates that match today's date"""
def return_capsules():
    print("running return capsules")

    # Create a date with time instance
    datetimeInstance = datetime.datetime.today()
    # Extract the date only from date time instance
    dateInstance = datetimeInstance.date()
    capsules = Capsule.get_capsules_due_today(dateInstance)
    print("got the capsules", capsules)
    for capsule in capsules:
        file_names_for_this_capsule = Image.get_file_names_from_capsule_id(capsule.id)
        urls = []
        for file_name in file_names_for_this_capsule:
            urls.append(get_files_from_aws(file_name))
        send_emails(urls)
        print(f"capsule no.{capsule.id} belonging to {capsule.user_id} has been sent to user")
        

def send_emails(urls, user_email="dongandrewchoi@gmail.com"):


    user = os.environ['PROGRAM_EMAIL']
    app_password = os.environ['PROGRAM_EMAIL_PASSWORD'] # a token for gmail
    to = user_email

    subject = 'Message from imagetimecapsule2022'
    #content = [body text, attachments, attachments] with each item, there will be a line break
    content = urls


    with yagmail.SMTP(user, app_password) as yag:
        yag.send(to, subject, content)


# return_capsules()

# schedule.every().day.at("17:52").do(return_capsules)
# while 1:
#     schedule.run_pending()
#     time.sleep(1)