"Call for submissions."

import copy

import flask

from . import constants
from . import utils
from .saver import AttachmentsSaver


CALLS_DESIGN_DOC = {
    'views': {
        'identifier': {'map': "function (doc) {if (doc.doctype !== 'call') return; emit(doc.identifier, null);}"},
        'closes': {'map': "function (doc) {if (doc.doctype !== 'call' || !doc.closes || !doc.opens) return; emit(doc.closes, null);}"},
        'open_ended': {'map': "function (doc) {if (doc.doctype !== 'call' || !doc.opens || doc.closes) return; emit(doc.opens, null);}"},
        'reviewer': {'map': "function (doc) {if (doc.doctype !== 'call') return; for (var i=0; i < doc.reviewers.length; i++) {emit(doc.reviewers[i], doc.identifier); }}"},
    }
}

blueprint = flask.Blueprint('call', __name__)

@blueprint.route('/', methods=['GET', 'POST'])
@utils.admin_required
def create():
    "Create a new call from scratch."
    if utils.http_GET():
        return flask.render_template('call/create.html')

    elif utils.http_POST():
        try:
            with CallSaver() as saver:
                saver.set_identifier(flask.request.form.get('identifier'))
                saver.set_title(flask.request.form.get('title'))
            call = saver.doc
        except ValueError as error:
            utils.flash_error(str(error))
            return flask.redirect(flask.url_for('.create'))
        return flask.redirect(flask.url_for('.edit', cid=call['identifier']))

@blueprint.route('/<cid>')
def display(cid):
    "Display the call."
    call = get_call(cid)
    if not call:
        utils.flash_error('No such call.')
        return flask.redirect(flask.url_for('home'))
    return flask.render_template('call/display.html', call=call)

@blueprint.route('/<cid>/edit', methods=['GET', 'POST', 'DELETE'])
@utils.admin_required
def edit(cid):
    "Edit the call, or delete it."
    call = get_call(cid)
    if not call:
        utils.flash_error('No such call.')
        return flask.redirect(flask.url_for('home'))

    if utils.http_GET():
        return flask.render_template('call/edit.html', call=call)

    elif utils.http_POST():
        try:
            with CallSaver(call) as saver:
                saver.set_title(flask.request.form.get('title'))
                saver['description'] = flask.request.form.get('description')
                saver['opens'] = utils.normalize_datetime(
                    flask.request.form.get('opens'))
                saver['closes'] = utils.normalize_datetime(
                    flask.request.form.get('closes'))
        except ValueError as error:
            utils.flash_error(str(error))
        return flask.redirect(flask.url_for('.display', cid=call['identifier']))

    elif utils.http_DELETE():
        if not is_editable(call):
            utils.flash_error('call cannot be deleted')
            return flask.redirect(
                flask.url_for('.display', cid=call['identifier']))
        utils.delete(call)
        utils.flash_message(f"Deleted call {call['identifier']}:{call['title']}.")
        return flask.redirect(flask.url_for('calls.all'))

@blueprint.route('/<cid>/documents', methods=['GET', 'POST'])
@utils.admin_required
def documents(cid):
    "Display documents for delete, or add document (attachment file)."
    call = get_call(cid)
    if not call:
        utils.flash_error('No such call.')
        return flask.redirect(flask.url_for('home'))

    if utils.http_GET():
        return flask.render_template('call/documents.html', call=call)

    elif utils.http_POST():
        infile = flask.request.files.get('document')
        if infile:
            description = flask.request.form.get('document_description')
            with CallSaver(call) as saver:
                saver.add_document(infile, description)
        else:
            utils.flash_error('No document selected.')
        return flask.redirect(flask.url_for('.display', cid=call['identifier']))

@blueprint.route('/<cid>/documents/<documentname>',
                 methods=['GET', 'POST', 'DELETE'])
