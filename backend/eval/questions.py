"""25 questions with hand-written reference SQL. Dates are fixed to the seed's AS_OF (2026-10-31).

`ordered=True` means row order matters for a correct answer (rankings).
`difficulty`: 1 = single table / simple filter, 2 = join or aggregate, 3 = multi-step (CTE, ratio, anti-join).
"""

OCT = "BETWEEN '2026-10-01' AND '2026-10-31'"

QUESTIONS = [
    # --- the demo question + rain ---
    dict(id=1, difficulty=2, q="Which site lost the most hours to rain this month?",
         sql=f"SELECT s.name FROM daily_logs d JOIN sites s ON s.id=d.site_id WHERE d.log_date {OCT} "
             "GROUP BY s.name ORDER BY SUM(d.rain_hours_lost) DESC LIMIT 1"),
    dict(id=2, difficulty=2, q="What are the total hours lost to rain across all sites in October?",
         sql=f"SELECT SUM(rain_hours_lost) FROM daily_logs WHERE log_date {OCT}"),
    dict(id=3, difficulty=2, q="How many rainy days did each site have in October?",
         sql=f"SELECT s.name, COUNT(*) FROM daily_logs d JOIN sites s ON s.id=d.site_id "
             f"WHERE d.weather='rain' AND d.log_date {OCT} GROUP BY s.name"),
    dict(id=4, difficulty=2, q="Which date had the most rain hours lost across all sites combined?",
         sql="SELECT log_date FROM daily_logs GROUP BY log_date ORDER BY SUM(rain_hours_lost) DESC LIMIT 1"),
    dict(id=5, difficulty=3, q="What is the average rain hours lost per rainy day across all sites in October?",
         sql=f"SELECT AVG(rain_hours_lost) FROM daily_logs WHERE weather='rain' AND log_date {OCT}"),
    dict(id=6, difficulty=3, q="Which month had the most rain hours lost overall?",
         sql="SELECT to_char(log_date,'YYYY-MM') FROM daily_logs GROUP BY 1 ORDER BY SUM(rain_hours_lost) DESC LIMIT 1"),
    dict(id=7, difficulty=3, q="How many sites lost more than 20 hours to rain in October?",
         sql=f"SELECT COUNT(*) FROM (SELECT site_id FROM daily_logs WHERE log_date {OCT} "
             "GROUP BY site_id HAVING SUM(rain_hours_lost) > 20) t"),

    # --- status / progress ---
    dict(id=8, difficulty=1, q="How many sites are at risk?",
         sql="SELECT COUNT(*) FROM sites WHERE status='at_risk'"),
    dict(id=9, difficulty=1, q="List the delayed sites.",
         sql="SELECT name FROM sites WHERE status='delayed'"),
    dict(id=10, difficulty=1, q="Which site has the highest progress percentage?",
         sql="SELECT name FROM sites ORDER BY progress_pct DESC LIMIT 1"),
    dict(id=11, difficulty=2, q="Which site is furthest behind its planned progress?",
         sql="SELECT name FROM sites ORDER BY (planned_pct - progress_pct) DESC LIMIT 1"),
    dict(id=12, difficulty=1, q="How many sites are scheduled to finish within the next 60 days?",
         sql="SELECT COUNT(*) FROM sites WHERE planned_end BETWEEN '2026-10-31' AND '2026-12-30'"),
    dict(id=13, difficulty=1, q="Which site has the largest budget?",
         sql="SELECT name FROM sites ORDER BY budget_inr DESC LIMIT 1"),
    dict(id=14, difficulty=1, q="What is the total budget of all at-risk sites?",
         sql="SELECT SUM(budget_inr) FROM sites WHERE status='at_risk'"),

    # --- milestones ---
    dict(id=15, difficulty=2, q="How many milestones are overdue?",
         sql="SELECT COUNT(*) FROM milestones WHERE actual_date IS NULL AND planned_date < '2026-10-31'"),
    dict(id=16, difficulty=3, q="Which site has the most overdue milestones?",
         sql="SELECT s.name FROM milestones m JOIN sites s ON s.id=m.site_id "
             "WHERE m.actual_date IS NULL AND m.planned_date < '2026-10-31' "
             "GROUP BY s.name ORDER BY COUNT(*) DESC, s.name LIMIT 1"),
    dict(id=17, difficulty=2, q="How many milestones were completed late, after their planned date?",
         sql="SELECT COUNT(*) FROM milestones WHERE actual_date > planned_date"),

    # --- labour ---
    dict(id=18, difficulty=2, q="What was the average number of workers per day at Kota Metro Mall in October?",
         sql=f"SELECT AVG(d.workers_present) FROM daily_logs d JOIN sites s ON s.id=d.site_id "
             f"WHERE s.name='Kota Metro Mall' AND d.log_date {OCT}"),
    dict(id=19, difficulty=2, q="Total labour hours at Jodhpur Tech Park in the last 7 days?",
         sql="SELECT SUM(d.hours_worked) FROM daily_logs d JOIN sites s ON s.id=d.site_id "
             "WHERE s.name='Jodhpur Tech Park' AND d.log_date BETWEEN '2026-10-25' AND '2026-10-31'"),
    dict(id=20, difficulty=2, q="Rank sites by total labour hours in October, highest first.",
         sql=f"SELECT s.name, SUM(d.hours_worked) FROM daily_logs d JOIN sites s ON s.id=d.site_id "
             f"WHERE d.log_date {OCT} GROUP BY s.name ORDER BY 2 DESC", ordered=True),
    dict(id=21, difficulty=1, q="How many working days did Alwar Greens Apartments log in October?",
         sql=f"SELECT COUNT(*) FROM daily_logs d JOIN sites s ON s.id=d.site_id "
             f"WHERE s.name='Alwar Greens Apartments' AND d.log_date {OCT}"),

    # --- materials ---
    dict(id=22, difficulty=2, q="What was the total cement cost across all sites this month?",
         sql=f"SELECT SUM(cost_inr) FROM material_usage WHERE material='cement' AND log_date {OCT}"),
    dict(id=23, difficulty=2, q="Which material has cost the most overall?",
         sql="SELECT material FROM material_usage GROUP BY material ORDER BY SUM(cost_inr) DESC LIMIT 1"),
    dict(id=24, difficulty=3, q="Which site used the most steel in September, in kg?",
         sql="SELECT s.name FROM material_usage u JOIN sites s ON s.id=u.site_id "
             "WHERE u.material='steel' AND u.log_date BETWEEN '2026-09-01' AND '2026-09-30' "
             "GROUP BY s.name ORDER BY SUM(u.qty) DESC LIMIT 1"),
    dict(id=25, difficulty=3, q="Which site spent the most on materials in October?",
         sql=f"SELECT s.name FROM material_usage u JOIN sites s ON s.id=u.site_id WHERE u.log_date {OCT} "
             "GROUP BY s.name ORDER BY SUM(u.cost_inr) DESC LIMIT 1"),
]
