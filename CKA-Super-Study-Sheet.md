# CKA Super Study Sheet

The single-page reference for the Certified Kubernetes Administrator exam. Read top to bottom once, then use it as a lookup. Every domain lists docs links, YAML you can retype from memory, mnemonics, and quick Q&A.

Docs you are allowed to use during the exam:
- https://kubernetes.io/docs/
- https://kubernetes.io/blog/
- https://helm.sh/docs/ (only when a task involves Helm)

---

## Exam Meta-Strategy

### Golden setup (type this first, before task 1)

```bash
alias k=kubectl
export do="--dry-run=client -o yaml"   # "do" = generate manifest
export now="--force --grace-period=0"  # "now" = delete immediately
source <(kubectl completion bash)
complete -o default -F __start_kubectl k
```

Use them like:

```bash
k create deploy web --image=nginx $do > web.yaml   # scaffold, then edit
k delete pod broken $now                            # kill stuck pod
```

### CREV: the per-task ritual

Run this on **every** task, no exceptions.

| Step | Action |
|------|--------|
| **C**ontext | `kubectl config use-context <name>` - the wrong cluster loses the marks |
| **R**ead | Parse the task. Note the namespace, the exact names, the success condition |
| **E**xecute | Do it. Prefer imperative commands; drop to YAML only when needed |
| **V**erify | `get` / `describe` to confirm the change actually landed |

### Time discipline

- ~15-20 questions, 2 hours. Budget roughly **6 minutes** per weighted point of value.
- **Flag and skip** anything that stalls you past its budget. Come back with leftover time.
- Never leave a partial edit that breaks a working resource. Revert if unsure.
- Set the namespace once per task: `kubectl config set-context --current --namespace=<ns>`.

---

## Domain 1: Storage (10%)

Docs:
- https://kubernetes.io/docs/concepts/storage/persistent-volumes/
- https://kubernetes.io/docs/concepts/storage/storage-classes/

### Access modes - ROW-X

| Token | Mode | Scope |
|-------|------|-------|
| **R** | ReadWriteOnce (RWO) | one **node** read-write |
| **O** | ReadOnlyMany (ROX) | many nodes read-only |
| **W** | ReadWriteMany (RWX) | many nodes read-write |
| **X** | ReadWriteOncePod (RWOP) | one **pod** read-write |

### Reclaim policies - RD-R

**R**etain (keep data, manual cleanup) - **D**elete (delete backing storage) - **R**ecycle (deprecated).
Dynamic provisioning defaults to **Delete**.

### PV / PVC / StorageClass

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-local
spec:
  capacity:
    storage: 1Gi
  accessModes: ["ReadWriteOnce"]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /mnt/data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-local
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: manual
  resources:
    requests:
      storage: 500Mi