def document(cid, documentname):
    "Download the given document (attachment file), or delete it."
    call = get_call(cid)
    if not call:
        utils.flash_error('No such call.')
        return flask.redirect(flask.url_for('home'))

    if utils.http_GET():
        if not (flask.g.is_admin or call['cache']['is_published']):
            utils.flash_error(f"Call {call['title']} has not been published.")
            return flask.redirect(flask.url_for('home'))
        try:
            stub = call['_attachments'][documentname]
        except KeyError:
            utils.flash_error('No such document in call.')
            return flask.redirect(
                flask.url_for('.display', cid=call['identifier']))
        outfile = flask.g.db.get_attachment(call, documentname)
        response = flask.make_response(outfile.read())
        response.headers.set('Content-Type', stub['content_type'])
        response.headers.set('Content-Disposition', 'attachment', 
                             filename=documentname)
        return response

    elif utils.http_DELETE():
        if not flask.g.is_admin:
            utils.flash_error('You may not delete a document in the call.')
            return flask.redirect(
                flask.url_for('.display', cid=call['identifier']))
        with CallSaver(call) as saver:
            saver.delete_document(documentname)
        return flask.redirect(
            flask.url_for('.documents', cid=call['identifier']))

@blueprint.route('/<cid>/fields', methods=['GET', 'POST'])
@utils.admin_required
def fields(cid):
    "Display submission fields for delete, and add field."
    call = get_call(cid)
    if not call:
        utils.flash_error('No such call.')
        return flask.redirect(flask.url_for('home'))

    if utils.http_GET():
        return flask.render_template('call/fields.html', call=call)

    elif utils.http_POST():
        try:
            with CallSaver(call) as saver:
                saver.add_field(form=flask.request.form)
        except ValueError as error:
            utils.flash_error(str(error))
        return flask.redirect(flask.url_for('.fields', cid=call['identifier']))

@blueprint.route('/<cid>/field/<fid>', methods=['POST', 'DELETE'])
@utils.admin_required
def field(cid, fid):
    "Edit or delete the submission field."
    call = get_call(cid)
    if not call:
        utils.flash_error('No such call.')
        return flask.redirect(flask.url_for('home'))

    if utils.http_POST():
        try:
            with CallSaver(call) as saver:
                saver.edit_field(fid, form=flask.request.form)
        except (KeyError, ValueError) as error:
            utils.flash_error(str(error))
        return flask.redirect(flask.url_for('.fields', cid=call['identifier']))

    elif utils.http_DELETE():
        try:
            with CallSaver(call) as saver:
                saver.delete_field(fid)
        except ValueError as error:
            utils.flash_error(str(error))
        return flask.redirect(flask.url_for('.fields', cid=call['identifier']))

@blueprint.route('/<cid>/reviewers', methods=['GET', 'POST', 'DELETE'])
@utils.admin_required
def reviewers(cid):
    "Edit the list of reviewers."
    import anubis.user
    call = get_call(cid)
    if not call:
        utils.flash_error('No such call.')
        return flask.redirect(flask.url_for('home'))

    if utils.http_GET():
        return flask.render_template('call/reviewers.html', call=call)

    elif utils.http_POST():
        reviewer = flask.request.form.get('reviewer')
        user = anubis.user.get_user(username=reviewer)
        if user is None:
            user = anubis.user.get_user(email=reviewer)
        if user is None:
            utils.flash_error('No such user.')
            return flask.redirect(
                flask.url_for('.reviewers', cid=call['identifier']))
        if user['username'] not in call['reviewers']:
            with CallSaver(call) as saver:
                saver['reviewers'].append(user['username'])
                if utils.to_bool(flask.request.form.get('chair')):
                    saver['chairs'].append(user['username'])
        return flask.redirect(
            flask.url_for('.reviewers', cid=call['identifier']))

    elif utils.http_DELETE():
        reviewer = flask.request.form.get('reviewer')
        if reviewer:
            with CallSaver(call) as saver:
                try:
                    saver['reviewers'].remove(reviewer)
                except ValueError:
                    pass
                try:
                    saver['chairs'].remove(reviewer)
                except ValueError:
                    pass
        return flask.redirect(
            flask.url_for('.reviewers', cid=call['identifier']))

@blueprint.route('/<cid>/evaluation', methods=['GET', 'POST'])
@utils.admin_required
def evaluation(cid):
    "Display evaluation fields for delete, and add field."
    call = get_call(cid)
    if not call:
        utils.flash_error('No such call.')
        return flask.redirect(flask.url_for('home'))

    if utils.http_GET():
        return flask.render_template('call/evaluation.html', call=call)

    elif utils.http_POST():
        try:
            with CallSaver(call) as saver:
                saver.add_evaluation_field(form=flask.request.form)
        except ValueError as error:
            utils.flash_error(str(error))
        return flask.redirect(
            flask.url_for('.evaluation', cid=call['identifier']))

