# CKA Exam Prep Kit

Everything I use to prep for the Certified Kubernetes Administrator (CKA) exam: a reference study sheet, a hands-on drill book, and a self-generating Anki deck (built with zero dependencies). There's also a GitHub Pages flashcard reviewer for quick review from any browser.

## File map

| File | What it is |
|------|-----------|
| [`CKA-Super-Study-Sheet.md`](CKA-Super-Study-Sheet.md) | The reference. Meta-strategy + all 5 domains with docs links, YAML, mnemonics, Q&A. |
| [`CKA-Drill-Book.md`](CKA-Drill-Book.md) | 36 hands-on drills (Task -> Solution -> Verify -> Reset), scoring, 6-week plan. |
| [`anki/cka-cards.tsv`](anki/cka-cards.tsv) | 62 flashcards, tab-separated (`Front`, `Back`, `tags`). |
| [`anki/build_apkg.py`](anki/build_apkg.py) | Zero-dependency `.apkg` builder (Python stdlib only). |
| [`anki/verify_apkg.py`](anki/verify_apkg.py) | Validates a built deck (zip + sqlite + card counts). |
| [`Makefile`](Makefile) | `make` to build + sync + verify. `make help` lists targets. |
| `anki/CKA-Deck.apkg` | The generated deck. Run `make build` to (re)create it. |
| [`docs/index.html`](docs/index.html) | GitHub Pages flashcard reviewer: random card, tap to flip. |
| `docs/cka-cards.tsv` | Pages copy of the cards (auto-synced by the builder; do not hand-edit). |
| `.github/workflows/build-anki-deck.yml` | CI: rebuilds, verifies, and checks the docs/ copy is in sync. |

## Domains & weights

| Domain | Weight |
|--------|--------|
| Storage | 10% |
| Workloads & Scheduling | 15% |
| Networking | 20% |
| Troubleshooting | 30% |
| Cluster Architecture, Installation & Configuration | 25% |

Troubleshooting is the single biggest slice. Spend your drill time accordingly.

## Quick start

1. **Cluster.** Spin up a practice cluster (kind, minikube, or a kubeadm lab).
2. **Golden aliases** (type these before anything else):
   ```bash
   alias k=kubectl
   export do="--dry-run=client -o yaml"
   export now="--force --grace-period=0"
   source <(kubectl completion bash); complete -o default -F __start_kubectl k
   ```
3. **Drill with TRSVR.** Work through [`CKA-Drill-Book.md`](CKA-Drill-Book.md): **T**ask -> **R**ead -> **S**olve -> **V**erify -> **R**eset. Score red/yellow/green.
4. **Flashcards.** Import the Anki deck (below) or open the web reviewer for spare-minute review.

## Anki deck

**Import:** open Anki -> *File > Import* -> select `anki/CKA-Deck.apkg`. Re-importing an updated deck **updates** cards instead of duplicating them (IDs are content-derived).

**Regenerate** after editing `anki/cka-cards.tsv`. One command rebuilds the deck, syncs the web reviewer's copy in `docs/`, and verifies everything:
```bash
make            # build + sync docs/ + verify + check sync
```
Then review the diff and commit `anki/CKA-Deck.apkg` and `docs/cka-cards.tsv`.

Other targets (`make help` lists them):
```bash
make build      # just rebuild the deck + sync docs/
make verify     # validate the .apkg (zip + sqlite + card counts)
make check-sync # fail if docs/ card copy drifted from the source
make serve      # preview the web reviewer at http://localhost:8000
```

Prefer no make? The builder alone does the build + sync:
```bash
python3 anki/build_apkg.py
# -> Wrote .../CKA-Deck.apkg with 62 cards.
# -> Synced .../docs/cka-cards.tsv
```
No pip installs: the builder uses only the Python standard library to assemble the `.apkg` (a ZIP of a SQLite `collection.anki2` in Anki schema v11 plus a `media` file).

## Web reviewer (GitHub Pages)

The site lives in [`docs/`](docs/). Enable Pages on this repo: **Settings > Pages > Deploy from a branch**, branch `main`, folder **`/docs`**. Then visit the Pages URL: `docs/index.html` loads `docs/cka-cards.tsv`, shows a random card, and flips on tap/click. Space/Enter flips, right-arrow (or the button) pulls the next random card. Nothing to install.

`docs/cka-cards.tsv` is a synced copy of `anki/cka-cards.tsv` (Pages only serves files under `docs/`). You edit `anki/cka-cards.tsv`; running the builder copies it into `docs/` for you. The `.nojekyll` file in `docs/` tells Pages to serve the files as-is without Jekyll.

## Mnemonic cheat-sheet

| Mnemonic | Domain | Meaning |
|----------|--------|---------|
| **CREV** | strategy | Context, Read, Execute, Verify (per task) |
| **TRSVR** | drills | Task, Read, Solve, Verify, Reset |
| **ROW-X** | storage | RWO, ROX, RWX, RWOP access modes |
| **RD-R** | storage | Retain, Delete, Recycle reclaim policies |
| **SHUR-R** | workloads | Set image, History, Undo, Restart, Rollout status |
| **NATTS-P** | scheduling | NodeSelector, Affinity, Taints, Tolerations, Spread, Priority |
| **NoS/NoE/NoX** | scheduling | NoSchedule, NoExecute, PreferNoSchedule |
| **CNL-E** | networking | ClusterIP, NodePort, LoadBalancer, ExternalName |
| **GC->G->R** | networking | GatewayClass, Gateway, Route |
| **LEDGE** | troubleshooting | Logs, Events, Describe, Get, Exec |
| **CJK** | troubleshooting | crictl, journalctl, kubelet (API down) |
| **DUCK-U** | cluster-arch | Drain, Upgrade kubeadm, Control-plane, Kubelet, Uncordon |

## 6-week plan (summary)

| Week | Focus |
|------|-------|
| 1 | Cluster Architecture + kubeadm/etcd |
| 2 | Troubleshooting + LEDGE / CJK |
| 3 | Networking + NetworkPolicy / DNS |
| 4 | Workloads & Scheduling (imperative reflex) |
| 5 | Storage + CKAD bonus |
| 6 | Full timed mocks (killer.sh x2) |

Full breakdown in the drill book.

## Exam-day non-negotiables

- Set the golden aliases before task 1.
- **Switch context first** on every task. Wrong cluster = lost marks.
- Set the namespace on the current context per task.
- Scaffold YAML with `$do`, then `kubectl apply -f`.
- **Verify every task** with `get`/`describe` before moving on.
- Flag and skip anything over budget. Never leave a working resource broken.

## Docs (allowed in the exam)

- https://kubernetes.io/docs/
- https://kubernetes.io/blog/
- https://helm.sh/docs/
