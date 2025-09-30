from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/odds")
def get_odds():
    # Simulação de odds em tempo real
    data = {
        "match": "Team A vs Team B",
        "markets": [
            {"type": "1x2", "odds": {"1": 2.1, "X": 3.2, "2": 3.5}},
            {"type": "over/under", "odds": {"over 2.5": 1.9, "under 2.5": 1.95}}
        ]
    }
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
