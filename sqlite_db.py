import sqlite3
import random
from datetime import datetime

# Local SQLite file for MVP
DB_PATH = "fleetchatbot_mvp.db"

# Connect to SQLite
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# --- Helper functions ---


def get_customer(customer_id: str):
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_driver(driver_id: str):
    cursor.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def list_drivers():
    cursor.execute("SELECT * FROM drivers")
    return [dict(r) for r in cursor.fetchall()]


def get_ride(ride_id: str):
    cursor.execute("SELECT * FROM rides WHERE id = ?", (ride_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def list_customers():
    cursor.execute("SELECT * FROM customers")
    return [dict(r) for r in cursor.fetchall()]


def list_rides():
    cursor.execute("SELECT * FROM rides")
    return [dict(r) for r in cursor.fetchall()]


def get_customer_rides(customer_id: str):
    cursor.execute("SELECT * FROM rides WHERE customer_id = ?", (customer_id,))
    return [dict(r) for r in cursor.fetchall()]


def reset_system():
    # Reset all drivers
    cursor.execute("UPDATE drivers SET status='available'")

    # Mark all active rides as completed
    cursor.execute("""
        UPDATE rides
        SET status='completed'
        WHERE status IN ('scheduled', 'ongoing')
    """)

    conn.commit()
    return "System reset successful"


# --- Core functions ---


def create_ride(customer_id: str, pickup: str, dropoff: str, payment_method="wallet"):
    # Find available drivers
    cursor.execute("SELECT id FROM drivers WHERE status='available'")
    drivers = [row["id"] for row in cursor.fetchall()]
    if not drivers:
        return None, "No drivers available."

    driver_id = random.choice(drivers)
    distance_km = round(random.uniform(3, 25), 1)
    fare = round(distance_km * 18 + 30, 2)
    eta = random.randint(3, 15)
    ride_id = f"R{int(datetime.now().timestamp())}"  # unique ID

    cursor.execute(
        """
        INSERT INTO rides (id, customer_id, driver_id, pickup, dropoff, status, fare,
        distance_km, booked_at, eta_minutes, delay_minutes, payment_method, refund_issued)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ride_id,
            customer_id,
            driver_id,
            pickup,
            dropoff,
            "scheduled",
            fare,
            distance_km,
            datetime.now().isoformat(),
            eta,
            0,
            payment_method,
            0,
        ),
    )

    cursor.execute("UPDATE drivers SET status='on_trip' WHERE id=?", (driver_id,))
    conn.commit()
    return ride_id, get_ride(ride_id)


def file_grievance(customer_id: str, ride_id: str, category: str, description: str):
    grievance_id = f"G{int(datetime.now().timestamp())}"
    cursor.execute(
        """
        INSERT INTO grievances (id, customer_id, ride_id, category, description, filed_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            grievance_id,
            customer_id,
            ride_id,
            category,
            description,
            datetime.now().isoformat(),
            "open",
        ),
    )
    conn.commit()
    return grievance_id, get_grievance_status(grievance_id)


def get_grievance_status(grievance_id: str):
    cursor.execute("SELECT * FROM grievances WHERE id=?", (grievance_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_ride_eta(ride_id: str):
    ride = get_ride(ride_id)
    status = ride.get("status")
    if not ride:
        return None, "Ride not found."
    if status in ["completed", "cancelled"]:
        return None, f"This ride is already {status}."
    return {
        "ride_id": ride_id,
        "status": ride["status"],
        "eta_minutes": ride["eta_minutes"],
        "delay_minutes": ride["delay_minutes"],
    }, None
