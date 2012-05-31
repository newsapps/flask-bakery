#!/bin/env python
import sys
sys.path.append('app/')
import app
import os, os.path
import gzip
import shutil
from jinja2 import Environment, FileSystemLoader
import time
import codecs
from optparse import OptionParser

TEMPLATE_DIR = "app/templates"

class FakeTime:
    def time(self):
        return 1261130520.0

# Hack to override gzip's time implementation
# See: http://stackoverflow.com/questions/264224/setting-the-gzip-timestamp-from-python
gzip.time = FakeTime()

def parse_args():
    parser = OptionParser()
    parser.add_option("-k", "--key-mode", dest="key_mode", action="store_true", 
                      help="Render the documents in 'key mode' so that microcopy is prefixed with its key")
    parser.add_option("-z", "--gzip", dest="gzip", action="store_true", 
                      help="After rendering the documents, replace them with gzip'd versions.")
    (options, args) = parser.parse_args()
    return options

if __name__ == '__main__':

    project_dir = '.'
    output_dir = 'pensions'
    opts = parse_args()

    shutil.rmtree(os.path.join(project_dir, output_dir), ignore_errors=True)
    shutil.copytree(os.path.join(project_dir, 'app/static'), os.path.join(project_dir, output_dir))

    cache_buster = time.time()
    for path,dirnames,filenames in os.walk(TEMPLATE_DIR):
        for fn in filenames:
            if fn[0] != '_':
                tpath = os.path.join(path,fn)
                if tpath.startswith('app/templates/'):
                    tpath = tpath[14:]
                with app.app.test_request_context('/preview/%s' % tpath):
                    content = app.preview(tpath,key_mode=opts.key_mode)
                    codecs.open(os.path.join(project_dir, output_dir,fn),"w", encoding='utf-8').write(content)

    if opts.gzip:
        for path, dirs, files in os.walk(os.path.join(project_dir, output_dir)):
            for filename in files:
                file_path = os.path.join(path, filename)
        
                f_in = open(file_path, 'rb')
                contents = f_in.readlines()
                f_in.close()
                f_out = gzip.open(file_path, 'wb')
                f_out.writelines(contents)
                f_out.close();
    
