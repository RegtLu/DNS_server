from flask import Flask, request, send_from_directory
import json

app = Flask(__name__)

@app.route('/api/add_A',methods=['POST'])
def add_A():
    domain = request.args.get('domain')
    ip = request.args.get('ip')
    return json.dumps({"status":'Success'}), 200, {"Content-Type":"application/json"}


@app.route('/api/add_CNAME',methods=['POST'])
def add_CNMAE():
    domain = request.args.get('domain')
    CNAME = request.args.get('CNAME')
    return json.dumps({"status":'Success'}), 200, {"Content-Type":"application/json"}

#@app.route('/api/delete_record',methods=['POST'])


@app.route('/api/dump_to_json',methods=['GET'])
def dump():
    directory='./'
    return send_from_directory(directory, path='dict.json', as_attachment=True)

#@app.route('/api/resolve',methods=['GET'])
#def resolve():


if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['JSON_AS_ASCII'] = False
    app.run(
        host='0.0.0.0',
        port=80
    )