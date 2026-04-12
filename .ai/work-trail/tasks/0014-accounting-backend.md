# Task 0014: Accounting Backend

## Branch: task/0014-accounting-backend

## Context Bundle

### Relevant Schema

```prisma
model Account {
  id        String    @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  code      String    @unique @db.VarChar(20)
  name      String    @db.VarChar(255)
  type      String    @db.VarChar(20)   -- asset / liability / equity / revenue / expense
  parentId  String?   @map("parent_id") @db.Uuid
  isActive  Boolean   @default(true) @map("is_active")
  createdAt DateTime  @default(now()) @map("created_at") @db.Timestamptz()
  updatedAt DateTime  @updatedAt @map("updated_at") @db.Timestamptz()
  parent            Account?           @relation("AccountParent", ...)
  children          Account[]          @relation("AccountParent")
  journalEntryLines JournalEntryLine[]
  @@map("accounts")
}

model JournalEntry {
  id            String   @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  entryNumber   String   @unique @map("entry_number") @db.VarChar(50)
  date          DateTime @default(now()) @db.Date
  description   String   @db.Text
  referenceType String?  @map("reference_type") @db.VarChar(50)
  referenceId   String?  @map("reference_id") @db.Uuid
  createdBy     String?  @map("created_by") @db.Uuid
  createdAt     DateTime @default(now()) @map("created_at") @db.Timestamptz()
  journalEntryLines JournalEntryLine[]
  @@map("journal_entries")
}

model JournalEntryLine {
  id             String  @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  journalEntryId String  @map("journal_entry_id") @db.Uuid
  accountId      String  @map("account_id") @db.Uuid
  debitAmount    Int     @default(0) @map("debit_amount")
  creditAmount   Int     @default(0) @map("credit_amount")
  description    String? @db.Text
  journalEntry JournalEntry @relation(...)
  account      Account      @relation(...)
  @@map("journal_entry_lines")
}

model Expense {
  id            String    @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  date          DateTime  @default(now()) @db.Date
  category      String    @db.VarChar(100)
  description   String    @db.Text
  amount        Int                          -- paisa
  paymentMethod String    @default("cash") @map("payment_method") @db.VarChar(20)
  receiptUrl    String?   @map("receipt_url") @db.VarChar(500)
  notes         String?   @db.Text
  recordedBy    String?   @map("recorded_by") @db.Uuid
  createdAt     DateTime  @default(now()) @map("created_at") @db.Timestamptz()
  updatedAt     DateTime  @updatedAt @map("updated_at") @db.Timestamptz()
  deletedAt     DateTime? @map("deleted_at") @db.Timestamptz()
  @@map("expenses")
}
```

**Prisma client model names (lowercase, no underscores):**
- `prisma.account`, `prisma.journalentry`, `prisma.journalentryline`, `prisma.expense`

**Prisma attribute mapping (Python = camelCase):**
- `account.code`, `account.name`, `account.type`, `account.parentId`, `account.isActive`
- `journalEntry.entryNumber`, `journalEntry.referenceType`, `journalEntry.referenceId`, `journalEntry.createdBy`
- `journalEntry.journalEntryLines` — relation, loaded via include
- `journalEntryLine.journalEntryId`, `journalEntryLine.accountId`, `journalEntryLine.debitAmount`, `journalEntryLine.creditAmount`
- `expense.date`, `expense.category`, `expense.description`, `expense.amount`, `expense.paymentMethod`, `expense.receiptUrl`, `expense.recordedBy`, `expense.deletedAt`

**Seeded account codes (key ones for journal entries):**
- `"1000"` → Cash (asset) — used as credit for expense entries
- `"4000"` → Sales Revenue (revenue)
- `"6500"` → Miscellaneous Expense (expense) — used as debit for ALL expense entries

### Relevant API Endpoints

