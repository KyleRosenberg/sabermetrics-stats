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
from scipy.stats import linregress

def rightData(df, group=None):
    dfRet = df.loc[df['yearID']>=2014].dropna()
    if group=='p':
        dfRet['FIP'] = (13*dfRet['HR'] + 3*(dfRet['BB']+dfRet['IBB']) - 2*dfRet['SO'])/(dfRet['IPouts']/3) + 3.2
    if group=='b':
        dfRet['1B'] = dfRet['H'] - dfRet['2B'] - dfRet['3B'] - dfRet['HR']
        dfRet['wOBA'] = (0.69*(dfRet['BB']-dfRet['IBB']) + 0.72*dfRet['HBP'] + 0.89*dfRet['1B'] + 1.27*dfRet['2B'] + 1.62*dfRet['3B'] + 2.1*dfRet['HR'])/(dfRet['AB']+dfRet['BB']-dfRet['IBB']+dfRet['SF']+dfRet['HBP'])
    if group=='t':
        dfRet = dfRet[['teamID', 'yearID', 'W']]
    return dfRet

PITCHING_DATA = rightData(pitching(), 'p')
BATTING_DATA = rightData(batting(), 'b')
TEAM_DATA = rightData(teams(), 't')

GROUPS = ['p', 'b']

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
    equation = json.loads(request.form['equation'])
    if 'name' not in request.form:
        return 'Stat name not provided', 400
    name = request.form['name']
    if 'customs' not in request.form:
        return 'Custom stat equations not provided (can be empty)', 400
    customs = json.loads(request.form['customs'])
    names = []
    try:
        dfStats, names = buildDataframe(equation, group, name, customs)
    except ValueError as e:
        return str(e), 400
    dist = getDistribution(dfStats, names)
    corrs = getCorrelations(dfStats, names)
    resid = getResiduals(dfStats, names, corrs)
    return render_template('visualize.html', result=dist.decode('utf8'), residuals=resid.decode('utf8'))

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

def getCorrelations(df, names):
    corrs = []
    x_name = names[0]
    y_names = names[1:]
    for n in y_names:
        corrs.append({'name':n, 'val':df[x_name].corr(df[n])})
    return corrs

def calculateNewStat(df, equation, name, constant):
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
    df[name] = (df['Numerator']/df['Denominator'])+constant
    return df

def hasAllStats(df, equation):

    for e in equation.keys():
        if e=="const":
            continue
        sname = re.sub(r'\d+$', '', e)
        if not sname in df.columns.values:
            return False
    return True

def calculateCustomStats(df, equation, customs, all_stats):
    leftover_stats = []
    for s in list(customs.keys()):
        sname = re.sub(r'\d+$', '', s)
        if sname in customs:
            new_equation = customs[sname]
            if hasAllStats(df, new_equation):
                constant = new_equation.pop('const')
                df, as_temp = calculateStatMods(df, new_equation, list(new_equation.keys()))
                if len(as_temp)>0:
                    pass#This probably shouldn't happen.. raise error?
                df = calculateNewStat(df, new_equation, s, constant)
            else:
                leftover_stats.append(s)
        else:
            pass#This probably shouldn't happen.. raise error?
    return df, leftover_stats

def calculateStatMods(df, equation, all_stats):
    for i in range(len(all_stats)-1, -1, -1):
        e = all_stats[i]
        sname = re.sub(r'\d+$', '', e)
        if sname in df:
            all_stats.pop(i)
            nums = equation[e]
            df[e] = nums[0] * (df[sname]**abs(nums[1]))
    return df, all_stats

def buildDataframe(equation, group, name, customs):
    constant = equation.pop('const')
    df = None
    names = [name]
    if group=='p':
        df = PITCHING_DATA.copy(True)
        names.append('FIP')
    if group=='b':
        df = BATTING_DATA.copy(True)
        names.append('wOBA')

    all_stats = list(equation.keys())
    #Calculate the stats we know
    dfStats, all_stats = calculateStatMods(df, equation, all_stats)
    #Calculate saved custom stats
    l = len(all_stats)
    while (l>0):
        dfStats, all_stats = calculateCustomStats(dfStats, equation, customs, all_stats)
        #TODO: Come up with some way to determine if there are missing stats
        l = len(all_stats)
    #Calculate the stats we know again, should return empty all_stats
    all_stats = list(equation.keys())
    dfStats, all_stats = calculateStatMods(df, equation, all_stats)
    if len(all_stats)>0:
        pass#Throw error?
    #Calculate new custom stat
    dfRet = calculateNewStat(dfStats, equation, name, constant)
    #Remove outliers
    dfNoOutliers = dfRet[(dfRet[name]<dfRet[name].quantile(0.95))&(dfRet[name]>dfRet[name].quantile(0.05))]
    return dfNoOutliers, names

def getDistribution(df, names):
    plt.clf()
    for n in names:
        a = 1/len(names)/2
        if n==names[0]:
            a = 1
        plt.hist(df[n], density=True, alpha=a, label=n)
    dfTeams = TEAM_DATA.copy(True)
    dfTeams['W_normalized'] = (df[names[0]].max()-df[names[0]].min())*(dfTeams['W']-dfTeams['W'].min())/(dfTeams['W'].max() - dfTeams['W'].min())
    plt.hist(dfTeams['W_normalized'], density=True, alpha=1/len(names)/2, label='Team Wins (Normalized)')
    plt.title(names[0] + ' Distribution')
    plt.ylabel('Relative Frequency')
    plt.xlabel('Stat Value')
    plt.legend()

    ret = getPlotPic()
    plt.clf()
    return ret

def getResiduals(df, names, corrs):
    if len(names)<2:
        raise ValueError('Must have at least 2 columns to compare')
    plt.clf()
    x_name = names[0]
    for c in corrs:
        plt.scatter(df[x_name], df[c['name']], alpha=1/len(corrs)/2, label=(c['name'] + ': %.3f' % c['val']))
        slope, intercept, r_value, p_value, std_err = linregress(df[x_name], df[c['name']])
        plt.plot(df[x_name], intercept + slope*df[x_name], label=c['name'] + ' Best Fit')
    comb = pd.merge(TEAM_DATA, df.groupby(['yearID', 'teamID']).mean(), on=['yearID', 'teamID'])
    if 'W' in df.columns.values:
        comb['W'] = comb['W_x']
    comb['W_normalized'] = (df[x_name].max()-df[x_name].min())*(comb['W']-comb['W'].min())/(comb['W'].max() - comb['W'].min())
    plt.scatter(comb[x_name], comb['W_normalized'], alpha=1/len(corrs)/2, label=('Team Wins (Normalized): %.3f' % comb[x_name].corr(comb['W_normalized'])))
    slope, intercept, r_value, p_value, std_err = linregress(comb[x_name], comb['W_normalized'])
    plt.plot(comb[x_name], intercept + slope*comb[x_name], label='Wins Best Fit')
    plt.xlabel(names[0] + ' Value')
    plt.ylabel('Comparison Stat Values')
    plt.title(names[0] + ' Correlation')
    plt.legend()

    ret = getPlotPic()
    plt.clf()
    return ret

def getPlotPic():
    from io import BytesIO
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    import base64
    figdata_png = base64.b64encode(figfile.getvalue())
    return figdata_png

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
