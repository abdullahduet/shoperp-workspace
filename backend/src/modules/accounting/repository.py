"""Accounting repository — database queries only. No business logic."""
from __future__ import annotations


class AccountingRepository:
    def __init__(self, prisma) -> None:
        self.prisma = prisma

    async def find_all_accounts(self) -> list:
        """Return all active accounts ordered by code."""
        return await self.prisma.account.find_many(
            where={"isActive": True},
            order=[{"code": "asc"}],
        )

    async def find_journal_entries_paginated(
        self, skip: int, take: int, where: dict
    ) -> tuple:
        """Return (list[JournalEntry], total_count) with journalEntryLines included."""
        items = await self.prisma.journalentry.find_many(
            skip=skip,
            take=take,
            where=where,
            order=[{"createdAt": "desc"}],
            include={"journalEntryLines": True},
        )
        total = await self.prisma.journalentry.count(where=where)
        return items, total

    async def count_today_journal_entries(self, today_str: str) -> int:
        """Count journal entries whose entryNumber starts with JE-{today_str}."""
        return await self.prisma.journalentry.count(
            where={"entryNumber": {"startsWith": f"JE-{today_str}"}}
        )

    async def find_account_by_id(self, account_id: str):
        """Return an Account by its id, or None."""
        return await self.prisma.account.find_first(
            where={"id": account_id}
        )

    async def upsert_accounts(self, accounts: list[dict]) -> None:
        """Upsert accounts by code — safe to call multiple times."""
        for account in accounts:
            await self.prisma.account.upsert(
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

    async def create_journal_entry_with_lines(
        self, entry_data: dict, lines_data: list[dict]
    ):
        """Atomically create a journal entry and its lines."""
        async with self.prisma.tx() as tx:
            entry = await tx.journalentry.create(data=entry_data)
            for line in lines_data:
                await tx.journalentryline.create(
                    data={"journalEntryId": entry.id, **line}
                )
        return await self.prisma.journalentry.find_first(
            where={"id": entry.id},
            include={"journalEntryLines": True},
        )
