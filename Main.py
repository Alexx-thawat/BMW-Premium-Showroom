"""BMW Premium Showroom - โปรแกรมหลัก"""

# ==================== ค่าตั้งต้น ====================
"""ค่าตั้งต้นของโชว์รูมและระบบจองสาธิต"""
import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DB_NAME = os.environ.get("BMW_DB_PATH", str(APP_DIR / "DB_BMW.db"))
DEPOSIT_AMOUNT = 10000.0
PAYMENT_MODE = "demo"
PAYMENT_INSTRUCTIONS = "โหมดสาธิตสำหรับโปรเจกต์ ไม่ต้องโอนเงินจริง ใช้ภาพหลักฐานจำลองเพื่อทดสอบให้พนักงานตรวจสอบ"
CONTACT = {"ชื่อ": "BMW Showroom Demo", "อีเมล": "demo@example.com", "โทรศัพท์": "0000000000",
           "ที่อยู่": "ข้อมูลสำหรับสาธิต", "Facebook": "BMW Showroom Demo"}



ROLE = {"customer": "ลูกค้า", "employee": "พนักงาน"}



STATUS = {"Available": "พร้อมขาย", "Sold": "ขายแล้ว", "Pending": "รอดำเนินการ",
          "Completed": "ซื้อสำเร็จ", "CancelRequested": "รออนุมัติยกเลิก",
          "Cancelled": "ยกเลิกแล้ว", "Unavailable": "รถไม่พร้อมขาย"}



SERIES = {"Series": ["1 Series", "2 Series", "3 Series", "4 Series", "5 Series", "7 Series", "8 Series"],
          "X": ["X1", "X2", "X3", "X4", "X5", "X6", "X7"],
          "i": ["i4", "i5", "i7", "iX", "iX1", "iX2", "iX3"], "Z": ["Z4"]}



STATUS.update({"Reserved":"ถูกจองไว้", "AwaitingPayment":"รอชำระค่าจอง", "PaymentReview":"รอตรวจสลิปค่าจอง", "Booked":"ยืนยันจองแล้ว"})

# ==================== ความปลอดภัย ====================
"""การสร้างและตรวจรหัสผ่าน"""
import hashlib
import hmac
import secrets

# หน้าที่: สร้างค่าแฮชพร้อมเกลือจากรหัสผ่านก่อนเก็บในฐานข้อมูล
def password_hash(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200000)
    return f"200000${salt.hex()}${digest.hex()}"


# หน้าที่: ตรวจว่ารหัสผ่านที่กรอกตรงกับค่าแฮชที่บันทึกไว้หรือไม่
def password_ok(password, stored):
    try:
        count, salt, expected = stored.split("$")
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(count)).hex()
        return hmac.compare_digest(actual, expected)
    except ValueError:
        return False



# ==================== ฐานข้อมูล ====================
"""เปิดฐานข้อมูลและเตรียมโครงสร้างตารางเดิม"""
import json
import sqlite3
from contextlib import closing
from pathlib import Path


# หน้าที่: เปิดไฟล์ฐานข้อมูล SQLite และเปิดการตรวจความสัมพันธ์ระหว่างตาราง
def db():
    """เปิดการเชื่อมต่อฐานข้อมูล DB_BMW.db และเปิดใช้ Foreign Key"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# หน้าที่: อ่านผลคำสั่ง SQL หลายแถวแล้วส่งกลับเป็นข้อมูลที่ใช้งานง่าย
def rows(sql, params=()):
    with closing(db()) as conn:
        return [dict(r) for r in conn.execute(sql, params)]


# หน้าที่: เรียกคำสั่ง SQL ที่เพิ่ม แก้ไข หรือลบข้อมูลและบันทึกผล
def run(sql, params=()):
    with closing(db()) as conn, conn:
        return conn.execute(sql, params).lastrowid


# หน้าที่: ตรวจตารางและคอลัมน์แบบอ่านอย่างเดียวก่อนเริ่มระบบ
def database_is_ready():
    """ตรวจโครงสร้างเดิมแบบอ่านอย่างเดียว เพื่อไม่เขียนฐานข้อมูลทุกครั้งที่เปิด"""
    if not Path(DB_NAME).is_file():
        return False
    try:
        with closing(sqlite3.connect(f"file:{Path(DB_NAME).as_posix()}?mode=ro", uri=True, timeout=3)) as conn:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {"cars", "customers", "users", "sales", "purchase_requests"} <= tables:
                return False
            car_columns = {row[1] for row in conn.execute("PRAGMA table_info(cars)")}
            user_columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
            sale_columns = {row[1] for row in conn.execute("PRAGMA table_info(sales)")}
            return ({"image_name", "image_data_2", "image_name_2", "image_data_3", "image_name_3"} <= car_columns
                    and "email" in user_columns
                    and "staff_snapshot" in sale_columns
                    and conn.execute("SELECT 1 FROM users WHERE role='employee'").fetchone() is not None)
    except sqlite3.Error:
        return False


# หน้าที่: เก็บชื่อผู้ดูแลรายการเก่า แล้วนำบัญชีผู้บริหารเดิมออกโดยไม่ลบประวัติ
def _retire_executive_accounts(conn):
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for account in conn.execute("SELECT * FROM users WHERE role='executive'").fetchall():
        user_id = account["user_id"]
        staff = dict(name=account["full_name"] or account["username"], code=account["staff_code"], phone=account["phone"])
        for sale in conn.execute("SELECT * FROM sales WHERE staff_user_id=? OR cancelled_by_user_id=?", (user_id, user_id)).fetchall():
            try:
                snapshot = json.loads(sale["staff_snapshot"] or "{}")
            except ValueError:
                snapshot = {}
            if not isinstance(snapshot, dict):
                snapshot = {}
            if sale["staff_user_id"] == user_id:
                snapshot.setdefault("sale_staff", staff)
            if sale["cancelled_by_user_id"] == user_id:
                snapshot.setdefault("cancellation_staff", staff)
            conn.execute("UPDATE sales SET staff_snapshot=? WHERE sale_id=?", (json.dumps(snapshot, ensure_ascii=False), sale["sale_id"]))
        referenced = conn.execute("""SELECT pr.*,s.staff_user_id AS sale_staff_id,s.cancelled_by_user_id AS sale_canceller_id
            FROM purchase_requests pr LEFT JOIN sales s ON s.sale_id=pr.sale_id
            WHERE pr.assigned_staff_id=? OR pr.cancelled_by_user_id=? OR s.staff_user_id=? OR s.cancelled_by_user_id=?""",
            (user_id, user_id, user_id, user_id)).fetchall()
        for request in referenced:
            try:
                snapshot = json.loads(request["snapshot"] or "{}")
            except ValueError:
                snapshot = {}
            if not isinstance(snapshot, dict):
                snapshot = {}
            if request["sale_staff_id"] == user_id:
                snapshot.setdefault("sale_staff", staff)
            if request["assigned_staff_id"] == user_id:
                snapshot.setdefault("booking_staff", staff)
            if request["cancelled_by_user_id"] == user_id or request["sale_canceller_id"] == user_id:
                snapshot.setdefault("cancellation_staff", staff)
            conn.execute("UPDATE purchase_requests SET snapshot=? WHERE request_id=?", (json.dumps(snapshot, ensure_ascii=False), request["request_id"]))
        for table, column in (("sales", "staff_user_id"), ("sales", "cancelled_by_user_id"),
                              ("purchase_requests", "assigned_staff_id"), ("purchase_requests", "cancelled_by_user_id")):
            conn.execute(f"UPDATE {table} SET {column}=NULL WHERE {column}=?", (user_id,))
        if "booking_payments" in tables:
            conn.execute("UPDATE booking_payments SET reviewed_by=NULL WHERE reviewed_by=?", (user_id,))
        conn.execute("DELETE FROM users WHERE user_id=? AND role='executive'", (user_id,))


# หน้าที่: สร้างหรือปรับตารางฐานข้อมูลเฉพาะเมื่อโครงสร้างยังไม่พร้อม
def init_db():
    if database_is_ready():
        return
    with closing(db()) as conn, conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS cars(car_id INTEGER PRIMARY KEY,model TEXT NOT NULL,year INTEGER NOT NULL,
          color TEXT NOT NULL,price REAL NOT NULL,status TEXT NOT NULL DEFAULT 'Available',series TEXT NOT NULL DEFAULT '',
          description TEXT NOT NULL DEFAULT '',image_data BLOB,image_name TEXT NOT NULL DEFAULT '',
          image_data_2 BLOB,image_name_2 TEXT NOT NULL DEFAULT '',
          image_data_3 BLOB,image_name_3 TEXT NOT NULL DEFAULT '',is_demo INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS customers(customer_id INTEGER PRIMARY KEY,fname TEXT NOT NULL,lname TEXT NOT NULL,
          phone TEXT NOT NULL,email TEXT,address TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,username TEXT NOT NULL UNIQUE COLLATE NOCASE,
          password_hash TEXT NOT NULL,role TEXT NOT NULL,customer_id INTEGER UNIQUE REFERENCES customers(customer_id),
          full_name TEXT NOT NULL DEFAULT '',staff_code TEXT NOT NULL DEFAULT '',phone TEXT NOT NULL DEFAULT '',
          email TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS sales(sale_id INTEGER PRIMARY KEY,customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
          car_id INTEGER NOT NULL REFERENCES cars(car_id),sale_date TEXT NOT NULL,sale_price REAL NOT NULL,
          staff_user_id INTEGER REFERENCES users(user_id),status TEXT NOT NULL DEFAULT 'Completed',cancelled_at TEXT,
          cancelled_by_user_id INTEGER REFERENCES users(user_id),staff_snapshot TEXT NOT NULL DEFAULT '{}');
        CREATE TABLE IF NOT EXISTS purchase_requests(request_id INTEGER PRIMARY KEY,customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
          car_id INTEGER NOT NULL REFERENCES cars(car_id),created_at TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'Pending',
          snapshot TEXT NOT NULL,sale_id INTEGER REFERENCES sales(sale_id),assigned_staff_id INTEGER REFERENCES users(user_id),
          cancellation_requested_at TEXT,cancelled_at TEXT,cancelled_by_user_id INTEGER REFERENCES users(user_id));
        """)
        car_columns={r[1] for r in conn.execute("PRAGMA table_info(cars)")}
        for name,kind in (("image_name","TEXT NOT NULL DEFAULT ''"),
                          ("image_data_2","BLOB"),("image_name_2","TEXT NOT NULL DEFAULT ''"),
                          ("image_data_3","BLOB"),("image_name_3","TEXT NOT NULL DEFAULT ''")):
            if name not in car_columns:
                conn.execute(f"ALTER TABLE cars ADD COLUMN {name} {kind}")
        user_columns={r[1] for r in conn.execute("PRAGMA table_info(users)")}
        if "email" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN email TEXT NOT NULL DEFAULT ''")
        sale_columns = {row[1] for row in conn.execute("PRAGMA table_info(sales)")}
        if "staff_snapshot" not in sale_columns:
            conn.execute("ALTER TABLE sales ADD COLUMN staff_snapshot TEXT NOT NULL DEFAULT '{}'")
        _retire_executive_accounts(conn)
        if not conn.execute("SELECT 1 FROM users WHERE role='employee'").fetchone():
            username = "P1"
            suffix = 1
            while conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
                username = f"P1_DEMO_{suffix}"
                suffix += 1
            conn.execute("INSERT INTO users(username,password_hash,role,full_name,staff_code,phone,email) "
                         "VALUES(?,?,'employee','พนักงานสาธิต','001','0990000001','staff@example.com')",
                         (username, password_hash("12345678")))



# ==================== สต็อกรถ ====================
"""จัดการจำนวนสต็อกโดยยังคงรถหนึ่งแถวต่อหนึ่งคันเพื่อให้การจองล็อกรถได้จริง"""
from contextlib import closing


GROUP_COLUMNS = ("model", "year", "series", "color", "price")