```

`volumeBindingMode: WaitForFirstConsumer` on a StorageClass delays binding until a pod using the PVC is scheduled (topology-aware). The alternative is `Immediate`.

Default StorageClass annotation: `storageclass.kubernetes.io/is-default-class: "true"`.

### Q&A

- **A PVC is stuck Pending. First check?** `kubectl describe pvc` - usually no matching PV (class/mode/size) or no provisioner.
- **How does binding work?** Exclusive one-to-one match on storageClassName + access modes + capacity.
- **Change the default StorageClass?** Patch the old one's annotation to `"false"`, patch the new one to `"true"`.

---

## Domain 2: Workloads & Scheduling (15%)

Docs:
- https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/
- https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

### Rollout verbs - SHUR-R

**S**et image - **H**istory - **U**ndo - **R**estart - **R**ollout status.

```bash
k set image deploy/web nginx=nginx:1.25   # update image
k rollout status deploy/web               # watch it roll
k rollout history deploy/web              # list revisions
k rollout undo deploy/web                 # back one revision
k rollout undo deploy/web --to-revision=2 # target a revision
k rollout restart deploy/web              # recycle pods, same image
k scale deploy/web --replicas=5           # scale
```

RollingUpdate defaults: `maxSurge: 25%`, `maxUnavailable: 25%`.

### Controllers

- **Deployment**: stateless replicas + rollout control (owns a ReplicaSet).
- **DaemonSet**: one pod per matching node (agents).
- **StatefulSet**: stable network IDs + ordered, persistent storage.
- **Job**: run to completion N times. **CronJob**: Jobs on a schedule (`concurrencyPolicy`, `startingDeadlineSeconds`).

### Scheduling levers - NATTS-P

**N**odeSelector - **A**ffinity - **T**aints - **T**olerations - **S**pread (topology) - **P**riority/Preemption.

### Taint effects - NoS / NoE / NoX

| Effect | Behavior |
|--------|----------|
| **NoSchedule** | no new pods without a matching toleration |
| **PreferNoSchedule** | soft avoid |
| **NoExecute** | also **evicts** running pods lacking a toleration |

```bash
k taint nodes node1 gpu=true:NoSchedule     # add
k taint nodes node1 gpu=true:NoSchedule-    # remove (trailing dash)
```

Topology spread: `topologyKey` + `maxSkew` to balance pods across zones/nodes.

### Q&A

- **nodeSelector vs affinity?** nodeSelector = exact hard match. Affinity = required/preferred + set operators (In/NotIn/Exists).
- **Run a pod on a control-plane node?** Add a toleration for its taint (e.g. `node-role.kubernetes.io/control-plane:NoSchedule`).

---

## Domain 3: Networking (20%)

Docs:
- https://kubernetes.io/docs/concepts/services-networking/service/
- https://kubernetes.io/docs/concepts/services-networking/ingress/
- https://kubernetes.io/docs/concepts/services-networking/network-policies/
- https://kubernetes.io/docs/concepts/services-networking/gateway/

### Service types - CNL-E

| Type | What it does |
|------|--------------|
| **C**lusterIP | internal virtual IP (default) |
| **N**odePort | port 30000-32767 on every node |
| **L**oadBalancer | external cloud LB -> NodePort -> ClusterIP |
| **E**xternalName | CNAME to an external DNS name |

```bash
k expose deploy web --port=80 --target-port=8080 --type=ClusterIP
```

### Ingress vs Service

Service = L4 (TCP/UDP). Ingress = L7 HTTP host/path routing, needs an Ingress controller.

### Gateway API - GC -> G -> R

**GatewayClass** (implementation) -> **Gateway** (listeners/infra) -> **Route** (HTTPRoute attaches to the Gateway).

### NetworkPolicy

Default is **allow-all** until a policy selects a pod; then that pod is default-deny for the selected direction.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}          # all pods
  policyTypes: ["Ingress"] # deny all inbound
```

### DNS

Service FQDN: `<svc>.<namespace>.svc.cluster.local`. Pods get a search domain so short names often resolve.

### Q&A

- **Service has no endpoints. Why?** Selector doesn't match pod labels, or pods aren't Ready.
- **Test DNS from a pod?** `kubectl run test --image=busybox --rm -it -- nslookup <svc>.<ns>`.

---

## Domain 4: Troubleshooting (30%)

The biggest slice. Docs:
- https://kubernetes.io/docs/tasks/debug/debug-application/
- https://kubernetes.io/docs/tasks/debug/debug-cluster/

### Debug order - LEDGE

**L**ogs -> **E**vents (describe) -> **D**escribe (pod/node) -> **G**et (wide) -> **E**xec (into container). Work outside-in.

```bash
k logs <pod> --previous      # last crashed instance
k describe pod <pod>         # Events at the bottom
k get pods -o wide           # node placement, IPs
k get events --sort-by=.lastTimestamp
k exec -it <pod> -- sh
```

### Common pod states

| State | Meaning | First move |
|-------|---------|-----------|
| Pending | can't schedule | `describe pod` - resources/taints/unbound PVC |
| CrashLoopBackOff | starts then exits | `logs --previous`, check exit code |
| ImagePullBackOff | can't pull image | bad tag / missing imagePullSecret |
| Init:Error | init container failing | logs of the init container |

### When the API server is down - CJK

**c**rictl - **j**ournalctl - **k**ubelet. The on-node toolkit.

```bash
sudo crictl ps                     # running containers via CRI
sudo crictl logs <id>
sudo journalctl -u kubelet -f      # kubelet logs
systemctl status kubelet
```

Static pod manifests live in `/etc/kubernetes/manifests/` and are watched by the **kubelet**. A broken control-plane manifest there takes down that component.

