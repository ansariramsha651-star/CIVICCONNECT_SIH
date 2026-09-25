def classify_complaint(description):

    text = description.lower()

    # Category and Department
    if any(word in text for word in ["garbage", "waste", "trash", "dirty"]):

        category = "Waste Management"
        department = "Sanitation"

    elif any(word in text for word in ["pothole", "road", "street", "footpath"]):

        category = "Roads"
        department = "Public Works"

    elif any(word in text for word in ["water", "leakage", "pipe", "drain"]):

        category = "Water Supply"
        department = "Water Department"

    elif any(word in text for word in ["light", "streetlight", "lamp"]):

        category = "Street Lighting"
        department = "Electrical Department"

    else:

        category = "Other"
        department = "General Department"


    # Priority
    if any(word in text for word in [
        "accident",
        "danger",
        "fire",
        "emergency",
        "injury",
        "flood"
    ]):

        priority = "High"

    elif any(word in text for word in [
        "large",
        "severe",
        "major",
        "bad",
        "overflow",
        "blocked"
    ]):

        priority = "Medium"

    else:

        priority = "Low"


    return category, department, priority