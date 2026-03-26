from app.database import Base, SessionLocal, engine
from app.models import TestCaseResult, TestRun


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(TestRun).count() > 0:
            print('Database already seeded')
            return

        runs = [
            TestRun(suite_name='Smoke Suite', environment='QA', build_version='v1.9.2', status='PASSED'),
            TestRun(suite_name='API Regression', environment='STAGING', build_version='v1.9.3', status='FAILED'),
            TestRun(suite_name='Payments E2E', environment='UAT', build_version='v2.0.0', status='RUNNING'),
        ]
        db.add_all(runs)
        db.flush()

        cases = [
            TestCaseResult(run_id=runs[0].id, name='Login', module='Auth', status='PASSED', duration_ms=1200),
            TestCaseResult(run_id=runs[0].id, name='Search product', module='Catalog', status='PASSED', duration_ms=1800),
            TestCaseResult(run_id=runs[0].id, name='Add to cart', module='Checkout', status='PASSED', duration_ms=1300),
            TestCaseResult(run_id=runs[1].id, name='Customer API contract', module='API', status='PASSED', duration_ms=900),
            TestCaseResult(run_id=runs[1].id, name='Inventory sync', module='Inventory', status='FAILED', duration_ms=3000, defect_id='DEF-118'),
            TestCaseResult(run_id=runs[1].id, name='Pricing rules', module='Pricing', status='PASSED', duration_ms=1700),
            TestCaseResult(run_id=runs[2].id, name='Authorize card', module='Payments', status='RUNNING', duration_ms=0),
            TestCaseResult(run_id=runs[2].id, name='Capture payment', module='Payments', status='RUNNING', duration_ms=0),
            TestCaseResult(run_id=runs[2].id, name='Email confirmation', module='Notifications', status='RUNNING', duration_ms=0),
        ]
        db.add_all(cases)
        db.commit()
        print('Demo data seeded')
    finally:
        db.close()


if __name__ == '__main__':
    seed()
