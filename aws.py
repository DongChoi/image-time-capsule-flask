import boto3
import os


""" Connect to S3 Service """
client_s3 = boto3.client(
    's3',
    'us-west-1',
    aws_access_key_id=os.environ['ACCESS_KEY'],
    aws_secret_access_key=os.environ['SECRET_KEY']
)


def send_files_to_aws(file, location):
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


def get_files_from_aws(file_name):
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

