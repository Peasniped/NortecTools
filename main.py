from flask import Flask, render_template
import backend, os

try:
    tz_offset = int(os.environ['TZ_OFFSET'])
    debug     = bool(os.environ['DEBUG_MSG'])
except:
    tz_offset = 0
    debug     = False

app = Flask(__name__)

time = backend.Tid(timezone_offset=tz_offset)
ladepris = backend.Ladepris(tids_objekt=time)

backend.delete_old_pngs()

@app.route('/')
def index():
    ladepris.check_data_expired(debug=debug)
    return render_template('index.html', img_filename = ladepris.img_filename)

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")