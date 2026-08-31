from flask import Flask, render_template, request, redirect
import sqlite3


app = Flask(__name__)


def get_database_connection():
    connection = sqlite3.connect("patients.db")
    connection.row_factory = sqlite3.Row
    return connection


# ==========================================
# داشبورد
# ==========================================

@app.route("/")
def home():

    connection = get_database_connection()

    patients = connection.execute(
        "SELECT * FROM patients ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template(
        "index.html",
        patients=patients,
        patient_count=len(patients)
    )


# ==========================================
# لیست بیماران
# ==========================================

@app.route("/patients")
def patients_list():

    search = request.args.get("search", "").strip()

    connection = get_database_connection()

    if search:

        patients = connection.execute(
            """
            SELECT * FROM patients
            WHERE first_name LIKE ?
               OR last_name LIKE ?
               OR national_id LIKE ?
            ORDER BY id DESC
            """,
            (
                f"%{search}%",
                f"%{search}%",
                f"%{search}%"
            )
        ).fetchall()

    else:

        patients = connection.execute(
            "SELECT * FROM patients ORDER BY id DESC"
        ).fetchall()

    connection.close()

    return render_template(
        "patients.html",
        patients=patients,
        search=search
    )


# ==========================================
# جزئیات بیمار
# ==========================================

@app.route("/patient/<int:patient_id>")
def patient_detail(patient_id):

    connection = get_database_connection()

    patient = connection.execute(
        "SELECT * FROM patients WHERE id = ?",
        (patient_id,)
    ).fetchone()

    connection.close()

    if patient is None:
        return "بیمار پیدا نشد", 404

    return render_template(
        "patient_detail.html",
        patient=patient
    )


# ==========================================
# حذف بیمار
# ==========================================

@app.route(
    "/delete-patient/<int:patient_id>",
    methods=["POST"]
)
def delete_patient(patient_id):

    connection = get_database_connection()

    connection.execute(
        "DELETE FROM patients WHERE id = ?",
        (patient_id,)
    )

    connection.commit()

    connection.close()

    return redirect("/patients")

@app.route("/reports")
def reports():

    connection = get_database_connection()

    # تعداد کل بیماران
    patient_count = connection.execute(
        "SELECT COUNT(*) FROM patients"
    ).fetchone()[0]

    # تعداد کل سوابق پزشکی
    record_count = connection.execute(
        "SELECT COUNT(*) FROM medical_records"
    ).fetchone()[0]

    # تعداد بیماران دارای سابقه پزشکی
    patients_with_records = connection.execute(
        """
        SELECT COUNT(DISTINCT patient_id)
        FROM medical_records
        """
    ).fetchone()[0]

    # تعداد بیماران دارای حساسیت
    patients_with_allergies = connection.execute(
        """
        SELECT COUNT(*)
        FROM patients
        WHERE allergies IS NOT NULL
          AND TRIM(allergies) != ''
        """
    ).fetchone()[0]

    # تعداد مردان
    male_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM patients
        WHERE gender = 'مرد'
        """
    ).fetchone()[0]

    # تعداد زنان
    female_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM patients
        WHERE gender = 'زن'
        """
    ).fetchone()[0]

    # آمار گروه‌های خونی
    blood_types = connection.execute(
        """
        SELECT blood_type, COUNT(*)
        FROM patients
        GROUP BY blood_type
        ORDER BY blood_type
        """
    ).fetchall()

    # میانگین وزن
    average_weight = connection.execute(
        """
        SELECT ROUND(AVG(weight), 2)
        FROM patients
        WHERE weight IS NOT NULL
        """
    ).fetchone()[0]

    # میانگین قد
    average_height = connection.execute(
        """
        SELECT ROUND(AVG(height), 2)
        FROM patients
        WHERE height IS NOT NULL
        """
    ).fetchone()[0]

    connection.close()

    return render_template(
        "reports.html",
        patient_count=patient_count,
        record_count=record_count,
        patients_with_records=patients_with_records,
        patients_with_allergies=patients_with_allergies,
        male_count=male_count,
        female_count=female_count,
        blood_types=blood_types,
        average_weight=average_weight,
        average_height=average_height
    )

# ==========================================
# ثبت بیمار جدید
# ==========================================

