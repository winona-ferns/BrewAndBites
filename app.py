from flask import Flask, render_template, request, redirect, session
import mysql.connector
import json
from dotenv import load_dotenv
import os

# Load database settings
load_dotenv()

app = Flask(__name__)
app.secret_key = "brew-and-bites-secret-key"


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    return connection


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username = %s
            AND password = %s
            """,
            (username, password)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect("/dashboard")

        else:
            return "Invalid username or password"

    return render_template("login.html")


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Today's sales
    cursor.execute(
        """
        SELECT COALESCE(SUM(total), 0) AS sales
        FROM orders
        WHERE DATE(order_date) = CURDATE()
        """
    )

    today_sales = cursor.fetchone()["sales"]

    # Today's orders
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM orders
        WHERE DATE(order_date) = CURDATE()
        """
    )

    today_orders = cursor.fetchone()["total"]

    # Total menu items
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM menu_items
        """
    )

    menu_count = cursor.fetchone()["total"]

    # Low stock items
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM menu_items
        WHERE stock <= low_stock_limit
        """
    )

    low_stock = cursor.fetchone()["total"]

    # Recent orders
    cursor.execute(
        """
        SELECT
            orders.id,
            orders.total,
            orders.status,
            orders.order_date,
            customers.name AS customer_name
        FROM orders
        LEFT JOIN customers
            ON orders.customer_id = customers.id
        ORDER BY orders.order_date DESC
        LIMIT 5
        """
    )

    recent_orders = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        today_sales=today_sales,
        today_orders=today_orders,
        menu_count=menu_count,
        low_stock=low_stock,
        recent_orders=recent_orders
    )


# --------------------------------------------------
# MENU MANAGEMENT
# --------------------------------------------------

