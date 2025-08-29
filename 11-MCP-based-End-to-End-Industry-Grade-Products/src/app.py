from flask import Flask, jsonify
from dotenv import load_dotenv
import os
from pyngrok import ngrok
from flask_cors import CORS


load_dotenv()

NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")
print(NGROK_AUTH_TOKEN)

"""---API Setup Start---"""

app = Flask(__name__)
CORS(app)

@app.route("/api/hello", methods=["GET"])
def test_line():
    return jsonify(
        {
            "messages": "Hello from the Linux Machine."
        }
    )


if __name__ == "__main__":
    port = 7001
    os.environ["FLASK_ENV"] = "development"

    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    public_url = ngrok.connect(port)

    print(f"Public URL: {public_url}/api/hello\n\n")

    app.run(port=port)