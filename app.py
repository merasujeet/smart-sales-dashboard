from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# =========================
# SECRET KEY
# =========================
app.secret_key = "founder_secret_key_123"


# =========================
# DATABASE CONNECTION
# =========================
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Ecom@2006#123",
        database="sales_dashboard"
    )


# =========================
# FOUNDER LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM admin
            WHERE username = %s
        """, (username,))

        admin = cursor.fetchone()

        cursor.close()
        db.close()

        if admin and check_password_hash(admin["password"], password):

            session["admin_logged_in"] = True
            session["admin_username"] = admin["username"]

            return redirect(url_for("home"))

        return "Invalid Founder Username or Password"

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================
# LOGIN PROTECTION
# =========================
def login_required():

    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    return None


# =========================================================
# AI BUSINESS ASSISTANT
# =========================================================

@app.route("/ai")
def ai_page():

    check = login_required()

    if check:
        return check

    return render_template("ai_assistant.html")


@app.route("/ai-assistant", methods=["POST"])
def ai_assistant():

    check = login_required()

    if check:
        return check

    question = request.form.get("question", "").strip().lower()

    if not question:
        return {"answer": "Please ask me a question."}

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:

        # =========================
        # TODAY'S SALES
        # =========================
        if "today" in question and "sale" in question:

            cursor.execute("""
                SELECT
                    COALESCE(SUM(total_amount), 0) AS sales,
                    COUNT(*) AS orders,
                    COALESCE(SUM(profit), 0) AS profit
                FROM sales
                WHERE DATE(sale_date) = CURDATE()
            """)

            result = cursor.fetchone()

            return {
                "answer": (
                    f"Today's sales are ₹{result['sales']}. "
                    f"You received {result['orders']} orders today, "
                    f"with a profit of ₹{result['profit']}."
                )
            }


        # =========================
        # TOTAL REVENUE
        # =========================
        elif "total revenue" in question or "overall revenue" in question:

            cursor.execute("""
                SELECT
                    COALESCE(SUM(total_amount), 0) AS revenue
                FROM sales
            """)

            result = cursor.fetchone()

            return {
                "answer": f"Your total revenue is ₹{result['revenue']}."
            }


        # =========================
        # TOTAL PROFIT
        # =========================
        elif "total profit" in question:

            cursor.execute("""
                SELECT
                    COALESCE(SUM(profit), 0) AS profit
                FROM sales
            """)

            result = cursor.fetchone()

            return {
                "answer": f"Your total profit is ₹{result['profit']}."
            }


        # =========================
        # TOTAL ORDERS
        # =========================
        elif "total orders" in question or "how many orders" in question:

            cursor.execute("""
                SELECT
                    COUNT(*) AS orders
                FROM sales
            """)

            result = cursor.fetchone()

            return {
                "answer": f"You have {result['orders']} total orders."
            }


        # =========================
        # LOW STOCK
        # =========================
        elif "low stock" in question:

            cursor.execute("""
                SELECT
                    name,
                    stock
                FROM products
                WHERE stock <= 10
                ORDER BY stock ASC
            """)

            products = cursor.fetchall()

            if not products:

                answer = "There are currently no low-stock products."

            else:

                items = ", ".join(
                    f"{p['name']} ({p['stock']} left)"
                    for p in products
                )

                answer = f"Low-stock products are: {items}."

            return {
                "answer": answer
            }


        # =========================
        # TOP SELLING PRODUCT
        # =========================
        elif "top selling" in question or "best selling" in question:

            cursor.execute("""
                SELECT
                    p.name,
                    SUM(s.quantity) AS units_sold
                FROM sales s
                JOIN products p
                ON s.product_id = p.id
                GROUP BY p.id, p.name
                ORDER BY units_sold DESC
                LIMIT 1
            """)

            result = cursor.fetchone()

            if result:

                answer = (
                    f"{result['name']} is your top-selling product "
                    f"with {result['units_sold']} units sold."
                )

            else:

                answer = "There are no sales records yet."

            return {
                "answer": answer
            }


        # =========================
        # DEFAULT AI RESPONSE
        # =========================
        else:

            return {
                "answer": (
                    "I can help with sales, revenue, profit, orders, "
                    "top-selling products and low-stock products. "
                    "Try asking: 'What are today's sales?'"
                )
            }


    except mysql.connector.Error as err:

        return {
            "answer": f"Database error: {err}"
        }


    finally:

        cursor.close()
        db.close()


# =========================
# DASHBOARD
# =========================
@app.route("/")
def home():

    check = login_required()

    if check:
        return check

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # =========================
    # PRODUCTS
    # =========================
    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """)

    products = cursor.fetchall()


    # =========================
    # TOTAL REVENUE
    # =========================
    cursor.execute("""
        SELECT
            COALESCE(SUM(total_amount), 0) AS total_revenue
        FROM sales
    """)

    total_revenue = cursor.fetchone()["total_revenue"]


    # =========================
    # TOTAL ORDERS
    # =========================
    cursor.execute("""
        SELECT
            COUNT(*) AS total_orders
        FROM sales
    """)

    total_orders = cursor.fetchone()["total_orders"]


    # =========================
    # TODAY ORDERS
    # =========================
    cursor.execute("""
        SELECT
            COUNT(*) AS today_orders
        FROM sales
        WHERE DATE(sale_date) = CURDATE()
    """)

    today_orders = cursor.fetchone()["today_orders"]


    # =========================
    # TOTAL TEAM MEMBERS
    # =========================
    cursor.execute("""
        SELECT
            COUNT(*) AS total_members
        FROM team_members
    """)

    total_members = cursor.fetchone()["total_members"]


    # =========================
    # LAST 7 DAYS SALES
    # =========================
    cursor.execute("""
        SELECT
            DATE(sale_date) AS sale_day,
            COALESCE(SUM(total_amount), 0) AS daily_sales
        FROM sales
        WHERE sale_date >= CURDATE() - INTERVAL 6 DAY
        GROUP BY DATE(sale_date)
        ORDER BY sale_day
    """)

    sales_data = cursor.fetchall()


    # =========================
    # SETTINGS
    # =========================
    cursor.execute("""
        SELECT
            business_name,
            currency,
            low_stock_limit
        FROM settings
        WHERE id = 1
    """)

    settings = cursor.fetchone()


    # =========================
    # DEFAULT SETTINGS
    # =========================
    if not settings:

        settings = {
            "business_name": "Smart Sales Dashboard",
            "currency": "₹",
            "low_stock_limit": 10
        }


    # =========================
    # LOW STOCK PRODUCTS
    # =========================
    cursor.execute("""
        SELECT *
        FROM products
        WHERE stock <= %s
        ORDER BY stock ASC
    """, (
        settings["low_stock_limit"],
    ))

    low_stock_products = cursor.fetchall()


    cursor.close()
    db.close()


    # =========================
    # DASHBOARD
    # =========================
    return render_template(
        "dashboard.html",
        products=products,
        total_revenue=total_revenue,
        total_orders=total_orders,
        today_orders=today_orders,
        total_members=total_members,
        sales_data=sales_data,
        settings=settings,
        low_stock_products=low_stock_products
    )


