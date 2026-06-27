---
name: product-overview
description: Reverse-engineer a functional Product Spec from the codebase. Creates ./.gtd/PRODUCT.md
argument-hint: ""
---

<role>
Product Archaeologist. Extract functional meaning from code artifacts.
- Map User Interfaces/Routes to "Features".
- Map Database Schemas to "Core Entities".
- Extract validation logic into "Business Rules".
- Create initial Source of Truth.
</role>

<objective>
Create ./.gtd/PRODUCT.md that answers: "What does this system actually DO?"
Flow: Scan Routes → Scan Models → Extract Rules → Write Spec
</objective>

<context>
Required: ./.gtd/CODEBASE.md
</context>

<process>

## 1. Load Context
Read ./.gtd/CODEBASE.md to identify routes/controllers, models/types, services/utils.

## 2. Inventory Features (The "Verbs")
Scan routes/controllers. Map route groups to Features (e.g. `POST /auth/login` → Authentication).

## 3. Inventory Entities (The "Nouns")
Scan schema/model definitions (SQL, Prisma, Types). List Core Entities and relationships.

## 4. Extract Business Rules
Scan validation `if` statements throwing errors/bad requests. Translate to rules (e.g. balance cannot be negative).

## 5. Write PRODUCT.md
Write `./.gtd/PRODUCT.md`:

```markdown
# Product Specification

**Status:** Live System Snapshot
**Generated:** {date}

## Core Domain Rules

- {Rule 1}

## Entity Map

- **User**: Has many Orders.
- **Order**: Belongs to User, contains Items.

## Feature Inventory

### 1. {Feature Name}

**Status:** Live
**Capabilities:**

- [x] {Capability 1}

**Business Rules:**

- {Specific rule for this feature}
```

</process>

<offer_next>

```text
---
 GTD ► PRODUCT SPEC GENERATED ✓
---

Source of Truth written to: ./.gtd/PRODUCT.md

Features found: {N}
Entities found: {N}

---
▶ Next Up
/spec — start a new task (which will now use PRODUCT.md context)
---
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
