from flask import Flask, render_template, request, redirect, url_for, flash, g
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from db import get_connection
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import paramiko

# ---------------- App Setup ----------------
app = Flask(__name__)
app.secret_key = "supersecretkey"

# File upload settings
UPLOAD_FOLDER = r"D:\MizanurRahman321\IT_APP_PYTHON\IT_APP\static\purchase_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'doc', 'docx', 'pdf'}

bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---------------- Helper ----------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------- User class ----------------
class User(UserMixin):
    def __init__(self, id_, username):
        self.id = id_
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT USER_ID, USERNAME FROM APP_USERS_IT WHERE USER_ID = :id", {"id": int(user_id)})
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return User(row[0], row[1])
    return None

# ---------------- Set g.username ----------------
@app.before_request
def before_request():
    g.username = current_user.username if current_user.is_authenticated else None

# ---------------- SFTP Upload ----------------
REMOTE_HOST = "192.168.21.8"
REMOTE_PORT = 2198
REMOTE_USER = "oracle"
REMOTE_PASS = "FoTass5.@"
REMOTE_FOLDER = "/home/oracle/Templates"


from flask import send_file
import io

def upload_file_to_server(local_file_path, filename):
    try:
        transport = paramiko.Transport((REMOTE_HOST, REMOTE_PORT))
        transport.connect(username=REMOTE_USER, password=REMOTE_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # Ensure remote folder exists
        try:
            sftp.chdir(REMOTE_FOLDER)
        except IOError:
            sftp.mkdir(REMOTE_FOLDER)
            sftp.chdir(REMOTE_FOLDER)

        remote_path = os.path.join(REMOTE_FOLDER, filename).replace("\\", "/")
        sftp.put(local_file_path, remote_path)

        sftp.close()
        transport.close()
        print(f"Uploaded {filename} to remote server successfully")
    except paramiko.AuthenticationException:
        print("Authentication failed, please check your username/password")
    except paramiko.SSHException as e:
        print(f"SSH error: {str(e)}")
    except Exception as e:
        print(f"Failed to upload {filename}: {str(e)}")
        
        
@app.route('/view_purchase_file/<filename>')
@login_required
def view_purchase_file(filename):
    try:
        transport = paramiko.Transport((REMOTE_HOST, REMOTE_PORT))
        transport.connect(username=REMOTE_USER, password=REMOTE_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)

        remote_path = f"{REMOTE_FOLDER}/{filename}"

        file_obj = io.BytesIO()
        sftp.getfo(remote_path, file_obj)
        file_obj.seek(0)

        sftp.close()
        transport.close()

        return send_file(
            file_obj,
            download_name=filename,
            as_attachment=False
        )

    except Exception as e:
        flash(f"Unable to open file: {str(e)}", "danger")
        return redirect(url_for("reports"))
        

# ---------------- Register ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        email = request.form['email']
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO APP_USERS_IT (USER_ID, USERNAME, PASSWORD_HASH, FULL_NAME, EMAIL)
                VALUES (SEQ_APP_USERS_IT.NEXTVAL, :username, :password_hash, :full_name, :email)
            """, {"username": username, "password_hash": password_hash, "full_name": full_name, "email": email})
            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        finally:
            cur.close()
            conn.close()
    return render_template("register.html")

# ---------------- Login ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT USER_ID, PASSWORD_HASH FROM APP_USERS_IT WHERE USERNAME = :username", {"username": username})
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row and bcrypt.check_password_hash(row[1], password):
            login_user(User(row[0], username))
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "danger")
    return render_template("login.html")

# ---------------- Dashboard ----------------
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html")

# ---------------- Logout ----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------------- Purchase Form ----------------
@app.route('/purchase', methods=['GET', 'POST'])
@login_required
def purchase():
    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        if request.method == "POST":
            vendor_id = request.form['vendor_id']
            product_name = request.form['product_name']
            product_code = request.form['product_code']
            branch_id = request.form['branch_id']
            category_id = request.form['asset_category_id']
            purchase_date = request.form['purchase_date']
            purchase_amount = request.form['purchase_amount']
            status = request.form['status']
            specification = request.form['specification']
            notes = request.form['notes']

            # username input by user
            pi_username = request.form.get("pi_username")

            # File upload
            file = request.files.get('purchase_file')
            file_path = None
            if file and file.filename:
                filename = secure_filename(file.filename)
                full_local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(full_local_path)

                upload_file_to_server(full_local_path, filename)
                file_path = filename

            cur.execute("""
                INSERT INTO PURCHASE_INFORMATION_IT
                (PI_ID, PI_VENDOR_ID, PI_PRODUCT_NAME, PI_PRODUCT_CODE, PI_BRANCH_ID,
                 PI_ASSET_CATEGORY_ID, PI_PURCHASE_DATE, PI_PURCHASE_AMOUNT, PI_STATUS,
                 PI_PRODUCT_SPECIFICATION, PI_USERNAME, PI_CREATEDAPPUSER,
                 PI_CREATEDSYSUSER, PI_CREATETIME, PI_NOTES, FILE_PATH)
                VALUES (SEQ_PI_ID.NEXTVAL, :vendor_id, :product_name, :product_code, :branch_id,
                        :category_id, TO_DATE(:purchase_date, 'YYYY-MM-DD'), :purchase_amount, :status,
                        :specification, :pi_username, :current_user, USER, SYSDATE, :notes, :file_path)
            """, {
                "vendor_id": vendor_id,
                "product_name": product_name,
                "product_code": product_code,
                "branch_id": branch_id,
                "category_id": category_id,
                "purchase_date": purchase_date,
                "purchase_amount": purchase_amount,
                "status": status,
                "specification": specification,
                "pi_username": pi_username,
                "current_user": current_user.username,
                "notes": notes,
                "file_path": file_path
            })

            conn.commit()
            flash("Purchase information saved successfully!", "success")
            return redirect(url_for("purchase"))

        # GET request dropdowns
        cur.execute("SELECT SI_ID, SI_VENDOR_NAME FROM VENDOR_INFO_IT")
        vendors = cur.fetchall()

        cur.execute("SELECT AC_ID, AC_TYPE FROM CATEGORY_IT")
        categories = cur.fetchall()

        cur.execute("SELECT BID, BNAME FROM BRANCH")
        branches = cur.fetchall()

        return render_template(
            "purchase_form.html",
            vendors=vendors,
            categories=categories,
            branches=branches
        )

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("purchase"))

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


    # Load dropdowns for GET
    cur.execute("SELECT SI_ID, SI_VENDOR_NAME FROM VENDOR_INFO_IT")
    vendors = cur.fetchall()
    cur.execute("SELECT AC_ID, AC_TYPE FROM CATEGORY_IT")
    categories = cur.fetchall()
    cur.execute("SELECT BID, BNAME FROM BRANCH")
    branches = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("purchase_form.html", vendors=vendors, categories=categories, branches=branches)


# ---------------- Vendor Form ----------------
@app.route('/vendor', methods=['GET', 'POST'])
@login_required
def vendor():
    if request.method == "POST":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO VENDOR_INFO_IT (SI_ID, SI_VENDOR_NAME, SI_VENDOR_TYPE, SI_CONTACT_NUMBER, SI_EMAIL, SI_ADDRESS,
        SI_SUPP_CONTACT_PERSON, SI_SUPP_CONTACT_PERSON_2, SI_SUPP_CONTACT_PERSON_3, SI_CREATETIME, SI_STATUS,
        SI_NOTES, SI_ENTRY_USER)
        VALUES (SUPPLIER_SEQ_ID.NEXTVAL, :name, :type, :contact, :email, :address,
        :contact_person1, :contact_person2, :contact_person3, SYSDATE, :status, :notes, :username)
        """, {
            "name": request.form['vendor_name'],
            "type": request.form['vendor_type'],
            "contact": request.form['contact_number'],
            "email": request.form['email'],
            "address": request.form['address'],
            "contact_person1": request.form['contact_person1'],
            "contact_person2": request.form['contact_person2'],
            "contact_person3": request.form['contact_person3'],
            "status": request.form['status'],
            "notes": request.form['notes'],
            "username": current_user.username
        })
        conn.commit()
        cur.close()
        conn.close()
        flash("Vendor saved successfully!", "success")
        return redirect(url_for("vendor"))
    return render_template("vendor_form.html")

