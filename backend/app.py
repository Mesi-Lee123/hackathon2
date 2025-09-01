from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL
from openai import OpenAI
import os

# Initialize Flask
app = Flask(__name__)
CORS(app)  # Allow all origins

# MySQL config
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "recipe"

mysql = MySQL(app)

# OpenAI client (using GitHub Models API)
client = OpenAI(
    base_url="https://models.github.ai/inference",
    api_key="",
)


@app.route("/")
def home():
    return jsonify({"message": "Welcome to Flask + OpenAI API!"})


# ✅ Get all recipes from DB
@app.route("/getrecipe", methods=["GET"])
def get_recipe():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, ingredients, recipe FROM my_recipe")
        rows = cur.fetchall()
        cur.close()

        recipes = []
        for row in rows:
            # Convert bytes → string if needed
            recipe_data = row[2]
            if isinstance(recipe_data, bytes):
                recipe_data = recipe_data.decode("utf-8")

            recipes.append({
                "id": row[0],
                "ingredients": row[1],
                "recipe": recipe_data
            })

        return jsonify({"recipes": recipes})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ✅ Generate a recipe with AI and save it in DB
@app.route("/recipe", methods=["POST"])
def recipe():
    try:
        data = request.get_json()
        ingredients = data.get("ingredients", "")

        if not ingredients:
            return jsonify({"error": "Ingredients field is required"}), 400

        prompt_messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful AI recipe generator. "
                "Always respond with a single paragraph of text only. "
                "Do not include explanations, comments, or code fences."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Using the following ingredients: {ingredients}, "
                "write a simple recipe in paragraph form. "
                "Keep it concise, step-by-step, but written as a single flowing paragraph. "
                "Return only the paragraph, nothing else."
            ),
        },
    ]




        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=prompt_messages,
            max_tokens=1000,
            temperature=0.9,
        )

        recipe_text = response.choices[0].message.content

        # Save into DB
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO my_recipe (ingredients, recipe) VALUES (%s, %s)",
            (ingredients, recipe_text),
        )
        mysql.connection.commit()
        cur.close()

        return jsonify({"recipe": recipe_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)

