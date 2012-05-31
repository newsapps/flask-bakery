from flask import Flask, request, redirect, flash, get_flashed_messages, render_template, session
from optparse import OptionParser
import time

import requests 
from StringIO import StringIO
import unicodecsv

from jinja2 import Markup
import sys

GOOGLE_DOC_SPREADSHEET_KEY = '0AjgNg5alNkjPdGxlNkZqc1pGazQxU05oU2xzRDhDdXc'
COMMON_MICROCOPY_WORKSHEET_NUMBER = '0' # 
PER_PAGE_MICROCOPY_WORKSHEET_NUMBER = '1' # 

app = Flask(__name__)

def get_google_csv_url(key,sheet=None):
    url = "https://docs.google.com/spreadsheet/pub?key=%s&single=true&output=csv" % key
    if sheet is not None:
        url += "&gid=%s" % sheet
    return url


def fetch_perpage_microcopy():
    """Fetch the microcopy deck and return a dict whose keys are the value in the first column
       and whose values are a dict of values for that (keys are column headers)"""
    resp = requests.get(get_google_csv_url(GOOGLE_DOC_SPREADSHEET_KEY, PER_PAGE_MICROCOPY_WORKSHEET_NUMBER))
    if not resp.ok: resp.raise_for_status()
    d = {}
    reader = unicodecsv.DictReader(StringIO(resp.content))
    for row in reader:
        # have to convert keys from unicode to str to satisfy python's insistence on strs for kwarg keys
        d2 = dict((str(k),v) for k,v in row.items())
        row_key = row[reader.fieldnames[0]]    
        d[row_key] = d2 
    return d
    
def fetch_frontpage_microcopy(include_features=False):
    """Fetch the microcopy deck and return a dict whose keys are a front page content ID and whose value is the second column"""
    resp = requests.get(get_google_csv_url(GOOGLE_DOC_SPREADSHEET_KEY, COMMON_MICROCOPY_WORKSHEET_NUMBER))
    if not resp.ok: resp.raise_for_status()
    d = {}
    for x in unicodecsv.DictReader(StringIO(resp.content)):
        k,v = (x['id'],x['copy']) # choose other names, or document these, or...?
        k = str(k)
        d[k] = v
    if include_features:
        d['features'] = fetch_perpage_microcopy(key_mode=key_mode)
    return d
    
@app.template_filter('process_microcopy_textblock')
def process_microcopy_textblock(text):
    if text:
        content = "<br>".join(text.strip().splitlines())
    else:
        content = ''
    return Markup(content)

def init_default_context():
    return {}

@app.route('/')
def default():
    return redirect('/index.html')
    
@app.route('/<path:template>')
def preview(template,key_mode=False):
    if not template.endswith('.html'):
        return app.send_static_file(template)
    
    template_key = template[:-5]
    context = init_default_context()
    # populate with copy from google docs?
    # find alternate template name based on key?
    
    try:
        getattr(sys.modules[__name__],template_key)(context)
    except AttributeError: pass

    return render_template("%s" % template,**context)

def parse_args():
    parser = OptionParser()
    parser.add_option("--host", dest="host", default='localhost',
                      help="override the 'host' value so that one can access the local server from other machines.")
    (options, args) = parser.parse_args()
    return options


if __name__ == '__main__':
    opts = parse_args()

    kwargs = { 'debug': True, 'host': opts.host }
    app.config['HOSTNAME'] = opts.host
    app.run(**kwargs)
