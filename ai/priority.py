PRIORITY_RULES = {
    "Pothole": ("HIGH", 48),
    "Garbage": ("MEDIUM", 48),
    "Drainage": ("HIGH", 24),
    "Water Leakage": ("HIGH", 24),
    "Streetlight": ("MEDIUM", 48),
    "Road Obstruction": ("HIGH", 24),
    "Flooding": ("CRITICAL", 12),
    "Traffic Signal": ("CRITICAL", 12),
    "Infrastructure Damage": ("HIGH", 48)
}
def get_priority(category):
    priority, sla_hours = PRIORITY_RULES.get(
        category,
        ("MEDIUM", 48)
    )
    return priority, sla_hours