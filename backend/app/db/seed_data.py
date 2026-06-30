from app.db.database import SessionLocal
from app.db.models import Department, SLA

def seed():
    db = SessionLocal()

    departments = [
        "Treasury & Investments", "KYC / AML", "Credit Risk",
        "Retail Banking Compliance", "IT & Cybersecurity",
        "HR & Conduct", "Legal & Regulatory Affairs",
        "Trade Finance", "Audit & Inspection"
    ]

    dept_objects = {}
    for name in departments:
        existing = db.query(Department).filter(Department.name == name).first()
        if not existing:
            d = Department(name=name)
            db.add(d)
            db.commit()
            db.refresh(d)
            dept_objects[name] = d
        else:
            dept_objects[name] = existing

    # Default SLA rules: source-specific overrides, fallback otherwise
    sla_rules = [
        ("Treasury & Investments", "RBI", 7),
        ("KYC / AML", "RBI", 5),
        ("Credit Risk", "RBI", 10),
        ("Legal & Regulatory Affairs", "SEBI", 21),
        ("Trade Finance", "RBI", 14),
    ]

    for dept_name, source, days in sla_rules:
        existing = db.query(SLA).filter(
            SLA.department_id == dept_objects[dept_name].id,
            SLA.circular_source == source
        ).first()
        if not existing:
            db.add(SLA(department_id=dept_objects[dept_name].id, circular_source=source, days_to_complete=days))

    db.commit()
    print("Seed data inserted.")

if __name__ == "__main__":
    seed()