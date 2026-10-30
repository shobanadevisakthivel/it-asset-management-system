from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote_plus
from functools import wraps
import pandas as pd
import os
import re


# --------------------------------------------------
# APPLICATION SETUP
# --------------------------------------------------

app = Flask(__name__)

app.secret_key = "it-asset-management-secret-key"

connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=IT_Asset_Management;"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mssql+pyodbc:///?odbc_connect="
    + quote_plus(connection_string)
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --------------------------------------------------
# ASSET MODEL
# --------------------------------------------------

class Asset(db.Model):

    __tablename__ = "Assets"

    ID = db.Column(db.Integer, primary_key=True)

    SystemNo = db.Column(db.String(50), nullable=False)

    Name = db.Column(db.String(100), nullable=False)

    MonitorSerialNo = db.Column(db.String(100))

    Type = db.Column(db.String(50))

    Processor = db.Column(db.String(100))

    RAM = db.Column(db.String(50))

    HardDisk = db.Column(db.String(50))

    ModelNo = db.Column(db.String(100))

    CreatedAt = db.Column(db.DateTime)


# --------------------------------------------------
# LOGIN PROTECTION
# --------------------------------------------------

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "logged_in" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if username == "admin" and password == "admin123":

            session["logged_in"] = True
            session["username"] = username

            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    total = Asset.query.count()

    desktops = Asset.query.filter(
        Asset.Type.ilike("%desktop%")
    ).count()

    laptops = Asset.query.filter(
        Asset.Type.ilike("%laptop%")
    ).count()

    recent_assets = Asset.query.order_by(
        Asset.ID.desc()
    ).limit(5).all()

    return render_template(
        "dashboard.html",
        total=total,
        desktops=desktops,
        laptops=laptops,
        recent=recent_assets
    )


# --------------------------------------------------
# ADD ASSET
# --------------------------------------------------

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_asset():

    if request.method == "POST":

        system_no = request.form.get("system_no", "").strip()
        name = request.form.get("name", "").strip()
        monitor_serial_no = request.form.get(
            "monitor_serial_no", ""
        ).strip()

        asset_type = request.form.get("type", "").strip()
        processor = request.form.get("processor", "").strip()
        ram = request.form.get("ram", "").strip()
        hard_disk = request.form.get("hard_disk", "").strip()
        model_no = request.form.get("model_no", "").strip()

        if not system_no or not name:

            flash(
                "System No and Name are required.",
                "error"
            )

            return redirect(url_for("add_asset"))

        asset = Asset(
            SystemNo=system_no,
            Name=name,
            MonitorSerialNo=monitor_serial_no,
            Type=asset_type,
            Processor=processor,
            RAM=ram,
            HardDisk=hard_disk,
            ModelNo=model_no
        )

        db.session.add(asset)
        db.session.commit()

        flash(
            "Asset added successfully.",
            "success"
        )

        return redirect(url_for("view_assets"))

    return render_template("add_asset.html")


# --------------------------------------------------
# VIEW ASSETS
# --------------------------------------------------

@app.route("/assets")
@login_required
def view_assets():

    search = request.args.get(
        "search",
        ""
    ).strip()

    if search:

        assets = Asset.query.filter(

            db.or_(

                Asset.SystemNo.ilike(
                    f"%{search}%"
                ),

                Asset.Name.ilike(
                    f"%{search}%"
                ),

                Asset.MonitorSerialNo.ilike(
                    f"%{search}%"
                ),

                Asset.Type.ilike(
                    f"%{search}%"
                ),

                Asset.Processor.ilike(
                    f"%{search}%"
                ),

                Asset.ModelNo.ilike(
                    f"%{search}%"
                )
            )

        ).order_by(
            Asset.ID.desc()
        ).all()

    else:

        assets = Asset.query.order_by(
            Asset.ID.desc()
        ).all()

    return render_template(
        "view_assets.html",
        assets=assets,
        search=search
    )


# --------------------------------------------------
# EDIT ASSET
# --------------------------------------------------

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_asset(id):

    asset = db.session.get(Asset, id)

    if not asset:

        flash(
            "Asset not found.",
            "error"
        )

        return redirect(url_for("view_assets"))

    if request.method == "POST":

        asset.SystemNo = request.form.get(
            "system_no",
            ""
        ).strip()

        asset.Name = request.form.get(
            "name",
            ""
        ).strip()

        asset.MonitorSerialNo = request.form.get(
            "monitor_serial_no",
            ""
        ).strip()

        asset.Type = request.form.get(
            "type",
            ""
        ).strip()

        asset.Processor = request.form.get(
            "processor",
            ""
        ).strip()

        asset.RAM = request.form.get(
            "ram",
            ""
        ).strip()

        asset.HardDisk = request.form.get(
            "hard_disk",
            ""
        ).strip()

        asset.ModelNo = request.form.get(
            "model_no",
            ""
        ).strip()

        if not asset.SystemNo or not asset.Name:

            flash(
                "System No and Name are required.",
                "error"
            )

            return redirect(
                url_for(
                    "edit_asset",
                    id=id
                )
            )

        db.session.commit()

        flash(
            "Asset updated successfully.",
            "success"
        )

        return redirect(
            url_for("view_assets")
        )

    return render_template(
        "edit_asset.html",
        asset=asset
    )


