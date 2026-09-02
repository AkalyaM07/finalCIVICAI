DEPARTMENT_MAP = {
    "Pothole": "Roads Department",
    "Garbage": "Sanitation Department",
    "Drainage": "Drainage Department",
    "Water Leakage": "Water Department",
    "Streetlight": "Electrical Department",
    "Road Obstruction": "Roads Department",
    "Flooding": "Disaster Management Department",
    "Traffic Signal": "Traffic Department",
    "Infrastructure Damage": "Public Works Department"
}
def get_department(category):
    return DEPARTMENT_MAP.get(
        category,
        "Municipal General Department"
    )