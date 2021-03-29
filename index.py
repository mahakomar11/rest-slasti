from pymongo import MongoClient
from application.service import make_app

client = MongoClient('localhost', 27017)
db = client['slasti']
app = make_app(db)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