@blueprint.route('/<cid>/evaluation/<fid>', methods=['POST', 'DELETE'])
@utils.admin_required
def evaluation_field(cid, fid):
    "Edit or delete the evaluation field."
    call = get_call(cid)
    if not call:
        utils.flash_error('No such call.')
        return flask.redirect(flask.url_for('home'))

    if utils.http_POST():
        try:
            with CallSaver(call) as saver:
                saver.edit_evaluation_field(fid, form=flask.request.form)
        except ValueError as error:
            utils.flash_error(str(error))
        return flask.redirect(
            flask.url_for('.evaluation', cid=call['identifier']))

    elif utils.http_DELETE():
        try:
            with CallSaver(call) as saver:
                saver.delete_evaluation_field(fid)
        except ValueError as error:
            utils.flash_error(str(error))
        return flask.redirect(
            flask.url_for('.evaluation', cid=call['identifier']))

@blueprint.route('/<cid>/clone', methods=['GET', 'POST'])
@utils.admin_required
def clone(cid):
    "Clone the call."
    call = get_call(cid)
    if not call:
        utils.flash_error('No such call.')
        return flask.redirect(flask.url_for('home'))

    if utils.http_GET():
        return flask.render_template('call/clone.html', call=call)

    elif utils.http_POST():
        try:
            with CallSaver() as saver:
                saver.set_identifier(flask.request.form.get('identifier'))
                saver.set_title(flask.request.form.get('title'))
                saver.doc['fields'] = copy.deepcopy(call['fields'])
                # Do not copy documents.
                # Do not copy reviewers or chairs.
            new = saver.doc
        except ValueError as error:
            utils.flash_error(str(error))
            return flask.redirect(flask.url_for('.clone', cid=cid))
        return flask.redirect(flask.url_for('.edit', cid=new['identifier']))

@blueprint.route('/<cid>/logs')
@utils.admin_required
def logs(cid):
    "Display the log records of the call."
    call = get_call(cid)
    if call is None:
        utils.flash_error('No such call.')
        return flask.redirect(flask.url_for('home'))

    return flask.render_template(
        'logs.html',
        title=f"Call {call['identifier']}",
        back_url=flask.url_for('.display', cid=call['identifier']),
        logs=utils.get_logs(call['_id']))

@blueprint.route('/<cid>/submission', methods=['POST'])
@utils.login_required
def submission(cid):
    "Create a new submission within the call."
    import anubis.submission 
    call = get_call(cid)
    if call is None:
        utils.flash_error('No such call.')
        return flask.redirect(flask.url_for('home'))

    if not call['cache']['is_open']:
        utils.flash_error(f"Call {call['title']} is not open.")

    if utils.http_POST():
        with anubis.submission.SubmissionSaver(call=call) as saver:
            pass
        doc = saver
        return flask.redirect(
            flask.url_for('submission.edit', sid=doc['identifier']))


