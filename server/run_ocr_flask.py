import json
import os
import yaml

from flask import Flask
from flask import request
from authenticate_process import authentication

authenticate = authentication()
work_bash = os.path.dirname(__file__)
send_back_dicts = {"status_code": 0, "result": {}, "tips": ""}
app = Flask(__name__)


def load_configs():
    f1 = open(os.path.join(work_bash, "configs.yaml"), encoding="utf-8")
    context = f1.read()
    dicts = yaml.load(context, yaml.FullLoader)
    return dicts


config_tips = load_configs()


@app.route('/ocr', methods=['GET', 'POST'])
def get_request():
    if request.method == "GET":
        return b"please use post method to access!"
    else:
        request_data = json.loads(request.get_data(as_text=True))
        result, status_code = authenticate.check_information(request_data)
        send_back_dicts["status_code"] = status_code
        send_back_dicts["result"] = result
        send_back_dicts["tips"] = config_tips[status_code]
        # print(json.dumps(send_back_dicts, indent=1))
        return json.dumps(send_back_dicts).encode()


if __name__ == "__main__":
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run()



