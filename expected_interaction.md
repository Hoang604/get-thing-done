# Expected Interaction Flow

This document demonstrates the expected communication reliability of the agent over a 5-turn task, strictly adhering to the `GEMINI.md` execution model, Intent Classification, and Critical Instructions.

## The Scenario
The user wants to replace an in-memory token cache with a Redis cache. This triggers `[MUTATE]` state, which enforces the Phase 1 `CONFIRM` (legwork, interview, contract) and Phase 2 `EXECUTE` pipeline.

---

### Turn 1: The Request
**User:**
> Update the auth logic to use Redis for caching tokens instead of our current memory cache.

---

### Turn 2: Legwork & Interview
**Agent:**
> `` `[MUTATE-explore]` ``
> 
> Need to understand current auth caching. Searching for token cache implementation.
> Search `cacheToken` in src/
> 
> *(System executes grep_search)*
> 
> Found memory cache in `auth.ts`. Need to check if Redis infrastructure already exists.
> Search `redis` in src/
> 
> *(System executes grep_search)*
> 
> No Redis client found. Missing infrastructure requirements. Stopping to interview user.
> 
> 1. Should I install `ioredis` or `redis` as the client?
> 2. What connection string/environment variable should the client use?
> 3. What is the exact TTL (Time To Live) for the tokens in Redis?

---

### Turn 3: User Clarification
**User:**
> 1. Use ioredis.
> 2. process.env.REDIS_URL
> 3. 1 hour.

---

### Turn 4: The Alignment Contract
**Agent:**
> `` `[MUTATE-confirm]` ``
> 
> - **Intent**: Replace in-memory token cache with Redis.
> - **Targets**: 
>   - Update `cacheToken` in `src/auth.ts`
>   - Create redis client in `src/redis.ts`
> - **Technical Choices**: Use `ioredis` package, connect via `process.env.REDIS_URL`, set token TTL to 3600 seconds (1 hour).
> - **Invariants/Out of Scope**: Migrating any other memory caches; adding Redis to docker-compose (assuming external setup).
> 
> Please confirm to execute.

---

### Turn 5: User Approval
**User:**
> Approved, execute.

---

### Turn 6: Execution (Fast-Track & Async)
**Agent:**
> `` `[MUTATE-execute]` ``
> 
> Installing `ioredis` dependency.
> Run `npm install ioredis`
> 
> *(System executes terminal task. Due to async rules, the agent stops calling tools here and waits for the system reactive wakeup)*

*(System wakes agent up: Task Completed)*

**Agent (Turn 7):**
> `` `[MUTATE-execute]` ``
> 
> Write `redis.ts` in [src/redis.ts](file:///path/src/redis.ts)
> 
> Update `cacheToken` in [src/auth.ts](file:///path/src/auth.ts)

*(Notice in Turn 7, because the agent is in a pre-approved EXECUTE phase, it legally bypasses the live-interview narration constraint to avoid tautologies. Furthermore, because it is performing two distinct semantic actions—"Write" and "Update"—it correctly outputs two separate declare lines, strictly adhering to the semantic grouping rules).*
