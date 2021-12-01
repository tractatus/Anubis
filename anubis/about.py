"Information page endpoints."

import os.path
import sys

import couchdb2
import flask
import jinja2
import marko
import xlsxwriter

import anubis
from anubis import constants
from anubis import utils


blueprint = flask.Blueprint('about', __name__)

@blueprint.route('/documentation/<page>')
def documentation(page):
    "Display the given documentation page."
    try:
        with open(os.path.join(flask.current_app.config['DOC_DIR'],
                               f"{page}.md")) as infile:
            text = infile.read()
    except (OSError, IOError):
        return utils.error('No such documentation page.')
    title = page.replace('-', ' ')
    return flask.render_template('about/documentation.html',
                                 title=title, text=text)

@blueprint.route('/contact')
def contact():
    "Display the contact information page."
    return flask.render_template('about/contact.html',
                                 text=utils.get_site_text("contact.md"))

@blueprint.route('/gdpr')
def gdpr():
    "Display the personal data policy page."
    return flask.render_template('about/gdpr.html',
                                 text=utils.get_site_text("gdpr.md"))

@blueprint.route('/software')
def software():
    "Show the current software versions."
    return flask.render_template('about/software.html',
                                 software=get_software())

def get_software():
    v = sys.version_info
    return [
        (constants.SOURCE_NAME, anubis.__version__, constants.SOURCE_URL),
        ('Python', f"{v.major}.{v.minor}.{v.micro}", 'https://www.python.org/'),
        ('Flask', flask.__version__, 'http://flask.pocoo.org/'),
        ('Jinja2', jinja2.__version__, 'https://pypi.org/project/Jinja2/'),
        ('CouchDB server', flask.g.db.server.version, 'https://couchdb.apache.org/'),
        ('CouchDB2 interface', couchdb2.__version__, 'https://pypi.org/project/couchdb2'),
        ('XslxWriter', xlsxwriter.__version__, 'https://xlsxwriter.readthedocs.io/'),
        ('Marko', marko.__version__, 'https://pypi.org/project/marko/'),
        ('Bootstrap', constants.BOOTSTRAP_VERSION, 'https://getbootstrap.com/'),
        ('jQuery', constants.JQUERY_VERSION, 'https://jquery.com/'),
        ('jQuery.localtime', '0.9.1', 'https://github.com/GregDThomas/jquery-localtime'),
        ('DataTables', constants.DATATABLES_VERSION, 'https://datatables.net/'),
        ('clipboard.js', '2.0.6', 'https://clipboardjs.com/'),
        ("Feather of Ma'at icon", '-', 'https://www.flaticon.com/authors/freepik'),
    ]

@blueprint.route('/settings')
@utils.login_required
def settings():
    "Display all configuration settings."
    if not (flask.g.am_admin or flask.g.am_staff):
        return utils.error('You are not allowed to view configuration settings.',
                           flask.url_for('home'))
    config = flask.current_app.config.copy()
    config["ROOT"] = constants.ROOT
    for key in ['SECRET_KEY', 'COUCHDB_PASSWORD', 'MAIL_PASSWORD']:
        if config[key]:
            config[key] = '<hidden>'
    return flask.render_template('about/settings.html',
                                 items=sorted(config.items()))