# ---------------- Category Form ----------------
@app.route('/category', methods=['GET', 'POST'])
@login_required
def category():
    if request.method == "POST":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO CATEGORY_IT (AC_ID, AC_TYPE)
        VALUES (category_seq_id.NEXTVAL, :type)
        """, {"type": request.form['category_name']})
        conn.commit()
        cur.close()
        conn.close()
        flash("Category saved successfully!", "success")
        return redirect(url_for("category"))
    return render_template("category_form.html")

# ---------------- Reports ----------------
from datetime import datetime

@app.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    conn = get_connection()
    cur = conn.cursor()

    # Which report user selected
    report_type = request.form.get("report_type", "")

    # Date filter
    from_date = request.form.get("from_date")
    to_date = request.form.get("to_date")

    if not from_date:
        from_date = datetime.today().replace(day=1).strftime("%Y-%m-%d")
    if not to_date:
        to_date = datetime.today().strftime("%Y-%m-%d")

    vendors = []
    categories = []
    purchases = []

    try:
        # -------- Vendor Report --------
        if report_type == "vendor":
            cur.execute("""
                SELECT SI_ID, SI_VENDOR_NAME, SI_VENDOR_TYPE,
                       SI_CONTACT_NUMBER, SI_EMAIL,
                       SI_ADDRESS, SI_CREATETIME
                FROM VENDOR_INFO_IT
                WHERE TRUNC(SI_CREATETIME)
                      BETWEEN TO_DATE(:from_date,'YYYY-MM-DD')
                      AND TO_DATE(:to_date,'YYYY-MM-DD')
                ORDER BY SI_CREATETIME DESC
            """, {
                "from_date": from_date,
                "to_date": to_date
            })
            vendors = cur.fetchall()

        # -------- Category Report --------
        elif report_type == "category":
            cur.execute("""
                SELECT AC_ID, AC_TYPE
                FROM CATEGORY_IT
                ORDER BY AC_ID DESC
            """)
            categories = cur.fetchall()

        # -------- Purchase Report --------
        else:
            cur.execute("""
                SELECT PI_ID, PI_PRODUCT_NAME, PI_PRODUCT_CODE,
                       PI_PURCHASE_DATE, PI_PURCHASE_AMOUNT,
                       PI_STATUS, PI_USERNAME, FILE_PATH
                FROM PURCHASE_INFORMATION_IT
                WHERE PI_PURCHASE_DATE
                      BETWEEN TO_DATE(:from_date,'YYYY-MM-DD')
                      AND TO_DATE(:to_date,'YYYY-MM-DD')
                ORDER BY PI_PURCHASE_DATE DESC
            """, {
                "from_date": from_date,
                "to_date": to_date
            })
            purchases = cur.fetchall()

    finally:
        cur.close()
        conn.close()

    return render_template(
        "reports.html",
        vendors=vendors,
        categories=categories,
        purchases=purchases,
        report_type=report_type,
        from_date=from_date,
        to_date=to_date
    )


# ---------------- Main ----------------
if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
