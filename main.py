import datetime
begin_time = datetime.datetime.now()
print(datetime.datetime.now())
import boto3
import mariadb
import os
import sys
from dotenv import load_dotenv

load_dotenv()

aws_access_key_id = os.getenv('aws_access_key_id')
aws_secret_access_key = os.getenv('aws_secret_access_key')
bucket_from = os.getenv('bucket_from')
bucket_to = os.getenv('bucket_to')

s3 = boto3.resource(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

try:
    conn = mariadb.connect(
      user=os.getenv('DBUser'),
      password=os.getenv('DBPassword'),
      host="127.0.0.1",
      port=3306)
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

src = s3.Bucket(bucket_from)



def move_files():
    for archive in src.objects.all():
        print(archive.key.split('/')[-1])
        filename='neeeeew/'+ archive.key.split('/')[-1]
        print(filename)
        s3.meta.client.copy_object(
            ACL='public-read',
            Bucket=bucket_to,
            CopySource={'Bucket': bucket_from, 'Key': archive.key},
            Key=filename
        )

move_files()
print(datetime.datetime.now() - begin_time)