class CallSaver(AttachmentsSaver):
    "Call document saver context."

    DOCTYPE = constants.CALL

    def initialize(self):
        self.doc['opens'] = None
        self.doc['closes'] = None
        self.doc['fields'] = []
        self.doc['documents'] = []
        self.doc['evaluation'] = []
        self.doc['reviewers'] = []
        self.doc['chairs'] = []

    def set_identifier(self, identifier):
        "Call identifier."
        if self.doc.get('identifier'):
            raise ValueError('Identifier has already been set.')
        if not identifier:
            raise ValueError('Identifier must be provided.')
        if len(identifier) > flask.current_app.config['CALL_IDENTIFIER_MAXLENGTH']:
            raise ValueError('Too long identifier.')
        if not constants.ID_RX.match(identifier):
            raise ValueError('Invalid identifier.')
        if get_call(identifier):
            raise ValueError('Identifier is already in use.')
        self.doc['identifier'] = identifier

    def set_title(self, title):
        "Call title: non-blank required."
        if not title:
            raise ValueError('Title must be provided.')
        self.doc['title'] = title

    def add_field(self, form=dict()):
        "Add a field to the submission definition."
        field = self.get_new_field(form=form)
        if field['identifier'] in [f['identifier'] for f in self.doc['fields']]:
            raise ValueError('Field identifier is already in use.')
        self.doc['fields'].append(field)

    def get_new_field(self, form=dict()):
        "Get the field definition from the form."
        fid = form.get('identifier')
        if not (fid and constants.ID_RX.match(fid)):
            raise ValueError('Invalid field identifier.')
        type = form.get('type')
        if type not in constants.FIELD_TYPES:
            raise ValueError('Invalid field type.')
        title = form.get('title') or fid.replace('_', ' ')
        title = ' '.join([w.capitalize() for w in title.split()])
        field = {'type': type,
                 'identifier': fid,
                 'title': title,
                 'description': form.get('description') or None,
                 'required': bool(form.get('required'))
                 }
        if type in (constants.TEXT, constants.LINE):
            try:
                maxlength = int(form.get('maxlength'))
                if maxlength <= 0: raise ValueError
            except (TypeError, ValueError):
                maxlength = None
            field['maxlength'] = maxlength

        elif type == constants.INTEGER:
            try:
                minimum = int(form.get('minimum'))
            except (TypeError, ValueError):
                minimum = None
            try:
                maximum = int(form.get('maximum'))
            except (TypeError, ValueError):
                maximum = None
            if minimum is not None and maximum is not None and maximum <= minimum:
                raise ValueError('Invalid score range.')
            field['minimum'] = minimum
            field['maximum'] = maximum

        elif type == constants.FLOAT:
            try:
                minimum = float(form.get('minimum'))
            except (TypeError, ValueError):
                minimum = None
            try:
                maximum = float(form.get('maximum'))
            except (TypeError, ValueError):
                maximum = None
            if minimum is not None and maximum is not None and maximum <= minimum:
                raise ValueError('Invalid score range.')
            field['minimum'] = minimum
            field['maximum'] = maximum

        elif type == constants.SCORE:
            try:
                minimum = int(form.get('minimum'))
            except (TypeError, ValueError):
                minimum = None
            try:
                maximum = int(form.get('maximum'))
            except (TypeError, ValueError):
                maximum = None
            if minimum is None or maximum is None or maximum <= minimum:
                raise ValueError('Invalid score range.')
            field['minimum'] = minimum
            field['maximum'] = maximum
            field['slider'] = utils.to_bool(form.get('slider'))

        return field

    def edit_field(self, fid, form=dict()):
        "Edit the field for the submission definition."
        for field in self.doc['fields']:
            if field['identifier'] == fid:
                self.update_field(field, form=form)
                break
        else:
            raise KeyError('No such submission field.')

    def update_field(self, field, form=dict()):
        "Edit the field definition from the form."
        title = form.get('title')
        if not title:
            title = ' '.join([w.capitalize() 
                              for w in field['identifier'].replace('_', ' ').split()])
        field['title'] = title
        field['description'] = form.get('description') or None
        field['required'] = bool(form.get('required'))
        if field['type'] in (constants.TEXT, constants.LINE):
            try:
                maxlength = int(form.get('maxlength'))
                if maxlength <= 0: raise ValueError
            except (TypeError, ValueError):
                maxlength = None
            field['maxlength'] = maxlength

        elif field['type'] == constants.INTEGER:
            try:
                minimum = int(form.get('minimum'))
            except (TypeError, ValueError):
                minimum = None
            field['minimum'] = minimum
            try:
                maximum = int(form.get('maximum'))
            except (TypeError, ValueError):
                maximum = None
            field['maximum'] = maximum

        elif field['type'] == constants.FLOAT:
            try:
                minimum = float(form.get('minimum'))
            except (TypeError, ValueError):
                minimum = None
            field['minimum'] = minimum
            try:
                maximum = float(form.get('maximum'))
            except (TypeError, ValueError):
                maximum = None
            field['maximum'] = maximum

        elif field['type'] == constants.SCORE:
            try:
                minimum = int(form.get('minimum'))
            except (TypeError, ValueError):
                minimum = None
            try:
                maximum = int(form.get('maximum'))
            except (TypeError, ValueError):
                maximum = None
            if minimum is None or maximum is None or maximum <= minimum:
                raise ValueError('Invalid score range.')
            field['minimum'] = minimum
            field['maximum'] = maximum
            field['slider'] = utils.to_bool(form.get('slider'))

    def delete_field(self, fid):
        for pos, field in enumerate(self.doc['fields']):
            if field['identifier'] == fid:
                self.doc['fields'].pop(pos)
                break
        else:
            raise ValueError('No such submission field.')

    def add_evaluation_field(self, form=dict()):
        field = self.get_new_field(form=form)
        if field['identifier'] in [f['identifier'] for f in self.doc['evaluation']]:
            raise ValueError('Field identifier is already in use.')
        self.doc['evaluation'].append(field)

    def edit_evaluation_field(self, fid, form=dict()):
        for field in self.doc['evaluation']:
            if field['identifier'] == fid:
                self.update_field(field, form=form)
                break
        else:
            raise KeyError('No such evaluation field.')

    def delete_evaluation_field(self, fid):
        for pos, field in enumerate(self.doc['evaluation']):
            if field['identifier'] == fid:
                self.doc['evaluation'].pop(pos)
                break
        else:
            raise ValueError('No such evaluation field.')

    def add_document(self, infile, description):
        "Add a document."
        self.add_attachment(infile.filename,
                            infile.read(),
                            infile.mimetype)
        for document in self.doc['documents']:
            if document['name'] == infile.filename:
                document['description'] = description
                break
        else:
            self.doc['documents'].append({'name': infile.filename,
                                          'description': description})

    def delete_document(self, documentname):
        "Add the named document."
        for pos, document in enumerate(self.doc['documents']):
            if document['name'] == documentname:
                self.delete_attachment(documentname)
                self.doc['documents'].pop(pos)
                break


