
from sqlalchemy import inspect, text
from app.db.session import engine

# Check whether the employees table already has shift_id.
inspector = inspect(engine)
columns = {
    column["name"]
    for column in inspector.get_columns("employees")
}

if "shift_id" in columns:
    print("shift_id column already exists.")
else:
    print("Adding shift_id column...")

    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE employees ADD COLUMN shift_id INT NULL")
        )

        connection.execute(
            text(
                "ALTER TABLE employees "
                "ADD CONSTRAINT fk_employees_shift "
                "FOREIGN KEY (shift_id) REFERENCES shifts(id)"
            )
        )

        connection.execute(
            text(
                "CREATE INDEX ix_employees_shift_id "
                "ON employees (shift_id)"
            )
        )

    print("shift_id column, foreign key, and index created.")

print("Migration finished.")