**Prefix: `/api/accounting`**

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | `/api/accounting/accounts` | Yes | admin, manager | Return all active accounts |
| GET | `/api/accounting/journal-entries` | Yes | admin, manager | Paginated entries. Params: `page`, `limit`, `start_date` (YYYY-MM-DD), `end_date`, `reference_type` |
| POST | `/api/accounting/journal-entries` | Yes | admin | Create manual balanced entry |

**Prefix: `/api/expenses`**

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | `/api/expenses` | Yes | admin, manager | Paginated. Params: `page`, `limit`, `start_date`, `end_date`, `category` |
| POST | `/api/expenses` | Yes | admin, manager | Create expense + auto journal entry |
| PUT | `/api/expenses/:id` | Yes | admin, manager | Update expense (not the journal entry) |
| DELETE | `/api/expenses/:id` | Yes | admin | Soft delete |

**GET /api/accounting/accounts response:**
```json
{"success": true, "data": [{"id": "...", "code": "1000", "name": "Cash", "type": "asset", "parent_id": null, "is_active": true, "created_at": "..."}]}
```

**GET /api/accounting/journal-entries response:**
```json
{"success": true, "data": [...], "pagination": {...}}
```
Each entry includes its lines:
```json
{
  "id": "...", "entry_number": "JE-20260411-001", "date": "2026-04-11",
  "description": "Sale recorded", "reference_type": "sale", "reference_id": "uuid",
  "created_by": "uuid", "created_at": "...",
  "lines": [
    {"id": "...", "account_id": "...", "debit_amount": 85000, "credit_amount": 0, "description": "Cash received"},
    {"id": "...", "account_id": "...", "debit_amount": 0, "credit_amount": 85000, "description": "Sales revenue"}
  ]
}
```

**POST /api/accounting/journal-entries request:**
```json
{
  "description": "Manual adjustment",
  "date": "2026-04-11",        // optional, defaults to today
  "lines": [
    {"account_id": "uuid", "debit_amount": 5000, "credit_amount": 0, "description": "optional"},
    {"account_id": "uuid", "debit_amount": 0, "credit_amount": 5000}
  ]
}
```
Validation: `sum(debit_amount) must equal sum(credit_amount)`, minimum 2 lines.

**POST /api/expenses request:**
```json
{
  "category": "Rent",
  "description": "Monthly office rent",
  "amount": 500000,          // paisa
  "payment_method": "cash",  // optional, default "cash"
  "date": "2026-04-01",      // optional, defaults to today
  "receipt_url": null,       // optional
  "notes": null              // optional
}
```

**POST/PUT /api/expenses response (201/200):**
```json
{
  "success": true,
  "data": {
    "id": "...", "date": "2026-04-01", "category": "Rent",
    "description": "Monthly office rent", "amount": 500000,
    "payment_method": "cash", "receipt_url": null, "notes": null,
    "recorded_by": "uuid", "created_at": "..."
  }
}
```

### Relevant Patterns

**Standard patterns (identical to existing modules):**
```python
from src.core.responses import success_response, paginated_response
from src.core.auth import get_current_user, require_roles
from src.core.exceptions import NotFoundError, ValidationError
from src import database
```

**Journal entry number generation (already established in sales module):**
```python
async def _generate_entry_number(self) -> str:
    from datetime import date
    today_str = date.today().strftime("%Y%m%d")
    count = await self.repo.count_today_journal_entries(today_str)
    return f"JE-{today_str}-{count + 1:03d}"
```
Repository: `await self.prisma.journalentry.count(where={"entryNumber": {"startswith": f"JE-{today_str}"}})`

**Transaction pattern for expense + journal entry:**
```python
async with self.prisma.tx() as tx:
    expense = await tx.expense.create(data=expense_data)
    entry = await tx.journalentry.create(data={...})
    await tx.journalentryline.create(data={"journalEntryId": entry.id, "accountId": debit_account_id, "debitAmount": amount, "creditAmount": 0})
    await tx.journalentryline.create(data={"journalEntryId": entry.id, "accountId": credit_account_id, "debitAmount": 0, "creditAmount": amount})
# After tx: fresh find_first
return await self.prisma.expense.find_first(where={"id": expense.id})
```

