"Endpoint for site-specific static files."

import http.client
import os.path

import flask


blueprint = flask.Blueprint("site", __name__)


@blueprint.route("/static/<filename>")
def static(filename):
    "Return the given site-specific static file."
    dirpath = flask.current_app.config["SITE_STATIC_DIR"]
    if not dirpath:
        raise ValueError("misconfiguration: SITE_STATIC_DIR not set")
    dirpath = os.path.expandvars(os.path.expanduser(dirpath))
    if dirpath:
        return flask.send_from_directory(dirpath, filename)
    else:
        flask.abort(http.client.NOT_FOUND)
