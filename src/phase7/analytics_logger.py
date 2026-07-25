#Phase 7 I want to save driver Activity and alerts to SQLite FOr my dashboard
import logging
import os
import sqlite3
import time
from datetime import datetime
from datetime import timedelta

logger = logging.getLogger(__name__)

class AnalyticsLogger:
    def __init__(self, db_path, distraction_activities=None):
        self._db_path = db_path #i am setting the database path
        self._distraction_activities = distraction_activities or [] #here i am setting the distraction acitivieis
        self._conn = None #i am setting the connection to None initially becaue i want to connect to the database later
        self._current_trip_id = None #i am also setting the cuureent ID trip to nONE initially because i want to start a new trip when the driver starts the car

        # i want to mke sure the data and folder exsists before i create the database file
        db_dir = os.path.dirname(db_path) #i am getting the directory of the datavase path
        if db_dir:
            os.makedirs(db_dir, exist_ok=True) # creating the directory if it does not eixists

        logger.info("i started the Analytics logger (db=%s)", db_path)
        self._create_tables() #i am calling the method for my databse tables
        self._tracking_activity = None #i am setting the tracking acivity to nONE
        self._tracking_start = None #the same too
        self._tracking_max_conf = 0.0



    def _connect(self): #i am creating a method to connect to the database
        if self._conn is None: #Opening one SQLite connection for this session
            # I allow Flask/other threads to read the same connection (dashboard API).
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row #i am setting the row factory to Row so i can access the columns because sqlite retuens a dictionary
        return self._conn


    
    def _create_tables(self):
        conn = self._connect()

        conn.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                trip_id TEXT PRIMARY KEY, 
                start_time REAL NOT NULL, 
                end_time REAL,
                total_distraction_sec REAL DEFAULT 0, 
                alert_count INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id TEXT NOT NULL,
                activity TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                duration_sec REAL NOT NULL,
                max_confidence REAL,
                FOREIGN KEY (trip_id) REFERENCES trips(trip_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id TEXT NOT NULL,
                activity TEXT NOT NULL,
                duration_at_alert REAL NOT NULL,
                threshold REAL NOT NULL,
                confidence REAL NOT NULL,
                shadow_mode INTEGER NOT NULL,
                message TEXT,
                timestamp REAL NOT NULL,
                FOREIGN KEY (trip_id) REFERENCES trips(trip_id)
            )
        """)

        conn.commit() #commitging the changes to the database
        logger.info("created tables into my SQLite database")


    
    def start_trip(self): #i want to creat a unique trip ID from the current date/time
        now = time.time() #i am getting the current time in seconds since the epoch, i am not using monotonic here becuse i need real time 
        trip_id = datetime.fromtimestamp(now).strftime("trip_%Y%m%d_%H%M%S")
        self._current_trip_id = trip_id

        conn = self._connect()
        conn.execute(
            "INSERT INTO trips (trip_id, start_time) VALUES (?, ?)",
            (trip_id, now),
        )
        conn.commit()

        logger.info("I started trip %s", trip_id)
        return trip_id
        


    def end_trip(self):
        if self._current_trip_id is None:
            logger.warning("I tried to end a trip  but none was started")
            return None

        self._flush_current_segment()

        now = time.time()
        trip_id = self._current_trip_id
        conn = self._connect()

        #i wannt to count hoow many alaets happened on this trip
        alert_count = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE trip_id = ?",
            (trip_id,),
        ).fetchone()[0]

        # I sum distraction time from activity rows (non-normal classes)
        placeholders = ",".join("?" for _ in self._distraction_activities)
        total_distraction_sec = 0.0
        if self._distraction_activities:
            row = conn.execute(
                f"""
                SELECT COALESCE(SUM(duration_sec), 0)
                FROM activities
                WHERE trip_id = ?
                  AND activity IN ({placeholders})
                """,
                (trip_id, *self._distraction_activities),
            ).fetchone()
            total_distraction_sec = row[0]
    
        conn.execute(
            """
            UPDATE trips
            SET end_time = ?,
                total_distraction_sec = ?,
                alert_count = ?
            WHERE trip_id = ?
            """,
            (now, total_distraction_sec, alert_count, trip_id),
        )
        conn.commit()

        duration_sec = now - conn.execute(
            "SELECT start_time FROM trips WHERE trip_id = ?",
            (trip_id,),
        ).fetchone()[0]

        summary = {
            "trip_id": trip_id,
            "duration_sec": duration_sec,
            "total_distraction_sec": total_distraction_sec,
            "alert_count": alert_count,
        }

        logger.info(
            "I ended trip %s | %.0fs | distraction %.1fs | alerts %d",
            trip_id,
            duration_sec,
            total_distraction_sec,
            alert_count,
        )

        self._current_trip_id = None
        return summary

    
    def close(self): #i want to close the databse connection
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            logger.info("I closed the analytics database connection")



    def _save_activity_segment(self, activity, start_time, end_time, max_confidence):
        if self._current_trip_id is None:
            return
        if activity == "normal_driving":
            return
        
        duration_sec = end_time - start_time
        if duration_sec <= 0 :
            return
        conn = self._connect()
        conn.execute(
            """
            INSERT INTO activities
                (trip_id, activity, start_time, end_time, duration_sec, max_confidence)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                self._current_trip_id,
                activity,
                start_time,
                end_time,
                duration_sec,
                max_confidence,
            ),
        )
        conn.commit()
        logger.info(
            "I logged activity %s | %.1fs | max conf %.0f%%",
            activity,
            duration_sec,
            max_confidence * 100,
        )

    def _flush_current_segment(self, end_time=None):
        if self._tracking_activity is None or self._tracking_start is None:
            return

        end_time = end_time or time.time()
        self._save_activity_segment(
            self._tracking_activity,
            self._tracking_start,
            end_time,
            self._tracking_max_conf,
        )
        self._tracking_activity = None
        self._tracking_start = None
        self._tracking_max_conf = 0.0



    def update_state(self, activity, confidence, activity_start_time):
        if self._current_trip_id is None:
            return

        if self._tracking_activity is None:
            self._tracking_activity = activity
            self._tracking_start = activity_start_time
            self._tracking_max_conf = confidence
            return

        if activity != self._tracking_activity:
            self._save_activity_segment(
                self._tracking_activity,
                self._tracking_start,
                activity_start_time,
                self._tracking_max_conf,
            )
            self._tracking_activity = activity
            self._tracking_start = activity_start_time
            self._tracking_max_conf = confidence
        else:
            self._tracking_max_conf = max(self._tracking_max_conf, confidence)



    def log_alert(self, alert): #i want to log an alaert to the database
        if self._current_trip_id is None:  #i am checking if there was an active trip
            logger.warning("I tried to log an alert but no trip was active")
            return
        if alert is None: 
            return

        conn = self._connect() #i am conecting to the database
        conn.execute(
            """
            INSERT INTO alerts 
                (trip_id, activity, duration_at_alert, threshold, confidence,
                shadow_mode, message, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self._current_trip_id,
                alert["activity"],
                alert["duration"],
                alert["threshold"],
                alert["confidence"],
                1 if alert["shadow_mode"] else 0,
                alert.get("message"),
                alert["timestamp"],
            ),
        )
        conn.commit()
        logger.info(
            "I logged alert | %s | %.1fs | shadow=%s",
            alert["activity"],
            alert["duration"],
            alert["shadow_mode"],
        )

    #Now this sections is for the dahsbord visualisation of the data, so i will be building 2 API endpoints for that
    #ENDPOINT 1: Current Day Acitivtyies + Last 6 days (7 days in total)
    #I am using all 7 days even though i did not drive everyday, the plot height shows 0
    def get_last_7_days_summary(self):
        """This will return 7 days (today + last 6 days) with distraction minutees
        used for plot 1 on the dashboard
        """
        conn = self._connect() #connecting to the database
        placeholders = ",".join("?" for _ in self._distraction_activities) #i am creating a placeholder for the distraction activities
        rows = [] #creating an empty list to store the resukts
        if self._distraction_activities:
            rows = conn.execute(
                f"""
                SELECT date(start_time, 'unixepoch', 'localtime') AS day,
                       COALESCE(SUM(duration_sec), 0) AS total_sec
                FROM activities
                WHERE activity IN ({placeholders})
                GROUP BY day
                """,
                tuple(self._distraction_activities),
            ).fetchall()
        totals_by_day = {row["day"]: row["total_sec"] for row in rows}
        today = datetime.now().date()
        summary = []
        for i in range(6, -1, -1): #i am iterating over the last 7 days in reverse order, so it looks like today 0 Wed, 1 Tue, 2 Mon, 3 Sun like that
            day = today - timedelta(days=i) #timedelta is like time duration (e.g., 3 days, 5 hours, 30 minutes).
            day_str = day.strftime("%Y-%m-%d") #i am formating the date as YYY-MM-DD
            total_sec = totals_by_day.get(day_str, 0.0) #i am getting the totsl distraction time for this day, if no data, then i am setting it to 0.0
            summary.append({
                "date": day_str,
                "weekday": day.strftime("%a"), #i am getting the weekday name in short format like Mon, Tue, Wed
                "total_distraction_minutes": round(total_sec / 60.0, 2), #rounding up the distractin time to 2 decimal points
            })
        return summary

   #ENDPOINT 2: Once user clicks on any of the day bars from ENDPOINT 1, i want it to return each activity distraction minutes for that particular day
    def get_activity_breakdown_for_day(self, date_str):
        conn = self._connect()
        placeholders = ",".join("?" for _ in self._distraction_activities)
        rows = []
        if self._distraction_activities:
            rows = conn.execute(
                f"""
                SELECT activity,
                       COALESCE(SUM(duration_sec), 0) AS total_sec
                FROM activities
                WHERE date(start_time, 'unixepoch', 'localtime') = ?
                  AND activity IN ({placeholders})
                GROUP BY activity
                ORDER BY total_sec DESC
                """,
                (date_str, *self._distraction_activities),
            ).fetchall()

    
        return [
            {
                "activity": row["activity"],
                "minutes": round(row["total_sec"] / 60.0, 2),
            }
            for row in rows
        ]