# รวมจำนวนรถตามรุ่นและสีสำหรับหน้าพนักงานและผู้บริหาร
def stock_summary():
    return rows("""SELECT
        COALESCE(MIN(CASE WHEN status='Available' THEN car_id END),MIN(car_id)) AS control_car_id,
        model,year,series,color,price,
        SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) AS available_qty,
        SUM(CASE WHEN status='Reserved' THEN 1 ELSE 0 END) AS reserved_qty,
        SUM(CASE WHEN status='Sold' THEN 1 ELSE 0 END) AS sold_qty,
        COUNT(*) AS total_qty
        FROM cars GROUP BY model,year,series,color,price
        ORDER BY series,model,year,color""")


def _group_where(car):
    return "model=? AND year=? AND series=? AND color=? AND price=?", tuple(car[key] for key in GROUP_COLUMNS)


# เพิ่มหรือลดเฉพาะรถพร้อมขาย โดยไม่แตะคันที่จองหรือขายแล้ว
def adjust_stock(car_id, delta):
    delta = int(delta)
    if delta == 0 or abs(delta) > 100:
        raise ValueError("เพิ่มหรือลดได้ครั้งละ 1–100 คัน")
    with closing(db()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            car = conn.execute("SELECT * FROM cars WHERE car_id=?", (int(car_id),)).fetchone()
            if not car:
                raise ValueError("ไม่พบรุ่นรถที่ต้องการปรับสต็อก")
            where, params = _group_where(car)
            if delta > 0:
                for _ in range(delta):
                    conn.execute("""INSERT INTO cars(model,year,color,price,status,series,description,
                        image_data,image_name,image_data_2,image_name_2,image_data_3,image_name_3,is_demo)
                        VALUES(?,?,?,?,'Available',?,?,?,?,?,?,?,?,?)""",
                        (car["model"], car["year"], car["color"], car["price"], car["series"],
                         car["description"], car["image_data"], car["image_name"],
                         car["image_data_2"], car["image_name_2"], car["image_data_3"],
                         car["image_name_3"], car["is_demo"]))
            else:
                wanted = -delta
                removable = conn.execute(f"""SELECT c.car_id FROM cars c WHERE {where} AND c.status='Available'
                    AND NOT EXISTS(SELECT 1 FROM purchase_requests p WHERE p.car_id=c.car_id)
                    AND NOT EXISTS(SELECT 1 FROM sales s WHERE s.car_id=c.car_id)
                    ORDER BY CASE WHEN c.image_data IS NULL THEN 0 ELSE 1 END,c.car_id DESC LIMIT ?""",
                    (*params, wanted)).fetchall()
                if len(removable) < wanted:
                    raise ValueError(f"ลดได้สูงสุด {len(removable)} คัน เพราะรถบางคันมีประวัติหรือกำลังใช้งาน")
                conn.executemany("DELETE FROM cars WHERE car_id=?", [(item[0],) for item in removable])
            quantity = conn.execute(f"SELECT COUNT(*) FROM cars WHERE {where} AND status='Available'", params).fetchone()[0]
            conn.commit()
            return quantity
        except Exception:
            conn.rollback()
            raise


# เติมรถพร้อมขายให้แต่ละรุ่นรวมตามเป้าหมาย และกระจายจำนวนระหว่างสีที่มีอยู่
def seed_stock_per_model(target=50):
    target = int(target)
    if target < 1 or target > 500:
        raise ValueError("จำนวนสต็อกต่อรุ่นต้องอยู่ระหว่าง 1–500")
    with closing(db()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            models = conn.execute("SELECT DISTINCT model,year,series,price FROM cars ORDER BY model").fetchall()
            changed = 0
            for model in models:
                colors = conn.execute("""SELECT color,MIN(car_id) AS template_id,
                    SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) AS available_qty
                    FROM cars WHERE model=? AND year=? AND series=? AND price=? GROUP BY color ORDER BY color""",
                    tuple(model)).fetchall()
                base, remainder = divmod(target, len(colors))
                for index, color in enumerate(colors):
                    desired = base + (1 if index < remainder else 0)
                    missing = max(0, desired - int(color["available_qty"]))
                    template = conn.execute("SELECT * FROM cars WHERE car_id=?", (color["template_id"],)).fetchone()
                    for _ in range(missing):
                        conn.execute("""INSERT INTO cars(model,year,color,price,status,series,description,
                            image_data,image_name,image_data_2,image_name_2,image_data_3,image_name_3,is_demo)
                            VALUES(?,?,?,?,'Available',?,?,NULL,'',NULL,'',NULL,'',?)""",
                            (template["model"], template["year"], template["color"], template["price"],
                             template["series"], template["description"], template["is_demo"]))
                    changed += missing
            conn.commit()
            return changed
        except Exception:
            conn.rollback()
            raise

# ==================== คำสั่งซื้อและการชำระเงิน ====================
"""งานจองรถ หลักฐานการชำระเงิน และสรุปข้อมูลจากฐานข้อมูลจริง."""
import io
import json
import re
from contextlib import closing, contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from PIL import Image


ACTIVE_STATUSES = ("AwaitingPayment", "PaymentReview", "Booked", "CancelRequested")
SCHEMA_VERSION = "2"


# เปิดรายการบันทึกแบบล็อกก่อนอ่าน เพื่อกันลูกค้าจองรถคันเดียวกันพร้อมกัน
@contextmanager
def _transaction():
    with closing(db()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


# สร้างวันเวลาสำหรับบันทึกประวัติรายการ
def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# อ่านภาพรวมที่บันทึกตอนจอง แม้ข้อมูลรถปัจจุบันจะถูกแก้ภายหลัง
def _snapshot(value):
    try:
        result = json.loads(value or "{}")
        return result if isinstance(result, dict) else {}
    except (ValueError, TypeError):
        return {}


# ตรวจจำนวนเงินให้เป็นบวกและปัดเป็นสองตำแหน่ง
def _amount(value):
    try:
        result = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("กรอกจำนวนเงินเป็นตัวเลข") from None
    if not result.is_finite() or result <= 0:
        raise ValueError("จำนวนเงินต้องมากกว่า 0")
    return float(result)


# ตรวจบทบาทจากบัญชีจริงในฐานข้อมูลก่อนทำรายการ
def _actor(conn, user, roles):
    found = conn.execute("SELECT * FROM users WHERE user_id=?", (user.get("user_id"),)).fetchone()
    if not found or found["role"] not in roles or found["role"] != user.get("role"):
        raise PermissionError("บัญชีนี้ไม่มีสิทธิ์ทำรายการ")
    return found


# ตรวจเจ้าของรายการก่อนเปิดดูหรือส่งหลักฐานการชำระเงิน
def _request(conn, user, request_id, roles=("customer", "employee")):
    actor = _actor(conn, user, roles)
    request = conn.execute("SELECT * FROM purchase_requests WHERE request_id=?", (request_id,)).fetchone()
    if not request:
        raise ValueError("ไม่พบรายการจอง")
    if actor["role"] == "customer" and request["customer_id"] != actor["customer_id"]:
        raise PermissionError("ดูได้เฉพาะรายการของตนเอง")
    return request


# ตรวจว่าปรับฐานข้อมูลจองเสร็จแล้วโดยอ่านอย่างเดียว
def _schema_ready():
    with closing(db()) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"booking_details", "booking_payments", "visitors", "booking_meta"} <= tables:
            return False
        version = conn.execute("SELECT value FROM booking_meta WHERE key='schema_version'").fetchone()
        return bool(version and version[0] == SCHEMA_VERSION)


# เพิ่มตารางจองและแปลงคำขอเก่าเพียงครั้งเดียว โดยเก็บประวัติเดิมไว้
def initialize_booking_system():
    if _schema_ready():
        return
    with _transaction() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS booking_details(
            request_id INTEGER PRIMARY KEY REFERENCES purchase_requests(request_id),
            deposit_amount REAL NOT NULL CHECK(deposit_amount>=0),
            purchase_method TEXT NOT NULL DEFAULT 'cash',
            order_type TEXT NOT NULL DEFAULT 'booking',delivery_date TEXT NOT NULL DEFAULT '',
            terms_accepted INTEGER NOT NULL DEFAULT 0,confirmed_at TEXT,
            cancellation_from TEXT NOT NULL DEFAULT '')""")
        booking_columns = {row[1] for row in conn.execute("PRAGMA table_info(booking_details)")}
        if "order_type" not in booking_columns:
            conn.execute("ALTER TABLE booking_details ADD COLUMN order_type TEXT NOT NULL DEFAULT 'booking'")
        conn.execute("""CREATE TABLE IF NOT EXISTS booking_payments(
            payment_id INTEGER PRIMARY KEY,request_id INTEGER NOT NULL REFERENCES purchase_requests(request_id),
            purpose TEXT NOT NULL CHECK(purpose IN ('Deposit','Balance')),
            amount REAL NOT NULL CHECK(amount>0),slip_data BLOB NOT NULL,slip_name TEXT NOT NULL,
            transferred_at TEXT NOT NULL,reference TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','Verified','Rejected')),
            review_note TEXT NOT NULL DEFAULT '',reviewed_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
            created_at TEXT NOT NULL,reviewed_at TEXT)""")
        conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS one_current_booking_payment
            ON booking_payments(request_id,purpose) WHERE status IN ('Pending','Verified')""")
        conn.execute("""CREATE TABLE IF NOT EXISTS visitors(visitor_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,phone TEXT NOT NULL,created_at TEXT NOT NULL)""")
        conn.execute("CREATE TABLE IF NOT EXISTS booking_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        for request in conn.execute("SELECT * FROM purchase_requests ORDER BY request_id").fetchall():
            snapshot = _snapshot(request["snapshot"])
            price = float(snapshot.get("price") or 0)
            legacy_paid = bool(request["sale_id"])
            deposit = 0 if legacy_paid else min(float(DEPOSIT_AMOUNT), price) if price > 0 else float(DEPOSIT_AMOUNT)
            conn.execute("""INSERT OR IGNORE INTO booking_details
                (request_id,deposit_amount,terms_accepted) VALUES(?,?,0)""", (request["request_id"], deposit))
            if request["status"] == "Pending":
                changed = conn.execute("UPDATE cars SET status='Reserved' WHERE car_id=? AND status='Available'",
                                       (request["car_id"],)).rowcount
                new_status = "AwaitingPayment" if changed else "Unavailable"
                conn.execute("UPDATE purchase_requests SET status=? WHERE request_id=?",
                             (new_status, request["request_id"]))
            elif request["status"] == "CancelRequested":
                original = "Completed" if request["sale_id"] else "AwaitingPayment"
                conn.execute("UPDATE booking_details SET cancellation_from=? WHERE request_id=?",
                             (original, request["request_id"]))
                if not request["sale_id"]:
                    other = conn.execute("""SELECT 1 FROM purchase_requests WHERE car_id=? AND request_id!=?
                        AND status IN ('AwaitingPayment','PaymentReview','Booked','CancelRequested')""",
                        (request["car_id"], request["request_id"])).fetchone()
                    car = conn.execute("SELECT status FROM cars WHERE car_id=?", (request["car_id"],)).fetchone()
                    if other or not car or car["status"] not in ("Available", "Reserved"):
                        conn.execute("UPDATE purchase_requests SET status='Unavailable' WHERE request_id=?",
                                     (request["request_id"],))
                    else:
                        conn.execute("UPDATE cars SET status='Reserved' WHERE car_id=? AND status='Available'",
                                     (request["car_id"],))
        conn.execute("INSERT OR REPLACE INTO booking_meta(key,value) VALUES('schema_version',?)", (SCHEMA_VERSION,))


# รับชื่อและเบอร์โทรของผู้เข้าชมก่อนเปิดแคตตาล็อก
def record_visitor(name, phone):
    name, phone = str(name).strip(), re.sub(r"[\s-]", "", str(phone))
    if len(name) < 2 or not re.fullmatch(r"0\d{8,9}", phone):
        raise ValueError("กรอกชื่อและเบอร์โทร 9–10 หลักที่ขึ้นต้นด้วย 0")
    with _transaction() as conn:
        return conn.execute("INSERT INTO visitors(name,phone,created_at) VALUES(?,?,?)", (name, phone, _now())).lastrowid


# แสดงประวัติผู้ที่กรอกชื่อและเบอร์โทรก่อนเข้าชมรถให้พนักงานตรวจสอบ
def visitor_rows(user):
    with closing(db()) as conn:
        _actor(conn, user, ("employee",))
        return [dict(row) for row in conn.execute("""SELECT visitor_id,name,phone,created_at
            FROM visitors ORDER BY visitor_id DESC""").fetchall()]


# ตรวจข้อมูลลูกค้าและกันรถหนึ่งคันไว้ในรายการจองทันที
def create_booking(user, car_id, details):
    method = "cash"
    order_type = "direct"
    if details.get("terms_accepted") not in (True, 1):
        raise ValueError("กรุณายอมรับเงื่อนไขการสั่งซื้อก่อนยืนยัน")
    delivery = ""
    with _transaction() as conn:
        actor = _actor(conn, user, ("customer",))
        customer = conn.execute("SELECT * FROM customers WHERE customer_id=?", (actor["customer_id"],)).fetchone()
        if not customer:
            raise ValueError("ไม่พบข้อมูลลูกค้าของบัญชีนี้")
        name = str(details.get("customer_name", f"{customer['fname']} {customer['lname']}")).strip()
        phone = re.sub(r"[\s-]", "", str(details.get("phone", customer["phone"]) or ""))
        email = str(details.get("email", customer["email"]) or "").strip()
        address = str(details.get("address", customer["address"]) or "").strip()
        if len(name) < 2 or not all((phone, email, address)):
            raise ValueError("กรอกชื่อ นามสกุล เบอร์โทร อีเมล และที่อยู่ในข้อมูลของฉันให้ครบก่อนสั่งซื้อ")
        if not re.fullmatch(r"0\d{8,9}", phone):
            raise ValueError("ตรวจสอบเบอร์โทรลูกค้าให้ถูกต้อง")
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise ValueError("ตรวจสอบอีเมลลูกค้าให้ถูกต้อง")
        car = conn.execute("SELECT * FROM cars WHERE car_id=? AND status='Available'", (car_id,)).fetchone()
        if not car:
            raise ValueError("รถสีนี้หมดแล้ว กรุณาเลือกสีอื่น")
        price = _amount(car["price"])
        deposit = price
        snapshot = dict(customer=name, phone=phone,
                        email=email, address=address, model=car["model"],
                        series=car["series"], year=car["year"], color=car["color"], price=price,
                        payment_mode=PAYMENT_MODE)
        conn.execute("UPDATE cars SET status='Reserved' WHERE car_id=? AND status='Available'", (car_id,))
        request_id = conn.execute("""INSERT INTO purchase_requests
            (customer_id,car_id,created_at,status,snapshot) VALUES(?,?,?,'AwaitingPayment',?)""",
            (customer["customer_id"], car_id, _now(), json.dumps(snapshot, ensure_ascii=False))).lastrowid
        conn.execute("""INSERT INTO booking_details
            (request_id,deposit_amount,purchase_method,order_type,delivery_date,terms_accepted)
            VALUES(?,?,?,?,?,1)""", (request_id, deposit, method, order_type, delivery))
        return request_id


# ตรวจว่าไฟล์สลิปเป็นภาพจริงและมีขนาดเหมาะสมก่อนเก็บ
def _validate_slip(slip_bytes, slip_name):
    if not isinstance(slip_bytes, (bytes, bytearray)) or not slip_bytes or len(slip_bytes) > 10 * 1024 * 1024:
        raise ValueError("เลือกสลิปภาพ JPG PNG หรือ WEBP ขนาดไม่เกิน 10 MB")
    try:
        with Image.open(io.BytesIO(slip_bytes)) as image:
            if image.format not in ("JPEG", "PNG", "WEBP") or max(image.size) > 8000:
                raise ValueError("สลิปต้องเป็นภาพ JPG PNG หรือ WEBP และไม่ใหญ่เกิน 8000 พิกเซล")
            image.verify()
    except (OSError, SyntaxError, Image.DecompressionBombError):
        raise ValueError("ไฟล์สลิปนี้ไม่ใช่ภาพที่เปิดได้") from None
    name = str(slip_name or "slip.png").replace("\\", "/").split("/")[-1].strip()
    return bytes(slip_bytes), name[:180] or "slip.png"


# รวมยอดที่พนักงานตรวจผ่านและสลิปที่ยังรอตรวจของหนึ่งรายการ
def _payment_totals(conn, request_id):
    amounts = dict(deposit_paid=0.0, balance_paid=0.0, pending_amount=0.0, pending_slip_count=0)
    for payment in conn.execute("SELECT purpose,amount,status FROM booking_payments WHERE request_id=?", (request_id,)):
        if payment["status"] == "Verified":
            key = "deposit_paid" if payment["purpose"] == "Deposit" else "balance_paid"
            amounts[key] += payment["amount"]
        elif payment["status"] == "Pending":
            amounts["pending_amount"] += payment["amount"]
            amounts["pending_slip_count"] += 1
    return amounts


# รับหลักฐานค่าจองหรือยอดคงเหลือ โดยยังไม่ถือว่าชำระแล้วจนพนักงานตรวจ
def upload_payment_slip(user, request_id, purpose, amount, slip_bytes, slip_name, transferred_at, reference=""):
    if purpose not in ("Deposit", "Balance"):
        raise ValueError("เลือกค่าจองหรือยอดคงเหลือ")
    amount = _amount(amount)
    slip_bytes, slip_name = _validate_slip(slip_bytes, slip_name)
    try:
        transferred = datetime.fromisoformat(str(transferred_at).strip())
    except ValueError:
        raise ValueError("กรอกวันเวลาโอนเป็น YYYY-MM-DD HH:MM") from None
    if transferred.tzinfo is not None:
        raise ValueError("กรอกวันเวลาโอนตามเวลาท้องถิ่น")
    if transferred > datetime.now() + timedelta(minutes=5):
        raise ValueError("วันเวลาโอนต้องไม่เป็นเวลาในอนาคต")
    reference = str(reference or "").strip()[:120]
    with _transaction() as conn:
        request = _request(conn, user, request_id, ("customer",))
        try:
            booked_date = datetime.fromisoformat(request["created_at"]).date()
        except ValueError:
            booked_date = date.min
        if transferred.date() < booked_date:
            raise ValueError("วันเวลาโอนต้องไม่ก่อนวันที่สร้างรายการจองนี้")
        wanted_status = "AwaitingPayment" if purpose == "Deposit" else "Booked"
        if request["status"] != wanted_status:
            raise ValueError("สถานะรายการยังไม่สามารถส่งสลิปประเภทนี้ได้")
        details = conn.execute("SELECT * FROM booking_details WHERE request_id=?", (request_id,)).fetchone()
        totals = _payment_totals(conn, request_id)
        price = float(_snapshot(request["snapshot"]).get("price") or 0)
        expected = details["deposit_amount"] if purpose == "Deposit" else round(price - totals["deposit_paid"], 2)
        if abs(amount - expected) > 0.005:
            raise ValueError(f"ยอดที่ต้องชำระสำหรับรายการนี้คือ {expected:,.2f} บาท")
        if conn.execute("SELECT 1 FROM booking_payments WHERE request_id=? AND purpose=? AND status IN ('Pending','Verified')",
                        (request_id, purpose)).fetchone():
            raise ValueError("มีสลิปประเภทนี้ที่รอตรวจหรือยืนยันแล้ว กรุณาตรวจรายการเดิม")
        if reference and conn.execute("""SELECT 1 FROM booking_payments WHERE UPPER(TRIM(reference))=UPPER(?)
            AND status IN ('Pending','Verified')""", (reference,)).fetchone():
            raise ValueError("เลขอ้างอิงการโอนนี้ถูกใช้ในสลิปที่รอตรวจหรือยืนยันแล้ว")
        payment_id = conn.execute("""INSERT INTO booking_payments
            (request_id,purpose,amount,slip_data,slip_name,transferred_at,reference,created_at)
            VALUES(?,?,?,?,?,?,?,?)""", (request_id, purpose, amount, slip_bytes, slip_name,
                                        transferred.strftime("%Y-%m-%d %H:%M:%S"), reference, _now())).lastrowid
        if purpose == "Deposit":
            conn.execute("UPDATE purchase_requests SET status='PaymentReview' WHERE request_id=?", (request_id,))
        return payment_id


# ให้พนักงานตรวจสลิปและยืนยันการจองเมื่อค่าจองผ่านการตรวจ
def review_payment(user, payment_id, approve, note=""):
    note = str(note or "").strip()
    if not approve and not note:
        raise ValueError("กรอกเหตุผลที่ไม่ผ่านเพื่อให้ลูกค้าแก้ไขสลิป")
    with _transaction() as conn:
        actor = _actor(conn, user, ("employee",))
        payment = conn.execute("SELECT * FROM booking_payments WHERE payment_id=?", (payment_id,)).fetchone()
        if not payment or payment["status"] != "Pending":
            raise ValueError("สลิปนี้ไม่มีรายการรอตรวจแล้ว")
        request = conn.execute("SELECT * FROM purchase_requests WHERE request_id=?", (payment["request_id"],)).fetchone()
        expected_status = "PaymentReview" if payment["purpose"] == "Deposit" else "Booked"
        if request["status"] != expected_status:
            raise ValueError("รายการกำลังยกเลิกหรือปิดแล้ว กรุณาตรวจสถานะการจองก่อน")
        status = "Verified" if approve else "Rejected"
        conn.execute("UPDATE booking_payments SET status=?,review_note=?,reviewed_by=?,reviewed_at=? WHERE payment_id=?",
                     (status, note, actor["user_id"], _now(), payment_id))
        if payment["purpose"] == "Deposit":
            if not approve:
                conn.execute("UPDATE purchase_requests SET status='AwaitingPayment',assigned_staff_id=? WHERE request_id=?",
                             (actor["user_id"], request["request_id"]))
                return
            details = conn.execute("SELECT * FROM booking_details WHERE request_id=?", (request["request_id"],)).fetchone()
            snapshot = _snapshot(request["snapshot"])
            staff = dict(name=actor["full_name"], code=actor["staff_code"], phone=actor["phone"])
            snapshot["booking_staff"] = staff
            conn.execute("UPDATE booking_details SET confirmed_at=? WHERE request_id=?", (_now(), request["request_id"]))
            if details["order_type"] == "direct":
                if conn.execute("UPDATE cars SET status='Sold' WHERE car_id=? AND status='Reserved'", (request["car_id"],)).rowcount != 1:
                    raise ValueError("รถคันนี้ไม่ได้อยู่ในสถานะพร้อมยืนยันขาย")
                price = _amount(snapshot.get("price"))
                sale_id = conn.execute("""INSERT INTO sales(customer_id,car_id,sale_date,sale_price,staff_user_id,status)
                    VALUES(?,?,?,?,?,'Completed')""", (request["customer_id"], request["car_id"], date.today().isoformat(),
                    price, actor["user_id"])).lastrowid
                snapshot["sale_staff"] = staff
                conn.execute("""UPDATE purchase_requests SET status='Completed',sale_id=?,assigned_staff_id=?,snapshot=?
                    WHERE request_id=?""", (sale_id, actor["user_id"], json.dumps(snapshot, ensure_ascii=False), request["request_id"]))
            else:
                conn.execute("UPDATE purchase_requests SET status='Booked',assigned_staff_id=?,snapshot=? WHERE request_id=?",
                             (actor["user_id"], json.dumps(snapshot, ensure_ascii=False), request["request_id"]))


# ปิดการขายเมื่อค่าจองและยอดคงเหลือได้รับการตรวจครบเท่านั้น
def confirm_sale(user, request_id):
    with _transaction() as conn:
        actor = _actor(conn, user, ("employee",))
        request = _request(conn, user, request_id, ("employee",))
        if request["status"] != "Booked" or request["sale_id"]:
            raise ValueError("ยืนยันขายได้เฉพาะรายการจองที่ยืนยันแล้ว")
        snapshot = _snapshot(request["snapshot"])
        price = _amount(snapshot.get("price"))
        details = conn.execute("SELECT * FROM booking_details WHERE request_id=?", (request_id,)).fetchone()
        totals = _payment_totals(conn, request_id)
        if totals["deposit_paid"] + 0.005 < details["deposit_amount"] or totals["deposit_paid"] + totals["balance_paid"] + 0.005 < price:
            raise ValueError("ต้องตรวจค่าจองและยอดคงเหลือให้ครบราคาของรถก่อนยืนยันขาย")
        if conn.execute("UPDATE cars SET status='Sold' WHERE car_id=? AND status='Reserved'", (request["car_id"],)).rowcount != 1:
            raise ValueError("รถคันนี้ไม่ได้อยู่ในสถานะจอง กรุณาตรวจข้อมูลรถ")
        sale_id = conn.execute("""INSERT INTO sales(customer_id,car_id,sale_date,sale_price,staff_user_id,status)
            VALUES(?,?,?,?,?,'Completed')""", (request["customer_id"], request["car_id"], date.today().isoformat(), price, actor["user_id"])).lastrowid
        snapshot["sale_staff"] = dict(name=actor["full_name"], code=actor["staff_code"], phone=actor["phone"])
        conn.execute("UPDATE purchase_requests SET status='Completed',sale_id=?,assigned_staff_id=?,snapshot=? WHERE request_id=?",
                     (sale_id, actor["user_id"], json.dumps(snapshot, ensure_ascii=False), request_id))
        return sale_id


# คืนรถพร้อมขายเมื่อไม่มีรายการจองอื่นกำลังใช้งานรถคันนั้น
def _release_car(conn, car_id, request_id):
    placeholders = ",".join("?" for _ in ACTIVE_STATUSES)
    other = conn.execute(f"SELECT 1 FROM purchase_requests WHERE car_id=? AND request_id!=? AND status IN ({placeholders})",
                         (car_id, request_id, *ACTIVE_STATUSES)).fetchone()
    existing_sale = conn.execute("SELECT 1 FROM sales WHERE car_id=? AND status='Completed'", (car_id,)).fetchone()
    if not other and not existing_sale:
        conn.execute("UPDATE cars SET status='Available' WHERE car_id=? AND status IN ('Reserved','Sold')", (car_id,))


# ลูกค้าขอยกเลิก และให้พนักงานอนุมัติเมื่อมีหลักฐานหรือเงินที่ตรวจแล้ว
def cancel_booking(user, request_id, approve=False):
    with _transaction() as conn:
        actor = _actor(conn, user, ("customer", "employee"))
        request = _request(conn, user, request_id, ("customer", "employee"))
        if request["status"] in ("Cancelled", "Unavailable"):
            raise ValueError("รายการนี้ปิดแล้ว")
        now = _now()
        if actor["role"] == "customer":
            if request["status"] == "CancelRequested":
                raise ValueError("รายการนี้รอพนักงานอนุมัติยกเลิกแล้ว")
            payment = conn.execute("SELECT 1 FROM booking_payments WHERE request_id=? AND status IN ('Pending','Verified')",
                                   (request_id,)).fetchone()
            if request["status"] == "AwaitingPayment" and not payment:
                conn.execute("UPDATE purchase_requests SET status='Cancelled',cancelled_at=?,cancelled_by_user_id=? WHERE request_id=?",
                             (now, actor["user_id"], request_id))
                _release_car(conn, request["car_id"], request_id)
            else:
                conn.execute("UPDATE booking_details SET cancellation_from=? WHERE request_id=?", (request["status"], request_id))
                conn.execute("UPDATE purchase_requests SET status='CancelRequested',cancellation_requested_at=? WHERE request_id=?",
                             (now, request_id))
            return
        if not approve or request["status"] != "CancelRequested":
            raise ValueError("อนุมัติยกเลิกได้เฉพาะรายการที่ลูกค้าขอยกเลิก")
        if request["sale_id"]:
            conn.execute("UPDATE sales SET status='Cancelled',cancelled_at=?,cancelled_by_user_id=? WHERE sale_id=?",
                         (now, actor["user_id"], request["sale_id"]))
        conn.execute("UPDATE booking_payments SET status='Rejected',review_note=?,reviewed_by=?,reviewed_at=? WHERE request_id=? AND status='Pending'",
                     ("ยุติการตรวจเนื่องจากอนุมัติยกเลิกรายการจอง", actor["user_id"], now, request_id))
        conn.execute("UPDATE purchase_requests SET status='Cancelled',cancelled_at=?,cancelled_by_user_id=? WHERE request_id=?",
                     (now, actor["user_id"], request_id))
        _release_car(conn, request["car_id"], request_id)


# อ่านการจองตามสิทธิ์พร้อมยอดชำระที่คำนวณใหม่จากหลักฐาน
def booking_rows(user):
    with closing(db()) as conn:
        actor = _actor(conn, user, ("customer", "employee"))
        sql = """SELECT pr.*,c.fname||' '||c.lname AS customer,ca.model,ca.year,ca.color,ca.series,ca.price,
            COALESCE(u.full_name,'-') AS staff_name,COALESCE(u.staff_code,'-') AS staff_code,COALESCE(u.phone,'-') AS staff_phone,
            bd.deposit_amount,bd.purchase_method,bd.order_type,bd.delivery_date,bd.terms_accepted,bd.confirmed_at,bd.cancellation_from,
            (SELECT bp.status FROM booking_payments bp WHERE bp.request_id=pr.request_id ORDER BY bp.payment_id DESC LIMIT 1) AS last_payment_status,
            (SELECT bp.review_note FROM booking_payments bp WHERE bp.request_id=pr.request_id ORDER BY bp.payment_id DESC LIMIT 1) AS last_payment_note
            FROM purchase_requests pr JOIN customers c ON c.customer_id=pr.customer_id
            JOIN cars ca ON ca.car_id=pr.car_id JOIN booking_details bd ON bd.request_id=pr.request_id
            LEFT JOIN users u ON u.user_id=pr.assigned_staff_id"""
        params = ()
        if actor["role"] == "customer":
            sql += " WHERE pr.customer_id=?"
            params = (actor["customer_id"],)
        result = []
        for row in conn.execute(sql + " ORDER BY pr.request_id DESC", params).fetchall():
            item = dict(row)
            snapshot = _snapshot(item["snapshot"])
            for key in ("model", "year", "color", "series", "price", "customer"):
                if key in snapshot:
                    item[key] = snapshot[key]
            if item["staff_name"] in ("", "-"):
                staff = snapshot.get("sale_staff") or snapshot.get("booking_staff") or {}
                item["staff_name"] = staff.get("name") or "-"
                item["staff_code"] = staff.get("code") or "-"
                item["staff_phone"] = staff.get("phone") or "-"
            item.update(_payment_totals(conn, item["request_id"]))
            item["legacy_payment"] = bool(item["sale_id"] and item["deposit_amount"] == 0)
            item["paid_amount"] = round(item["deposit_paid"] + item["balance_paid"], 2)
            if item["legacy_payment"]:
                item["paid_amount"] = float(item["price"])
            item["remaining_amount"] = max(0.0, round(float(item["price"]) - item["paid_amount"], 2))
            item["refund_due"] = round(item["deposit_paid"] + item["balance_paid"], 2) if item["status"] == "Cancelled" else 0.0
            item["payment_status"] = ("Paid" if item["remaining_amount"] == 0 else "PendingReview" if item["pending_slip_count"]
                                      else "PartiallyPaid" if item["paid_amount"] else "Unpaid")
            result.append(item)
        return result


# อ่านรายการสลิปตามสิทธิ์ โดยไม่ส่งภาพทั้งหมดมาที่ตาราง
def payment_rows(user, request_id=None):
    with closing(db()) as conn:
        actor = _actor(conn, user, ("customer", "employee"))
        if request_id is not None:
            _request(conn, user, request_id)
        sql = """SELECT p.payment_id,p.request_id,p.purpose,p.amount,p.slip_name,p.transferred_at,p.reference,
            p.status,p.review_note,p.reviewed_by,p.created_at,p.reviewed_at,
            c.fname||' '||c.lname AS customer,c.phone AS customer_phone,c.email AS customer_email,
            ca.model,ca.color,ca.year,pr.created_at AS ordered_at,pr.snapshot,pr.status AS request_status
            FROM booking_payments p JOIN purchase_requests pr ON pr.request_id=p.request_id
            JOIN customers c ON c.customer_id=pr.customer_id JOIN cars ca ON ca.car_id=pr.car_id"""
        conditions, params = [], []
        if actor["role"] == "customer":
            conditions.append("pr.customer_id=?")
            params.append(actor["customer_id"])
        if request_id is not None:
            conditions.append("p.request_id=?")
            params.append(request_id)
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        result = []
        for row in conn.execute(sql + " ORDER BY p.payment_id DESC", params):
            item = dict(row)
            snapshot = _snapshot(item.pop("snapshot"))
            for key in ("customer", "model", "color", "year"):
                item[key] = snapshot.get(key, item[key])
            result.append(item)
        return result


# เปิดภาพสลิปที่ผู้ใช้มีสิทธิ์ดูเท่านั้น
def payment_slip(user, payment_id):
    with closing(db()) as conn:
        payment = conn.execute("SELECT * FROM booking_payments WHERE payment_id=?", (payment_id,)).fetchone()
        if not payment:
            raise ValueError("ไม่พบสลิป")
        _request(conn, user, payment["request_id"])
        return dict(payment)


# สรุปยอดลูกค้าโดยแยกชำระครบ ค่าจอง และสลิปรอตรวจอย่างชัดเจน
def customer_summary(user):
    if user.get("role") != "customer":
        raise PermissionError("ใช้สำหรับสรุปข้อมูลลูกค้า")
    requests = booking_rows(user)
    active = [item for item in requests if item["status"] not in ("Cancelled", "Unavailable")]
    bought = [item for item in active if item["status"] == "Completed" or item["cancellation_from"] == "Completed"]
    paid_count = sum(item["remaining_amount"] == 0 for item in active)
    return dict(bought_count=len(bought), bought_total=round(sum(float(item["price"]) for item in bought), 2),
                order_count=len(active), order_total=round(sum(float(item["price"]) for item in active), 2),
                paid_count=paid_count, unpaid_count=len(active) - paid_count,
                paid_amount=round(sum(item["paid_amount"] for item in active), 2),
                remaining_amount=round(sum(item["remaining_amount"] for item in active), 2),
                cancelled_count=sum(item["status"] == "Cancelled" for item in requests),
                deposit_paid_count=sum(item["deposit_paid"] > 0 for item in active),
                pending_slip_count=sum(item["pending_slip_count"] for item in active),
                pending_review_count=sum(item["pending_slip_count"] for item in active),
                awaiting_payment_count=sum(item["status"] == "AwaitingPayment" for item in active),
                awaiting_deposit_count=sum(item["status"] == "AwaitingPayment" for item in active),
                booked_count=sum(item["status"] == "Booked" for item in active))


# กำหนดช่วงวันที่ของยอดขายที่นำมาวิเคราะห์
def _period_filter(period):
    today = date.today()
    if period in ("all", None):
        return "", ()
    if period == "month":
        start = today.replace(day=1)
    elif period == "year":
        start = today.replace(month=1, day=1)
    else:
        raise ValueError("เลือกช่วงทั้งหมด เดือนนี้ หรือปีนี้")
    return " AND s.sale_date>=? AND s.sale_date<=?", (start.isoformat(), today.isoformat())


# จัดอันดับรถขายดีจากการขายที่สำเร็จ พร้อมจำนวนรถพร้อมขายปัจจุบัน
def best_sellers(period="all"):
    date_sql, params = _period_filter(period)
    sales = rows("""SELECT s.sale_id,s.sale_price,ca.model,ca.series,
        (SELECT pr.snapshot FROM purchase_requests pr WHERE pr.sale_id=s.sale_id LIMIT 1) AS snapshot
        FROM sales s JOIN cars ca ON ca.car_id=s.car_id WHERE s.status='Completed'""" + date_sql, params)
    stock = {(item["model"], item["series"]): item["quantity"] for item in rows(
        "SELECT model,series,COUNT(*) AS quantity FROM cars WHERE status='Available' GROUP BY model,series")}
    groups = {}
    for sale in sales:
        snapshot = _snapshot(sale["snapshot"])
        model, series = snapshot.get("model", sale["model"]), snapshot.get("series", sale["series"])
        group = groups.setdefault((model, series), dict(model=model, series=series, sold_count=0, revenue=0.0))
        group["sold_count"] += 1
        group["revenue"] += sale["sale_price"]
    result = []
    for key, item in groups.items():
        item["available_qty"] = stock.get(key, 0)
        item["revenue"] = round(item["revenue"], 2)
        item["stock_note"] = ("พิจารณาเติมสต็อก" if item["sold_count"] >= item["available_qty"]
                              else "มีรถพร้อมขายเพียงพอเมื่อเทียบกับยอดขายช่วงนี้")
        result.append(item)
    return sorted(result, key=lambda item: (-item["sold_count"], -item["revenue"], item["model"]))


# สรุปยอดขายตามช่วงเวลาและงานจองปัจจุบันสำหรับพนักงาน
def staff_summary(period="all"):
    date_sql, params = _period_filter(period)
    sale = rows("SELECT COUNT(*) AS sold_count,COALESCE(SUM(s.sale_price),0) AS revenue FROM sales s WHERE s.status='Completed'" + date_sql, params)[0]
    stock = {item["status"]: item["quantity"] for item in rows("SELECT status,COUNT(*) AS quantity FROM cars GROUP BY status")}
    bookings = {item["status"]: item["quantity"] for item in rows("SELECT status,COUNT(*) AS quantity FROM purchase_requests GROUP BY status")}
    return dict(sold_count=sale["sold_count"], revenue=sale["revenue"], available_qty=stock.get("Available", 0),
                reserved_qty=stock.get("Reserved", 0), awaiting_payment_count=bookings.get("AwaitingPayment", 0),
                payment_review_count=bookings.get("PaymentReview", 0), booked_count=bookings.get("Booked", 0),
                pending_slip_count=rows("SELECT COUNT(*) AS quantity FROM booking_payments WHERE status='Pending'")[0]["quantity"])

# สร้างข้อมูลกราฟและคำแนะนำสต็อกสำหรับแดชบอร์ดช่วยตัดสินใจของพนักงาน
def decision_dashboard(period="all", month_count=6):
    """สรุปข้อมูลสำหรับกราฟ เพื่อให้หน้าจอมีหน้าที่แสดงผลอย่างเดียว"""
    ranking = best_sellers(period)
    today = date.today()
    months = []
    year, month = today.year, today.month
    for offset in range(month_count - 1, -1, -1):
        absolute = year * 12 + month - 1 - offset
        months.append(f"{absolute // 12:04d}-{absolute % 12 + 1:02d}")
    monthly_rows = rows("""SELECT SUBSTR(sale_date,1,7) AS month,COUNT(*) AS sold_count,
        COALESCE(SUM(sale_price),0) AS revenue FROM sales
        WHERE status='Completed' AND SUBSTR(sale_date,1,7)>=?
        GROUP BY SUBSTR(sale_date,1,7) ORDER BY month""", (months[0],))
    monthly_map = {row["month"]: row for row in monthly_rows}
    monthly = [dict(month=key, sold_count=monthly_map.get(key, {}).get("sold_count", 0),
                    revenue=monthly_map.get(key, {}).get("revenue", 0)) for key in months]
    grouped_series = {}
    for item in ranking:
        key = item["series"] or "อื่น ๆ"
        current = grouped_series.setdefault(key, {"series": key, "sold_count": 0, "revenue": 0})
        current["sold_count"] += item["sold_count"]
        current["revenue"] += item["revenue"]
    series_sales = sorted(grouped_series.values(), key=lambda item: (-item["sold_count"], -item["revenue"]))
    stock = {item["status"]: item["quantity"] for item in rows(
        "SELECT status,COUNT(*) AS quantity FROM cars GROUP BY status")}
    stock_mix = [dict(status=status, quantity=stock.get(status, 0))
                 for status in ("Available", "Reserved", "Sold")]
    recommendations = []
    for item in ranking:
        sold, available = int(item["sold_count"]), int(item["available_qty"])
        if not sold:
            continue
        if available == 0:
            level, reason = "สูง", "ไม่มีรถพร้อมขาย แต่มีประวัติขายสำเร็จ"
        elif sold >= available:
            level, reason = "สูง", "ยอดขายไม่น้อยกว่าจำนวนรถพร้อมขาย"
        elif sold * 2 >= available:
            level, reason = "เฝ้าระวัง", "ยอดขายอยู่ใกล้ครึ่งหนึ่งของสต็อกพร้อมขาย"
        else:
            level, reason = "ปกติ", "สต็อกพร้อมขายยังสูงกว่ายอดขายในช่วงที่เลือก"
        recommendations.append(dict(model=item["model"], sold_count=sold, available_qty=available,
                                    level=level, reason=reason))
    return dict(summary=staff_summary(period), ranking=ranking, monthly=monthly,
                series_sales=series_sales, stock_mix=stock_mix,
                recommendations=recommendations)

# ==================== ลูกค้าและรถยนต์ ====================
"""กฎการทำงานและการอ่านข้อมูลรถ ลูกค้า และบัญชี"""
import io
import json
import math
import re
import sqlite3
from contextlib import closing
from datetime import date, datetime
from pathlib import Path
try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk
except ImportError:
    Image = ImageDraw = ImageFont = ImageOps = ImageTk = None


# หน้าที่: ตรวจชื่อผู้ใช้ รหัสผ่าน และประเภทบัญชีตอนเข้าสู่ระบบ
def authenticate(username, password, role):
    if role not in ROLE:
        return None
    found = rows("SELECT * FROM users WHERE username=? AND role=?", (username.strip(), role))
    return found[0] if found and password_ok(password, found[0]["password_hash"]) else None


# หน้าที่: ตรวจเบอร์โทรและอีเมลก่อนตั้งรหัสผ่านใหม่
def reset_password(username, role, phone, email, new_password):
    """เทียบเบอร์และอีเมลกับข้อมูลที่บันทึกไว้ก่อนเปลี่ยนรหัสผ่าน"""
    if role != "customer":
        raise ValueError("การตั้งรหัสผ่านใหม่ใช้ได้เฉพาะบัญชีลูกค้า")
    if len(new_password) < 8:
        raise ValueError("รหัสผ่านใหม่ต้องมีอย่างน้อย 8 ตัว")
    username, phone, email = username.strip(), phone.strip(), email.strip().lower()
    if not all((username, phone, email)):
        raise ValueError("กรอกชื่อผู้ใช้ เบอร์โทร และอีเมลให้ครบ")
    with closing(db()) as conn, conn:
        user = conn.execute("""SELECT u.user_id FROM users u JOIN customers c ON c.customer_id=u.customer_id
            WHERE u.username=? AND u.role='customer' AND c.phone=? AND LOWER(TRIM(c.email))=?""",
            (username, phone, email)).fetchone()
        if not user:
            raise ValueError("ข้อมูลไม่ตรงกับบัญชีที่ลงทะเบียนไว้")
        conn.execute("UPDATE users SET password_hash=? WHERE user_id=?",
                     (password_hash(new_password), user["user_id"]))


# หน้าที่: หาตระกูลรถจากชื่อซีรีส์
def group_of(series):
    return next((group for group, items in SERIES.items() if series in items), "อื่น ๆ")


# หน้าที่: จัดรูปแบบจำนวนเงินเป็นบาทให้อ่านง่าย
def money(value):
    return f"{float(value):,.2f} บาท"


# หน้าที่: ตรวจรถที่เลือกแล้วบันทึกคำขอซื้อของลูกค้า
def request_purchase(user, car_id):
    return create_booking(user,car_id,{"purchase_method":"cash","delivery_date":"","terms_accepted":True})


# หน้าที่: ยืนยันคำขอซื้อ บันทึกการขาย และเปลี่ยนสถานะรถ
def complete_sale(user, customer_id, car_id, price, request_id=None):
    if not request_id:
        raise ValueError("กรุณาเลือกรายการจองที่ชำระครบก่อนยืนยันขาย")
    return confirm_sale(user,request_id)


# หน้าที่: รับคำขอยกเลิกหรืออนุมัติยกเลิกตามสิทธิ์ผู้ใช้
def cancel_request(user, request_id, customer_request=False):
    return cancel_booking(user,request_id,approve=user["role"]=="employee" and customer_request)


# หน้าที่: อ่านไฟล์ภาพเพื่อเก็บรูปไว้กับข้อมูลรถ
def image_bytes(path):
    if not Image: raise ValueError("กรุณาติดตั้ง Pillow เพื่อเพิ่มรูป JPG/PNG")
    with Image.open(path) as picture:
        picture.thumbnail((1200, 800)); out = io.BytesIO()
        picture.convert("RGB").save(out, "JPEG", quality=88)
        return out.getvalue()


# หน้าที่: อ่านรายชื่อพนักงานสำหรับแสดงบนหน้าติดต่อ
def list_staff():
    return rows("SELECT full_name,staff_code,phone FROM users WHERE role='employee' ORDER BY user_id")


# หน้าที่: บันทึกข้อมูลลูกค้าและสร้างบัญชีเข้าสู่ระบบ
def create_customer(values):
    with closing(db()) as conn, conn:
        customer_id = conn.execute(
            "INSERT INTO customers(fname,lname,phone,email,address) VALUES(?,?,?,?,?)",
            (values["fname"], values["lname"], values["phone"], values["email"], values["address"]),
        ).lastrowid
        conn.execute(
            "INSERT INTO users(username,password_hash,role,customer_id) VALUES(?,?,'customer',?)",
            (values["user"], password_hash(values["pass"]), customer_id),
        )
    return customer_id


# หน้าที่: อ่านรถที่ใช้แสดงเป็นการ์ดในหน้ารวมรถ
def catalog_cars():
    return rows("""SELECT c.car_id,c.model,c.year,c.color,c.price,c.series,c.description FROM cars c
        WHERE c.car_id=(SELECT x.car_id FROM cars x WHERE x.model=c.model AND x.year=c.year
        AND x.price=c.price AND x.series=c.series ORDER BY CASE WHEN x.status='Available' THEN 0 ELSE 1 END,
        CASE WHEN x.model='BMW 120 M Sport' AND x.color='Alpine White' THEN 0 ELSE 1 END,x.car_id LIMIT 1)
        ORDER BY c.series,c.model""")


# หน้าที่: ค้นข้อมูลรถหนึ่งคันจากรหัสรถ
def get_car(car_id):
    found = rows("SELECT * FROM cars WHERE car_id=?", (car_id,))
    if not found:
        return None
    car = dict(found[0])
    # รถที่เพิ่มเป็นจำนวนสต็อกไม่ทำสำเนารูปซ้ำในฐานข้อมูล จึงใช้รูปจากรถรุ่น/สีเดียวกัน
    if not car.get("image_data"):
        pictures = rows("""SELECT image_data,image_name,image_data_2,image_name_2,image_data_3,image_name_3
            FROM cars WHERE model=? AND year=? AND series=? AND color=? AND price=? AND image_data IS NOT NULL
            ORDER BY car_id LIMIT 1""", (car["model"], car["year"], car["series"], car["color"], car["price"]))
        if pictures:
            car.update(pictures[0])
    return car


# หน้าที่: หาสีที่พร้อมขายและจำนวนคงเหลือของรุ่นที่เลือก
def available_car_colors(car):
    """สีของรุ่นพร้อมสถานะคงเหลือ โดยไม่เปิดเผยจำนวนต่อผู้ใช้"""
    return rows("""SELECT color,COALESCE(MIN(CASE WHEN status='Available' THEN car_id END),MIN(car_id)) AS car_id,
        SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) AS quantity
        FROM cars WHERE model=? AND year=? AND price=? AND series=?
        GROUP BY color ORDER BY color""",
        (car["model"],car["year"],car["price"],car["series"]))


# หน้าที่: อ่านรายการรถทั้งหมดสำหรับหน้าพนักงาน
def list_cars():
    return rows("SELECT * FROM cars ORDER BY car_id DESC")


# หน้าที่: นับรถพร้อมขายแยกตามรุ่น ปี ซีรีส์ และสี
def stock_summary():
    """หนึ่งแถวต่อรุ่น ปี และสี โดยนับเฉพาะรถที่พร้อมขาย"""
    return rows("""SELECT model,year,series,color,COUNT(*) AS quantity
        FROM cars WHERE status='Available'
        GROUP BY model,year,series,color
        ORDER BY series,model,year,color""")


# หน้าที่: ตรวจความครบถ้วนและความถูกต้องของข้อมูลรถก่อนบันทึก
def validate_car(model, year, color, price, description, image_data=None, require_image=False):
    year, price = int(year), float(price)
    if not 1900 <= year <= 2100 or not math.isfinite(price) or price <= 0:
        raise ValueError("ตรวจสอบปีและราคา")
    if not model.strip() or not color.strip() or not description.strip() or (require_image and not image_data):
        raise ValueError("กรอกข้อมูลรถให้ครบ")
    return year, price


# หน้าที่: เพิ่มรถใหม่หนึ่งคันพร้อมรายละเอียดและรูปภาพ
def add_car(model, year, color, price, series, description, image_data, image_name, extra_images=None):
    year, price = validate_car(model, year, color, price, description, image_data, True)
    if re.match(r"^BMW\s+(M[23458]\b|X[56]\s+M\b|XM\b)", model.strip(), re.I):
        raise ValueError("ไม่เพิ่มตระกูล M")
    extra_images = extra_images or ((None, ""), (None, ""))
    return run(
        "INSERT INTO cars(model,year,color,price,status,series,description,image_data,image_name,"
        "image_data_2,image_name_2,image_data_3,image_name_3,is_demo) "
        "VALUES(?,?,?,?,'Available',?,?,?,?,?,?,?,?,0)",
        (model.strip(), year, color.strip(), price, series, description.strip(), image_data, image_name,
         extra_images[0][0], extra_images[0][1], extra_images[1][0], extra_images[1][1]),
    )


# หน้าที่: แก้ข้อมูลรถและเปลี่ยนเฉพาะรูปที่ผู้ใช้เลือกใหม่
def update_car(car_id, model, year, color, price, series, description, image_data=None, image_name="", extra_images=None):
    year, price = validate_car(model, year, color, price, description)
    params = [model.strip(), year, color.strip(), price, series, description.strip()]
    sql = "UPDATE cars SET model=?,year=?,color=?,price=?,series=?,description=?"
    if image_data:
        sql += ",image_data=?,image_name=?"
        params.extend((image_data, image_name))
    for index, (data, name) in enumerate(extra_images or (), start=2):
        if data:
            sql += f",image_data_{index}=?,image_name_{index}=?"
            params.extend((data, name))
    run(sql + " WHERE car_id=?", (*params, car_id))


# หน้าที่: ลบรถพร้อมขายที่ไม่มีคำขอซื้อหรือประวัติการขายอ้างอิง
def delete_car(car_id):
    car = rows("SELECT status FROM cars WHERE car_id=?", (car_id,))
    if not car:
        raise ValueError("ไม่พบรถคันนี้")
    if car[0]["status"] != "Available":
        raise ValueError("รถที่ขายแล้วไม่สามารถลบได้")
    requests = rows("SELECT COUNT(*) AS total FROM purchase_requests WHERE car_id=?", (car_id,))[0]["total"]
    sales = rows("SELECT COUNT(*) AS total FROM sales WHERE car_id=?", (car_id,))[0]["total"]
    if requests or sales:
        raise ValueError("รถคันนี้มีประวัติคำขอซื้อหรือการขาย จึงลบไม่ได้ เพื่อเก็บข้อมูลย้อนหลังให้ถูกต้อง")
    run("DELETE FROM cars WHERE car_id=?", (car_id,))


# หน้าที่: อ่านรายชื่อลูกค้าและข้อมูลติดต่อ
def list_customers():
    return rows("SELECT * FROM customers ORDER BY customer_id DESC")


# หน้าที่: อ่านคำขอซื้อที่ผู้ใช้ประเภทนั้นมีสิทธิ์ดู
def list_requests(user):
    if user.get("role") not in ROLE:
        raise PermissionError("บัญชีนี้ไม่มีสิทธิ์ดูรายการ")
    sql = """SELECT pr.*,c.fname||' '||c.lname customer,ca.model,ca.price,
           COALESCE(u.full_name,'-') staff_name,COALESCE(u.staff_code,'-') staff_code,COALESCE(u.phone,'-') staff_phone
           FROM purchase_requests pr JOIN customers c ON c.customer_id=pr.customer_id
           JOIN cars ca ON ca.car_id=pr.car_id LEFT JOIN users u ON u.user_id=pr.assigned_staff_id"""
    params = ()
    if user["role"] == "customer":
        sql += " WHERE pr.customer_id=?"
        params = (user["customer_id"],)
    return rows(sql + " ORDER BY pr.request_id DESC", params)


# หน้าที่: อ่านรายการขายที่ผู้ใช้ประเภทนั้นมีสิทธิ์ดู
def list_sales(user):
    if user.get("role") not in ROLE:
        raise PermissionError("บัญชีนี้ไม่มีสิทธิ์ดูรายการ")
    sql = """SELECT s.*,c.fname||' '||c.lname customer,c.phone customer_phone,c.email,c.address,ca.model,ca.year,ca.color,
           COALESCE((SELECT pr.snapshot FROM purchase_requests pr WHERE pr.sale_id=s.sale_id LIMIT 1),s.staff_snapshot) staff_snapshot,
           COALESCE(u.full_name,'-') staff_name,COALESCE(u.staff_code,'-') staff_code,COALESCE(u.phone,'-') staff_phone
           FROM sales s JOIN customers c ON c.customer_id=s.customer_id JOIN cars ca ON ca.car_id=s.car_id
           LEFT JOIN users u ON u.user_id=s.staff_user_id"""
    params = ()
    if user["role"] == "customer":
        sql += " WHERE s.customer_id=?"
        params = (user["customer_id"],)
    return rows(sql + " ORDER BY s.sale_id DESC", params)


# หน้าที่: คำนวณตัวเลขสรุปสำหรับหน้ารายงาน
def report_stats():
    return rows("""SELECT (SELECT COUNT(*) FROM cars) cars,
        (SELECT COUNT(*) FROM cars WHERE status='Available') available,
        (SELECT COUNT(*) FROM customers) customers,
        (SELECT COUNT(*) FROM sales WHERE status='Completed') sales,
        (SELECT COALESCE(SUM(sale_price),0) FROM sales WHERE status='Completed') revenue""")[0]


# หน้าที่: อ่านข้อมูลส่วนตัวของลูกค้า
def customer_profile(customer_id):
    return rows("SELECT * FROM customers WHERE customer_id=?", (customer_id,))[0]


# หน้าที่: บันทึกข้อมูลส่วนตัวที่ลูกค้าแก้ไข
def save_customer_profile(customer_id, values):
    run("UPDATE customers SET fname=?,lname=?,phone=?,email=?,address=? WHERE customer_id=?",
        (*(values[k] for k in ("fname", "lname", "phone", "email", "address")), customer_id))


# หน้าที่: เลือกชื่อที่เหมาะสมสำหรับแสดงบนแถบบัญชี
def display_user_name(user):
    if user["role"] == "customer":
        customer = customer_profile(user["customer_id"])
        return f"{customer['fname']} {customer['lname']}".strip()
    return user.get("full_name") or user["username"]


# หน้าที่: เลือกชื่อพนักงานที่แสดงในประวัติการขาย
def sale_staff_name(sale):
    name= sale.get("staff_name")
    if name and name not in ("-", "พนักงาน P1"):
        return name
    snapshot=json.loads(sale.get("staff_snapshot") or "{}")
    return snapshot.get("sale_staff",{}).get("name") or "ไม่ระบุพนักงานในข้อมูลเดิม"


# หน้าที่: เลือกชื่อพนักงานที่แสดงในรายการคำขอซื้อ
def request_staff_name(request):
    if request.get("staff_name") not in (None, "", "-"):
        return request["staff_name"]
    snapshot = json.loads(request.get("snapshot") or "{}")
    return (snapshot.get("sale_staff", {}).get("name") or snapshot.get("booking_staff", {}).get("name")
            or "รอพนักงานยืนยัน")



# ==================== เอกสาร PDF ====================
"""สร้างเอกสาร PDF จากรายการของระบบ"""
import io
import json
import math
import re
import sqlite3
from contextlib import closing
from datetime import date, datetime
from pathlib import Path
try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTk
except ImportError:
    Image = ImageDraw = ImageFont = ImageOps = ImageTk = None

from tkinter import filedialog

# หน้าที่: นำข้อมูลรายการมาจัดหน้าและบันทึกเอกสาร PDF
def export_pdf(title, document_no, issued_at, customer, vehicle, staff, status, filename=None, payment=None):
    """สร้างเอกสาร A4 จากข้อมูลเป็นหมวด เพื่อให้อ่านและนำเสนอได้ง่าย"""
    if not Image: raise ValueError("กรุณาติดตั้ง Pillow เพื่อสร้าง PDF")
    filename=filename or filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF","*.pdf")])
    if not filename: return
    page=Image.new("RGB",(1240,1754),"white"); draw=ImageDraw.Draw(page)
    # Leelawadee UI เป็นฟอนต์ภาษาไทยของ Windows ที่แยกสระและวรรณยุกต์ชัดกว่า Tahoma
    regular=r"C:\Windows\Fonts\LeelawUI.ttf"; bold_path=r"C:\Windows\Fonts\LeelaUIb.ttf"
    f18=ImageFont.truetype(regular,18); f21=ImageFont.truetype(regular,21); f22b=ImageFont.truetype(bold_path,22)
    f26b=ImageFont.truetype(bold_path,26); f34b=ImageFont.truetype(bold_path,34); f42b=ImageFont.truetype(bold_path,42)
    blue="#0066B1"; blue2="#004B87"; text="#202124"; gray="#60656B"; border="#AEB4BA"; light="#F1F3F5"
    # Pillow ที่ไม่มี HarfBuzz จะวางสระ/วรรณยุกต์ไทยซ้อนผิดตำแหน่ง
    # จึงให้ Windows GDI วาดข้อความลงเป็น mask ก่อน แล้วจึงวางลงบนหน้า PDF
    original_text=draw.text
    try:
        import ctypes
        from ctypes import wintypes
        from PIL import ImageColor
        gdi32=ctypes.windll.gdi32; user32=ctypes.windll.user32
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_=[("biSize",wintypes.DWORD),("biWidth",wintypes.LONG),("biHeight",wintypes.LONG),
                      ("biPlanes",wintypes.WORD),("biBitCount",wintypes.WORD),("biCompression",wintypes.DWORD),
                      ("biSizeImage",wintypes.DWORD),("biXPelsPerMeter",wintypes.LONG),("biYPelsPerMeter",wintypes.LONG),
                      ("biClrUsed",wintypes.DWORD),("biClrImportant",wintypes.DWORD)]
        class RGBQUAD(ctypes.Structure):
            _fields_=[("rgbBlue",ctypes.c_ubyte),("rgbGreen",ctypes.c_ubyte),("rgbRed",ctypes.c_ubyte),("rgbReserved",ctypes.c_ubyte)]
        class BITMAPINFO(ctypes.Structure):
            _fields_=[("bmiHeader",BITMAPINFOHEADER),("bmiColors",RGBQUAD*1)]
        handle=ctypes.c_void_p
        gdi32.CreateCompatibleDC.restype=handle
        gdi32.CreateFontW.restype=handle
        gdi32.CreateDIBSection.argtypes=[handle,ctypes.POINTER(BITMAPINFO),wintypes.UINT,
                                        ctypes.POINTER(ctypes.c_void_p),handle,wintypes.DWORD]
        gdi32.CreateDIBSection.restype=handle
        gdi32.SelectObject.argtypes=[handle,handle]; gdi32.SelectObject.restype=handle
        gdi32.SetTextColor.argtypes=[handle,wintypes.DWORD]
        gdi32.SetBkColor.argtypes=[handle,wintypes.DWORD]
        gdi32.SetBkMode.argtypes=[handle,ctypes.c_int]
        gdi32.DeleteObject.argtypes=[handle]; gdi32.DeleteDC.argtypes=[handle]
        user32.DrawTextW.argtypes=[handle,wintypes.LPCWSTR,ctypes.c_int,ctypes.POINTER(wintypes.RECT),wintypes.UINT]
        # หน้าที่: เตรียมข้อความภาษาไทยให้วาดลง PDF บน Windows ได้
        def windows_text_mask(value,font):
            value=str(value); size=max(8,int(getattr(font,"size",20))); bold="LeelaUIb" in str(getattr(font,"path",""))
            hdc=gdi32.CreateCompatibleDC(0)
            hfont=gdi32.CreateFontW(-size,0,0,0,700 if bold else 400,0,0,0,1,0,0,5,0,"Leelawadee UI")
            old_font=gdi32.SelectObject(hdc,hfont)
            measure=wintypes.RECT(0,0,4000,size*4)
            user32.DrawTextW(hdc,value,-1,ctypes.byref(measure),0x0400|0x0020|0x0001)
            width=max(2,measure.right-measure.left+6); height=max(size+8,measure.bottom-measure.top+8)
            info=BITMAPINFO(); info.bmiHeader.biSize=ctypes.sizeof(BITMAPINFOHEADER)
            info.bmiHeader.biWidth=width; info.bmiHeader.biHeight=-height; info.bmiHeader.biPlanes=1
            info.bmiHeader.biBitCount=32; info.bmiHeader.biCompression=0
            bits=ctypes.c_void_p(); bitmap=gdi32.CreateDIBSection(hdc,ctypes.byref(info),0,ctypes.byref(bits),None,0)
            old_bitmap=gdi32.SelectObject(hdc,bitmap); ctypes.memset(bits,255,width*height*4)
            gdi32.SetTextColor(hdc,0x000000); gdi32.SetBkColor(hdc,0xFFFFFF); gdi32.SetBkMode(hdc,2)
            rect=wintypes.RECT(2,2,width,height)
            user32.DrawTextW(hdc,value,-1,ctypes.byref(rect),0x0020|0x0001)
            raw=ctypes.string_at(bits,width*height*4)
            rendered=Image.frombytes("RGB",(width,height),raw,"raw","BGRX").convert("L")
            mask=rendered.point(lambda pixel:255-pixel)
            gdi32.SelectObject(hdc,old_bitmap); gdi32.SelectObject(hdc,old_font)
            gdi32.DeleteObject(bitmap); gdi32.DeleteObject(hfont); gdi32.DeleteDC(hdc)
            return mask
        # หน้าที่: วาดข้อความลง PDF ตามตำแหน่งและฟอนต์ที่กำหนด
        def shaped_text(xy,value,font=None,fill=text,**_):
            mask=windows_text_mask(value,font or f21); color=ImageColor.getrgb(fill) if isinstance(fill,str) else fill
            page.paste(color,(int(round(xy[0])),int(round(xy[1]))),mask)
        draw.text=shaped_text
    except Exception:
        # ใช้การวาดเดิมเป็นทางสำรองสำหรับเครื่องที่ไม่ใช่ Windows
        draw.text=original_text
    # หน้าที่: ตัดข้อความยาวเป็นบรรทัดตามความกว้างที่กำหนด
    def wrapped_lines(value,font,width):
        words=str(value or "-").split(); lines=[]; line=""
        for word in words:
            trial=(line+" "+word).strip()
            if draw.textbbox((0,0),trial,font=font)[2] <= width: line=trial
            else:
                if line: lines.append(line)
                line=word
        if line: lines.append(line)
        return lines
    # หน้าที่: วางค่าข้อมูลในกรอบเอกสาร PDF
    def value_text(x,y,value,width,font=f21):
        for index,part in enumerate(wrapped_lines(value,font,width)[:2]): draw.text((x,y+index*28),part,font=font,fill=text)
    # หน้าที่: วาดหัวข้อย่อยในเอกสาร PDF
    def section_header(y,label):
        draw.rectangle((65,y,1175,y+48),fill=light,outline=border,width=1)
        draw.rectangle((65,y,73,y+48),fill=blue)
        draw.text((92,y+10),label,font=f22b,fill=text)
    # หัวกระดาษแบบเอกสารสำนักงานทั่วไป
    draw.text((65,48),"BMW",font=f42b,fill=text)
    draw.line((176,48,176,101),fill=blue,width=5)
    draw.text((198,61),"SHOWROOM",font=f22b,fill=gray)
    title_width=draw.textbbox((0,0),title,font=f34b)[2]
    draw.text(((1240-title_width)/2,135),title,font=f34b,fill=text)
    draw.text((875,48),f"เลขที่  {document_no}",font=f21,fill=text)
    draw.text((875,82),f"วันที่  {issued_at}",font=f18,fill=gray)
    draw.line((65,205,1175,205),fill=blue,width=4)
    draw.text((65,230),"สถานะ:",font=f21,fill=gray)
    status_color="#16834A" if status in ("ซื้อสำเร็จ","ยืนยันจองแล้ว","ยืนยันการจองแล้ว") else "#B42318" if "ยกเลิก" in status else "#865A12"
    draw.text((145,230),status,font=f22b,fill=status_color)
    # ตารางข้อมูลลูกค้า
    section_header(285,"ข้อมูลลูกค้า")
    draw.rectangle((65,333,1175,548),outline=border,width=1)
    draw.line((620,333,620,548),fill=border,width=1); draw.line((65,438,1175,438),fill=border,width=1)
    draw.text((88,352),"ชื่อ-นามสกุล",font=f18,fill=gray); value_text(88,383,customer.get("name"),480)
    draw.text((645,352),"โทรศัพท์",font=f18,fill=gray); value_text(645,383,customer.get("phone"),470)
    draw.text((88,457),"อีเมล",font=f18,fill=gray); value_text(88,488,customer.get("email"),480)
    draw.text((645,457),"ที่อยู่",font=f18,fill=gray); value_text(645,488,customer.get("address"),470)
    # ตารางข้อมูลรถยนต์
    section_header(590,"ข้อมูลรถยนต์")
    draw.rectangle((65,638,1175,876),outline=border,width=1)
    draw.line((620,638,620,758),fill=border,width=1); draw.line((860,638,860,758),fill=border,width=1)
    draw.line((65,758,1175,758),fill=border,width=1)
    draw.text((88,658),"รุ่นรถ",font=f18,fill=gray); value_text(88,695,vehicle.get("model"),490)
    draw.text((645,658),"ปี",font=f18,fill=gray); value_text(645,695,vehicle.get("year"),180)
    draw.text((885,658),"สี",font=f18,fill=gray); value_text(885,695,vehicle.get("color"),250)
    draw.text((88,797),"ราคาขาย",font=f21,fill=gray)
    price_text=money(vehicle.get("price",0)); price_width=draw.textbbox((0,0),price_text,font=f34b)[2]
    draw.text((1140-price_width,793),price_text,font=f34b,fill=blue2)
    # ตารางพนักงาน
    section_header(920,"พนักงานผู้ดูแล")
    draw.rectangle((65,968,1175,1088),outline=border,width=1)
    draw.line((545,968,545,1088),fill=border,width=1); draw.line((815,968,815,1088),fill=border,width=1)
    draw.text((88,988),"ชื่อพนักงาน",font=f18,fill=gray); value_text(88,1023,staff.get("name"),410)
    draw.text((570,988),"รหัสพนักงาน",font=f18,fill=gray); value_text(570,1023,staff.get("code"),200)
    draw.text((840,988),"โทรศัพท์",font=f18,fill=gray); value_text(840,1023,staff.get("phone"),280)
    # หมายเหตุและช่องลงนาม
    draw.text((65,1135),"หมายเหตุ",font=f22b,fill=text); draw.line((65,1173,1175,1173),fill=border,width=1)
    note="กรุณาตรวจสอบข้อมูลลูกค้า รุ่นรถ ราคา และสถานะของรายการก่อนลงนาม"
    if payment:
        note="เอกสารฉบับนี้ออกจากระบบ BMW Showroom โปรดตรวจสอบข้อมูลและสถานะล่าสุดก่อนลงนาม"
    draw.text((65,1193),note,font=f18,fill=gray)
    if payment:
        deposit_label = "ยอดชำระราคารถ" if payment.get("order_type") == "direct" else "ค่าจองที่กำหนด"
        for index,(label,value) in enumerate(((deposit_label,payment.get("deposit_amount",0)),
                                             ("ยอดที่ตรวจรับแล้ว",payment.get("paid_amount",0)),
                                             ("ยอดคงเหลือของราคารถ",payment.get("remaining_amount",0)))):
            draw.text((65,1230+index*34),f"{label}  {money(value)}",font=f21,fill=text)
        if payment.get("legacy_payment"):
            draw.text((65,1340),"ยอดข้อมูลขายเดิมก่อนเพิ่มระบบตรวจสลิป",font=f18,fill=gray)
        elif payment.get("refund_due",0)>0:
            draw.text((65,1340),f"รอตรวจสอบคืนเงินสาธิต  {money(payment['refund_due'])}",font=f18,fill="#B42318")
    draw.line((105,1435,505,1435),fill=text,width=1); draw.line((735,1435,1135,1435),fill=text,width=1)
    draw.text((210,1453),"ลงชื่อ ลูกค้า",font=f21,fill=text); draw.text((825,1453),"ลงชื่อ พนักงาน",font=f21,fill=text)
    draw.text((65,1515),"วันที่ ____ / ____ / ______",font=f18,fill=gray); draw.text((735,1515),"วันที่ ____ / ____ / ______",font=f18,fill=gray)
    draw.line((65,1660,1175,1660),fill=border,width=1)
    draw.text((65,1678),"BMW Showroom",font=f18,fill=gray)
    footer=f"เอกสารเลขที่ {document_no}"
    footer_width=draw.textbbox((0,0),footer,font=f18)[2]; draw.text((1175-footer_width,1678),footer,font=f18,fill=gray)
    page.save(filename,"PDF",resolution=150)
    return filename



# ==================== เอกสารจากเว็บไซต์ ====================
"""สร้างเอกสารรายการจองสำหรับเปิดหรือพิมพ์จากเว็บ"""
import json
import tempfile
from pathlib import Path



DOCUMENT_TITLES = {
    "booking": {
        "AwaitingPayment": "ใบคำขอจองรถยนต์",
        "PaymentReview": "ใบรับหลักฐานค่าจอง",
        "Booked": "ใบยืนยันการจองรถยนต์",
        "CancelRequested": "ใบคำขอยกเลิกการจองรถยนต์",
        "Cancelled": "ใบแจ้งยกเลิกการจองรถยนต์",
        "Completed": "ใบยืนยันการจองและส่งมอบรถยนต์",
    },
    "order": {
        "AwaitingPayment": "ใบสั่งซื้อรถยนต์ — รอชำระค่าจอง",
        "PaymentReview": "ใบสั่งซื้อรถยนต์ — รอตรวจหลักฐาน",
        "Booked": "ใบสั่งซื้อรถยนต์ — ยืนยันการจองแล้ว",
        "CancelRequested": "ใบคำขอยกเลิกคำสั่งซื้อรถยนต์",
        "Cancelled": "ใบแจ้งยกเลิกคำสั่งซื้อรถยนต์",
        "Completed": "ใบยืนยันการซื้อขายรถยนต์",
    },
    "status": {},
}
PREFIX = {"booking": "BOOK", "order": "ORDER", "status": "STATUS"}


# สร้าง PDF ตามข้อมูลและสถานะล่าสุด โดยตรวจสิทธิ์ผ่าน booking_rows ก่อนเสมอ
def build_request_document(user, request_id, kind):
    if kind not in DOCUMENT_TITLES:
        raise ValueError("เลือกใบจอง ใบสั่งซื้อ หรือใบแจ้งสถานะ")
    record = next((item for item in booking_rows(user) if int(item["request_id"]) == int(request_id)), None)
    if not record:
        raise ValueError("ไม่พบรายการหรือไม่มีสิทธิ์เปิดเอกสารนี้")
    snapshot = json.loads(record.get("snapshot") or "{}")
    if kind == "order" and record.get("order_type") == "direct":
        direct_titles = {"AwaitingPayment": "ใบสั่งซื้อรถยนต์ — รอชำระราคารถ", "PaymentReview": "ใบสั่งซื้อรถยนต์ — รอตรวจหลักฐานการชำระ", "Booked": "ใบสั่งซื้อรถยนต์ — ชำระครบแล้ว", "Completed": "ใบยืนยันการซื้อขายรถยนต์"}
        title = direct_titles.get(record["status"], "ใบสั่งซื้อรถยนต์")
    else:
        title = ("ใบแจ้งสถานะรายการรถยนต์" if kind == "status" else
                 DOCUMENT_TITLES[kind].get(record["status"], "ใบจองรถยนต์" if kind == "booking" else "ใบสั่งซื้อรถยนต์"))
    prefix = PREFIX[kind]
    document_no = f"{prefix}-{int(request_id):06d}"
    customer = {
        "name": snapshot.get("customer", record.get("customer", "-")),
        "phone": snapshot.get("phone", "-"),
        "email": snapshot.get("email", "-"),
        "address": snapshot.get("address", "-"),
    }
    vehicle = {
        "model": snapshot.get("model", record.get("model", "-")),
        "year": snapshot.get("year", record.get("year", "-")),
        "color": snapshot.get("color", record.get("color", "-")),
        "price": snapshot.get("price", record.get("price", 0)),
    }
    staff = {
        "name": record.get("staff_name") or "รอพนักงานตรวจสอบ",
        "code": record.get("staff_code") or "-",
        "phone": record.get("staff_phone") or "-",
    }
    output = Path(tempfile.gettempdir()) / f"{document_no}.pdf"
    export_pdf(title, document_no, record.get("created_at", "-"), customer, vehicle, staff,
               STATUS.get(record["status"], record["status"]), filename=str(output), payment=record)
    data = output.read_bytes()
    output.unlink(missing_ok=True)
    return data, f"{document_no}.pdf"
# ==================== เว็บเซิร์ฟเวอร์ ====================
"""เว็บภายในเครื่องสำหรับ BMW Showroom ใช้ฐานข้อมูลและกฎชุดเดียวกับโปรแกรมเดิม"""
import base64
import io
import json
import mimetypes
import secrets
import webbrowser
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Timer
from urllib.parse import parse_qs, urlparse
from PIL import Image


WEB_DIR = Path(__file__).resolve().parent / "static"
SESSIONS = {}
APP_VERSION = "2026.10.27-stock-v2"


def clean(value):
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items() if not key.endswith("_data") and key != "password_hash"}
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, bytes):
        return None
    return value


