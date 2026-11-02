#Phase 9 - I want to compute hybrid saferty score from Phase 7 Activity Data
import logging
import sqlite3
from datetime import datetime, timedelta
logger = logging.getLogger(__name__)

class SafetyScoreEngine:
    def __init__(self, weights=None, scale_factor=0.15, bands=None, exposure_unit="minutes", db_path = None):
        self._weights = weights or {} # this is the dictionary of weights for each behaviour
        self._scale_factor = scale_factor # this is the scale factor for the score
        self._bands = bands or {"excellent": 90, "good": 80, "fair": 70, "poor": 70} #this is the dictionary of bands for the score
        self._exposure_unit = exposure_unit #this is the unit of exposure for the score 
        self._db_path = db_path #thisc is the psth to the database
        logger.info(
            "I started the Safety Score Engine (scale_factor=%s, %d weights)",
            scale_factor,
            len(self._weights),
        )

    #This method converts the duration in seconds to minutes
    def _to_minutes(self, duration_sec): 
        if self._exposure_unit == "minutes": #if the exposure unit is minutes, then return the duration in minutes
            return duration_sec / 60.0
        return duration_sec

    
    #This method computes the contributions of each activity to the total risk
    def compute_contributions(self, activity_durations):
        contributions = {} #this is the dictionary for each acitivty
        total_risk = 0.0 #total risk of the activities

        for activity, duration_sec in activity_durations.items(): #for each activity, get the diration in seconds
            weight = self._weights.get(activity, 0) #get the weight for the acitivity
            if weight == 0 or duration_sec <= 0: #if the weight is 0 or less than 0, then continue
                continue

            minutes = self._to_minutes(duration_sec) #this is going to convert the duration in seconds to minutes
            points = minutes * weight
            contributions[activity] = round(points, 2) #rounding it up to 2 decimal places
            total_risk += points #adding the points to the total risk

        return contributions, round(total_risk, 2) #returning the contributions and the total risk

    
    #This computes the safety score from the total risk
    def compute_safety_score(self, total_risk):
        normalized_risk = min(100.0, total_risk * self._scale_factor) #this is going to help me normalise the risk to 100 (it is part of my hybrid approach i wrote down)
        safety_score = max(0.0, 100.0 - normalized_risk) 
        return round(safety_score, 1) #rounding it up to 1 decimal placee


   
   #THIs helps me classify the safety score into bands
    def classify_band(self, safety_score):
        if safety_score >= self._bands["excellent"]:
            return "Excellent"
        if safety_score >= self._bands["good"]:
            return "Good"
        if safety_score >= self._bands["fair"]:
            return "Fair"
        return "High risk"



    #This method will wrap all methods together and help me run the full chain for convenience
    def score_from_durations(self, activity_durations):
        contributions, total_risk = self.compute_contributions(activity_durations) #this is going to compute the contributions of each activity to the total risj
        safety_score = self.compute_safety_score(total_risk) 
        band = self.classify_band(safety_score)
        return {
            "contributions": contributions,
            "total_risk": total_risk,
            "safety_score": safety_score,
            "band": band,  
        }

    #This method helps me collect the trip durations from the database
    def _get_trip_durations(self, trip_id):
        if not self._db_path:
            raise ValueError("I need db_path to read trip activities")

        conn = sqlite3.connect(self._db_path)
        rows = conn.execute(
            """
            SELECT activity, SUM(duration_sec) AS total_sec
            FROM activities
            WHERE trip_id = ?
            GROUP BY activity
            """,
            (trip_id,),
        ).fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

        #This method help me compute the trip score from the trip id
    def compute_trip_score(self, trip_id):
        durations = self._get_trip_durations(trip_id)
        result = self.score_from_durations(durations)
        result["trip_id"] = trip_id
        result["activity_durations_sec"] = durations
        result["top_contributors"] = self.get_top_contributors(
            result["contributions"],
            n=3,
            total_risk=result["total_risk"],
        )
        return result


    #Ths helps me get ttimebounds for the last 7 days
    def _get_week_bounds(self, end_date = None):
        if end_date is None:
            end = datetime.now().date()
        else:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        start = end - timedelta(days = 6)
        start_ts = datetime.combine(start, datetime.min.time()).timestamp()
        end_ts = datetime.combine(end, datetime.max.time()).timestamp()
        return start, end, start_ts, end_ts

    #This method helps me get the weekly duratyions from the database
    def _get_week_durations(self, end_date = None):
        if not self._db_path:
            raise ValueError("I need db_path to read weekly data")

        start, end, start_ts, end_ts = self._get_week_bounds(end_date)
        conn = sqlite3.connect(self._db_path)

        rows = conn.execute(
            """
            SELECT activity, SUM(duration_sec) AS total_sec
            FROM activities
            WHERE start_time >= ? AND start_time <= ?
            GROUP BY activity
            """,
            (start_ts, end_ts),
        ).fetchall()

        trip_row = conn.execute(
            """
            SELECT COALESCE(SUM(end_time - start_time), 0)
            FROM trips
            WHERE start_time >= ? AND start_time <= ?
              AND end_time IS NOT NULL
            """,
            (start_ts, end_ts),
        ).fetchone()
        conn.close()

        durations = {row[0]: row[1] for row in rows}
        total_driving_sec = trip_row[0] if trip_row else 0.0
        return start, end, durations, total_driving_sec

    def _compute_percentage(self, durations, total_driving_sec):
        if not durations and total_driving_sec <= 0:
            return 0.0, {}

        distraction_sec = sum(durations.values())
        denominator = max(total_driving_sec, distraction_sec)
        if denominator <= 0:
            return 0.0, {}

        safe_sec = max(0.0, denominator - distraction_sec)
        safe_pct = round((safe_sec / denominator) * 100, 1)

        behavior_pct = {
            activity: round((sec / denominator) * 100, 1)
            for activity, sec in durations.items()
        }
        return safe_pct, behavior_pct

    def get_top_contributors(self, contributions, n=3, total_risk=None):
        """Return top N behaviors by risk contribution, sorted descending."""
        ranked = sorted(contributions.items(), key=lambda item: item[1], reverse=True)
        top = []
        for behavior, contribution in ranked[:n]:
            entry = {"behavior": behavior, "contribution": round(contribution, 2)}
            if total_risk and total_risk > 0:
                entry["pct_of_total_risk"] = round((contribution / total_risk) * 100, 1)
            top.append(entry)
        return top

    def compute_weekly_score(self, end_date = None):
        start, end, durations, total_driving_sec = self._get_week_durations(end_date)
        safe_pct, behavior_pct = self._compute_percentage(durations, total_driving_sec)

        has_data = total_driving_sec > 0 or bool(durations)
        if not has_data:
            score_result = {
                "contributions": {},
                "total_risk": 0.0,
                "safety_score": None,
                "band": "No data",
                "top_contributors": [],
            }
        else:
            score_result = self.score_from_durations(durations)
            score_result["top_contributors"] = self.get_top_contributors(
                score_result["contributions"],
                n=3,
                total_risk=score_result["total_risk"],
            )

        return {
            "week_start": start.isoformat(),
            "week_end": end.isoformat(),
            "total_driving_minutes": round(total_driving_sec / 60.0, 1),
            "safe_driving_pct": safe_pct,
            "behavior_pct": behavior_pct,
            "has_data": has_data,
            **score_result,
        }
