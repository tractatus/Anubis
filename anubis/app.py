"Web app template."

import flask

import anubis.about
import anubis.config
import anubis.user
import anubis.call
import anubis.site

import anubis.api.about
import anubis.api.root
import anubis.api.schema
import anubis.api.user
from anubis import constants
from anubis import utils


app = flask.Flask(__name__)

# Add URL map converters.
app.url_map.converters['name'] = utils.NameConverter
app.url_map.converters['iuid'] = utils.IuidConverter

# Get the configuration.
anubis.config.init(app)

# Init the mail handler.
utils.mail.init_app(app)

# Add template filters.
app.add_template_filter(utils.thousands)

@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context of Jinja2 templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token,
                enumerate=enumerate)

@app.before_first_request
def init_database():
    flask.g.db = utils.get_db()
    utils.update_designs()

@app.before_request
def prepare():
    "Open the database connection; get the current user."
    flask.g.dbserver = utils.get_dbserver()
    flask.g.db = utils.get_db(dbserver=flask.g.dbserver)
    flask.g.current_user = anubis.user.get_current_user()
    flask.g.is_admin = flask.g.current_user and \
                       flask.g.current_user['role'] == constants.ADMIN

app.after_request(utils.log_access)

@app.route('/')
def home():
    "Home page. Redirect to API root if JSON is accepted."
    if utils.accept_json():
        return flask.redirect(flask.url_for('api_root'))
    else:
        return flask.render_template('home.html')

# Set up the URL map.
app.register_blueprint(anubis.about.blueprint, url_prefix='/about')
app.register_blueprint(anubis.user.blueprint, url_prefix='/user')
app.register_blueprint(anubis.call.blueprint, url_prefix='/call')
app.register_blueprint(anubis.site.blueprint, url_prefix='/site')

app.register_blueprint(anubis.api.root.blueprint, url_prefix='/api')
app.register_blueprint(anubis.api.about.blueprint, url_prefix='/api/about')
app.register_blueprint(anubis.api.schema.blueprint, url_prefix='/api/schema')
app.register_blueprint(anubis.api.user.blueprint, url_prefix='/api/user')


# This code is used only during development.
if __name__ == '__main__':
    app.run()