def get_call(cid):
    "Return the call with the given identifier."
    result = [r.doc for r in flask.g.db.view('calls', 'identifier',
                                             key=cid,
                                             include_docs=True)]
    if len(result) == 1:
        return set_call_cache(result[0])
    else:
        return None

def set_call_cache(call):
    """Set the 'cache' item of the call.
    This is computed data that will not be stored with the document.
    Depends on login, privileges, etc.
    """
    from anubis.submissions import get_submissions_count
    from anubis.evaluations import get_call_evaluations_count
    # XXX disallow even admin if open?
    call['cache'] = cache = dict(is_editable=flask.g.is_admin,
                                 is_reviewer=False)
    # Submissions count
    if flask.g.is_admin:
        cache['submissions_count'] = get_submissions_count(call=call)
        cache['is_reviewer'] = True
    if flask.g.current_user:
        cache['my_submissions_count'] = get_submissions_count(
            username=flask.g.current_user['username'], call=call)
        cache['is_reviewer'] = flask.g.current_user['username'] in call['reviewers']
        cache['evaluations_count'] = get_call_evaluations_count(call)
    # Open/closed status
    now = utils.normalized_local_now()
    if call['opens']:
        if call['opens'] > now:
            cache['is_open'] = False
            cache['is_closed'] = False
            cache['is_published'] = False
            cache['text'] = 'Not yet open.'
            cache['color'] = 'secondary'
        elif call['closes']:
            remaining = utils.days_remaining(call['closes'])
            if remaining > 7.0:
                cache['is_open'] = True
                cache['is_closed'] = False
                cache['is_published'] = True
                cache['text'] = f"{remaining:.0f} days remaining."
                cache['color'] = 'success'
            elif remaining > 2.0:
                cache['is_open'] = True
                cache['is_closed'] = False
                cache['is_published'] = True
                cache['text'] = f"{remaining:.0f} days remaining."
                cache['color'] = 'info'
            elif remaining >= 1.0:
                cache['is_open'] = True
                cache['is_closed'] = False
                cache['is_published'] = True
                cache['text'] = "Less than two days remaining."
                cache['color'] = 'warning'
            elif remaining >= 0.0:
                cache['is_open'] = True
                cache['is_closed'] = False
                cache['is_published'] = True
                cache['text'] = "Less than one day remaining."
                cache['color'] = 'danger'
            else:
                cache['is_open'] = False
                cache['is_closed'] = True
                cache['is_published'] = True
                cache['text'] = 'Closed.'
                cache['color'] = 'dark'
        else:
            cache['is_open'] = True
            cache['is_closed'] = False
            cache['is_published'] = True
            cache['text'] = 'Open with no closing date.'
            cache['color'] = 'success'
    else:
        if call['closes']:
            cache['is_open'] = False
            cache['is_closed'] = False
            cache['is_published'] = False
            cache['text'] = 'No open date set.'
            cache['color'] = 'secondary'
        else:
            cache['is_open'] = False
            cache['is_closed'] = False
            cache['is_published'] = False
            cache['text'] = 'No open or close dates set.'
            cache['color'] = 'secondary'
    return call
