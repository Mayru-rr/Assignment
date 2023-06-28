from flask import *
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"
DATABASE = "database.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.execute(
            "CREATE TABLE IF NOT EXISTS auth (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS customer (id INTEGER PRIMARY KEY, order_date TEXT, company TEXT, owner TEXT, item TEXT, quantity INTEGER, weight REAL, request_for_shipment TEXT, shipment_size TEXT, box_count INTEGER, specification TEXT, checklist_quantity TEXT, customer_id INTEGER)"
        )
        dummy_auth_data = [
            ("admin", "admin", "admin"),
            ("customer1", "customer1", "customer"),
            ("customer2", "customer2", "customer"),
        ]
        for auth in dummy_auth_data:
            cursor = db.execute("SELECT id FROM auth WHERE username = ?", (auth[0],))
            data = cursor.fetchone()
            if data is None:
                db.execute(
                    "INSERT INTO auth (username, password, role) VALUES (?, ?, ?)", auth
                )
        db.commit()
    return db


@app.teardown_appcontext
def close_db(error):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def validate_fields(
    order_date,
    company,
    owner,
    item,
    quantity,
    weight,
    request_for_shipment,
    shipment_size,
    box_count,
    specification,
    checklist_quantity,
):
    errors = []
    return errors


@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        connection = get_db()
        cursor = connection.execute(
            "SELECT role FROM auth WHERE username = ? AND password = ?",
            (username, password),
        )
        data = cursor.fetchone()
        if data:
            session["username"] = username
            session["role"] = data[0]
            return redirect("/dashboard")
        error = "Invalid credentials. Please try again."
        return render_template("login.html", error=error)
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "username" in session:
        if session["role"] == "admin":
            connection = get_db()
            cursor = connection.execute(
                "SELECT customer_id, SUM(quantity), SUM(weight), SUM(box_count) FROM customer GROUP BY customer_id"
            )
            customers = cursor.fetchall()
            customer1_quantity = 0
            customer2_quantity = 0
            customer1_weight = 0
            customer2_weight = 0
            customer1_box_count = 0
            customer2_box_count = 0
            for customer in customers:
                if customer[0] == "customer1":
                    customer1_quantity = customer[1]
                    customer1_weight = customer[2]
                    customer1_box_count = customer[3]
                elif customer[0] == "customer2":
                    customer2_quantity = customer[1]
                    customer2_weight = customer[2]
                    customer2_box_count = customer[3]
            total_quantity = customer1_quantity + customer2_quantity
            total_weight = customer1_weight + customer2_weight
            total_box_count = customer1_box_count + customer2_box_count
            return render_template(
                "admin.html",
                customer1_quantity=customer1_quantity,
                customer2_quantity=customer2_quantity,
                total_quantity=total_quantity,
                customer1_weight=customer1_weight,
                customer2_weight=customer2_weight,
                total_weight=total_weight,
                customer1_box_count=customer1_box_count,
                customer2_box_count=customer2_box_count,
                total_box_count=total_box_count,
            )
        return render_template("customer.html")
    return redirect("/login")


@app.route("/submit", methods=["POST"])
def submit():
    if "username" in session:
        if session["role"] == "customer":
            order_date = request.form["order_date"]
            company = request.form["company"]
            owner = request.form["owner"]
            item = request.form["item"]
            quantity = request.form["quantity"]
            weight = request.form["weight"]
            request_for_shipment = request.form["request_for_shipment"]
            shipment_size = request.form["shipment_size"]
            box_count = request.form["box_count"]
            specification = request.form["specification"]
            checklist_quantity = request.form["checklist_quantity"]
            customer_id = session["username"]
            errors = validate_fields(
                order_date,
                company,
                owner,
                item,
                quantity,
                weight,
                request_for_shipment,
                shipment_size,
                box_count,
                specification,
                checklist_quantity,
            )
            if errors:
                return render_template("customer.html", errors=errors)
            connection = get_db()
            connection.execute(
                "INSERT INTO customer (order_date, company, owner, item, quantity, weight, request_for_shipment, shipment_size, box_count, specification, checklist_quantity, customer_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    order_date,
                    company,
                    owner,
                    item,
                    quantity,
                    weight,
                    request_for_shipment,
                    shipment_size,
                    box_count,
                    specification,
                    checklist_quantity,
                    customer_id,
                ),
            )
            connection.commit()
            return redirect("/dashboard")
    return redirect("/login")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