### Q&A

- **kubectl hangs/refused?** API server down. Check its static pod manifest, then CJK on the node.
- **Node NotReady?** `describe node` for conditions; check kubelet + container runtime + network plugin.

---

## Domain 5: Cluster Architecture, Installation & Configuration (25%)

Docs:
- https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/
- https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/
- https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/
- https://kubernetes.io/docs/reference/access-authn-authz/rbac/

### kubeadm upgrade - DUCK-U

**D**rain -> **U**pgrade kubeadm -> **C**ontrol-plane apply -> **K**ubelet+kubectl -> **U**ncordon. One node at a time.

```bash
k drain node1 --ignore-daemonsets --delete-emptydir-data
sudo apt-get install -y kubeadm=1.31.x-*      # upgrade kubeadm first
sudo kubeadm upgrade plan
sudo kubeadm upgrade apply v1.31.x            # control plane (or 'upgrade node' on workers)
sudo apt-get install -y kubelet=1.31.x-* kubectl=1.31.x-*
sudo systemctl daemon-reload && sudo systemctl restart kubelet
k uncordon node1
```

### etcd backup & restore

```bash
ETCDCTL_API=3 etcdctl snapshot save /opt/snap.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

etcdctl snapshot status /opt/snap.db
etcdctl snapshot restore /opt/snap.db --data-dir /var/lib/etcd-restore
# then point /etc/kubernetes/manifests/etcd.yaml at the new data dir and restart
```

etcd manifest: `/etc/kubernetes/manifests/etcd.yaml`. Data dir: `/var/lib/etcd`. Certs: `/etc/kubernetes/pki/etcd`.

### Join a node

```bash
kubeadm token create --print-join-command   # run on a control-plane node
```

### RBAC - four objects

| Namespaced | Cluster-wide |
|------------|--------------|
| Role | ClusterRole |
| RoleBinding | ClusterRoleBinding |

```bash
k create role reader --verb=get,list --resource=pods
k create rolebinding reader-b --role=reader --serviceaccount=dev:app
k auth can-i list pods --as=system:serviceaccount:dev:app -n dev
```

- **Role vs ClusterRole?** Role = one namespace. ClusterRole = cluster-scoped, cluster resources (nodes), reusable across namespaces.
- **ServiceAccount?** Namespaced pod identity via `spec.serviceAccountName`; projected token mounted for API auth.

---

## Master Mnemonic Table

| Mnemonic | Domain | Meaning |
|----------|--------|---------|
| **CREV** | strategy | Context, Read, Execute, Verify (per task) |
| **TRSVR** | drills | Task, Read, Solve, Verify, Reset (drill loop) |
| **ROW-X** | storage | RWO, ROX, RWX, RWOP access modes |
| **RD-R** | storage | Retain, Delete, Recycle reclaim policies |
| **SHUR-R** | workloads | Set image, History, Undo, Restart, Rollout status |
| **NATTS-P** | scheduling | NodeSelector, Affinity, Taints, Tolerations, Spread, Priority |
| **NoS/NoE/NoX** | scheduling | NoSchedule, NoExecute, PreferNoSchedule effects |
| **CNL-E** | networking | ClusterIP, NodePort, LoadBalancer, ExternalName |
| **GC->G->R** | networking | GatewayClass, Gateway, Route |
| **LEDGE** | troubleshooting | Logs, Events, Describe, Get, Exec |
| **CJK** | troubleshooting | crictl, journalctl, kubelet (API down) |
| **DUCK-U** | cluster-arch | Drain, Upgrade kubeadm, Control-plane, Kubelet, Uncordon |

---

## Exam-Day Checklist

- [ ] Golden aliases set (`k`, `$do`, `$now`) + bash completion.
- [ ] Read the task fully; note namespace and success condition.
- [ ] **Switch context first** on every task.
- [ ] Prefer imperative + `$do` to scaffold YAML.
- [ ] Set the namespace on the current context to avoid `-n` on every command.
- [ ] Verify with `get` / `describe` before moving on.
- [ ] Flag and skip anything over budget; return later.
- [ ] Never leave a working resource broken. Revert if unsure.
- [ ] Bookmark the docs sections above; use the search box, not memory, for long YAML.
