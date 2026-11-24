#!/usr/bin/env python3
"""Convert a local Apple Health export into public weekly workout totals."""

import argparse
import json
import math
import tempfile
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("Asia/Tokyo")
START = date(2026, 1, 1)
CATEGORIES = ("functionalStrengthTraining", "skatingSports", "outdoorWalking")
DURATION = {"s": 1, "min": 60, "hr": 3600}
ENERGY = {"kcal": 1, "kJ": 1 / 4.184, "J": 1 / 4184}


def monday(day):
    return day - timedelta(days=day.weekday())


def weeks_through(through):
    weeks = {}
    week = monday(START)
    while week <= through:
        weeks[week] = {
            "start": week.isoformat(),
            "end": (week + timedelta(days=6)).isoformat(),
            "outdoorIncomplete": False,
            "activities": {
                category: {"count": 0, "seconds": 0, "kcal": 0, "missingEnergy": 0}
                for category in CATEGORIES
            },
        }
        week += timedelta(days=7)
    return weeks


def workouts(path):
    events = iter(ET.iterparse(path, events=("start", "end")))
    _, root = next(events)
    if root.tag != "HealthData":
        raise ValueError("Expected an Apple Health export.xml")
    depth = 1
    for event, element in events:
        if event == "start":
            depth += 1
            continue
        if depth == 2:
            if element.tag == "Workout":
                yield element
            root.remove(element)
        depth -= 1


def quantity(value, unit, factors):
    result = float(value) * factors[unit]
    if result < 0 or not math.isfinite(result):
        raise ValueError("Invalid workout quantity")
    return result


def energy(workout):
    for stat in workout.findall("WorkoutStatistics"):
        if stat.get("type") == "HKQuantityTypeIdentifierActiveEnergyBurned" and stat.get("sum") is not None:
            return quantity(stat.get("sum"), stat.get("unit"), ENERGY)
    if workout.get("totalEnergyBurned") is not None:
        return quantity(workout.get("totalEnergyBurned"), workout.get("totalEnergyBurnedUnit"), ENERGY)
    return None


def aggregate(path, through):
    weeks = weeks_through(through)
    for workout in workouts(path):
        activity = workout.attrib["workoutActivityType"].removeprefix("HKWorkoutActivityType")
        activity = activity[:1].lower() + activity[1:]
        if activity not in (*CATEGORIES, "walking"):
            continue
        started = datetime.strptime(workout.attrib["startDate"], "%Y-%m-%d %H:%M:%S %z")
        day = started.astimezone(ZONE).date()
        if not START <= day <= through:
            continue
        week = weeks[monday(day)]
        if activity == "walking":
            indoor = workout.find("./MetadataEntry[@key='HKIndoorWorkout']")
            flag = indoor.get("value", "").lower() if indoor is not None else ""
            if flag not in ("0", "false"):
                if flag not in ("1", "true"):
                    week["outdoorIncomplete"] = True
                continue
            activity = "outdoorWalking"
        totals = week["activities"][activity]
        totals["count"] += 1
        totals["seconds"] += quantity(workout.attrib["duration"], workout.attrib["durationUnit"], DURATION)
        kcal = energy(workout)
        if kcal is None:
            totals["missingEnergy"] += 1
        else:
            totals["kcal"] += kcal
    for week in weeks.values():
        for totals in week["activities"].values():
            for key in ("seconds", "kcal"):
                totals[key] = round(totals[key], 3)
    return {"timeZone": ZONE.key, "through": through.isoformat(), "weeks": list(reversed(weeks.values()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export_xml", type=Path, help="Apple Health export.xml stored outside the repository")
    parser.add_argument("--through", type=date.fromisoformat, required=True, help="Last covered local date (YYYY-MM-DD)")
    args = parser.parse_args()
    if not START <= args.through <= datetime.now(ZONE).date():
        parser.error("--through must be between 2026-01-01 and today in Asia/Tokyo")
    result = aggregate(args.export_xml, args.through)
    target = Path(__file__).resolve().parent.parent / "workouts.json"
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent, delete=False) as temp:
        temporary_path = Path(temp.name)
        try:
            json.dump(result, temp, ensure_ascii=False, indent=2, allow_nan=False)
            temp.write("\n")
            temp.close()
            temporary_path.replace(target)
        finally:
            temporary_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
