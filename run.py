from backend.app import app
from waitress import serve

if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=5000, threads=6, url_scheme='http')
    serve(app, host="127.0.0.1", port=5000)