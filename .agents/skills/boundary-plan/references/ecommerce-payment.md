# Simple E-Commerce Payment & Refund Reference

> **Reference Notice**: This document is a domain reference, not a blind checklist. Before applying any protocol contract, architectural branch, or boundary rule below, inspect the target system's existing architecture, regulatory scope, PSP capabilities, and business requirements to judge whether the mechanism fits the system under design or modification.

## 1. Core Definitions

| Term | Observable Technical Definition |
| :--- | :--- |
| **Payment Service Provider (`PSP` / `TPSP`)** | A PCI DSS-validated third-party service provider that hosts payment credential collection UI, executes authorization/capture/refund clearing with card schemes or banks, and emits signed asynchronous lifecycle webhooks. |
| **Smallest Currency Unit (`Minor Unit`)** | A positive integer (`BIGINT`) representing a monetary value in the target ISO 4217 currency's indivisible base unit without decimals (`100` cents for `$1.00` USD, `100` for `100₫` VND or `¥100` JPY). |
| **Payload Fingerprint** | A deterministic cryptographic hash or canonical field digest of a request's business parameters stored alongside its `Idempotency-Key` to detect parameter tampering across retries reusing the same key. |
| **Net Captured Share** | The integer `Minor Unit` amount actually collected for an individual line item after prorating order-level discounts across items, with any integer-rounding remainder assigned to the final refundable item so the sum across all items equals `captured_amount`. |
| **Non-Failed Refunds** | All refund records associated with a payment whose status is in-flight (`REFUND_PENDING`) or settled (`REFUND_SUCCEEDED`), excluding terminal failures (`REFUND_FAILED` / `REFUND_REVERSED`). |
| **Monotonic State-Transition Precondition** | An atomic database predicate (`WHERE status IN (...)`) that permits a payment or refund record to advance only to a strictly higher lifecycle state, turning out-of-order or stale webhook events into no-ops. |

---

## 2. Closed Contracts for Monetary Units, PCI Scope, Idempotency & Reversals

### 2.1. ISO 4217 Minor-Unit Integer Representation

Represent, store, and transmit every monetary amount across orders, payment sessions, captures, and refunds as an exact integer (`BIGINT`) in the currency's ISO 4217 `Minor Unit`, converting from decimal input only at the ingress boundary and formatting for human display only at the presentation boundary:
- **Two-decimal currencies** (`USD`, `EUR`, `GBP`, ...): integer value equals major currency amount multiplied by `100`.
- **Zero-decimal currencies** (`VND`, `JPY`, `KRW`, ...): integer value equals exact major currency amount.
- **Three-decimal currencies** (`BHD`, `KWD`, `OMR`, ...): integer value equals major currency amount multiplied by `1000`.

### 2.2. PCI DSS v4.0 SAQ A Outsourcing Eligibility Contract

A merchant system qualifies for full cardholder-data environment (CDE) exemption under **PCI DSS v4.0 SAQ A** only when all four conditions below hold simultaneously:

| SAQ A Requirement | Mandatory System State |
| :--- | :--- |
| **Card-not-present channel** | Accepts only online / card-not-present transactions. |
| **Full TPSP processing delegation** | Delegates all cardholder data processing, clearing, and vaulting to a PCI DSS-validated PSP. |
| **Zero electronic CHD on merchant premises** | Never electronically stores, processes, or transmits raw Primary Account Numbers (`PAN`) or sensitive authentication data (`CVV`/`PIN`) on merchant servers, logs, or networks. |
| **Direct PSP origin of payment UI** | Delivers all payment form elements to the buyer's browser directly from the PSP's domain via **Full-Page Hosted Checkout Redirect** (zero script-monitoring overhead on merchant pages) or **PSP-Hosted Embedded `<iframe>`** (which under PCI DSS v4.0 Req. 6.4.3 & 11.6.1 requires maintaining a script inventory, Content Security Policy, and 7-day page/header integrity monitoring on the parent merchant page). |

### 2.3. HTTP `Idempotency-Key` & Retry Protocol Contract

| Protocol Scenario | Mandatory System & Gateway Behavior |
| :--- | :--- |
| **First-time mutating request (`POST` / `PATCH`)** | Persist `(scope_id, idempotency_key, payload_fingerprint)` atomically in the database, execute the operation, persist the resulting HTTP status code and response body, and return the response. Do not attach idempotency keys to naturally idempotent `GET` or `DELETE` requests. |
| **Completed request retry (matching key & fingerprint)** | Return the exact saved HTTP status code and response body without re-executing business logic or calling the PSP again. |
| **Keyless request on a protected mutation endpoint** | Reject immediately with HTTP `400 Bad Request`. |
| **Key reused with a different `Payload Fingerprint`** | Reject immediately without executing business logic and return HTTP `422 Unprocessable Content` (or `400 Bad Request` per PSP convention). |
| **Concurrent in-flight duplicate request** | Reject the second arriving request while the first is still executing and return HTTP `409 Conflict` so the caller backs off and retries. |
| **Retry after PSP key-pruning cutoff ($\ge 24\text{ hours}$)** | Stop blind `POST` retries once the PSP's idempotency retention window (24 hours) expires; query the PSP's transaction status by merchant reference or metadata before minting a new key. |

