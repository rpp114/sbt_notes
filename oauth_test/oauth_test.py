import datetime, pytz

import flask
import httplib2

from apiclient import discovery
from oauth2client import client

app = flask.Flask(__name__)

@app.route('/')
def index():
    print('session params: ', flask.session)
    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('oauth2callback'))
    credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])
    if credentials.access_token_expired:
        return flask.redirect(flask.url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http_auth)
        calendar = service.calendars().get(calendarId='primary').execute()
        d = datetime.datetime.now()

        d_tz = d.replace(tzinfo=pytz.timezone('US/Pacific'))

        tomorrow = d_tz + datetime.timedelta(days=1)

        eventsResults = service.events().list(calendarId='primary', timeMin=d_tz.isoformat(), timeMax=tomorrow.isoformat()).execute()
        # print('results: ', eventsResults)
        # events = eventsResults.get('items', [])
        # print('events: ', events)
        return flask.jsonify(eventsResults.get('items'))

@app.route('/oauth2callback')
def oauth2callback():
    print('args: ', flask.request.args)
    flow = client.flow_from_clientsecrets('/home/ray/coding/sbt_notes/sbt_notes_access.json',
            scope='https://www.googleapis.com/auth/calendar.readonly',
            redirect_uri=flask.url_for('oauth2callback', _external=True))

    # flow.params['include_granted_scopes']='true'

    if 'code' not in flask.request.args:
        auth_uri = flow.step1_get_authorize_url()
        return flask.redirect(auth_uri)
    else:
        auth_code = flask.request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        flask.session['credentials'] = credentials.to_json()
        return flask.redirect(flask.url_for('index'))

if __name__ == '__main__':
    import uuid
    app.secret_key = str(uuid.uuid4())
    app.debug = False
    app.run()