# =========================
# PRODUCTS
# =========================
@app.route("/products")
def products_page():

    check = login_required()

    if check:
        return check

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """)

    products = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "products.html",
        products=products
    )


# =========================
# ADD PRODUCT
# =========================
@app.route("/add_product", methods=["POST"])
def add_product():

    check = login_required()

    if check:
        return check

    name = request.form["name"]
    category = request.form["category"]
    price = float(request.form["price"])
    stock = int(request.form["stock"])
    cost_price = float(request.form["cost_price"])

    margin = price - cost_price
    profit = margin * stock

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO products
        (
            name,
            category,
            price,
            stock,
            cost_price,
            margin,
            profit
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        name,
        category,
        price,
        stock,
        cost_price,
        margin,
        profit
    ))

    db.commit()

    cursor.close()
    db.close()

    return redirect(url_for("products_page"))


# =========================
# EDIT PRODUCT
# =========================
@app.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):

    check = login_required()

    if check:
        return check

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT *
            FROM products
            WHERE id = %s
        """, (product_id,))

        product = cursor.fetchone()

        if not product:
            return "Product Not Found", 404


        if request.method == "POST":

            name = request.form.get("name", "").strip()
            category = request.form.get("category", "").strip()

            price_text = request.form.get("price", "").strip()
            stock_text = request.form.get("stock", "").strip()
            cost_price_text = request.form.get("cost_price", "").strip()


            if not name:
                return "Product name is required"

            if not category:
                return "Category is required"

            if not price_text:
                return "Selling price is required"

            if not stock_text:
                return "Stock is required"

            if not cost_price_text:
                return "Cost price is required"


            price = float(price_text)
            stock = int(stock_text)
            cost_price = float(cost_price_text)


            if price < 0:
                return "Selling price cannot be negative"

            if cost_price < 0:
                return "Cost price cannot be negative"

            if stock < 0:
                return "Stock cannot be negative"


            margin = price - cost_price

            profit = margin * stock


            cursor.execute("""
                UPDATE products
                SET
                    name = %s,
                    category = %s,
                    price = %s,
                    stock = %s,
                    cost_price = %s,
                    margin = %s,
                    profit = %s
                WHERE id = %s
            """, (
                name,
                category,
                price,
                stock,
                cost_price,
                margin,
                profit,
                product_id
            ))

            db.commit()

            return redirect(url_for("products_page"))


        return render_template(
            "edit_product.html",
            product=product
        )


    except ValueError:

        db.rollback()

        return "Please enter valid numbers for Price, Cost Price and Stock"


    except mysql.connector.Error as err:

        db.rollback()

        return f"Database update failed: {err}"


    finally:

        try:
            cursor.close()
        except:
            pass

        try:
            db.close()
        except:
            pass