### 2.4. Payment Reversal & Asynchronous Refund Exception Contract

Select the reversal operation and handle asynchronous post-submission webhook transitions strictly according to the original payment's capture state and `pspReference` availability:

| Payment State / Webhook Event | Mandatory API Operation & State Transition |
| :--- | :--- |
| **Authorized but uncaptured (`requires_capture` / `authorized`) with known `pspReference`** | Invoke **Cancel / Void** on the original payment reference to release the authorization hold without incurring capture-and-refund settlement fees. |
| **Uncertain authorization after network timeout (missing `pspReference`, within 24h)** | Invoke **Technical Cancel** keyed by the unique internal `merchant_order_reference` within 24 hours of the authorization attempt. |
| **Captured / settled (`succeeded` / `captured`)** | Invoke **Refund** referencing the captured payment/charge ID with an integer `Minor Unit` amount not exceeding the remaining unrefunded balance. |
| **Uncertain capture state on a single full-amount payment (zero partial captures, zero splits)** | Invoke **Cancel or Refund (Reversal)** so the PSP cancels if uncaptured or refunds in full if captured. Never call `cancelOrRefund` on payments with multiple partial captures or marketplace splits. |
| **Webhook: `REFUND` (`success: false`)** | Transition the refund record from `REFUND_PENDING` to `REFUND_FAILED`, release the locked refund ceiling amount, and record the rejection `reason`. |
| **Webhook: `REFUND_FAILED` / `refund.failed` (card scheme rejection after initial acceptance)** | Transition the refund record from `REFUND_PENDING` (or provisionally accepted) to `REFUND_FAILED`, restore the failed amount to the remaining refundable ceiling, and flag the order for out-of-band alternative customer reimbursement. |
| **Webhook: `REFUNDED_REVERSED` (bounced bank/iDEAL/Bancontact refund)** | Record that the refunded funds returned to the merchant's PSP balance, transition the refund record to `REFUND_REVERSED`, and trigger an exception workflow to collect a valid payout instrument from the customer. |
| **Webhook: `charge.dispute.created` / `CHARGEBACK` opened** | Set `has_open_dispute = TRUE` on the payment record and block all merchant-initiated API refunds while the dispute remains open so reimbursement occurs exclusively through the PSP dispute workflow. |

---

## 3. Generative Rules for Architecture, Payment Collection & Refund Execution

