import sqlite3


def create_database():

    connection = sqlite3.connect("patients.db")

    cursor = connection.cursor()


    # ==============================
    # جدول بیماران
    # ==============================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            national_id TEXT,
            birth_date TEXT,
            gender TEXT,
            phone TEXT,
            blood_type TEXT,
            weight REAL,
            height REAL,
            emergency_phone TEXT,
            medical_history TEXT,
            allergies TEXT,
            notes TEXT
        )
    """)


    # ==============================
    # جدول سوابق پزشکی
    # ==============================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medical_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            patient_id INTEGER NOT NULL,

            visit_date TEXT,

            reason TEXT,

            diagnosis TEXT,

            medications TEXT,

            doctor_name TEXT,

            notes TEXT,

            FOREIGN KEY (patient_id)
                REFERENCES patients(id)
                ON DELETE CASCADE
        )
    """)


    connection.commit()

    connection.close()


if __name__ == "__main__":

    create_database()

    print("Database created successfully.")