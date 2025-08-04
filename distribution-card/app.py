from flask import Flask, render_template, request
import json
import os

app = Flask(__name__)

rotation_file = "rotation_index.json"

def load_rotation_indices():
    if os.path.exists(rotation_file):
        with open(rotation_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"tehran_morning_index": 0, "tehran_evening_index": 0, "shahrestan_index": 0}

def save_rotation_indices(indices):
    with open(rotation_file, "w", encoding="utf-8") as f:
        json.dump(indices, f, ensure_ascii=False, indent=4)

def calculated_needed_people(total_cards, max_limit):
    return (total_cards + max_limit - 1) // max_limit

def assign_people_rotational(people, count, start_index):
    assigned = []
    n = len(people)
    for i in range(count):
        idx = (start_index + i) % n
        assigned.append(people[idx])
    new_index = (start_index + count) % n
    return assigned, new_index

def distribute_with_limit(total_cards, team, max_limit):
    distribution = {}
    remaining_cards = total_cards

    for person in team:
        if remaining_cards <= 0:
            distribution[person] = 0
        else:
            share = min(max_limit, remaining_cards)
            distribution[person] = share
            remaining_cards -= share

    return distribution

def distribute_quality_check(total_quality_check, team, total_cards_distribution):
    distribution = {}
    total_cards_sum = sum(total_cards_distribution.values())
    if total_cards_sum == 0:
        base_share = total_quality_check // len(team)
        extra = total_quality_check % len(team)
        for i, person in enumerate(team):
            distribution[person] = base_share + (1 if i < extra else 0)
    else:
        allocated = 0
        for i, person in enumerate(team):
            if i == len(team) - 1:
                distribution[person] = total_quality_check - allocated
            else:
                share = round(total_quality_check * total_cards_distribution[person] / total_cards_sum)
                distribution[person] = share
                allocated += share
    return distribution

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        people = [p.strip() for p in request.form["people"].split(",") if p.strip()]
        tehran_morning_total = int(request.form["tehran_morning_total"])
        tehran_morning_quality = int(request.form["tehran_morning_quality"])
        tehran_evening_total = int(request.form["tehran_evening_total"])
        tehran_evening_quality = int(request.form["tehran_evening_quality"])
        shahrestan_total = int(request.form["shahrestan_total"])
        shahrestan_quality = int(request.form["shahrestan_quality"])
        max_limit = int(request.form["max_limit"])

        needed_morning = calculated_needed_people(tehran_morning_total, max_limit)
        needed_evening = calculated_needed_people(tehran_evening_total, max_limit)
        needed_shahrestan = calculated_needed_people(shahrestan_total, max_limit)

        if needed_morning + needed_evening + needed_shahrestan > len(people):
            return render_template("index.html", error="❌ تعداد افراد کافی نیست!")

        indices = load_rotation_indices()

        tehran_morning_team, indices["tehran_morning_index"] = assign_people_rotational(people, needed_morning, indices["tehran_morning_index"])
        remaining_after_morning = [p for p in people if p not in tehran_morning_team]

        tehran_evening_team, indices["tehran_evening_index"] = assign_people_rotational(remaining_after_morning, needed_evening, indices["tehran_evening_index"])
        remaining_after_evening = [p for p in remaining_after_morning if p not in tehran_evening_team]

        shahrestan_team, indices["shahrestan_index"] = assign_people_rotational(remaining_after_evening, needed_shahrestan, indices["shahrestan_index"])
        remaining_people = [p for p in remaining_after_evening if p not in shahrestan_team]

        save_rotation_indices(indices)

        morning_cards = distribute_with_limit(tehran_morning_total, tehran_morning_team, max_limit)
        evening_cards = distribute_with_limit(tehran_evening_total, tehran_evening_team, max_limit)
        shahrestan_cards = distribute_with_limit(shahrestan_total, shahrestan_team, max_limit)

        morning_quality = distribute_quality_check(tehran_morning_quality, tehran_morning_team, morning_cards)
        evening_quality = distribute_quality_check(tehran_evening_quality, tehran_evening_team, evening_cards)
        shahrestan_quality = distribute_quality_check(shahrestan_quality, shahrestan_team, shahrestan_cards)

        return render_template("result.html",
                               tehran_morning_team=tehran_morning_team,
                               tehran_evening_team=tehran_evening_team,
                               shahrestan_team=shahrestan_team,
                               remaining_people=remaining_people,
                               morning_cards=morning_cards,
                               evening_cards=evening_cards,
                               shahrestan_cards=shahrestan_cards,
                               morning_quality=morning_quality,
                               evening_quality=evening_quality,
                               shahrestan_quality=shahrestan_quality)

    return render_template("index.html")

@app.route("/reset", methods=["POST"])
def reset_rotation():
    default_indices = {"tehran_morning_index": 0, "tehran_evening_index": 0, "shahrestan_index": 0}
    save_rotation_indices(default_indices)
    return render_template("index.html", message="✅ نوبت‌دهی با موفقیت ریست شد!")

if __name__ == "__main__":
    app.run(debug=True)
