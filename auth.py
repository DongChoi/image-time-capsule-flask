import jwt
import os
from models import Capsule
# TODO: make sure you have it raise errors.
def check_bearer_token(header):
    '''Check for bearer token'''
    PREFIX = "Bearer "
    if not header.startswith(PREFIX):
        return False
    return header[len(PREFIX):]

def decode_token_get_user_info(token):
    '''decodes token'''
    payload = jwt.decode(token, os.environ['SECRET_KEY_TOKEN'], algorithms=[os.environ['TOKEN_ALGORITHMS']])
    if payload:
        return payload
    else:
        raise ValueError("INVALID TOKEN!")

def create_token(username, capsules):
    capsules = [Capsule.serialize(capsule) for capsule in capsules]
    token = jwt.encode({
        "username": username, 
        "capsules": capsules}, 
        os.environ["SECRET_KEY_TOKEN"])
    return token