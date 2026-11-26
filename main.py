# Smart Parking Fee Management
# Validates entry and exit times, handles overnight parking and daily caps,
# applies vehicle category rates and penalty rules, and generates a fee summary.

import math

VEHICLE_RATES = {
    "BIKE": {"hourly": 15.0, "daily_cap": 100.0, "overnight_fee": 30.0},
    "CAR": {"hourly": 40.0, "daily_cap": 300.0, "overnight_fee": 80.0},
    "SUV": {"hourly": 60.0, "daily_cap": 450.0, "overnight_fee": 120.0},
    "TRUCK": {"hourly": 100.0, "daily_cap": 750.0, "overnight_fee": 200.0},
}


def parse_time_to_minutes(time_str):
    """
    Validates 'HH:MM' (24-hour format, 00:00 to 23:59) and converts to minutes since 00:00.
    Returns None if invalid.
    """
    parts = time_str.strip().split(":")
    if len(parts) != 2:
        return None
    hh_str, mm_str = parts
    if not (hh_str.isdigit() and mm_str.isdigit()):
        return None
    hours = int(hh_str)
    minutes = int(mm_str)
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        return None
    return hours * 60 + minutes


def calculate_parking_fee(
    vehicle_type,
    entry_time_str,
    exit_time_str,
    overnight_stay=False,
    lost_ticket=False,
    overstay_penalty_rate=50.0,
    max_allowed_hours=24,
):
    v_type = vehicle_type.strip().upper()
    if v_type not in VEHICLE_RATES:
        raise ValueError(f"Unsupported vehicle category '{vehicle_type}'.")

    entry_mins = parse_time_to_minutes(entry_time_str)
    exit_mins = parse_time_to_minutes(exit_time_str)

    if entry_mins is None or exit_mins is None:
        raise ValueError("Invalid time format. Use HH:MM in 24-hour format (00:00 to 23:59).")

    # If exit time is earlier than entry time (or overnight_stay is explicitly True and exit <= entry),
    # treat as crossing midnight into the next day.
    crossed_midnight = False
    if exit_mins < entry_mins:
        duration_mins = (24 * 60 - entry_mins) + exit_mins
        crossed_midnight = True
    elif exit_mins == entry_mins and overnight_stay:
        duration_mins = 24 * 60
        crossed_midnight = True
    elif exit_mins == entry_mins and not overnight_stay:
        raise ValueError("Entry and exit times cannot be identical for a same-day session.")
    else:
        duration_mins = exit_mins - entry_mins
        if overnight_stay:
            crossed_midnight = True

    total_hours_exact = duration_mins / 60.0
    billable_hours = max(1, math.ceil(total_hours_exact))

    rates = VEHICLE_RATES[v_type]
    hourly_rate = rates["hourly"]
    daily_cap = rates["daily_cap"]
    overnight_fee = rates["overnight_fee"] if crossed_midnight else 0.0

    # Calculate base parking charge across full days + remaining hours, capped per day
    full_days = billable_hours // 24
    rem_hours = billable_hours % 24

    full_day_charge = full_days * daily_cap
    partial_day_charge = min(rem_hours * hourly_rate, daily_cap)
    base_parking_charge = full_day_charge + partial_day_charge

    # Penalties: lost ticket flat penalty + overstay penalty if exceeding allowed hours
    penalty = 0.0
    penalty_reasons = []

    if lost_ticket:
        lost_fee = daily_cap * 1.5
        penalty += lost_fee
        penalty_reasons.append(f"Lost Ticket ({lost_fee:.2f})")

    if billable_hours > max_allowed_hours:
        extra_hours = billable_hours - max_allowed_hours
        overstay_fee = extra_hours * overstay_penalty_rate
        penalty += overstay_fee
        penalty_reasons.append(f"Overstay {extra_hours}h ({overstay_fee:.2f})")

    total_payable = base_parking_charge + overnight_fee + penalty

    return {
        "vehicle_type": v_type,
        "entry_time": entry_time_str.strip(),
        "exit_time": exit_time_str.strip(),
        "duration_hours": total_hours_exact,
        "billable_hours": billable_hours,
        "crossed_midnight": crossed_midnight,
        "base_parking_charge": base_parking_charge,
        "overnight_fee": overnight_fee,
        "penalty": penalty,
        "penalty_reasons": penalty_reasons,
        "total_payable": total_payable,
    }


def print_parking_receipt(summary, currency="INR"):
    print("\n" + "=" * 58)
    print("SMART PARKING FEE RECEIPT")
    print("=" * 58)
    print(f"Vehicle Category   : {summary['vehicle_type']}")
    print(f"Entry -> Exit Time : {summary['entry_time']} -> {summary['exit_time']}")
    print(f"Actual Duration    : {summary['duration_hours']:.2f} hours")
    print(f"Billable Hours     : {summary['billable_hours']} hour(s)")
    print(f"Overnight Stay     : {'Yes' if summary['crossed_midnight'] else 'No'}")
    print("-" * 58)
    print(f"Base Parking Fee   : {summary['base_parking_charge']:>8.2f} {currency}")
    print(f"Overnight Surcharge : {summary['overnight_fee']:>8.2f} {currency}")

    if summary["penalty_reasons"]:
        reasons_str = ", ".join(summary["penalty_reasons"])
        print(f"Penalties          : {summary['penalty']:>8.2f} {currency} [{reasons_str}]")
    else:
        print(f"Penalties          : {summary['penalty']:>8.2f} {currency} [None]")

    print("-" * 58)
    print(f"TOTAL PAYABLE      : {summary['total_payable']:>8.2f} {currency}")
    print("=" * 58)


def main():
    print("Available Vehicle Categories:", ", ".join(VEHICLE_RATES.keys()))
    vehicle_type = input("Enter vehicle category: ").strip()
    entry_time_str = input("Enter entry time (HH:MM, 24-hr): ").strip()
    exit_time_str = input("Enter exit time (HH:MM, 24-hr): ").strip()
    overnight_input = input("Is this an overnight stay? (y/n): ").strip().lower()
    lost_input = input("Is the parking ticket lost? (y/n): ").strip().lower()

    overnight_stay = overnight_input in ("y", "yes")
    lost_ticket = lost_input in ("y", "yes")

    try:
        summary = calculate_parking_fee(
            vehicle_type=vehicle_type,
            entry_time_str=entry_time_str,
            exit_time_str=exit_time_str,
            overnight_stay=overnight_stay,
            lost_ticket=lost_ticket,
        )
        print_parking_receipt(summary)
    except ValueError as err:
        print(f"\nInput Error: {err}")


if __name__ == "__main__":
    main()
