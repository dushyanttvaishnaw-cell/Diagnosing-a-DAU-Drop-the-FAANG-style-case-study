"""
generate_data.py
Generates 120 days of daily session-level event data for a consumer app,
with a genuine (synthetically injected) root cause for a DAU drop: a
login-failure bug shipped in iOS app version 4.2, affecting a subset of
iOS users starting on day 75. This mirrors the classic "diagnose a metric
drop" case study format used in analyst interview loops (Meta, Google,
Amazon): the investigator does not know the cause in advance and must
find it through segmentation.
"""
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(21)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

N_DAYS = 120
START = datetime(2025, 6, 1)
DATES = [START + timedelta(days=i) for i in range(N_DAYS)]

PLATFORMS = ["iOS", "Android", "Web"]
PLATFORM_SHARE = [0.42, 0.38, 0.20]
COUNTRIES = ["US", "UK", "DE", "IN", "BR"]
COUNTRY_SHARE = [0.35, 0.15, 0.12, 0.23, 0.15]
CHANNELS = ["Organic", "Paid Social", "Push Notification", "Referral"]

BASE_DAU = 42000
BUG_START_DAY = 75          # login-failure bug ships in iOS v4.2
BUG_AFFECTED_VERSION_SHARE = 0.55   # 55% of iOS users are on the buggy version by day 75+
BUG_FAILURE_RATE = 0.34     # of affected users, 34% fail to complete login that day

records = []
for day_idx, date in enumerate(DATES):
    # Overall organic trend: mild weekly seasonality (weekend dip) + slow growth
    weekday = date.weekday()
    weekend_factor = 0.90 if weekday >= 5 else 1.0
    trend_factor = 1.0 + 0.0015 * day_idx  # slow underlying growth
    day_dau_target = BASE_DAU * weekend_factor * trend_factor

    for platform, p_share in zip(PLATFORMS, PLATFORM_SHARE):
        platform_target = day_dau_target * p_share * np.random.normal(1.0, 0.03)

        # iOS app version mix: v4.1 baseline, v4.2 rolls out starting day 70,
        # ramping to ~55% of iOS traffic by day 75+ (typical staged rollout)
        if platform == "iOS":
            if day_idx < 70:
                v42_share = 0.0
            elif day_idx < 78:
                v42_share = min(BUG_AFFECTED_VERSION_SHARE, (day_idx - 70) / 8 * BUG_AFFECTED_VERSION_SHARE)
            else:
                v42_share = BUG_AFFECTED_VERSION_SHARE
        else:
            v42_share = 0.0  # not applicable to Android/Web

        for country, c_share in zip(COUNTRIES, COUNTRY_SHARE):
            segment_target = platform_target * c_share

            for channel in CHANNELS:
                ch_weight = {"Organic": 0.45, "Paid Social": 0.25,
                             "Push Notification": 0.20, "Referral": 0.10}[channel]
                base_sessions = int(max(0, np.random.poisson(segment_target * ch_weight)))
                if base_sessions == 0:
                    continue

                if platform == "iOS" and v42_share > 0:
                    n_v42 = int(base_sessions * v42_share)
                    n_v41 = base_sessions - n_v42
                    # Bug only active from BUG_START_DAY onward (rollout != bug trigger date;
                    # the bug was in v4.2 code but only manifested after a server-side config
                    # change on day 75, a common real-world "it's not just the release" wrinkle)
                    if day_idx >= BUG_START_DAY:
                        failed = int(n_v42 * BUG_FAILURE_RATE)
                        successful_v42 = n_v42 - failed
                    else:
                        failed = 0
                        successful_v42 = n_v42
                    records.append((date.date(), platform, country, channel, "4.2",
                                     successful_v42, failed))
                    records.append((date.date(), platform, country, channel, "4.1",
                                     n_v41, 0))
                else:
                    version = "N/A" if platform != "iOS" else "4.1"
                    records.append((date.date(), platform, country, channel, version,
                                     base_sessions, 0))

df = pd.DataFrame(records, columns=[
    "date", "platform", "country", "channel", "app_version",
    "successful_sessions", "failed_login_sessions"
])
df.to_csv(os.path.join(DATA_DIR, "daily_sessions.csv"), index=False)

print(f"daily_sessions: {df.shape}")
print(f"Bug window starts day {BUG_START_DAY} ({DATES[BUG_START_DAY].date()})")
print("Saved to /data")
