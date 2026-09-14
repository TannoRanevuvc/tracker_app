# Спека модуля: finance

## 1. Назначение

Финансовый трекер: счета, транзакции, категории, регулярные операции и бюджеты по
категориям. Деньги — всегда integer в копейках (см. CLAUDE.md §10).

## 2. Границы (Scope)

**Входит в модуль:**
- CRUD счетов, категорий, транзакций
- Регулярные операции (recurring), материализующиеся в обычные транзакции
- Бюджеты по категориям на период (месяц) с уведомлением о превышении
- Опциональная подписка на `food.meal_logged` для авто-учёта трат на еду

**Явно НЕ входит (Out of scope):**
- Интеграция с банками/автоматическая выгрузка выписок
- Мультивалютность (одна валюта — рубль, копейки — в MVP)
- Разделение счетов между несколькими пользователями (совместный бюджет)

## 3. Модель данных

Схема Postgres: `finance`

### `finance.account`

| Поле | Тип | Обязательное | Ограничения / примечания |
|---|---|---|---|
| id | UUID | да | PK |
| user_id | UUID | да | |
| name | text | да | |
| balance_kopecks | bigint | да | кэш, обновляется атомарно при каждой транзакции |
| created_at | timestamptz | да | |

### `finance.category`

| Поле | Тип | Обязательное | Ограничения / примечания |
|---|---|---|---|
| id | UUID | да | PK |
| user_id | UUID | да | |
| name | text | да | |
| type | enum: `income`, `expense` | да | |

### `finance.transaction`

| Поле | Тип | Обязательное | Ограничения / примечания |
|---|---|---|---|
| id | UUID | да | PK |
| user_id | UUID | да | |
| account_id | UUID | да | FK на `finance.account` |
| category_id | UUID | нет | FK на `finance.category` |
| amount_kopecks | bigint | да | знак: положительное = доход, отрицательное = расход |
| occurred_at | date | да | |
| description | text | нет | |
| recurring_rule_id | UUID | нет | заполнено, если транзакция материализована из правила |
| source | enum: `manual`, `recurring`, `food_module` | да | default `manual` — откуда пришла транзакция |
| created_at | timestamptz | да | |

### `finance.recurring_rule`

| Поле | Тип | Обязательное | Ограничения / примечания |
|---|---|---|---|
| id | UUID | да | PK |
| user_id | UUID | да | |
| account_id | UUID | да | |
| category_id | UUID | нет | |
| amount_kopecks | bigint | да | |
| description | text | нет | |
| frequency | enum: `monthly`, `weekly` | да | |
| day_of_month | int | нет | 1–28, обязателен при `monthly` |
| day_of_week | int | нет | 0–6, обязателен при `weekly` |
| next_due_date | date | да | обновляется после каждой материализации |
| active | boolean | да | default `true` |

### `finance.budget`

| Поле | Тип | Обязательное | Ограничения / примечания |
|---|---|---|---|
| id | UUID | да | PK |
| user_id | UUID | да | |
| category_id | UUID | да | |
| period | text | да | формат `YYYY-MM` |
| limit_kopecks | bigint | да | |

## 4. API-контракт

| Метод | Путь | Запрос | Ответ | Коды |
|---|---|---|---|---|
| POST | /api/finance/accounts | `{name}` | `Account` | 201 |
| GET | /api/finance/accounts | — | `Account[]` | 200 |
| POST | /api/finance/categories | `{name, type}` | `Category` | 201 |
| GET | /api/finance/categories | — | `Category[]` | 200 |
| POST | /api/finance/transactions | `{account_id, amount_kopecks, category_id?, occurred_at, description?}` | `Transaction` | 201, 404, 422 |
| GET | /api/finance/transactions | query: `account_id?, category_id?, from?, to?` | `Transaction[]` | 200 |
| DELETE | /api/finance/transactions/{id} | — | — | 204, 404 |
| POST | /api/finance/recurring-rules | `{account_id, amount_kopecks, category_id?, frequency, day_of_month?, day_of_week?}` | `RecurringRule` | 201, 422 |
| GET | /api/finance/recurring-rules | — | `RecurringRule[]` | 200 |
| PATCH | /api/finance/recurring-rules/{id} | `{active?, amount_kopecks?}` | `RecurringRule` | 200, 404 |
| POST | /api/finance/budgets | `{category_id, period, limit_kopecks}` | `Budget` | 201, 422 |
| GET | /api/finance/summary | query: `period` | `{by_category: [...], total_income, total_expense}` | 200 |