# =========================
# DELETE PRODUCT
# =========================
@app.route("/delete_product/<int:product_id>")
def delete_product(product_id):

    check = login_required()

    if check:
        return check

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute(
            "DELETE FROM sales WHERE product_id = %s",
            (product_id,)
        )

        cursor.execute(
            "DELETE FROM products WHERE id = %s",
            (product_id,)
        )

        db.commit()

    except mysql.connector.Error as err:

        db.rollback()

        cursor.close()
        db.close()

        return f"Product delete failed: {err}"

    cursor.close()
    db.close()

    return redirect(url_for("products_page"))


# =========================
# SALES
# =========================
@app.route("/sales")
def sales_page():

    check = login_required()

    if check:
        return check

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            sales.id,
            sales.product_id,
            products.name AS product_name,
            sales.quantity,
            sales.cost_price,
            products.price AS selling_price,
            sales.total_amount,
            sales.profit,
            sales.sale_date
        FROM sales
        JOIN products
        ON sales.product_id = products.id
        ORDER BY sales.sale_date DESC
    """)

    sales = cursor.fetchall()


    cursor.execute("""
        SELECT *
        FROM products
        WHERE stock > 0
        ORDER BY name
    """)

    products = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "sales.html",
        sales=sales,
        products=products
    )


# =========================
# ADD SALE
# =========================
@app.route("/add_sale", methods=["POST"])
def add_sale():

    check = login_required()

    if check:
        return check

    product_id = request.form["product_id"]
    quantity = int(request.form["quantity"])

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM products
        WHERE id = %s
    """, (product_id,))

    product = cursor.fetchone()

    if not product:

        cursor.close()
        db.close()

        return redirect(url_for("sales_page"))


    if quantity <= 0 or quantity > product["stock"]:

        cursor.close()
        db.close()

        return redirect(url_for("sales_page"))


    selling_price = product["price"]
    cost_price = product["cost_price"]

    total_amount = selling_price * quantity

    profit = (selling_price - cost_price) * quantity


    cursor.execute("""
        INSERT INTO sales
        (
            product_id,
            quantity,
            cost_price,
            total_amount,
            profit
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        product_id,
        quantity,
        cost_price,
        total_amount,
        profit
    ))


    sale_id = cursor.lastrowid


    cursor.execute("""
        UPDATE products
        SET stock = stock - %s
        WHERE id = %s
    """, (
        quantity,
        product_id
    ))


    db.commit()

    cursor.close()
    db.close()


    return redirect(url_for("bill", sale_id=sale_id))


# =========================
# BILL / INVOICE
# =========================
@app.route("/bill/<int:sale_id>")
def bill(sale_id):

    check = login_required()

    if check:
        return check

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            sales.id,
            sales.quantity,
            sales.total_amount,
            sales.sale_date,
            products.name AS product_name,
            products.price AS selling_price
        FROM sales
        JOIN products
        ON sales.product_id = products.id
        WHERE sales.id = %s
    """, (sale_id,))

    sale = cursor.fetchone()

    cursor.close()
    db.close()

    if not sale:
        return "Bill Not Found"


    return render_template(
        "bill.html",
        sale=sale
    )


