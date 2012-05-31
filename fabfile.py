# Chicago Tribune News Applications fabfile
# No copying allowed
from fabric.api import *
from urllib import quote_plus
from urllib2 import urlopen
import os
"""
Base configuration
"""
env.project_name = 'pensions'
env.path = '/home/newsapps/sites/%(project_name)s' % env
env.log_path = '/home/newsapps/logs/%(project_name)s' % env
env.env_path = '%(path)s/env' % env
env.repo_path = '%(path)s/repository' % env
env.apache_config_path = '/home/newsapps/sites/apache/%(project_name)s' % env
env.python = 'python2.6'
env.repository_url = 'git@tribune.unfuddle.com:tribune/%(project_name)s.git' % env

"""
Environments
"""
def production():
    """
    Work on production environment
    """
    env.settings = 'production'
    env.user = 'newsapps'
    env.s3_bucket = 'media.apps.chicagotribune.com'

def staging():
    """
    Work on staging environment
    """
    env.settings = 'staging'
    env.user = 'newsapps'
    env.s3_bucket = 'media-beta.tribapps.com'
    

"""
Commands - deployment
"""
def deploy():
    """
    Deploy the latest version of the site to S3 from LOCAL files -- 
    there is nothing to do with git here...
    """
    local('python render_templates.py')
    local(('python s3deploy.py -b %(s3_bucket)s' % env))

