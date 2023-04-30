import joblib
from flask import Flask, send_from_directory, redirect, url_for, request

app = Flask(__name__)
model = joblib.load('../stacking_model.pkl')

@app.route("/predict", methods=['POST'])
def predict():
    # Get the data from the json
    district = request.json['district']
    status = request.json['status']
    balcony = int(request.json['balcony'])
    area_kitchen = int(request.json['area_kitchen'])
    area = int(request.json['area'])
    floor = int(request.json['floor'])
    age = request.json['age']
    
    prediction = model.predict([[district, status, balcony, area_kitchen, area, floor, age]])
    price = prediction[0].round(2)
    return {
        "price": price
    }


@app.route("/<path:path>")
def assets(path):
    return send_from_directory("assets", path)


@app.route("/")
def index():
    return redirect(url_for("assets", path="index.html"))
