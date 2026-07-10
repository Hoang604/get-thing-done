---
name: create-postman-collection
description: Design and write importable Postman collections with deterministic request flows, schema-validated responses, and explicit prerequisite discovery
disable-model-invocation: true
---

# CORE DIRECTIVE

Investigate controllers, request/response DTOs, and service layer boundaries before producing Postman Collection v2.1 JSON.
Design deterministic workflows with explicit setup dependencies (`Authentication, Role Guards, Resource Prerequisite IDs`). Never invent endpoints or guess JSON payload schemas.

**Interface & Discovery Discipline (`Literal Contract & Prerequisite Safety`):**
- **The API Contract is the Test Surface (`Exact DTO & Route Path`):** Every request must strictly trace to an existing controller route and exact DTO payload shape (`CODE [file:line]`). Never invent fictional fields or speculative query parameters.
- **Explicit Prerequisite Discovery (`No Silent Hardcoding`):** If a workflow requires authentication tokens or existing database resource IDs (`e.g., userId, orderId`), they must either be auto-discovered via explicit setup requests (`saving to collection variables: {{accessToken}}, {{resourceId}}`) or explicitly declared as required manual prerequisites. Never silently hardcode placeholder UUIDs (`e.g., 123e4567-...`) inside request URLs or bodies.

---

## Phase 1: CONFIRM (`Investigation & Collection Plan Proposal`)

Perform exhaustive **Legwork** on the target (`feature flow, endpoint family, controller, DTO wrapper`) to map exact HTTP methods, routes, headers, request bodies, auth guards, and JSON response paths. Detect existing envelope structures (`e.g., { data: ... }, pagination wrappers`).
- **Legwork Completion Criterion (`Zero Hallucination Proof`)**: Before drafting the matrix, you must explicitly cite the exact read file paths and line ranges (`CODE [file:line]`) verified during investigation. Never infer payload structures, dependencies, or route paths solely from naming conventions.

Present the concrete **Collection Strategy Proposal** and wait for explicit user approval:

### A. Prerequisite & Auth Audit (`Discovery Verification`)
- **Target Endpoint Family / Seam:** State exactly the controller class/module and base path being covered (`e.g., [OrderController](file:///path#L15) -> /api/v1/orders`).
- **Auth & Prerequisite Map:** Declare required role guards (`e.g., Admin vs User JWT`) and exactly how required resource IDs are obtained (`e.g., Setup Request POST /login -> saves {{accessToken}}; Setup Request POST /users -> saves {{userId}}`).

### B. Oracle Declaration (`Ground Truth vs Assumptions`)
- **Behavioral & Boundary Claims:** Cite exact route signatures and expected HTTP status codes (`e.g., CLAIM: POST /orders returns 201 with OrderDTO -> SOURCE: [OrderController.py:L40](file:///path#L40)`).
- **Data Discovery Claims:** Specify auto-discovered variables vs required manual environment variables.
- **Unverified Assumptions:** Explicitly flag any untraced claims with `⚠️ ASSUMPTION — needs human confirmation`.

### C. Request Workflow Matrix (`Deterministic Verification`)
For each request in the sequence, declare its exact verification target and failure condition (`Breaks-If Mutation`):

| Category | HTTP Request & Route Seam | Variables Consumed -> Produced | Verification Target (`Assertions / JSON Path`) | Breaks-If Mutation (`Specific API Bug That Fails This`) |
| :--- | :--- | :--- | :--- | :--- |
| **Setup** | `POST /api/v1/auth/login` | `{email, password}` -> `{{accessToken}}` | `status == 200 && pm.collectionVariables.set(...)` | Auth service returning token in body vs header envelope mismatch |
| **Flow** | `POST /api/v1/orders` | `{{accessToken}}, {{userId}}` -> `{{orderId}}` | `status == 201 && json.data.status === 'PENDING'` | Missing required DTO validation or wrong response envelope shape |
| **Guard** | `POST /api/v1/orders` (`No Auth`) | `None` -> `None` | `status == 401 Unauthorized` | Missing authentication middleware on controller route |
| **Edge** | `GET /api/v1/orders/999999` | `{{accessToken}}` -> `None` | `status == 404 Not Found && json.error` | Returning 500 Internal Error instead of 404 on missing entity |

**Hard Stop:** Output exactly: `Please review the proposed request workflow matrix and assumptions. I will not write Postman JSON until explicitly confirmed.`

---

## Phase 2: EXECUTE (`JSON Generation & Schema Proof`)

Upon user confirmation, execute the collection strategy:
1. **Write Collection JSON:** Create the `.postman_collection.json` file following strict Postman Collection v2.1 schema. Wire all setup variables (`pm.collectionVariables.set`) and exact request test scripts (`pm.test`).
2. **Mark Unverified Oracles:** If any `⚠️ ASSUMPTION` remained unverified, attach an item-level description note inside the JSON request: `⚠️ UNVERIFIED ORACLE: <reason>`.
3. **Mechanical Validation:** Verify that the JSON structure is valid (`e.g., node -e "JSON.parse(fs.readFileSync('...'))"` or python json check) and that every consumed variable matches a produced or declared collection variable.