@app.route(
    "/add-patient",
    methods=["GET", "POST"]
)
def add_patient():

    if request.method == "POST":

        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        national_id = request.form["national_id"]
        birth_date = request.form["birth_date"]
        gender = request.form["gender"]
        phone = request.form["phone"]
        blood_type = request.form["blood_type"]
        weight = request.form["weight"]
        height = request.form["height"]
        emergency_phone = request.form["emergency_phone"]
        medical_history = request.form["medical_history"]
        allergies = request.form["allergies"]
        notes = request.form["notes"]

        connection = get_database_connection()

        connection.execute(
            """
            INSERT INTO patients (
                first_name,
                last_name,
                national_id,
                birth_date,
                gender,
                phone,
                blood_type,
                weight,
                height,
                emergency_phone,
                medical_history,
                allergies,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                first_name,
                last_name,
                national_id,
                birth_date,
                gender,
                phone,
                blood_type,
                weight,
                height,
                emergency_phone,
                medical_history,
                allergies,
                notes
            )
        )

        connection.commit()

        connection.close()

        return redirect("/")

    return render_template("add_patient.html")


# ==========================================
# فهرست کلی سوابق پزشکی
# ==========================================

@app.route("/medical-records")
def medical_records_list():

    connection = get_database_connection()

    patients = connection.execute(
        """
        SELECT
            patients.id,
            patients.first_name,
            patients.last_name,
            patients.national_id,
            COUNT(medical_records.id) AS record_count
        FROM patients
        LEFT JOIN medical_records
            ON patients.id = medical_records.patient_id
        GROUP BY patients.id
        ORDER BY patients.id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "medical_records_list.html",
        patients=patients
    )

# ==========================================
# سوابق پزشکی بیمار
# ==========================================

@app.route(
    "/patient/<int:patient_id>/medical-records",
    methods=["GET"]
)
def medical_records(patient_id):

    connection = get_database_connection()

    patient = connection.execute(
        """
        SELECT *
        FROM patients
        WHERE id = ?
        """,
        (patient_id,)
    ).fetchone()

    if patient is None:

        connection.close()

        return "بیمار پیدا نشد", 404


    records = connection.execute(
        """
        SELECT *
        FROM medical_records
        WHERE patient_id = ?
        ORDER BY id DESC
        """,
        (patient_id,)
    ).fetchall()


    connection.close()


    return render_template(
        "medical_records.html",
        patient=patient,
        records=records
    )


# ==========================================
# ثبت سابقه پزشکی جدید
# ==========================================

@app.route(
    "/patient/<int:patient_id>/medical-records",
    methods=["POST"]
)
def add_medical_record(patient_id):

    visit_date = request.form.get(
        "visit_date",
        ""
    ).strip()

    reason = request.form.get(
        "reason",
        ""
    ).strip()

    diagnosis = request.form.get(
        "diagnosis",
        ""
    ).strip()

    medications = request.form.get(
        "medications",
        ""
    ).strip()

    doctor_name = request.form.get(
        "doctor_name",
        ""
    ).strip()

    notes = request.form.get(
        "notes",
        ""
    ).strip()


    connection = get_database_connection()


    patient = connection.execute(
        """
        SELECT id
        FROM patients
        WHERE id = ?
        """,
        (patient_id,)
    ).fetchone()


    if patient is None:

        connection.close()

        return "بیمار پیدا نشد", 404


    connection.execute(
        """
        INSERT INTO medical_records (
            patient_id,
            visit_date,
            reason,
            diagnosis,
            medications,
            doctor_name,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            patient_id,
            visit_date,
            reason,
            diagnosis,
            medications,
            doctor_name,
            notes
        )
    )


    connection.commit()

    connection.close()


    return redirect(
        f"/patient/{patient_id}/medical-records"
    )


# ==========================================
# حذف سابقه پزشکی
# ==========================================

@app.route(
    "/medical-record/<int:record_id>/delete",
    methods=["POST"]
)
def delete_medical_record(record_id):

    connection = get_database_connection()


    record = connection.execute(
        """
        SELECT patient_id
        FROM medical_records
        WHERE id = ?
        """,
        (record_id,)
    ).fetchone()


    if record is None:

        connection.close()

        return "سابقه پزشکی پیدا نشد", 404


    patient_id = record["patient_id"]


    connection.execute(
        """
        DELETE FROM medical_records
        WHERE id = ?
        """,
        (record_id,)
    )


    connection.commit()

    connection.close()


    return redirect(
        f"/patient/{patient_id}/medical-records"
    )


# ==========================================
# اجرای برنامه
# ==========================================
if __name__ == "__main__":

    app.run(debug=True)