# =========================
# TEAM
# =========================
@app.route("/team")
def team_page():

    check = login_required()

    if check:
        return check

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            name,
            email,
            phone,
            role,
            status,
            created_at
        FROM team_members
        ORDER BY id DESC
    """)

    team_members = cursor.fetchall()


    cursor.execute("""
        SELECT COUNT(*) AS total_members
        FROM team_members
    """)

    total_members = cursor.fetchone()["total_members"]


    cursor.execute("""
        SELECT COUNT(*) AS active_members
        FROM team_members
        WHERE status = 'Active'
    """)

    active_members = cursor.fetchone()["active_members"]


    cursor.execute("""
        SELECT COUNT(*) AS inactive_members
        FROM team_members
        WHERE status = 'Inactive'
    """)

    inactive_members = cursor.fetchone()["inactive_members"]


    cursor.execute("""
        SELECT COUNT(*) AS sales_team
        FROM team_members
        WHERE role LIKE '%Sales%'
    """)

    sales_team = cursor.fetchone()["sales_team"]


    cursor.close()
    db.close()

    return render_template(
        "team.html",
        team_members=team_members,
        total_members=total_members,
        active_members=active_members,
        inactive_members=inactive_members,
        sales_team=sales_team
    )


# =========================
# ADD TEAM MEMBER
# =========================
@app.route("/add_team_member", methods=["POST"])
def add_team_member():

    check = login_required()

    if check:
        return check

    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]
    role = request.form["role"]
    status = request.form["status"]

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO team_members
        (name, email, phone, role, status)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        name,
        email,
        phone,
        role,
        status
    ))

    db.commit()

    cursor.close()
    db.close()

    return redirect(url_for("team_page"))


# =========================
# EDIT TEAM MEMBER
# =========================
@app.route("/edit_team_member/<int:member_id>", methods=["GET", "POST"])
def edit_team_member(member_id):

    check = login_required()

    if check:
        return check

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        role = request.form["role"]
        status = request.form["status"]

        cursor.execute("""
            UPDATE team_members
            SET
                name = %s,
                email = %s,
                phone = %s,
                role = %s,
                status = %s
            WHERE id = %s
        """, (
            name,
            email,
            phone,
            role,
            status,
            member_id
        ))

        db.commit()

        cursor.close()
        db.close()

        return redirect(url_for("team_page"))


    cursor.execute("""
        SELECT *
        FROM team_members
        WHERE id = %s
    """, (member_id,))

    member = cursor.fetchone()

    cursor.close()
    db.close()

    if not member:
        return "Team Member Not Found"


    return render_template(
        "edit_team_member.html",
        member=member
    )


# =========================
# DELETE TEAM MEMBER
# =========================
@app.route("/delete_team_member/<int:member_id>")
def delete_team_member(member_id):

    check = login_required()

    if check:
        return check

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM team_members
        WHERE id = %s
    """, (member_id,))

    db.commit()

    cursor.close()
    db.close()

    return redirect(url_for("team_page"))


