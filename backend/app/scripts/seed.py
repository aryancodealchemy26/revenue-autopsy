"""CLI command to seed development and demo data into local database."""

import asyncio
import sys

from app.infrastructure.database.seed import seed_development_data
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


async def run_seed() -> None:
    """Execute the development database seed script."""
    print("==================================================")
    print(" Revenue Autopsy - Development Database Seeder")
    print("==================================================")

    async with AsyncSessionLocal() as session:
        uow = SQLAlchemyUnitOfWork(session)
        async with uow:
            result = await seed_development_data(uow)

    merchant = result["merchant"]
    incidents = result["incidents"]
    evidences = result["evidences"]

    print(f"\n[+] Seeded Merchant:")
    print(f"    - ID:       {merchant.merchant_id}")
    print(f"    - Name:     {merchant.name}")
    print(f"    - Currency: {merchant.currency}")
    print(f"    - Status:   {merchant.status.value}")

    print(f"\n[+] Seeded {len(incidents)} Incidents:")
    for inc in incidents:
        print(f"    - [{inc.severity.value.upper()}] {inc.incident_id} | {inc.incident_type.value} | {inc.currency} {inc.revenue_at_risk} | Status: {inc.status.value}")

    print(f"\n[+] Seeded {len(evidences)} Diagnostic Evidence Records.")
    print("\n[SUCCESS] Development database seeded successfully and ready for Incident Cockpit E2E.")
    print("==================================================")


def main() -> None:
    try:
        asyncio.run(run_seed())
    except Exception as e:
        print(f"\n[ERROR] Seeding failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
