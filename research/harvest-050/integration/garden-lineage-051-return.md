# Garden Whisperer lineage return — GW1
need: recover dormant receipt ancestry tool discovered in the seeded Garden Whisperer circulation
owner: the-static-collective/garden-whisperer
used: 8490c60ca07fc8f8b891f3e0355a037ebc84511d; existing authenticated browser traceLineage, receipt RLS migration and unauthenticated MCP scaffold
disposition: adapted existing browser route, not replacement service
result: https://github.com/the-static-collective/garden-whisperer/pull/2
evidence: 12 isolated Node/TypeScript test methods, including 128 generated DAGs compared against independent BFS. Core, test and runner Git blob hashes verified. Browser wrapper and UI committed, full app build and real user isolation unverified. No live data access, deployment or identity changes.
next: run full build and two-account RLS test using synthetic receipts; preserve MCP HOLD until per-user OAuth is verified.
admission: none