**Date parsing:**
- `expense.date` is a `datetime` object in Prisma (from `@db.Date` type). Access as `expense.date.date().isoformat()` OR `expense.date.strftime("%Y-%m-%d")`.
- Journal entry `date` similarly: `entry.date.isoformat()` (but it's already a date object).
- When storing from ISO string: `datetime.fromisoformat(date_str)` (for Date columns, use `date.fromisoformat(date_str)`).

**Router registration — accounting uses sub-paths under `/accounting` prefix:**
```python
# accounting/router.py
router = APIRouter(prefix="/accounting", tags=["accounting"])
router.add_api_route("/accounts", controller.list_accounts, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/journal-entries", controller.list_journal_entries, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/journal-entries", controller.create_journal_entry, methods=["POST"],
                     dependencies=[Depends(require_roles("admin"))])
```

```python
# expenses/router.py
router = APIRouter(prefix="/expenses", tags=["expenses"])
router.add_api_route("", controller.list_expenses, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("", controller.create_expense, methods=["POST"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/{expense_id}", controller.update_expense, methods=["PUT"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/{expense_id}", controller.delete_expense, methods=["DELETE"],
                     dependencies=[Depends(require_roles("admin"))])
```

**main.py registration:**
```python
from src.modules.accounting.router import router as accounting_router
from src.modules.expenses.router import router as expenses_router
# ...
app.include_router(accounting_router, prefix="/api")
app.include_router(expenses_router, prefix="/api")
```

### Architecture Rules That Apply

- Rule #8: `ExpenseService.create()` uses `async with self.prisma.tx() as tx:` to atomically write expense + journal entry + 2 journal entry lines.
- Rule #11: Repositories contain only DB queries. Balance check (`sum(debit) == sum(credit)`) goes in `AccountingService`, not the repo. Date computation goes in service.
- Rule #13: `NotFoundError`, `ValidationError` for typed errors.
- Rule #21: Every journal entry must balance — `sum(debit_amount) == sum(credit_amount)`. Enforced in `AccountingService.create_journal_entry()`. The automatic expense JE is always balanced by construction (both debit and credit = `expense.amount`).
- Rule #25: `ExpenseService` does NOT import `AccountingRepository` directly. It has its own `ExpenseRepository` which handles the journal entry DB writes for the expense's auto-created entry. The accounting module's service is for reading/creating manual entries only.

## What to Build

### Module 1: `backend/src/modules/accounting/`

#### `schemas.py`

```python
class AccountResponse(BaseModel):
    id: str
    code: str
    name: str
    type: str
    parent_id: Optional[str]
    is_active: bool
    created_at: str

    @classmethod
    def model_validate(cls, obj):
        return cls(
            id=obj.id, code=obj.code, name=obj.name, type=obj.type,
            parent_id=obj.parentId, is_active=obj.isActive,
            created_at=obj.createdAt.isoformat(),
        )

class JournalEntryLineCreate(BaseModel):
    account_id: str
    debit_amount: int = 0
    credit_amount: int = 0
    description: Optional[str] = None

class JournalEntryCreate(BaseModel):
    description: str
    date: Optional[str] = None   # YYYY-MM-DD, defaults to today if None
    lines: list[JournalEntryLineCreate] = Field(min_length=2)

class JournalEntryLineResponse(BaseModel):
    id: str
    account_id: str
    debit_amount: int
    credit_amount: int
    description: Optional[str]

    @classmethod
    def model_validate(cls, obj):
        return cls(
            id=obj.id, account_id=obj.accountId,
            debit_amount=obj.debitAmount, credit_amount=obj.creditAmount,
            description=obj.description,
        )

class JournalEntryResponse(BaseModel):
    id: str
    entry_number: str
    date: str
    description: str
    reference_type: Optional[str]
    reference_id: Optional[str]
    created_by: Optional[str]
    lines: list[JournalEntryLineResponse]
    created_at: str

    @classmethod
    def model_validate(cls, obj):
        return cls(
            id=obj.id, entry_number=obj.entryNumber,
            date=obj.date.strftime("%Y-%m-%d"),
            description=obj.description,
            reference_type=obj.referenceType,
            reference_id=obj.referenceId,
            created_by=obj.createdBy,
            lines=[JournalEntryLineResponse.model_validate(l) for l in (obj.journalEntryLines or [])],
            created_at=obj.createdAt.isoformat(),
        )
```

Note: `obj.date` from Prisma `@db.Date` is a `datetime` object — use `.strftime("%Y-%m-%d")` to format it.

```python
@dataclass
class PaginatedJournalEntries:
    items: list[JournalEntryResponse]
    total: int
```

#### `repository.py`

Methods:
- `find_all_accounts()` → list of Account objects (`isActive=True`, ordered by code)
- `find_journal_entries_paginated(skip, take, where)` → `(list[JournalEntry], int)` — include `journalEntryLines`
- `count_today_journal_entries(today_str: str)` → int
- `find_account_by_id(account_id: str)` → Account | None
- `create_journal_entry_with_lines(entry_data: dict, lines_data: list[dict])` → JournalEntry with lines

`create_journal_entry_with_lines` uses a transaction:
```python
async with self.prisma.tx() as tx:
    entry = await tx.journalentry.create(data=entry_data)
    for line in lines_data:
        await tx.journalentryline.create(data={"journalEntryId": entry.id, **line})
return await self.prisma.journalentry.find_first(
    where={"id": entry.id},
    include={"journalEntryLines": True},
)
```

#### `service.py`

```python
class AccountingService:
    def __init__(self, repo: AccountingRepository) -> None:
        self.repo = repo

    async def list_accounts(self) -> list[AccountResponse]:
        accounts = await self.repo.find_all_accounts()
        return [AccountResponse.model_validate(a) for a in accounts]

    async def list_journal_entries(
        self, page, limit, start_date, end_date, reference_type
    ) -> PaginatedJournalEntries:
        where: dict = {}
        if reference_type:
            where["referenceType"] = reference_type
        date_filter: dict = {}
        if start_date:
            date_filter["gte"] = date.fromisoformat(start_date)
        if end_date:
            date_filter["lte"] = date.fromisoformat(end_date)
        if date_filter:
            where["date"] = date_filter
        skip = (page - 1) * limit
        items, total = await self.repo.find_journal_entries_paginated(skip, limit, where)
        return PaginatedJournalEntries(
            items=[JournalEntryResponse.model_validate(e) for e in items],
            total=total,
        )

    async def create_journal_entry(
        self, input: JournalEntryCreate, created_by: str
    ) -> JournalEntryResponse:
        # Rule #21: validate balance
        total_debit = sum(l.debit_amount for l in input.lines)
        total_credit = sum(l.credit_amount for l in input.lines)
        if total_debit != total_credit:
            raise ValidationError(
                f"Journal entry does not balance: debits={total_debit}, credits={total_credit}"
            )
        if total_debit == 0:
            raise ValidationError("Journal entry must have non-zero amounts")

        # Validate each account exists
        for line in input.lines:
            account = await self.repo.find_account_by_id(line.account_id)
            if account is None:
                raise NotFoundError("Account", line.account_id)

        today = date.today()
        entry_date = date.fromisoformat(input.date) if input.date else today
        entry_number = await self._generate_entry_number()

        entry_data = {
            "entryNumber": entry_number,
            "date": datetime(entry_date.year, entry_date.month, entry_date.day, tzinfo=timezone.utc),
            "description": input.description,
            "referenceType": "manual",
            "createdBy": created_by,
        }
        lines_data = [
            {
                "accountId": l.account_id,
                "debitAmount": l.debit_amount,
                "creditAmount": l.credit_amount,
                "description": l.description,
            }
            for l in input.lines
        ]
        entry = await self.repo.create_journal_entry_with_lines(entry_data, lines_data)
        return JournalEntryResponse.model_validate(entry)

    async def _generate_entry_number(self) -> str:
        today_str = date.today().strftime("%Y%m%d")
        count = await self.repo.count_today_journal_entries(today_str)
        return f"JE-{today_str}-{count + 1:03d}"
```

#### `controller.py`

Three functions: `list_accounts`, `list_journal_entries`, `create_journal_entry`.

`list_accounts` → `success_response(data_list, "Accounts retrieved")`
`list_journal_entries` → `paginated_response(items, page, limit, total)`
`create_journal_entry` → `success_response(result, "Journal entry created", status_code=201)`

#### `router.py`

```python
router = APIRouter(prefix="/accounting", tags=["accounting"])
router.add_api_route("/accounts", controller.list_accounts, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/journal-entries", controller.list_journal_entries, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/journal-entries", controller.create_journal_entry, methods=["POST"],
                     dependencies=[Depends(require_roles("admin"))])
```

---

### Module 2: `backend/src/modules/expenses/`

#### `schemas.py`

```python
PaymentMethod = Literal["cash", "card", "mobile", "credit"]

class ExpenseCreate(BaseModel):
    category: str
    description: str
    amount: int = Field(gt=0)    # paisa
    payment_method: PaymentMethod = "cash"
    date: Optional[str] = None   # YYYY-MM-DD, defaults to today
    receipt_url: Optional[str] = None
    notes: Optional[str] = None

class ExpenseUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[int] = None
    payment_method: Optional[str] = None
    date: Optional[str] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None

class ExpenseResponse(BaseModel):
    id: str
    date: str
    category: str
    description: str
    amount: int
    payment_method: str
    receipt_url: Optional[str]
    notes: Optional[str]
    recorded_by: Optional[str]
    created_at: str

    @classmethod
    def model_validate(cls, obj):
        return cls(
            id=obj.id,
            date=obj.date.strftime("%Y-%m-%d"),
            category=obj.category,
            description=obj.description,
            amount=obj.amount,
            payment_method=obj.paymentMethod,
            receipt_url=obj.receiptUrl,
            notes=obj.notes,
            recorded_by=obj.recordedBy,
            created_at=obj.createdAt.isoformat(),
        )

@dataclass
class PaginatedExpenses:
    items: list[ExpenseResponse]
    total: int
```

#### `repository.py`

Methods:
- `find_by_id(expense_id: str)` → Expense | None (where deletedAt is None)
- `find_paginated(skip, take, where)` → `(list[Expense], int)`
- `update(expense_id: str, data: dict)` → Expense
- `soft_delete(expense_id: str)` → None
- `count_today_journal_entries(today_str: str)` → int — `await self.prisma.journalentry.count(where={"entryNumber": {"startswith": f"JE-{today_str}"}})`
- `find_account_by_code(code: str)` → Account | None
- `create_expense_atomic(expense_data: dict, entry_number: str, debit_account_id: str, credit_account_id: str)` → Expense

`create_expense_atomic`:
```python
async with self.prisma.tx() as tx:
    expense = await tx.expense.create(data=expense_data)
    entry = await tx.journalentry.create(data={
        "entryNumber": entry_number,
        "description": f"Expense: {expense_data.get('category', 'General')} — {expense_data.get('description', '')}",
        "referenceType": "expense",
        "referenceId": expense.id,
        "createdBy": expense_data.get("recordedBy"),
    })
    await tx.journalentryline.create(data={
        "journalEntryId": entry.id,
        "accountId": debit_account_id,
        "debitAmount": expense_data["amount"],
        "creditAmount": 0,
        "description": "Expense recorded",
    })
    await tx.journalentryline.create(data={
        "journalEntryId": entry.id,
        "accountId": credit_account_id,
        "debitAmount": 0,
        "creditAmount": expense_data["amount"],
        "description": "Cash paid",
    })
return await self.prisma.expense.find_first(where={"id": expense.id})
```

Note: `entry_number` is generated in the service and passed in (same pattern as sale_number in SalesRepository).

#### `service.py`

```python
class ExpenseService:
    def __init__(self, repo: ExpenseRepository) -> None:
        self.repo = repo

    async def list(self, page, limit, start_date, end_date, category) -> PaginatedExpenses:
        where: dict = {"deletedAt": None}
        if category:
            where["category"] = {"contains": category, "mode": "insensitive"}
        date_filter: dict = {}
        if start_date:
            date_filter["gte"] = date.fromisoformat(start_date)
        if end_date:
            date_filter["lte"] = date.fromisoformat(end_date)
        if date_filter:
            where["date"] = date_filter
        skip = (page - 1) * limit
        items, total = await self.repo.find_paginated(skip, limit, where)
        return PaginatedExpenses(
            items=[ExpenseResponse.model_validate(e) for e in items],
            total=total,
        )

    async def create(self, input: ExpenseCreate, recorded_by: str) -> ExpenseResponse:
        # Look up accounts
        expense_account = await self.repo.find_account_by_code("6500")  # Miscellaneous Expense
        cash_account = await self.repo.find_account_by_code("1000")     # Cash
        if expense_account is None or cash_account is None:
            raise ValidationError("Chart of accounts not seeded. Run prisma/seed.py first.")

        today = date.today()
        expense_date = date.fromisoformat(input.date) if input.date else today
        entry_number = await self._generate_entry_number()

        expense_data: dict = {
            "date": datetime(expense_date.year, expense_date.month, expense_date.day, tzinfo=timezone.utc),
            "category": input.category,
            "description": input.description,
            "amount": input.amount,
            "paymentMethod": input.payment_method,
            "recordedBy": recorded_by,
        }
        if input.receipt_url:
            expense_data["receiptUrl"] = input.receipt_url
        if input.notes:
            expense_data["notes"] = input.notes

        expense = await self.repo.create_expense_atomic(
            expense_data, entry_number, expense_account.id, cash_account.id
        )
        return ExpenseResponse.model_validate(expense)

    async def update(self, expense_id: str, input: ExpenseUpdate) -> ExpenseResponse:
        existing = await self.repo.find_by_id(expense_id)
        if existing is None:
            raise NotFoundError("Expense", expense_id)

        data: dict = {}
        if input.category is not None:
            data["category"] = input.category
        if input.description is not None:
            data["description"] = input.description
        if input.amount is not None:
            data["amount"] = input.amount
        if input.payment_method is not None:
            data["paymentMethod"] = input.payment_method
        if input.date is not None:
            d = date.fromisoformat(input.date)
            data["date"] = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        if input.receipt_url is not None:
            data["receiptUrl"] = input.receipt_url
        if input.notes is not None:
            data["notes"] = input.notes

        expense = await self.repo.update(expense_id, data)
        return ExpenseResponse.model_validate(expense)

    async def delete(self, expense_id: str) -> None:
        existing = await self.repo.find_by_id(expense_id)
        if existing is None:
            raise NotFoundError("Expense", expense_id)
        await self.repo.soft_delete(expense_id)

    async def _generate_entry_number(self) -> str:
        today_str = date.today().strftime("%Y%m%d")
        count = await self.repo.count_today_journal_entries(today_str)
        return f"JE-{today_str}-{count + 1:03d}"
```

**Important:** The journal entry created by expense is NOT updated when the expense is updated. It is immutable once created (like stock movements).

#### `controller.py`

- `list_expenses(page, limit, start_date, end_date, category, current_user)` → `paginated_response`
- `create_expense(input: ExpenseCreate, current_user)` → `success_response(..., status_code=201)`
- `update_expense(expense_id, input: ExpenseUpdate, current_user)` → `success_response`
- `delete_expense(expense_id, current_user)` → `success_response(None, "Expense deleted", status_code=200)` or 204

Use `success_response(None, "Expense deleted")` with status_code=200 for delete (consistent with other modules that don't use 204).

#### `router.py`

```python
router = APIRouter(prefix="/expenses", tags=["expenses"])
router.add_api_route("", controller.list_expenses, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("", controller.create_expense, methods=["POST"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/{expense_id}", controller.update_expense, methods=["PUT"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/{expense_id}", controller.delete_expense, methods=["DELETE"],
                     dependencies=[Depends(require_roles("admin"))])
```

---

### Register in `backend/src/main.py`

```python
from src.modules.accounting.router import router as accounting_router
from src.modules.expenses.router import router as expenses_router
# ...
app.include_router(accounting_router, prefix="/api")
app.include_router(expenses_router, prefix="/api")
```

---

### Tests

**`backend/tests/unit/modules/accounting/test_service.py`**

```
TestListAccounts:
  test_returns_list_of_account_responses

TestListJournalEntries:
  test_returns_paginated_entries
  test_applies_start_date_filter
  test_applies_end_date_filter
  test_applies_reference_type_filter

TestCreateJournalEntry:
  test_raises_validation_error_if_debits_not_equal_credits
  test_raises_validation_error_if_amounts_are_zero
  test_raises_not_found_if_account_missing
  test_creates_balanced_entry_with_correct_data
```

**`backend/tests/unit/modules/expenses/test_service.py`**

```
TestCreate:
  test_raises_if_accounts_not_seeded
  test_creates_expense_and_calls_repo_atomic
  test_uses_today_if_date_not_provided

TestUpdate:
  test_raises_not_found_if_missing
  test_updates_only_provided_fields
  test_does_not_update_journal_entry

TestDelete:
  test_raises_not_found_if_missing
  test_soft_deletes_expense

TestList:
  test_returns_paginated_expenses
  test_applies_category_filter
  test_applies_date_range_filter
```

**`backend/tests/integration/test_accounting_api.py`**

```
TestListAccounts:
  test_admin_gets_200_with_account_list
  test_manager_gets_200
  test_staff_gets_403
  test_unauthenticated_gets_401

TestListJournalEntries:
  test_admin_gets_200_paginated
  test_staff_gets_403

TestCreateJournalEntry:
  test_admin_creates_balanced_entry_returns_201
  test_unbalanced_entry_returns_422
  test_manager_gets_403_on_create
  test_staff_gets_403_on_create
```

**`backend/tests/integration/test_expenses_api.py`**

```
TestListExpenses:
  test_admin_gets_200_paginated
  test_staff_gets_403

TestCreateExpense:
  test_admin_creates_expense_returns_201
  test_manager_creates_expense_returns_201
  test_staff_gets_403

TestUpdateExpense:
  test_admin_updates_expense_returns_200
  test_staff_gets_403

TestDeleteExpense:
  test_admin_deletes_expense_returns_200
  test_manager_gets_403_on_delete
```

**Test file locations:**
- `backend/tests/unit/modules/accounting/__init__.py`
- `backend/tests/unit/modules/accounting/test_service.py`
- `backend/tests/unit/modules/expenses/__init__.py`
- `backend/tests/unit/modules/expenses/test_service.py`
- `backend/tests/integration/test_accounting_api.py`
- `backend/tests/integration/test_expenses_api.py`

## Acceptance Criteria

- [ ] `ruff check backend/` exits 0
- [ ] `pytest backend/` exits 0 — full suite passes
- [ ] `GET /api/accounting/accounts` returns all active accounts (admin/manager), 403 for staff
- [ ] `GET /api/accounting/journal-entries` paginated with date/reference_type filters
- [ ] `POST /api/accounting/journal-entries` validates balance (sum debits == sum credits), 422 if unbalanced
- [ ] `POST /api/accounting/journal-entries` is admin-only (403 for manager/staff)
- [ ] `GET /api/expenses` paginated with date/category filters (admin/manager), 403 staff
- [ ] `POST /api/expenses` creates expense + balanced journal entry atomically (debit 6500, credit 1000)
- [ ] `PUT /api/expenses/:id` updates expense fields only (journal entry unchanged)
- [ ] `DELETE /api/expenses/:id` soft deletes (admin only)
- [ ] All `from __future__ import annotations` present
- [ ] CONTEXT.md updated in all touched directories

## Files to Create

**Accounting module (new):**
- `backend/src/modules/accounting/__init__.py`
- `backend/src/modules/accounting/schemas.py`
- `backend/src/modules/accounting/repository.py`
- `backend/src/modules/accounting/service.py`
- `backend/src/modules/accounting/controller.py`
- `backend/src/modules/accounting/router.py`
- `backend/src/modules/accounting/CONTEXT.md`

**Expenses module (new):**
- `backend/src/modules/expenses/__init__.py`
- `backend/src/modules/expenses/schemas.py`
- `backend/src/modules/expenses/repository.py`
- `backend/src/modules/expenses/service.py`
- `backend/src/modules/expenses/controller.py`
- `backend/src/modules/expenses/router.py`
- `backend/src/modules/expenses/CONTEXT.md`

**Tests (new):**
- `backend/tests/unit/modules/accounting/__init__.py`
- `backend/tests/unit/modules/accounting/test_service.py`
- `backend/tests/unit/modules/expenses/__init__.py`
- `backend/tests/unit/modules/expenses/test_service.py`
- `backend/tests/integration/test_accounting_api.py`
- `backend/tests/integration/test_expenses_api.py`

**Modified:**
- `backend/src/main.py` — add accounting and expenses router imports/registration
- `backend/src/modules/CONTEXT.md`

## Known Pitfalls

1. **`obj.date` from Prisma `@db.Date`** — Prisma returns this as a Python `datetime` object, not a `date`. Use `.strftime("%Y-%m-%d")` in model_validate. When storing a date from a string: pass `datetime(year, month, day, tzinfo=timezone.utc)` (not just `date`).

2. **Journal entry `referenceType="manual"`** for manually created entries. Expense journal entries use `referenceType="expense"`. Don't mix these up.

3. **`create_expense_atomic` in ExpenseRepository** uses `expense_data.get("category")` and `expense_data.get("description")` for the journal entry description. Make sure these keys exist in `expense_data` (they always will since they're required fields).

4. **`find_paginated` for journal entries must include lines** — `include={"journalEntryLines": True}` otherwise `JournalEntryResponse.model_validate()` will have `obj.journalEntryLines = None`.

5. **Account validation in create_journal_entry** — validate each `line.account_id` exists before calling the repo's create method. If any account is missing, raise `NotFoundError` before starting the transaction.

6. **Integration test mock DB** — accounting tests mock: `db.account`, `db.journalentry`, `db.journalentryline`. Expenses tests mock: `db.expense`, `db.account`, `db.journalentry`, `db.journalentryline`. Also mock `db.tx()` as async context manager (see test_promotions_api.py for the pattern).

7. **`category` filter uses Prisma `contains` with `mode: insensitive`** for case-insensitive partial match. Prisma-client-py syntax: `where={"category": {"contains": category, "mode": "insensitive"}}`.

8. **Delete endpoint returns 200** (not 204) — match existing pattern: `success_response(None, "Expense deleted")` where `success_response` sets status_code=200 by default.

9. **Accounting service `list_journal_entries` date filter** — the `date` column is `@db.Date` (not timestamptz). Prisma filter uses `date.fromisoformat()` objects (Python `date` type), NOT `datetime`.

## Exit Signal

```bash
ruff check backend/
pytest backend/ -q
# Must exit 0. Report total passing test count.
```
