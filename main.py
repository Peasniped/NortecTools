from flask import Flask, render_template
import backend, os

###  D E B U G  ###
debug = True
###################

try:
    tz_offset = os.environ['TZ_OFFSET']
except:
    tz_offset = 0

app = Flask(__name__)

time = backend.Tid(timezone_offset=tz_offset)
ladepris = backend.Ladepris(tids_objekt=time)

@app.route('/')
def index():
    ladepris.check_data_expired(debug=debug)

    return render_template('index.html', img_filename = ladepris.img_filename)

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")