## 5. События

**PUBLISHES:**

| Событие | Когда | Payload |
|---|---|---|
| `finance.transaction_added` | после создания любой транзакции (ручной, рекуррентной, из food) | `{transaction_id, user_id, account_id, category_id, amount_kopecks, occurred_at}` |
| `finance.budget_exceeded` | если сумма расходов по категории за период превышает `limit_kopecks` после добавления транзакции | `{user_id, category_id, period, limit_kopecks, spent_kopecks}` |

**SUBSCRIBES_TO:**

| Событие | Источник | Обработчик делает |
|---|---|---|
| `food.meal_logged` | `food` | Если в payload есть `price_kopecks` (не `NULL`) — создать транзакцию с `amount_kopecks = -price_kopecks`, `source = food_module`, категория — фиксированная предустановленная категория "Еда" (создаётся автоматически при первом срабатывании, если у пользователя её ещё нет) |

## 6. Бизнес-правила и edge cases

- **Баланс счёта — кэш, не вычисляемое поле.** Обновляется атомарно в той же БД-транзакции,
  что и вставка/удаление финансовой транзакции (`UPDATE ... SET balance_kopecks = balance_kopecks + :delta`),
  чтобы избежать пересчёта суммы по всей истории при каждом запросе.
- **Материализация recurring — лениво**, как и просрочка в `tasks`: при каждом GET
  `/transactions` или `/summary` для пользователя проверяются его активные
  `recurring_rule` с `next_due_date <= сегодня`; для каждой создаётся транзакция с
  `source = recurring`, `next_due_date` сдвигается на следующий период. Если пропущено
  несколько периодов подряд (например, приложением не пользовались месяц) —
  материализуются все пропущенные периоды по очереди, а не только один.
- **Бюджет проверяется только по расходным категориям** (`type = expense`); превышение
  считается по модулю суммы всех транзакций категории за период `period`.
- **Удаление транзакции** — атомарно откатывает `balance_kopecks` счёта; повторная
  проверка бюджета после удаления не публикует "бюджет больше не превышен" — событие
  `budget_exceeded` не имеет обратного (публикуется только при превышении, не при
  возврате в норму).
- **Категория при удалении** — если у категории есть транзакции, удаление запрещено
  (409), сначала нужно переназначить транзакции.

## 7. Критерии приёмки

1. **Given** счёт с балансом 0, **When** POST транзакции `amount_kopecks: 500000` (5000₽),
   **Then** баланс счёта становится 500000, публикуется `finance.transaction_added`.
2. **Given** бюджет категории "Еда" на текущий месяц `limit_kopecks: 1000000`,
   **Then When** сумма расходных транзакций категории "Еда" за месяц превышает 1000000
   после очередной транзакции, **Then** публикуется `finance.budget_exceeded` с
   `spent_kopecks` больше `limit_kopecks`.
3. **Given** активное `recurring_rule` (monthly, `day_of_month: 1`) с `next_due_date`
   в прошлом, **When** GET `/api/finance/transactions`, **Then** создаётся новая
   транзакция с `source: recurring`, `next_due_date` правила сдвигается на следующий
   месяц.
4. **Given** `recurring_rule` не запускалось 3 месяца подряд, **When** GET списка
   транзакций, **Then** материализуются все 3 пропущенных периода отдельными
   транзакциями.
5. **Given** событие `food.meal_logged` с `price_kopecks: 35000`, **When** обработчик
   срабатывает, **Then** создаётся транзакция `amount_kopecks: -35000`,
   `source: food_module`, в категории "Еда".
6. **Given** событие `food.meal_logged` без `price_kopecks` (`NULL`), **When**
   обработчик срабатывает, **Then** транзакция не создаётся.
7. **Given** транзакция создана, **When** DELETE транзакции, **Then** баланс счёта
   возвращается к значению до её создания.
8. **Given** категория с существующими транзакциями, **When** попытка удалить
   категорию, **Then** 409.

## 8. Нефункциональные заметки

- Индексы: `(user_id, account_id, occurred_at)` на транзакциях, `(user_id, category_id, occurred_at)`
  для быстрого расчёта бюджета/summary.

## 9. Открытые вопросы

- Нужны ли переводы между своими счетами как отдельный тип операции (а не две
  раздельные транзакции) — отложено до появления второго счёта на практике.
- Нужна ли гибкая периодичность recurring (не только месяц/неделя, например
  "раз в квартал") — отложено.
