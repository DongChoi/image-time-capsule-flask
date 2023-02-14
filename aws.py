import boto3
import os


def send_files_to_aws(client_s3, file, location):
    """ Accepts file and uploads to aws s3. """
    try:
        client_s3.put_object(
            Body=file,
            Bucket="image-time-capsule",
            Key=location,
            ContentType= file.mimetype
            )
    except Exception as e:
        print("Exception caught while sending files to aws", e)
        return e
    return "{}{}".format(location, str(file.filename))

def get_links_from_aws_s3_bucket(file_name):
    " Requests presigned url using key stored in PostgreSQL"
    try:
        url = client_s3.generate_presigned_url('get_object',
                                Params={
                                    'Bucket': app.config['AWS_BUCKET_NAME'],
                                    'Key': file_name,
                                },                                  
                                ExpiresIn=86400)
    except Exception as e:
        print(e)
    return url
