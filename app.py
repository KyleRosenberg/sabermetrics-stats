from flask import Flask, jsonify, request, render_template, send_file, send_from_directory, session, Markup, after_this_request, url_for, Response
from io import BytesIO as IO
import gzip
import functools
import json
import re
import base64
import io

from pybaseball.lahman import *
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import pandas as pd

def rightData(df):
    dfRet = df.loc[df['yearID']>2006].dropna()
    return dfRet

PITCHING_DATA = rightData(pitching())
BATTING_DATA = rightData(batting())
FIELDING_DATA = rightData(fielding())
TEAM_DATA = rightData(teams())

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

@app.route('/visualize', methods=['POST'])
@gzipped
def visualize():
    if 'group' not in request.form:
        return 'Stat group not specified', 400
    group = request.form['group']
    if group not in GROUPS:
        return 'Invalid stat group', 400
    if 'equation' not in request.form:
        return 'Equation not provided', 400
    equation = request.form['equation']
    if 'name' not in request.form:
        return 'Stat name not provided', 400
    name = request.form['name']
    dfStats = buildDataframe(json.loads(equation), group, name)
    dist = getDistribution(dfStats, name)
    return render_template('visualize.html', result=dist.decode('utf8'))

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

def calculateNewStat(df, equation, name):
    numerator = []
    denominator = []
    for e in equation.keys():
        nums = equation[e]
        if nums[1]>0:
            numerator.append(e)
        else:
            denominator.append(e)
    if len(numerator)==0:
        df['Numerator'] = 1
    else:
        df['Numerator'] = df[numerator].sum(axis=1)
    if len(denominator)==0:
        df['Denominator'] = 1
    else:
        df['Denominator'] = df[denominator].sum(axis=1)
    df[name] = df['Numerator']/df['Denominator']
    return df

def buildDataframe(equation, group, name):
    df = None
    if group=='p':
        df = PITCHING_DATA
    if group=='b':
        df = BATTING_DATA
    if group=='f':
        df = FIELDING_DATA
    dfStats = pd.DataFrame(columns=[e for e in equation.keys()])
    for e in equation.keys():
        sname = re.sub(r'\d+$', '', e)
        nums = equation[e]
        dfStats[e] = nums[0] * (df[sname]**abs(nums[1]))
    dfRet = calculateNewStat(dfStats, equation, name)
    return dfRet

def getDistribution(df, name):
    plt.hist(df[name], density=True)
    plt.title('Custom Stat: ' + name)
    plt.ylabel('Frequency')
    plt.xlabel('Stat Value')

    from io import BytesIO
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)  # rewind to beginning of file
    import base64
    #figdata_png = base64.b64encode(figfile.read())
    figdata_png = base64.b64encode(figfile.getvalue())
    plt.clf()
    return figdata_png

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
