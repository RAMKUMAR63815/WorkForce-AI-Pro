
import logging
import threading
from datetime import datetime

from sqlalchemy.orm import sessionmaker

from app.db.session import engine
from app.models.workforce_monitoring import WorkforceMonitoring
from app.api.workforce_monitoring import calculate_metrics
from app.models.workforce_kpi_target import WorkforceKPITarget
from app.models.workforce_kpi_breach import WorkforceKPIBreach
from app.api.workforce_dashboard import get_workforce_kpis
from app.api.employee_risk_alert import (
    evaluate_employee_risk_changes,
)

logger = logging.getLogger(__name__)

# Create independent database sessions for background work.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

# Run the snapshot every 15 minutes.
INTERVAL_SECONDS = 15 * 60

_stop_event = threading.Event()
_scheduler_thread = None


def save_monitoring_snapshot() -> None:
    """Calculate current workforce metrics and save a snapshot."""
    db = SessionLocal()

    try:
        metrics = calculate_metrics(db)

        snapshot = WorkforceMonitoring(
            **metrics,
            snapshot_at=datetime.now(),
        )

        db.add(snapshot)
        db.commit()

        logger.info(
            "Automated workforce snapshot saved: id=%s",
            snapshot.id,
        )

    except Exception:
        db.rollback()
        logger.exception("Automated workforce snapshot failed")

    finally:
        db.close()


def _scheduler_loop() -> None:
    """Run snapshots repeatedly until shutdown."""
    while not _stop_event.wait(INTERVAL_SECONDS):
        save_monitoring_snapshot()
        evaluate_kpi_breaches_automatically()
        evaluate_employee_risk_alerts_automatically()


def start_monitoring_scheduler() -> None:
    """Start one background scheduler thread."""
    global _scheduler_thread

    if _scheduler_thread and _scheduler_thread.is_alive():
        logger.info("Workforce monitoring scheduler is already running")
        return

    _stop_event.clear()

    # Save an initial snapshot when the scheduler starts.
    save_monitoring_snapshot()

    _scheduler_thread = threading.Thread(
        target=_scheduler_loop,
        name="workforce-monitoring-scheduler",
        daemon=True,
    )
    _scheduler_thread.start()

    logger.info("Workforce monitoring scheduler started")


def stop_monitoring_scheduler() -> None:
    """Stop the scheduler gracefully."""
    _stop_event.set()

    if _scheduler_thread and _scheduler_thread.is_alive():
        _scheduler_thread.join(timeout=5)

    logger.info("Workforce monitoring scheduler stopped")

def evaluate_kpi_breaches_automatically() -> None:
    """Evaluate KPI targets during each scheduler cycle."""
    db = SessionLocal()

    lower_is_better = {
        "high_risk_employees",
        "high_risk_percentage",
        "open_alerts",
    }

    try:
        # The dashboard function calculates KPIs from the database.
        # Its current_user parameter is not used in the calculation.
        kpis = get_workforce_kpis(db, None)
        targets = db.query(WorkforceKPITarget).all()

        for target in targets:
            current_value = float(kpis[target.metric_key])
            target_value = float(target.target_value)

            if target.metric_key in lower_is_better:
                breached = current_value > target_value
                deviation = current_value - target_value
            else:
                breached = current_value < target_value
                deviation = target_value - current_value

            existing = (
                db.query(WorkforceKPIBreach)
                .filter(
                    WorkforceKPIBreach.metric_key == target.metric_key,
                    WorkforceKPIBreach.status == "OPEN",
                )
                .order_by(WorkforceKPIBreach.detected_at.desc())
                .first()
            )

            if breached:
                severity = "HIGH" if deviation >= 20 else "MEDIUM"
                message = (
                    f"{target.metric_key}: current value "
                    f"{current_value:g} misses target {target_value:g}."
                )

                if existing:
                    # Update an existing alert instead of duplicating it.
                    existing.current_value = current_value
                    existing.target_value = target_value
                    existing.severity = severity
                    existing.message = message
                else:
                    db.add(
                        WorkforceKPIBreach(
                            metric_key=target.metric_key,
                            current_value=current_value,
                            target_value=target_value,
                            severity=severity,
                            status="OPEN",
                            message=message,
                        )
                    )

            elif existing:
                # Resolve the alert when the target is met again.
                existing.status = "RESOLVED"
                existing.resolved_at = datetime.now()

        db.commit()
        logger.info(
            "Automated KPI breach evaluation completed; targets checked=%s",
            len(targets),
        )

    except Exception:
        db.rollback()
        logger.exception("Automated KPI breach evaluation failed")

    finally:
        db.close()



def evaluate_employee_risk_alerts_automatically() -> None:
    """Automatically evaluate employee risk changes."""
    db = SessionLocal()

    try:
        result = evaluate_employee_risk_changes(
            db=db,
            current_user=None,
        )

        logger.info(
            "Automated employee risk evaluation completed: "
            "checked=%s, created=%s, updated=%s, resolved=%s",
            result["employees_checked"],
            result["alerts_created"],
            result["alerts_updated"],
            result["alerts_resolved"],
        )

    except Exception:
        db.rollback()
        logger.exception(
            "Automated employee risk evaluation failed"
        )

    finally:
        db.close()