class Handler(BaseHTTPRequestHandler):
    server_version = "BMWShowroom/2.0"

    def log_message(self, fmt, *args):
        return

    def send_json(self, data, status=200, cookie=None):
        payload = json.dumps(clean(data), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def body(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size > 15 * 1024 * 1024:
            raise ValueError("ข้อมูลที่ส่งมีขนาดใหญ่เกินไป")
        return json.loads(self.rfile.read(size) or b"{}")

    def session(self):
        jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        token = jar.get("bmw_session")
        return SESSIONS.get(token.value) if token else None

    def require(self, *roles):
        user = self.session()
        if not user or user.get("role") not in roles:
            raise PermissionError("กรุณาเข้าสู่ระบบด้วยบัญชีที่มีสิทธิ์")
        return user

    def do_GET(self):
        try:
            route = urlparse(self.path)
            query = parse_qs(route.query)
            if route.path == "/api/session":
                user = self.session()
                return self.send_json({"user": clean(user), "name": display_user_name(user) if user else "", "roles": ROLE, "version": APP_VERSION})
            if route.path == "/api/cars":
                result = []
                for car in catalog_cars():
                    item = clean(car)
                    item["colors"] = available_car_colors(car)
                    result.append(item)
                return self.send_json(result)
            if route.path == "/api/car":
                car = get_car(int(query.get("id", [0])[0]))
                if not car:
                    return self.send_json({"error": "ไม่พบรถ"}, 404)
                item = clean(car)
                item["colors"] = available_car_colors(car)
                return self.send_json(item)
            if route.path == "/api/car-image":
                car = get_car(int(query.get("id", [0])[0]))
                slot = max(1, min(3, int(query.get("slot", [1])[0])))
                key = "image_data" if slot == 1 else f"image_data_{slot}"
                name = (car or {}).get("image_name" if slot == 1 else f"image_name_{slot}", "")
                data = (car or {}).get(key)
                if not data:
                    return self.send_error(404)
                mime = mimetypes.guess_type(name)[0] or "image/jpeg"
                self.send_response(200); self.send_header("Content-Type", mime)
                self.send_header("Cache-Control", "public, max-age=3600")
                self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
            if route.path == "/api/document":
                user = self.require("customer", "employee")
                data, filename = build_request_document(user, int(query.get("id", [0])[0]), query.get("kind", ["status"])[0])
                self.send_response(200); self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Disposition", f'inline; filename="{filename}"')
                self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(data)))
                self.end_headers(); self.wfile.write(data); return
            if route.path == "/api/customer/profile":
                user = self.require("customer")
                return self.send_json(customer_profile(user["customer_id"]))
            if route.path == "/api/payment-image":
                user = self.require("customer", "employee")
                payment = payment_slip(user, int(query.get("id", [0])[0]))
                data = payment.get("slip_data")
                if not data:
                    return self.send_error(404)
                mime = mimetypes.guess_type(payment.get("slip_name", ""))[0] or "image/png"
                self.send_response(200); self.send_header("Content-Type", mime)
                self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(data)))
                self.end_headers(); self.wfile.write(data); return
            if route.path == "/api/customer/overview":
                user = self.require("customer")
                return self.send_json({"summary": customer_summary(user), "bookings": booking_rows(user)})
            if route.path == "/api/employee/dashboard":
                self.require("employee")
                period = query.get("period", ["all"])[0]
                return self.send_json(decision_dashboard(period))
            if route.path == "/api/employee/bookings":
                user = self.require("employee")
                return self.send_json({"bookings": booking_rows(user), "payments": payment_rows(user)})
            if route.path == "/api/employee/inventory":
                self.require("employee")
                return self.send_json(stock_summary())
            if route.path == "/api/employee/customers":
                self.require("employee")
                return self.send_json(list_customers())
            if route.path == "/api/employee/visitors":
                user = self.require("employee")
                return self.send_json(visitor_rows(user))
            if route.path == "/api/employee/sales":
                user = self.require("employee")
                return self.send_json(list_sales(user))
            return self.static(route.path)
        except PermissionError as error:
            self.send_json({"error": str(error)}, 403)
        except Exception as error:
            self.send_json({"error": str(error)}, 400)

    def do_POST(self):
        try:
            path = urlparse(self.path).path
            data = self.body()
            if path == "/api/visitor":
                record_visitor(data.get("name"), data.get("phone"))
                return self.send_json({"ok": True})
            if path == "/api/login":
                role = data.get("role")
                if role not in ROLE:
                    raise ValueError("เลือกประเภทผู้ใช้")
                user = authenticate(data.get("username", ""), data.get("password", ""), role)
                if not user:
                    raise ValueError("ชื่อผู้ใช้ รหัสผ่าน หรือประเภทผู้ใช้ไม่ถูกต้อง")
                token = secrets.token_urlsafe(32); SESSIONS[token] = user
                return self.send_json({"ok": True, "role": role}, cookie=f"bmw_session={token}; Path=/; HttpOnly; SameSite=Strict")
            if path == "/api/logout":
                jar = cookies.SimpleCookie(self.headers.get("Cookie", "")); token = jar.get("bmw_session")
                if token: SESSIONS.pop(token.value, None)
                return self.send_json({"ok": True}, cookie="bmw_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict")
            if path == "/api/reset-password":
                reset_password(data.get("username", ""), data.get("role", ""), data.get("phone", ""),
                    data.get("email", ""), data.get("password", ""))
                return self.send_json({"ok": True})
            if path == "/api/customer/profile":
                user = self.require("customer")
                values = {key: str(data.get(key, "")).strip() for key in ("fname", "lname", "phone", "email", "address")}
                if not all(values.values()):
                    raise ValueError("กรอกข้อมูลลูกค้าให้ครบ")
                save_customer_profile(user["customer_id"], values)
                return self.send_json({"ok": True})
            if path == "/api/register":
                values = {key: str(data.get(key, "")).strip() for key in ("username", "password", "fname", "lname", "phone", "email", "address")}
                if not all(values.values()) or len(values["password"]) < 8:
                    raise ValueError("กรอกข้อมูลให้ครบและใช้รหัสผ่านอย่างน้อย 8 ตัว")
                create_customer({"user": values["username"], "pass": values["password"], "fname": values["fname"],
                    "lname": values["lname"], "phone": values["phone"], "email": values["email"], "address": values["address"]})
                return self.send_json({"ok": True})
            if path == "/api/bookings":
                user = self.require("customer")
                request_id = create_booking(user, int(data["car_id"]), data)
                return self.send_json({"ok": True, "request_id": request_id})
            if path == "/api/payments":
                user = self.require("customer")
                encoded = data.get("slip", "").split(",", 1)[-1]
                payment_id = upload_payment_slip(user, int(data["request_id"]), data["purpose"],
                    data["amount"], base64.b64decode(encoded), data.get("slip_name", "slip.png"),
                    data["transferred_at"], data.get("reference", ""))
                return self.send_json({"ok": True, "payment_id": payment_id})
            if path == "/api/payments/review":
                user = self.require("employee")
                review_payment(user, int(data["payment_id"]), bool(data.get("approve")), data.get("note", ""))
                return self.send_json({"ok": True})
            if path == "/api/sales/confirm":
                user = self.require("employee")
                sale_id = confirm_sale(user, int(data["request_id"]))
                return self.send_json({"ok": True, "sale_id": sale_id})
            if path == "/api/bookings/cancel":
                user = self.require("customer", "employee")
                cancel_booking(user, int(data["request_id"]), bool(data.get("approve")))
                return self.send_json({"ok": True})
            if path == "/api/stock/adjust":
                self.require("employee")
                quantity = adjust_stock(int(data["car_id"]), int(data["delta"]))
                return self.send_json({"ok": True, "quantity": quantity})
            if path == "/api/cars/save":
                self.require("employee")
                def picture(value, name):
                    if not value:
                        return None, ""
                    raw = base64.b64decode(value.split(",", 1)[-1])
                    if len(raw) > 10 * 1024 * 1024:
                        raise ValueError("รูปแต่ละไฟล์ต้องไม่เกิน 10 MB")
                    try:
                        with Image.open(io.BytesIO(raw)) as source:
                            source.verify()
                        with Image.open(io.BytesIO(raw)) as source:
                            source.thumbnail((1600, 1100))
                            output = io.BytesIO(); source.convert("RGB").save(output, "JPEG", quality=90)
                    except Exception:
                        raise ValueError("เลือกไฟล์รูป JPG, PNG หรือ WEBP ที่เปิดได้") from None
                    return output.getvalue(), name or "car.jpg"
                primary = picture(data.get("image"), data.get("image_name", "car.jpg"))
                extras = [picture(data.get(f"image{number}"), data.get(f"image_name{number}", f"car-{number}.jpg")) for number in (2, 3)]
                values = (data.get("model", ""), data.get("year", ""), data.get("color", ""),
                          data.get("price", ""), data.get("series", ""), data.get("description", ""))
                if data.get("car_id"):
                    update_car(int(data["car_id"]), *values, primary[0], primary[1], extras)
                    car_id = int(data["car_id"])
                    quantity = None
                else:
                    quantity = int(data.get("quantity", 1))
                    if quantity < 1 or quantity > 100:
                        raise ValueError("จำนวนรถเริ่มต้นต้องอยู่ระหว่าง 1–100 คัน")
                    car_id = add_car(*values, primary[0], primary[1], extras)
                    if quantity > 1:
                        adjust_stock(car_id, quantity - 1)
                return self.send_json({"ok": True, "car_id": car_id, "quantity": quantity})
            if path == "/api/cars/delete":
                self.require("employee"); delete_car(int(data["car_id"])); return self.send_json({"ok": True})
            return self.send_json({"error": "ไม่พบคำสั่ง"}, 404)
        except PermissionError as error:
            self.send_json({"error": str(error)}, 403)
        except Exception as error:
            self.send_json({"error": str(error)}, 400)

    def static(self, path):
        name = "index.html" if path in ("", "/") else path.lstrip("/")
        target = (WEB_DIR / name).resolve()
        if WEB_DIR.resolve() not in target.parents and target != WEB_DIR.resolve():
            return self.send_error(403)
        if not target.is_file():
            target = WEB_DIR / "index.html"
        data = target.read_bytes(); mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200); self.send_header("Content-Type", f"{mime}; charset=utf-8" if mime.startswith("text/") else mime)
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)


def main(open_browser=True):
    init_db(); initialize_booking_system()
    server = ThreadingHTTPServer(("127.0.0.1", 8772), Handler)
    print("BMW Showroom: http://127.0.0.1:8772")
    if open_browser: Timer(0.6, lambda: webbrowser.open("http://127.0.0.1:8772")).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
