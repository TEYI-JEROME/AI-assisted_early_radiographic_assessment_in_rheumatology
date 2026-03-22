from datetime import datetime, date
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.role import Role
from app.models.user import User
from app.models.patient import Patient
from app.services.password_service import PasswordService


def get_or_create_role(db, name: str) -> Role:
    role = db.query(Role).filter(Role.name == name).first()
    if role:
        return role

    role = Role(
        id=str(uuid4()),
        name=name,
        created_at=datetime.utcnow(),
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def get_or_create_user(db, *, email: str, full_name: str, password: str, roles: list[Role]) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user

    password_service = PasswordService()
    now = datetime.utcnow()

    user = User(
        id=str(uuid4()),
        email=email,
        full_name=full_name,
        password_hash=password_service.hash_password(password),
        is_active=True,
        failed_login_attempts=0,
        locked_until=None,
        last_login_at=None,
        created_at=now,
        updated_at=now,
    )
    user.roles = roles
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_patient(db, *, patient_id: str, hospital_number: str, full_name: str, dob: date, sex: str) -> Patient:
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if patient:
        return patient

    now = datetime.utcnow()
    patient = Patient(
        id=str(uuid4()),
        patient_id=patient_id,
        hospital_number=hospital_number,
        full_name=full_name,
        date_of_birth=dob,
        sex=sex,
        notes="Demo seeded patient",
        created_at=now,
        updated_at=now,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def main():
    db = SessionLocal()
    try:
        admin_role = get_or_create_role(db, "Admin")
        rheum_role = get_or_create_role(db, "Rheumatologist")
        resident_role = get_or_create_role(db, "Resident")

        get_or_create_user(
            db,
            email="admin@local.demo",
            full_name="Local Admin",
            password="AdminPassword!ChangeMe",
            roles=[admin_role],
        )

        get_or_create_user(
            db,
            email="rheum@local.demo",
            full_name="Demo Rheumatologist",
            password="RheumPassword!ChangeMe",
            roles=[rheum_role],
        )

        get_or_create_user(
            db,
            email="resident@local.demo",
            full_name="Demo Resident",
            password="ResidentPassword!ChangeMe",
            roles=[resident_role],
        )

        get_or_create_patient(
            db,
            patient_id="P-0001",
            hospital_number="H-10001",
            full_name="Jane Doe",
            dob=date(1971, 5, 2),
            sex="female",
        )

        get_or_create_patient(
            db,
            patient_id="P-0002",
            hospital_number="H-10002",
            full_name="John Doe",
            dob=date(1964, 11, 18),
            sex="male",
        )

        print("Seed completed successfully.")
        print("Demo users:")
        print("  admin@local.demo / AdminPassword!ChangeMe")
        print("  rheum@local.demo / RheumPassword!ChangeMe")
        print("  resident@local.demo / ResidentPassword!ChangeMe")

    finally:
        db.close()


if __name__ == "__main__":
    main()