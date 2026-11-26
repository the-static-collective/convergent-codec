# CIRCULATION 023 — CC1

Experimental local directory snapshot transfer. Python 3.10+, standard library only. Run from this directory.

- Sender: `python circulation.py pack SOURCE first.cc1`
- Receiver: `python circulation.py restore first.cc1 STORE SNAPSHOT1`
- Receiver: `python circulation.py inventory STORE receiver.inv`
- Sender: `python circulation.py pack SOURCE second.cc1 --inventory receiver.inv`
- Receiver: `python circulation.py restore second.cc1 STORE SNAPSHOT2`

Copy the bundles and inventory between machines by an independent transport. `inspect` reports manifest and object counts. Output directories must be new, and source, store and outputs distinct. Use local trusted directories and a stable source. Existing snapshots are never overwritten; deletions are represented by absence from the new snapshot. The object store accumulates data and has no garbage collection.

CC1 contains a compressed JSON path/file manifest and a list of missing objects, each with a SHA-256 digest and length. File contents are verified before restore. Content-defined chunks: 2 KiB minimum, 8 KiB mask, 16 KiB maximum. Fixed control uses 8 KiB chunks. The receiver advertises a sorted list of validated object hashes; every inventory byte counts. Optional EC1 object encoding never won this test. No changes to existing EC1 or Int32 frame.

The local benchmark uses eight stdlib modules, the tested codec source, random binary and controlled edits. Total across six stages including inventory: LZMA fresh tar 2,151,612 B; fixed chunks 758,473 B; content-defined chunks 457,943 B. Incremental stages only: 65,354 B for CDC vs 1,792,888 B fresh LZMA. Initial CDC is larger than LZMA. Final CDC object-store payload 423,357 B, excluding restored snapshots and filesystem overhead. Twelve test methods passed normally and under optimized Python; all 18 benchmark restores verified. Four ported source/test/benchmark files matched locally tested Git blob hashes. See receipt.json.

Reproduce: `python -m unittest -v`, `python -O -m unittest -v`, `python benchmark.py`. Local tests and CLI smoke passed; remote CI results not verified.

Limitations: regular-file bytes, directories and portable paths only; not permissions, timestamps, links, Git history or metadata. No live networking, authentication, encryption, hostile-directory concurrency support or independent security audit. 64 MiB total content and bounded manifest/objects, not a total RAM guarantee. One local sequence; no rsync/Git pack or established CDC library benchmark. Tar baseline not wire-format matched. No claim of a new chunking algorithm.