@app.route("/menu")
def menu():

    if "user_id" not in session:
        return redirect("/")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM menu_items
        ORDER BY id DESC
        """
    )

    menu_items = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "menu.html",
        menu_items=menu_items
    )


# --------------------------------------------------
# ADD MENU ITEM
# --------------------------------------------------

@app.route("/menu/add", methods=["POST"])
def add_menu():

    if "user_id" not in session:
        return redirect("/")

    name = request.form["name"]
    category = request.form["category"]
    price = request.form["price"]
    stock = request.form["stock"]
    low_stock_limit = request.form["low_stock_limit"]

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO menu_items
        (
            name,
            category,
            price,
            stock,
            low_stock_limit,
            available
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            TRUE
        )
        """,
        (
            name,
            category,
            price,
            stock,
            low_stock_limit
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/menu")


# --------------------------------------------------
# EDIT MENU ITEM
# --------------------------------------------------

@app.route("/menu/edit/<int:item_id>", methods=["GET", "POST"])
def edit_menu(item_id):

    if "user_id" not in session:
        return redirect("/")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        name = request.form["name"]
        category = request.form["category"]
        price = request.form["price"]
        stock = request.form["stock"]
        low_stock_limit = request.form["low_stock_limit"]

        cursor.execute(
            """
            UPDATE menu_items
            SET
                name = %s,
                category = %s,
                price = %s,
                stock = %s,
                low_stock_limit = %s
            WHERE id = %s
            """,
            (
                name,
                category,
                price,
                stock,
                low_stock_limit,
                item_id
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect("/menu")

    cursor.execute(
        """
        SELECT *
        FROM menu_items
        WHERE id = %s
        """,
        (item_id,)
    )

    item = cursor.fetchone()

    cursor.close()
    connection.close()

    if item is None:
        return "Menu item not found"

    return render_template(
        "edit_menu.html",
        item=item
    )


# --------------------------------------------------
# DELETE MENU ITEM
# --------------------------------------------------

@app.route("/menu/delete/<int:item_id>", methods=["POST"])
def delete_menu(item_id):

    if "user_id" not in session:
        return redirect("/")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM menu_items
        WHERE id = %s
        """,
        (item_id,)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/menu")


# --------------------------------------------------
# POS / NEW ORDER
# --------------------------------------------------

@app.route("/pos")
def pos():

    if "user_id" not in session:
        return redirect("/")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get available menu items
    cursor.execute(
        """
        SELECT *
        FROM menu_items
        WHERE available = TRUE
        AND stock > 0
        ORDER BY name
        """
    )

    menu_items = cursor.fetchall()

    # Get customers
    cursor.execute(
        """
        SELECT *
        FROM customers
        ORDER BY name
        """
    )

    customers = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "pos.html",
        menu_items=menu_items,
        customers=customers
    )


# --------------------------------------------------
# PLACE ORDER
# --------------------------------------------------

@app.route("/order/place", methods=["POST"])
def place_order():

    if "user_id" not in session:
        return redirect("/")

    customer_id = request.form.get("customer_id")
    cart_data = request.form.get("cart")

    if not cart_data:
        return "Cart is empty"

    cart = json.loads(cart_data)

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # Calculate subtotal
        subtotal = 0

        for item in cart:
            subtotal = subtotal + (
                float(item["price"]) *
                int(item["quantity"])
            )

        # Calculate GST
        gst = subtotal * 0.05

        # Calculate grand total
        total = subtotal + gst

        # Save order
        cursor.execute(
            """
            INSERT INTO orders
            (
                customer_id,
                subtotal,
                gst,
                total,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                'Pending'
            )
            """,
            (
                customer_id if customer_id else None,
                subtotal,
                gst,
                total
            )
        )

        # Get newly created order ID
        order_id = cursor.lastrowid

        # Save order items and reduce stock
        for item in cart:

            item_id = int(item["id"])
            quantity = int(item["quantity"])
            price = float(item["price"])

            # Check stock
            cursor.execute(
                """
                SELECT stock
                FROM menu_items
                WHERE id = %s
                """,
                (item_id,)
            )

            result = cursor.fetchone()

            if result is None:
                raise Exception("Menu item not found")

            current_stock = result[0]

            if current_stock < quantity:
                raise Exception(
                    "Not enough stock for " +
                    item["name"]
                )

            # Insert order item
            cursor.execute(
                """
                INSERT INTO order_items
                (
                    order_id,
                    menu_item_id,
                    quantity,
                    price
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    order_id,
                    item_id,
                    quantity,
                    price
                )
            )

            # Reduce stock
            cursor.execute(
                """
                UPDATE menu_items
                SET stock = stock - %s
                WHERE id = %s
                """,
                (
                    quantity,
                    item_id
                )
            )

        connection.commit()

    except Exception as error:

        connection.rollback()

        return "Could not place order: " + str(error)

    finally:

        cursor.close()
        connection.close()

    return redirect("/orders")


# --------------------------------------------------
# ORDER MANAGEMENT
# --------------------------------------------------

@app.route("/orders")
def orders():

    if "user_id" not in session:
        return redirect("/")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            orders.id,
            orders.order_date,
            orders.subtotal,
            orders.gst,
            orders.total,
            orders.status,
            customers.name AS customer_name
        FROM orders
        LEFT JOIN customers
            ON orders.customer_id = customers.id
        ORDER BY orders.order_date DESC
        """
    )

    orders = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "orders.html",
        orders=orders
    )


# --------------------------------------------------
# UPDATE ORDER STATUS
# --------------------------------------------------

@app.route("/order/status/<int:order_id>", methods=["POST"])
def update_order_status(order_id):

    if "user_id" not in session:
        return redirect("/")

    status = request.form["status"]

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE orders
        SET status = %s
        WHERE id = %s
        """,
        (status, order_id)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/orders")


# --------------------------------------------------
# BILL / RECEIPT
# --------------------------------------------------

@app.route("/bill/<int:order_id>")
def bill(order_id):

    if "user_id" not in session:
        return redirect("/")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get order details
    cursor.execute(
        """
        SELECT
            orders.id,
            orders.order_date,
            orders.subtotal,
            orders.gst,
            orders.total,
            orders.status,
            customers.name AS customer_name,
            customers.phone AS customer_phone
        FROM orders
        LEFT JOIN customers
            ON orders.customer_id = customers.id
        WHERE orders.id = %s
        """,
        (order_id,)
    )

    order = cursor.fetchone()

    if order is None:

        cursor.close()
        connection.close()

        return "Order not found"

    # Get items in the order
    cursor.execute(
        """
        SELECT
            menu_items.name,
            order_items.quantity,
            order_items.price
        FROM order_items
        JOIN menu_items
            ON order_items.menu_item_id = menu_items.id
        WHERE order_items.order_id = %s
        """,
        (order_id,)
    )

    items = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "bill.html",
        order=order,
        items=items
    )


# --------------------------------------------------
# INVENTORY MANAGEMENT
# --------------------------------------------------

@app.route("/inventory")
def inventory():

    if "user_id" not in session:
        return redirect("/")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM menu_items
        ORDER BY name
        """
    )

    items = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "inventory.html",
        items=items
    )


# --------------------------------------------------
# UPDATE STOCK
# --------------------------------------------------

@app.route("/inventory/update/<int:item_id>", methods=["POST"])
def update_stock(item_id):

    if "user_id" not in session:
        return redirect("/")

    stock = request.form["stock"]

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE menu_items
        SET stock = %s
        WHERE id = %s
        """,
        (stock, item_id)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/inventory")


# --------------------------------------------------
# CUSTOMER MANAGEMENT
# --------------------------------------------------

@app.route("/customers")
def customers():

    if "user_id" not in session:
        return redirect("/")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM customers
        ORDER BY name
        """
    )

    customers = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "customers.html",
        customers=customers
    )


# --------------------------------------------------
# ADD CUSTOMER
# --------------------------------------------------

@app.route("/customers/add", methods=["POST"])
def add_customer():

    if "user_id" not in session:
        return redirect("/")

    name = request.form["name"]
    phone = request.form["phone"]
    email = request.form["email"]

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO customers
            (
                name,
                phone,
                email
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
            """,
            (
                name,
                phone,
                email
            )
        )

        connection.commit()

    except Exception as error:

        connection.rollback()

        return "Could not add customer: " + str(error)

    finally:

        cursor.close()
        connection.close()

    return redirect("/customers")


