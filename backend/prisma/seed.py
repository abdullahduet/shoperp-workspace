"""
Seed script — inserts the default chart of accounts.

Safe to run multiple times: uses upsert on the unique `code` column so
existing rows are never duplicated or overwritten.

Usage:
    python prisma/seed.py
"""
import asyncio

from prisma import Prisma

ACCOUNTS = [
    {"code": "1000", "name": "Cash",                     "type": "asset"},
    {"code": "1100", "name": "Accounts Receivable",      "type": "asset"},
    {"code": "1200", "name": "Inventory",                "type": "asset"},
    {"code": "2000", "name": "Accounts Payable",         "type": "liability"},
    {"code": "3000", "name": "Owner's Equity",           "type": "equity"},
    {"code": "4000", "name": "Sales Revenue",            "type": "revenue"},
    {"code": "5000", "name": "Cost of Goods Sold",       "type": "expense"},
    {"code": "6000", "name": "Rent Expense",             "type": "expense"},
    {"code": "6100", "name": "Utilities Expense",        "type": "expense"},
    {"code": "6200", "name": "Salary Expense",           "type": "expense"},
    {"code": "6300", "name": "Marketing Expense",        "type": "expense"},
    {"code": "6400", "name": "Office Supplies Expense",  "type": "expense"},
    {"code": "6500", "name": "Miscellaneous Expense",    "type": "expense"},
]


async def main() -> None:
    db = Prisma()
    await db.connect()
    try:
        for account in ACCOUNTS:
            await db.account.upsert(
                where={"code": account["code"]},
                data={
                    "create": {
                        "code": account["code"],
                        "name": account["name"],
                        "type": account["type"],
                    },
                    "update": {},
                },
            )
        print(f"Seeded {len(ACCOUNTS)} accounts.")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