- **When** designing the service boundary and persistence topology for a single-merchant e-commerce store (as opposed to a multi-vendor marketplace requiring split-escrow platforms such as `Stripe Connect` or `Adyen for Platforms`), delegate all sensitive payment credential capture and financial network clearing to a single PCI DSS-compliant PSP through a browser flow loaded directly from the PSP's origin and a single thin backend Gateway adapter, while storing and mutating `orders`, `inventory_reservations`, `order_payments`, `payment_refunds`, and `processed_webhook_events` inside one shared ACID relational database. Allowing raw card credentials or custom card-collection forms onto merchant servers expands PCI DSS audit scope from SAQ A to SAQ A-EP/SAQ D, and splitting order, payment, and inventory state across separate microservice databases introduces distributed Two-Phase Commit (`2PC`) or compensating Saga overhead that a single local ACID transaction eliminates.
- **When** creating a payment session or payment intent for a customer order, compute every line item's price, applicable promotion, and payable total on the server from authoritative database catalog records keyed solely by client-submitted item IDs and positive integer quantities, and lock that server-computed total, currency, and line-item `Net Captured Share` breakdown into an immutable order snapshot before calling the PSP. Accepting prices, discount rates, or pre-calculated totals from client requests exposes the checkout flow to parameter tampering, and re-reading live catalog prices during asynchronous webhook settlement instead of comparing against the locked order snapshot causes valid paid orders to fail verification if an administrator edits catalog prices while the buyer is completing payment.
- **When** initiating checkout for inventory-constrained goods, atomically decrement available stock into a time-bounded reservation (`available_stock >= requested_quantity`) inside the local database before creating the PSP checkout session, pass the reservation's exact deadline into the PSP session's `expires_at` parameter, and release reserved stock back to available inventory only when the PSP confirms session expiration (`checkout.session.expired`) or payment cancellation. Deducting inventory only after asynchronous payment webhook delivery causes overselling under concurrent checkouts for the last item in stock, while releasing reserved stock via an independent local timer before the PSP payment session expires allows a customer who completes payment just before the PSP deadline to pay for an already-reallocated item.
- **When** originating or receiving any network request that mutates payment or refund state—both from the buyer's client to the merchant backend and from the merchant backend to the PSP—commit a deterministic `Idempotency-Key` (derived from the persisted local domain attempt ID) and the request's `Payload Fingerprint` into the durable ACID database *before* executing the mutation or transmitting the outbound HTTP call, and restrict automated network retries to the target server's key-retention window (24 hours) before switching to state-reconciliation queries. Generating fresh random UUIDs inside retry loops, storing idempotency keys only in volatile caches without database uniqueness guarantees, or blindly re-posting after the PSP prunes expired keys causes duplicate charges or duplicate refunds across network timeouts and worker restarts.
- **When** transitioning an order to a paid state or triggering order fulfillment, execute the transition exclusively inside the server-side webhook handler (or an authenticated server-to-server PSP status reconciliation job) after verifying the cryptographic HMAC signature and replay-window timestamp ($\le 5\text{ minutes}$) against the unparsed raw request bytes, recording the PSP `event_id` in a deduplication table (`UNIQUE(psp_event_id)`) within the same atomic database transaction, verifying that the captured amount and currency match the locked order snapshot, and guarding the status update with a `Monotonic State-Transition Precondition` (`WHERE status IN (...)`) before enqueuing heavy fulfillment side effects asynchronously and returning HTTP `200 OK`. Triggering fulfillment from client-side browser redirect URLs loses paid orders whenever the buyer's browser closes or drops connectivity prior to redirect, parsing JSON before signature verification invalidates the raw-body HMAC digest, and updating order status without a monotonic state precondition allows delayed earlier-stage webhooks (`processing`) to overwrite a completed (`PAID`) order.
- **When** executing a customer reimbursement or order cancellation, acquire a row-level lock (`SELECT ... FOR UPDATE`) on the parent payment record inside the local ACID database, verify that no open chargeback dispute exists (`has_open_dispute = FALSE`), select the reversal operation matching the payment's capture state from Section 2.4, and—for partial or full refunds on captured payments—compute any line-item amount from its prorated `Net Captured Share` (assigning any integer-rounding remainder to the final refundable item) and persist a `REFUND_PENDING` record with its own deterministic `Idempotency-Key` only if the sum of all `Non-Failed Refunds` (`REFUND_PENDING + REFUND_SUCCEEDED`) plus the requested integer `Minor Unit` amount does not exceed `captured_amount`, keeping the refund in `REFUND_PENDING` until a terminal webhook (`REFUND_SUCCEEDED`, `REFUND_FAILED`, or `REFUNDED_REVERSED`) arrives. Evaluating the refundable balance without locking the parent payment row or without counting in-flight `REFUND_PENDING` records allows concurrent partial-refund requests to over-refund the original charge, refunding pre-discount item prices leaks merchant funds, issuing an API refund during an open dispute double-reimburses the buyer, and marking a refund completed on synchronous HTTP `200 OK` hides subsequent card-scheme rejections (`REFUND_FAILED`) and closed-account bank reversals (`REFUNDED_REVERSED`).

---

## 4. Completion Criterion & Verification Anchor

A design, implementation plan, or codebase modification for a simple e-commerce payment and refund system is complete only when accompanied by a 4-column verification table proving that every applicable rule in Sections 2 and 3 holds on the target system:
1. **PCI DSS SAQ A & Single-ACID Boundary**: All payment credential inputs originate directly from the PSP (Hosted Redirect or PCI v4.0-monitored iframe), and `orders`, `reservations`, `payments`, `refunds`, and `webhook_events` share one atomic ACID database without distributed 2PC/Saga orchestration.
2. **Server-Side Valuation, Minor Units & Inventory Reservation**: All monetary columns and payloads use integer `Minor Units` (`BIGINT`), order totals and prorated `Net Captured Share` values are computed server-side and locked into an immutable snapshot before PSP session creation, and stock reservations are bound to the PSP session's `expires_at` lifecycle.
3. **Two-Hop Durable Idempotency**: Both client-to-merchant and merchant-to-PSP mutations persist deterministic `Idempotency-Key` and `Payload Fingerprint` records in the database before execution and bound automated retries to the PSP's key-retention window.
4. **Raw-Body Webhook Fulfillment & Monotonic Transitions**: Order fulfillment is triggered exclusively by signature- and timestamp-verified raw-body webhooks, deduplicated via atomic `UNIQUE(psp_event_id)` insertion, and guarded by a `Monotonic State-Transition Precondition`.
5. **Capture-Aware Reversal, Locked Refund Ceiling & Async Exception Handling**: Pre-capture cancellations use `Cancel / Void` (or `Technical Cancel`), post-capture refunds lock the parent payment row (`SELECT ... FOR UPDATE`), enforce `has_open_dispute = FALSE` and `SUM(non_failed_refunds) + requested_amount <= captured_amount`, and remain `REFUND_PENDING` until settled or routed to exception handling on `REFUND_FAILED` / `REFUNDED_REVERSED`.

**Verification Table Shape Anchor** (illustrated in a domain-free cold-chain delivery check):

| Verification Item | Governing Rule | Observable State in Target System | Verdict |
| :--- | :--- | :--- | :--- |
| Insulated crate reception temperature | Cold-chain perishables rule | Thermometer probe reads $3^\circ\text{C}$ and dry-ice seal is intact prior to signature | Passed |
