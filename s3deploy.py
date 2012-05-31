import sys, os.path
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import os
import mimetypes
import gzip
import tempfile
import logging
import shutil
from optparse import OptionParser

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
CONCURRENCY = 32

def _s3conn(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY):
    if aws_access_key_id is None or aws_secret_access_key is None:
        raise Exception("AWS access key ID and secret access key must be provided. The easiest way is to set the environment variables AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
    return S3Connection(aws_access_key_id, aws_secret_access_key)

def deploy_to_s3(directory, bucket):
    """
    Deploy a directory to an s3 bucket.
    """
    directory = directory.rstrip('/')
    slug = directory.split('/')[-1]

    tempdir = tempfile.mkdtemp('s3deploy')
    for keyname, absolute_path in find_file_paths(directory):
        s3_upload(slug, keyname, absolute_path, bucket, tempdir)

    shutil.rmtree(tempdir,True)
    return True

def s3_upload(slug, keyname, absolute_path, bucket, tempdir):
    """
    Upload a file to s3
    """
    conn = _s3conn()
    bucket = conn.get_bucket(bucket)

    mimetype = mimetypes.guess_type(absolute_path)
    options = { 'Content-Type' : mimetype[0] }

    # There's a possible race condition if files have the same name
    if mimetype[0] is not None and mimetype[0].startswith('text/'):
        upload = open(absolute_path);
        options['Content-Encoding'] = 'gzip'
        key_parts = keyname.split('/')
        filename = key_parts.pop()
        temp_path = os.path.join(tempdir, filename)
        gzfile = gzip.open(temp_path, 'wb')
        gzfile.write(upload.read())
        gzfile.close()
        absolute_path = temp_path

    k = Key(bucket)
    k.key = '%s/%s' % (slug, keyname)
    k.set_contents_from_filename(absolute_path, options, policy='public-read')

def find_file_paths(directory):
    """
    A generator function that recursively finds all files in the upload directory.
    """
    for root, dirs, files in os.walk(directory):
        rel_path = os.path.relpath(root, directory)

        for f in files:
            if rel_path == '.':
                yield (f, os.path.join(root, f))
            else:
                yield (os.path.join(rel_path, f), os.path.join(root, f))

def parse_args():
    parser = OptionParser()
    parser.add_option("-b", "--bucket", dest="bucket", action="store",
                      help="Specify the S3 bucket to which the files should be deployed")
    parser.add_option("-d", "--dir", dest="dir", action="store",
                      help="Specify the directory which should be copied to the remote bucket. Default 'pensions'")
    (options, args) = parser.parse_args()
    return options

if __name__ == '__main__':
    opts = parse_args()
    if not opts.bucket:
        raise ValueError("A bucket must be specified.")
    deploy_to_s3(opts.dir,opts.bucket)

