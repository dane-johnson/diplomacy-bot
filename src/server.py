from flask import Flask, request
app = Flask(__name__)

@app.route("/")
def hello():
  return "Hello World"

@app.route("/event", methods=['POST'])
def returnRequestChallenge():
	print request.get_json()
	return request.get_json()['challenge']

if __name__ == '__main__':
  app.run('0.0.0.0', port=80)
