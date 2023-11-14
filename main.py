from flask import Flask, render_template
import backend, os

try:
    tz_offset = int(os.environ['TZ_OFFSET'])
    debug     = bool(os.environ['DEBUG_MSG'])
except:
    tz_offset = 0
    debug     = False

debug = True

app = Flask(__name__)

time = backend.Tid(timezone_offset=tz_offset)
ladepris = backend.Ladepris(tids_objekt=time)

backend.delete_old_pngs()
print(f"DEBUG: LeafTools debug messages are {'active' if debug else 'deactivated'}!")

@app.after_request
def after_request(response):
    seconds_to_next_hour = time.get_time()["s_to_next_hr"]
    response.headers["Cache-Control"] = f"max-age={seconds_to_next_hour}"
    if debug: print("Seconds to next hour:", seconds_to_next_hour)
    return response

@app.route('/')
def index():
    ladepris.check_data_expired(debug=debug)
    return render_template('index.html', img_filename = ladepris.img_filename)

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0")