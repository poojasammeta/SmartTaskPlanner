from flask import Flask, request, jsonify
from flask_cors import CORS
from planner import create_task_plan
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
load_dotenv()
import os

app = Flask(__name__)
CORS(app)

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["smart_task_planner"]
plans_collection = db["plans"]

def serialize_plan(plan):
    plan["_id"] = str(plan["_id"])
    return plan


@app.route("/generate-plan", methods=["POST"])
def generate_plan():
    data = request.get_json()
    goal = data.get("goal", "")
    if not goal:
        return jsonify({"error": "Goal is required"}), 400

    try:
        plan = create_task_plan(goal)

        
        result = plans_collection.insert_one({
            "goal": goal,
            "plan": plan
        })

        return jsonify({
            "message": "Plan generated and saved successfully",
            "plan_id": str(result.inserted_id),
            "plan": plan
        })
    except Exception:
       return jsonify({"error": "Server encountered an error. Please try again later."}), 500



@app.route("/plans", methods=["GET"])
def get_all_plans():
    plans = list(plans_collection.find())
    return jsonify([serialize_plan(p) for p in plans])


@app.route("/plan/<plan_id>", methods=["GET"])
def get_plan(plan_id):
    try:
        plan = plans_collection.find_one({"_id": ObjectId(plan_id)})
        if not plan:
            return jsonify({"error": "Plan not found"}), 404
        return jsonify(serialize_plan(plan))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)