# --------------------------------------------------
# DELETE ASSET
# --------------------------------------------------

@app.route(
    "/delete/<int:id>",
    methods=["POST"]
)
@login_required
def delete_asset(id):

    asset = db.session.get(
        Asset,
        id
    )

    if asset:

        db.session.delete(asset)
        db.session.commit()

        flash(
            "Asset deleted successfully.",
            "success"
        )

    return redirect(
        url_for("view_assets")
    )


# --------------------------------------------------
# NORMALIZE EXCEL COLUMN NAME
# --------------------------------------------------

def normalize_column(column):

    column = str(column).strip().lower()

    column = re.sub(
        r"[^a-z0-9]",
        "",
        column
    )

    return column


# --------------------------------------------------
# AUTOMATIC COLUMN RECOGNITION
# --------------------------------------------------

COLUMN_ALIASES = {

    "system_no": [
        "systemno",
        "systemnumber",
        "systemid",
        "system",
        "assetid",
        "assetnumber",
        "assetno",
        "computerid",
        "computername",
        "computer",
        "pcid",
        "pcno"
    ],

    "name": [
        "name",
        "username",
        "employeename",
        "employee",
        "user",
        "assignedto",
        "assigneduser",
        "staffname"
    ],

    "monitor_serial_no": [
        "monitorserialno",
        "monitorserialnumber",
        "monitorserial",
        "monitorsn",
        "monitornumber",
        "monitorsnno",
        "displayserial",
        "displaysn"
    ],

    "type": [
        "type",
        "assettype",
        "devicetype",
        "machinetype",
        "computer type",
        "device"
    ],

    "processor": [
        "processor",
        "cpu",
        "cpudetails",
        "processorname",
        "processortype"
    ],

    "ram": [
        "ram",
        "ramsize",
        "memory",
        "memorysize",
        "systemmemory"
    ],

    "hard_disk": [
        "harddisk",
        "harddiskcapacity",
        "disk",
        "disksize",
        "storage",
        "storagecapacity",
        "hdd",
        "ssd"
    ],

    "model_no": [
        "model",
        "modelno",
        "modelnumber",
        "modelname",
        "devicemodel"
    ]
}


def find_matching_field(column):

    normalized = normalize_column(column)

    for field, aliases in COLUMN_ALIASES.items():

        normalized_aliases = [
            normalize_column(alias)
            for alias in aliases
        ]

        if normalized in normalized_aliases:
            return field

    return None


# --------------------------------------------------
# IMPORT EXCEL
# --------------------------------------------------

@app.route(
    "/import-excel",
    methods=["GET", "POST"]
)
@login_required
def import_excel():

    if request.method == "POST":

        file = request.files.get("file")

        if not file or not file.filename:

            flash(
                "Please select an Excel file.",
                "error"
            )

            return redirect(
                url_for("import_excel")
            )

        if not file.filename.lower().endswith(
            (".xlsx", ".xls")
        ):

            flash(
                "Only Excel files are supported.",
                "error"
            )

            return redirect(
                url_for("import_excel")
            )

        try:

            dataframe = pd.read_excel(file)

            if dataframe.empty:

                flash(
                    "The uploaded Excel file is empty.",
                    "error"
                )

                return redirect(
                    url_for("import_excel")
                )

            mapping = {}

            for column in dataframe.columns:

                field = find_matching_field(
                    column
                )

                if field and field not in mapping:

                    mapping[field] = column

            if "system_no" not in mapping:

                flash(
                    "Could not identify the System No column.",
                    "error"
                )

                return redirect(
                    url_for("import_excel")
                )

            if "name" not in mapping:

                flash(
                    "Could not identify the Name column.",
                    "error"
                )

                return redirect(
                    url_for("import_excel")
                )

            imported = 0
            skipped = 0

            for _, row in dataframe.iterrows():

                system_no = str(
                    row.get(
                        mapping.get("system_no"),
                        ""
                    )
                ).strip()

                name = str(
                    row.get(
                        mapping.get("name"),
                        ""
                    )
                ).strip()

                if system_no == "nan":
                    system_no = ""

                if name == "nan":
                    name = ""

                if not system_no or not name:

                    skipped += 1
                    continue

                def get_value(field):

                    column = mapping.get(field)

                    if not column:
                        return ""

                    value = row.get(column, "")

                    if pd.isna(value):
                        return ""

                    return str(value).strip()

                asset = Asset(

                    SystemNo=system_no,

                    Name=name,

                    MonitorSerialNo=get_value(
                        "monitor_serial_no"
                    ),

                    Type=get_value(
                        "type"
                    ),

                    Processor=get_value(
                        "processor"
                    ),

                    RAM=get_value(
                        "ram"
                    ),

                    HardDisk=get_value(
                        "hard_disk"
                    ),

                    ModelNo=get_value(
                        "model_no"
                    )
                )

                db.session.add(asset)

                imported += 1

            db.session.commit()

            flash(
                f"{imported} asset record(s) imported successfully. "
                f"{skipped} record(s) skipped.",
                "success"
            )

            return redirect(
                url_for("view_assets")
            )

        except Exception as error:

            db.session.rollback()

            flash(
                f"Import failed: {error}",
                "error"
            )

            return redirect(
                url_for("import_excel")
            )

    return render_template(
        "import_excel.html"
    )


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )