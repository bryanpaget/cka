# CKA Exam Prep Kit

Everything I use to prep for the Certified Kubernetes Administrator (CKA) exam: a reference study sheet, a hands-on drill book, and a self-generating Anki deck (built with zero dependencies). There's also a GitHub Pages flashcard reviewer for quick review from any browser.

## File map

| File | What it is |
|------|-----------|
| [`CKA-Super-Study-Sheet.md`](CKA-Super-Study-Sheet.md) | The reference. Meta-strategy + all 5 domains with docs links, YAML, mnemonics, Q&A. |
| [`CKA-Drill-Book.md`](CKA-Drill-Book.md) | 36 hands-on drills (Task -> Solution -> Verify -> Reset), scoring, 6-week plan. |
| [`anki/cka-cards.tsv`](anki/cka-cards.tsv) | 62 flashcards, tab-separated (`Front`, `Back`, `tags`). |
| [`anki/build_apkg.py`](anki/build_apkg.py) | Zero-dependency `.apkg` builder (Python stdlib only). |
| `anki/CKA-Deck.apkg` | The generated deck. Run the builder to (re)create it. |
| [`index.html`](index.html) | GitHub Pages flashcard reviewer: random card, tap to flip. |
| `.github/workflows/build-anki-deck.yml` | CI: rebuilds, verifies, and publishes the deck. |

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

**Regenerate** after editing `anki/cka-cards.tsv`:
```bash
cd anki && python3 build_apkg.py
# -> Wrote .../CKA-Deck.apkg with 62 cards.
```
No pip installs. The builder uses only the Python standard library to assemble the `.apkg` (a ZIP of a SQLite `collection.anki2` in Anki schema v11 plus a `media` file).

## Web reviewer (GitHub Pages)

Enable Pages on this repo (Settings -> Pages -> deploy from `main`, root). Then visit the Pages URL: it loads `anki/cka-cards.tsv`, shows a random card, and flips on tap/click. Space or the button pulls the next random card. Nothing to install.

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