# --------------------------------------------------
# DELETE CUSTOMER
# --------------------------------------------------

@app.route("/customers/delete/<int:customer_id>", methods=["POST"])
def delete_customer(customer_id):

    if "user_id" not in session:
        return redirect("/")

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM customers
            WHERE id = %s
            """,
            (customer_id,)
        )

        connection.commit()

    except Exception as error:

        connection.rollback()

        return "Could not delete customer: " + str(error)

    finally:

        cursor.close()
        connection.close()

    return redirect("/customers")


# --------------------------------------------------
# SMART REORDER ALERTS
# --------------------------------------------------

@app.route("/reorder-alerts")
def reorder_alerts():

    if "user_id" not in session:
        return redirect("/")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            id,
            name,
            category,
            stock,
            low_stock_limit
        FROM menu_items
        WHERE stock <= low_stock_limit
        ORDER BY stock ASC
        """
    )

    items = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "reorder_alerts.html",
        items=items
    )


# --------------------------------------------------
# DAILY CAFE INSIGHTS
# --------------------------------------------------

@app.route("/insights")
def insights():

    if "user_id" not in session:
        return redirect("/")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Today's sales and orders
    cursor.execute(
        """
        SELECT
            COALESCE(SUM(total), 0) AS sales,
            COUNT(*) AS orders
        FROM orders
        WHERE DATE(order_date) = CURDATE()
        """
    )

    summary = cursor.fetchone()

    # Average order value
    cursor.execute(
        """
        SELECT
            COALESCE(AVG(total), 0) AS average_order
        FROM orders
        WHERE DATE(order_date) = CURDATE()
        """
    )

    average_order = cursor.fetchone()["average_order"]

    # Best-selling item
    cursor.execute(
        """
        SELECT
            menu_items.name,
            SUM(order_items.quantity) AS quantity
        FROM order_items
        JOIN orders
            ON order_items.order_id = orders.id
        JOIN menu_items
            ON order_items.menu_item_id = menu_items.id
        WHERE DATE(orders.order_date) = CURDATE()
        GROUP BY menu_items.id, menu_items.name
        ORDER BY quantity DESC
        LIMIT 1
        """
    )

    best_item = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template(
        "insights.html",
        summary=summary,
        average_order=average_order,
        best_item=best_item
    )


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# --------------------------------------------------
# START APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)