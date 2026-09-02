from ai_engine import analyze_complaint
from routing import get_department
from priority import get_priority
complaint = input("Enter complaint: ")
result = analyze_complaint(complaint)
category = result["category"]
department = get_department(category)
priority, sla_hours = get_priority(category)
print("\n========== CIVICAI ANALYSIS ==========")
print("Complaint:", complaint)
print("Category:", category)
print("Confidence:", result["confidence"])
print("Priority:", priority)
print("Department:", department)
print("SLA:", sla_hours, "hours")
print("======================================")