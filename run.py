from backend.app import app
from waitress import serve

if __name__ == "__main__":
    print(f"Started at host 127.0.0.1:5000")
    serve(app, host="127.0.0.1", port=5000)