import os
from flask import Flask, jsonify, request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy import null
from models import db, connect_db, Capsule, Image, User
import boto3
import uuid
from botocore.exceptions import ClientError
from flask_cors import CORS
from auth import check_bearer_token, decode_token_get_user_info, create_token
from aws import send_files_to_aws, get_links_from_aws_s3_bucket
import yagmail
import datetime

##############################################################################
# Initialize app

#app layer(flask) - data layer(stores data)

### Flask set up
app = Flask(__name__)


CORS(app)



### S3 Keys
app.config['ACCESS_KEY_ID'] = os.environ['ACCESS_KEY_ID']
app.config['SECRET_ACCESS_KEY'] = os.environ['SECRET_ACCESS_KEY']

### Secret Key for Tokens
app.config['SECRET_KEY_TOKEN'] = os.environ['SECRET_KEY_TOKEN']
app.config['TOKEN_ALGORITHMS'] = os.environ['TOKEN_ALGORITHMS']


### SQLA Configs
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False


### AWS Lambda Keys

app.config["LAMBDA_PASSWORD"] = os.environ["LAMBDA_PASSWORD"]

### Yagmail Keys
app.config["PROGRAM_EMAIL"] = os.environ["PROGRAM_EMAIL"]
app.config["PROGRAM_EMAIL_PASSWORD"] = os.environ["PROGRAM_EMAIL_PASSWORD"]


if 'RDS_HOSTNAME' in os.environ:
    driver = 'postgresql+psycopg2://'
    app.config['SQLALCHEMY_DATABASE_URI'] = driver \
                                            + os.environ['RDS_USERNAME'] + ':' + os.environ['RDS_PASSWORD'] \
                                            +'@' + os.environ['RDS_HOSTNAME']  +  ':' + os.environ['RDS_PORT'] \
                                            + '/' + os.environ['RDS_DB_NAME']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.environ['DATABASE_URL'].replace("postgres://", "postgresql://"))

### connect to database and create tables
connect_db(app)
# db.create_all()

### Connect to AWS S3 client
client_s3 = boto3.client(
    's3',
    'us-west-1',
    aws_access_key_id=app.config['ACCESS_KEY_ID'],
    aws_secret_access_key=app.config['SECRET_ACCESS_KEY']
)


##############################################################################
# User signup/login/logout

@app.route('/', methods=["GET"])
def homepage():
    return "HOME PAGE WORKS"

@app.route('/login', methods=["POST"])
def login():
    """Handle user login."""
    user = User.authenticate(request.json["username"],
                        request.json["password"])
    if user:
        token = create_token(user.username, user.capsules)
        return jsonify({"token" : token})
    else:
        return jsonify({"error" : "Invalid username or password"})


@app.route('/signup', methods=["POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """
    try:
        user = User.signup(
            username=request.json["username"],
            password=request.json["password"],
            email=request.json["email"],
        )
        db.session.commit()
    except IntegrityError as e:
        return {"error": "Sorry, the username is already taken"}
    token = create_token(user.username, user.capsules)
    return jsonify({"token": token})





# ##############################################################################
# Automation for returning capsules daily




@app.route("/capsules", methods=["POST"])
def create_capsule():
    """creates capsule for the user"""
    auth_header = request.headers["Authorization"]
    token = check_bearer_token(auth_header)
    try:
        user_payload = decode_token_get_user_info(token)
    except ValueError as e:
        return {"Error": e}
    if user_payload["username"] == request.json["username"]:
        name = request.json["name"]
        message = request.json["message"]
        return_date = request.json["date"]
        user = User.query.filter_by(username=user_payload["username"]).one()
        capsule = Capsule(name=name, message=message, return_date = return_date, user_id=user.id)
        db.session.add(capsule)
        db.session.commit()
        token = create_token(user.username, user.capsules)
        return {"token": token, "capsule_id": capsule.id} 


@app.route("/capsules/<int:capsule_id>/images", methods=["POST"])
def addImage(capsule_id):
    for image_file in request.files.getlist("file"):
        if image_file.filename ==("/\.(jpg|JPG|jpeg|JPEG|png|PNG|gif|GIF)$/"):
            return jsonify({"error": "Sorry! This app can only accept Jpg, jpeg, png and gif format."})

        #Standardizes filenames
        file_name = str(uuid.uuid1()) + image_file.filename
        image_url = f'https://s3.us-west-1.amazonaws.com/image-time-capsule/{file_name}'

        print(f"sending to s3, image file : {image_file}, file_name:  {file_name}")
        response = send_files_to_aws(client_s3, image_file, file_name)

        #posts to databse
        photo = Image(image_key=f'{file_name}',capsule_id=capsule_id ,image_url=image_url)
        db.session.add(photo)

    db.session.commit()
    return jsonify({"Successful": "Your capsule and images have been successfully uploaded!"})


@app.route("/aws_lambda", methods=["POST"])
def aws_lambda():
    if request.json["password"] == app.config["LAMBDA_PASSWORD"]:
        capsules = return_capsules()
        return_message = "capsules to"
    for capsule in capsules:
        file_names_for_this_capsule = Image.get_file_names_from_capsule_id(capsule.id)
        user_email = capsule.user.email
        capsule_name = capsule.name
        capsule_message = capsule.message
        urls = [capsule_message]
        for file_name in file_names_for_this_capsule:
            urls.append(get_links_from_aws_s3_bucket(client_s3, file_name))
        send_emails(capsule_name,urls, user_email)
        print(f"capsule no.{capsule.id} belonging to {capsule.user_id} has been sent to {capsule.user.username}")
        return_message = return_message + f" {capsule.user.username},"
    if return_message == "capsules to ":
        return "no capsules were emailed"
    else:
        
        return jsonify({"return message": f"{return_message} has been emailed"})
    else:
        return Response(status=403)

### Checks to see if any capsules are due today and calls send_emails
def return_capsules():
    # Create a date with time instance
    datetimeInstance = datetime.datetime.today()
    # Extract the date only from date time instance
    dateInstance = datetimeInstance.date()
    capsules = Capsule.get_capsules_due_today(dateInstance)
    return capsules



### Sends emails to users' emails with their capsule_name as title, capsule message and image links as body
def send_emails(capsule_name, urls_and_message, user_email="dongandrewchoi@gmail.com"): 
    """ Sends urls via email to users"""
    user = app.config['PROGRAM_EMAIL']
    app_password = app.config['PROGRAM_EMAIL_PASSWORD'] # a token for gmail
    to = user_email
    subject = capsule_name
    #content = [body text, attachments, attachments] with each item, there will be a line break
    content = urls_and_message


    with yagmail.SMTP(user, app_password) as yag:
        yag.send(to, subject, content)
    print("sent emails")
