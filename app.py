from flask import Flask, jsonify, request, render_template, send_file, send_from_directory, session, Markup, after_this_request, url_for
from io import BytesIO as IO
import gzip
import functools

from pybaseball.lahman import *
import pandas as pd

PITCHING_DATA = pitching()
BATTING_DATA = batting()
FIELDING_DATA = fielding()
TEAM_DATA = teams()

GROUPS = ['p', 'b', 'f']

app = Flask(__name__, static_url_path='/static')
app.config['HTML_FOLDER'] = 'templates/'
app.config['JS_FOLDER'] = 'js/'
app.config['CSS_FOLDER'] = 'css/'
app.config['IMAGE_FOLDER'] = 'images/'


def gzipped(f):
    @functools.wraps(f)
    def view_func(*args, **kwargs):
        @after_this_request
        def zipper(response):
            accept_encoding = request.headers.get('Accept-Encoding', '')

            if 'gzip' not in accept_encoding.lower():
                return response

            response.direct_passthrough = False

            if (response.status_code < 200 or
                response.status_code >= 300 or
                'Content-Encoding' in response.headers):
                return response
            gzip_buffer = IO()
            gzip_file = gzip.GzipFile(mode='wb',
                                      fileobj=gzip_buffer)
            gzip_file.write(response.data)
            gzip_file.close()

            response.data = gzip_buffer.getvalue()
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Vary'] = 'Accept-Encoding'
            response.headers['Content-Length'] = len(response.data)

            return response

        return f(*args, **kwargs)

    return view_func

def open_template(file):
    try:
        with open(file, 'r') as f:
            return Markup(f.read())
    except:
        return "Error loading template %s" % file

@app.route('/css/<path:filename>')
@gzipped
def css(filename):
    return send_from_directory(app.config['CSS_FOLDER'], filename)

@app.route('/js/<path:filename>')
@gzipped
def js(filename):
    return send_from_directory(app.config['JS_FOLDER'], filename)

@app.route('/groupinfo', methods=['POST'])
@gzipped
def groupinfo():
    if 'group' not in request.form:
        return 'Stat group not specified', 400
    group = request.form['group']
    if group not in GROUPS:
        return 'Invalid stat group', 400
    if group=='p':
        return jsonify(PITCHING_DATA.columns.values.tolist()[7:])
    if group=='b':
        return jsonify(BATTING_DATA.columns.values.tolist()[5:])
    if group=='f':
        return jsonify(FIELDING_DATA.columns.values.tolist()[6:])
    return 'Something went wrong', 400

@app.route('/')
@gzipped
def default():
    headers = open_template('templates/headers.html')
    top_bar = open_template('templates/top_bar.html')
    return render_template('index.html',
        headers=headers,
        top_bar=top_bar,
        stats=PITCHING_DATA.columns.values[7:]
    )

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
