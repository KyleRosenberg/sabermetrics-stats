from flask import Flask, jsonify, request, render_template, send_file, send_from_directory, session, Markup, after_this_request
from io import BytesIO as IO
import gzip
import functools

app = Flask(__name__)
app.config['TESTING'] = True
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

@app.route('/css/<path:filename>')
def css(filename):
    return send_from_directory(app.config['CSS_FOLDER'], filename)

@app.route('/js/<path:filename>')
def js(filename):
    return send_from_directory(app.config['JS_FOLDER'], filename)

@app.route('/')
@gzipped
def default():
    headers = ""
    with open('templates/headers.html', 'r') as f:
        headers = f.read()
    if headers=="":
        return "Something went wrong"
    return render_template('index.html',
        headers=Markup(headers)
    )

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
