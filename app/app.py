import logging.config
import configparser
import os
import base64

import flask
import flask_session
import flask_wtf.csrf
import waitress
import spotipy
import wtforms

# App Configuration
config = configparser.ConfigParser()

dev = False
if 'env' in os.environ:
    dev = os.environ['env'] == 'DEV'

if dev:
    config.read("config-dev.ini")
else:
    config.read("config.ini")

LOG_PATH = config['LOGGING']['PATH']
LOG_LEVEL = config['LOGGING']['LEVEL']
LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'

DATABASE_PATH = config['DATABASE']['PATH']

PORT = config['NETWORK']['PORT']

SCOPES = config["SPOTIFY"]["SCOPES"]

TEMPLATES_PATH = config['FLASK']['TEMPLATES']
SESSION_SECRET = config['FLASK']['SECRET']
SESSION_PATH = config['FLASK']['SESSION_PATH']

# Logging Setup

logging.config.dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': LOG_FORMAT,
    }},
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        'file': {
            'class' : 'logging.FileHandler',
            'filename': LOG_PATH,
            'encoding': 'utf-8',
            'formatter': 'default'
        }
    },
    'root': {
        'level': LOG_LEVEL,
        'handlers': ['wsgi', 'file']
    }
})

import db
import user_pages

app = flask.Flask(__name__, static_url_path='', static_folder='static')
app.register_blueprint(user_pages.user)

csrf = flask_wtf.csrf.CSRFProtect()
csrf.init_app(app)

app.logger.info(f"Selected ENV: {os.environ['env']}")

# Session Setup
app.config['SECRET_KEY'] = base64.b64decode(SESSION_SECRET)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = SESSION_PATH
flask_session.Session(app)



class SettingsForm(flask_wtf.FlaskForm):
    checkbox = wtforms.BooleanField('Public')




@app.route('/')
def root():

    auth_manager = spotipy.oauth2.SpotifyOAuth(scope=SCOPES, show_dialog=True)

    # Being redirected from Spotify auth page
    if flask.request.args.get("code"):
        auth_manager.get_access_token(flask.request.args.get("code"))

        # Get user info
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        user_info = spotify.me()

        flask.session["user"] = user_info
        flask.session["api"] = spotify

        # if user is not in database
        if not db.user_exists(user_info['id']):

            print("User not in database, adding...")

            # Save token for use in tracking container
            cache_handler = spotipy.CacheFileHandler(cache_path=f"data/.{user_info['id']}-cache")
            cache_handler.save_token_to_cache(auth_manager.get_cached_token())

            # Add user to database
            db.add_user(user_info['display_name'], user_info['id'])

        return flask.redirect('/')

    if 'user' not in flask.session:
        auth_url = auth_manager.get_authorize_url()

        return flask.render_template('login_index.html', auth_url=auth_url)

    else:
        user_id = db.get_user_id(flask.session['user']['id'])

        print(f'redirect to /{user_id}/')
        return flask.redirect(f'/{user_id}/')

@app.route('/settings/')
def settings():

    form = SettingsForm()

    if 'user' in flask.session:
        display_name = flask.session['user']['display_name']
        user_pfp_url = flask.session['user']['images'][0]['url']
    else:
        return flask.redirect('/')

    return flask.render_template('user_settings.html',
                                 display_name=display_name,
                                 user_pfp_url=user_pfp_url,
                                 form=form)

@app.route('/settings/save/', methods=['POST'])
def settings_save():
    form = SettingsForm(csrf_enabled=True)

    user_spotify_id = flask.session['user']['id']

    db.update_public(user_spotify_id, form.checkbox.data)

    return flask.redirect('/settings/')

@app.route('/logout/')
def logout():
    if 'user' in flask.session:
        flask.session.pop('user')
    if 'api' in flask.session:
        flask.session.pop('api')
    return flask.redirect('/')

@app.route('/db/')
def database():
    return flask.send_file(DATABASE_PATH)

@app.route('/health')
def health():
    app.logging.info('Health Endpoint Accessed')
    return 'healthy for now :)'

if __name__ == '__main__':
    waitress.serve(app, host='0.0.0.0', port=PORT)