# =========================
# SETTINGS
# =========================
@app.route("/settings", methods=["GET", "POST"])
def settings_page():

    check = login_required()

    if check:
        return check

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:

        if request.method == "POST":

            business_name = request.form.get(
                "business_name", ""
            ).strip()

            currency = request.form.get(
                "currency", "₹"
            ).strip()

            low_stock_limit = request.form.get(
                "low_stock_limit", "10"
            ).strip()


            if not business_name:
                business_name = "Smart Sales Dashboard"

            if not currency:
                currency = "₹"


            try:
                low_stock_limit = int(low_stock_limit)
            except ValueError:
                low_stock_limit = 10


            if low_stock_limit < 0:
                low_stock_limit = 0


            cursor.execute("""
                INSERT INTO settings
                (
                    id,
                    business_name,
                    currency,
                    low_stock_limit
                )
                VALUES
                (
                    1,
                    %s,
                    %s,
                    %s
                )
                ON DUPLICATE KEY UPDATE
                    business_name = VALUES(business_name),
                    currency = VALUES(currency),
                    low_stock_limit = VALUES(low_stock_limit)
            """, (
                business_name,
                currency,
                low_stock_limit
            ))

            db.commit()

            return redirect(url_for("settings_page"))


        cursor.execute("""
            SELECT
                id,
                business_name,
                currency,
                low_stock_limit
            FROM settings
            WHERE id = 1
        """)

        settings = cursor.fetchone()


        if not settings:

            settings = {
                "id": 1,
                "business_name": "Smart Sales Dashboard",
                "currency": "₹",
                "low_stock_limit": 10
            }


        return render_template(
            "settings.html",
            settings=settings
        )


    except mysql.connector.Error as err:

        db.rollback()

        return f"""
        <h2>Settings Save Error</h2>
        <p>{err}</p>
        """


    finally:

        try:
            cursor.close()
        except:
            pass

        try:
            db.close()
        except:
            pass


# =========================
# ANALYTICS
# =========================
@app.route("/analytics")
def analytics_page():

    check = login_required()

    if check:
        return check

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)


    # =========================
    # TOP SELLING PRODUCTS
    # =========================
    cursor.execute("""
        SELECT
            p.id,
            p.name,
            COALESCE(SUM(s.quantity), 0) AS total_sold
        FROM products p
        LEFT JOIN sales s
        ON p.id = s.product_id
        GROUP BY p.id, p.name
        ORDER BY total_sold DESC
        LIMIT 5
    """)

    top_products = cursor.fetchall()


    # =========================
    # REVENUE BY PRODUCT
    # =========================
    cursor.execute("""
        SELECT
            p.id,
            p.name,
            COALESCE(SUM(s.total_amount), 0) AS total_revenue
        FROM products p
        LEFT JOIN sales s
        ON p.id = s.product_id
        GROUP BY p.id, p.name
        ORDER BY total_revenue DESC
        LIMIT 5
    """)

    revenue_by_product = cursor.fetchall()


    # =========================
    # TOTAL REVENUE
    # =========================
    cursor.execute("""
        SELECT
            COALESCE(SUM(total_amount), 0) AS total_revenue
        FROM sales
    """)

    total_revenue = cursor.fetchone()["total_revenue"]


    # =========================
    # TOTAL ORDERS
    # =========================
    cursor.execute("""
        SELECT
            COUNT(*) AS total_orders
        FROM sales
    """)

    total_orders = cursor.fetchone()["total_orders"]


    cursor.close()
    db.close()


    return render_template(
        "analytics.html",
        top_products=top_products,
        revenue_by_product=revenue_by_product,
        total_revenue=total_revenue,
        total_orders=total_orders
    )


# =========================
# RUN FLASK
# =========================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )