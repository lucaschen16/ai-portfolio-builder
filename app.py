from dotenv import load_dotenv
from flask import Flask, render_template

from news_explainer import news_explainer_bp
from technical_analyst import technical_analyst_bp

load_dotenv()

app = Flask(__name__)
app.register_blueprint(news_explainer_bp)
app.register_blueprint(technical_analyst_bp)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/class2")
def class2():
    return render_template("class2.html")


@app.get("/class3")
def class3():
    return render_template("class3.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
