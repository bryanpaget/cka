# CKA Drill Book

The hands-on dojo. 36 scenario drills that mirror the killer.sh CKA course, each in the same shape so you build muscle memory:

> **Task** -> **Solution** (exact keystrokes) -> **Verify** -> **Reset** -> *time budget*

Run every drill through the **TRSVR** loop: **T**ask, **R**ead, **S**olve, **V**erify, **R**eset. Do it against a real cluster (kind/minikube/kubeadm). Aliases assumed: `k=kubectl`, `do="--dry-run=client -o yaml"`, `now="--force --grace-period=0"`.

Counts: Storage 4 - Workloads 9 - Networking 6 - Troubleshooting 6 - Cluster Arch 8 - CKAD bonus 3 = **36**.

---

## Scoring: red / yellow / green

Score yourself after each drill:

- **Green**: solved from memory, inside budget, verified clean. Move on.
- **Yellow**: solved but needed docs or went over budget. Re-drill tomorrow.
- **Red**: got stuck or produced a broken resource. Re-drill today, then again tomorrow.

Track it in a table. Two greens in a row on a drill = retire it for the week.

---

## Storage (4)

### S1. Static PV + PVC bind
**Task:** Create a 1Gi hostPath PV `pv-data` (RWO, Retain, class `manual`) and a PVC `pvc-data` requesting 500Mi that binds to it. *(4 min)*

**Solution:**
```bash
cat <<'EOF' | k apply -f -
apiVersion: v1
kind: PersistentVolume
metadata: { name: pv-data }
spec:
  capacity: { storage: 1Gi }
  accessModes: ["ReadWriteOnce"]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath: { path: /mnt/data }
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: pvc-data }
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: manual
  resources: { requests: { storage: 500Mi } }
EOF
```
**Verify:** `k get pvc pvc-data` shows `Bound` to `pv-data`.
**Reset:** `k delete pvc pvc-data; k delete pv pv-data`

### S2. Consume a PVC in a pod
**Task:** Run a pod `app` mounting `pvc-data` at `/data`. *(4 min)*

**Solution:**
```bash
k run app --image=busybox $do --command -- sleep 3600 > app.yaml
# add volumes + volumeMounts, then:
k apply -f app.yaml
```
**Verify:** `k exec app -- df -h /data` shows the mount.
**Reset:** `k delete pod app`

### S3. Default StorageClass swap
**Task:** Make StorageClass `fast` the cluster default; remove default from `standard`. *(3 min)*

**Solution:**
```bash
k patch sc standard -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
k patch sc fast -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```
**Verify:** `k get sc` marks `fast (default)`.
**Reset:** patch the annotations back.

### S4. Resize a PVC
**Task:** Expand `pvc-data` from 500Mi to 1Gi (class must allow expansion). *(3 min)*

**Solution:**
```bash
k patch pvc pvc-data -p '{"spec":{"resources":{"requests":{"storage":"1Gi"}}}}'
```
**Verify:** `k get pvc pvc-data` shows 1Gi (or `FileSystemResizePending`).
**Reset:** recreate the PVC.

---

## Workloads & Scheduling (9)

### W1. Deployment from scratch
**Task:** Create deployment `web` (image `nginx:1.25`, 3 replicas). *(2 min)*

**Solution:** `k create deploy web --image=nginx:1.25 --replicas=3`
**Verify:** `k get deploy web` -> 3/3 ready.
**Reset:** `k delete deploy web`

### W2. Rolling image update + status
**Task:** Update `web` to `nginx:1.26` and watch the rollout. *(2 min)*

**Solution:** `k set image deploy/web nginx=nginx:1.26 && k rollout status deploy/web`
**Verify:** `k describe deploy web | grep Image`.
**Reset:** `k rollout undo deploy/web`

### W3. Rollback
**Task:** Roll `web` back to the previous revision. *(2 min)*

**Solution:** `k rollout undo deploy/web`
**Verify:** `k rollout history deploy/web` + confirm image.
**Reset:** n/a.

### W4. Rolling restart
**Task:** Recycle all `web` pods without changing the image. *(1 min)*

**Solution:** `k rollout restart deploy/web`
**Verify:** pod AGE resets in `k get pods`.
**Reset:** n/a.

### W5. Scale
**Task:** Scale `web` to 5 replicas. *(1 min)*

**Solution:** `k scale deploy/web --replicas=5`
**Verify:** `k get deploy web` -> 5/5.
**Reset:** `k scale deploy/web --replicas=3`

### W6. DaemonSet
**Task:** Create a DaemonSet `node-agent` running `busybox sleep 3600` on every node. *(4 min)*

**Solution:** write a DaemonSet manifest (`kind: DaemonSet`, selector + template) and `k apply -f`.
**Verify:** `k get ds node-agent` -> DESIRED == READY == node count.
**Reset:** `k delete ds node-agent`

### W7. CronJob
**Task:** Create a CronJob `hello` printing the date every minute. *(3 min)*

**Solution:** `k create cronjob hello --image=busybox --schedule="*/1 * * * *" -- /bin/sh -c "date"`
**Verify:** `k get jobs -w` shows Jobs appearing.
**Reset:** `k delete cronjob hello`

### W8. Taint + toleration
**Task:** Taint `node1` `gpu=true:NoSchedule`; run a pod that tolerates it. *(4 min)*

**Solution:**
```bash
k taint nodes node1 gpu=true:NoSchedule
k run gpu-pod --image=nginx $do > gpu.yaml
# add tolerations: [{key: gpu, value: "true", effect: NoSchedule}]
k apply -f gpu.yaml
```
**Verify:** pod schedules onto `node1`.
**Reset:** `k delete pod gpu-pod; k taint nodes node1 gpu=true:NoSchedule-`

### W9. nodeSelector placement
**Task:** Label `node1` `disk=ssd` and schedule pod `fast` only there. *(3 min)*

**Solution:**
```bash
k label node node1 disk=ssd
k run fast --image=nginx $do > fast.yaml   # add nodeSelector: {disk: ssd}
k apply -f fast.yaml
```
**Verify:** `k get pod fast -o wide` -> on node1.
**Reset:** `k delete pod fast; k label node node1 disk-`

---

## Networking (6)

### N1. Expose ClusterIP
**Task:** Expose `web` on port 80 -> targetPort 80 as ClusterIP `web-svc`. *(2 min)*

**Solution:** `k expose deploy web --name=web-svc --port=80 --target-port=80`
**Verify:** `k get svc web-svc` + `k get endpoints web-svc` has IPs.
**Reset:** `k delete svc web-svc`

### N2. NodePort
**Task:** Expose `web` as a NodePort. *(2 min)*

**Solution:** `k expose deploy web --name=web-np --port=80 --type=NodePort`
**Verify:** `k get svc web-np` shows a 3xxxx port; curl `<nodeIP>:<port>`.
**Reset:** `k delete svc web-np`

### N3. Debug a broken Service selector
**Task:** Service `web-svc` has no endpoints. Fix it. *(4 min)*

**Solution:** compare `k get svc web-svc -o yaml` selector to `k get pods --show-labels`; patch the selector to match.
**Verify:** `k get endpoints web-svc` now lists pod IPs.
**Reset:** n/a.

### N4. Default-deny NetworkPolicy
**Task:** In namespace `secure`, deny all ingress to every pod. *(3 min)*

**Solution:**
```bash
cat <<'EOF' | k apply -n secure -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: deny-ingress }
spec: { podSelector: {}, policyTypes: ["Ingress"] }
EOF
```
**Verify:** a curl from another pod to a `secure` pod now times out.
**Reset:** `k delete netpol deny-ingress -n secure`

### N5. Allow one namespace in
**Task:** Allow ingress to `secure` pods only from pods labeled `role=frontend`. *(5 min)*

**Solution:** NetworkPolicy with `ingress.from[].podSelector.matchLabels.role=frontend`.
**Verify:** frontend pod reaches it; others don't.
**Reset:** delete the policy.

### N6. DNS resolution check
**Task:** Confirm `web-svc.default.svc.cluster.local` resolves from a pod. *(2 min)*

**Solution:** `k run t --image=busybox:1.28 --rm -it --restart=Never -- nslookup web-svc.default`
**Verify:** returns the ClusterIP.
**Reset:** pod auto-removed by `--rm`.

---

## Troubleshooting (6)

### T1. Pending pod
**Task:** Pod `stuck` stays Pending. Diagnose. *(4 min)*

**Solution:** `k describe pod stuck` -> read Events (insufficient resources / taint / unbound PVC). Apply the fix the events point to.
**Verify:** pod goes Running.
**Reset:** n/a.

### T2. CrashLoopBackOff
**Task:** Pod `crasher` is CrashLooping. Find the cause. *(4 min)*

**Solution:** `k logs crasher --previous` + `k describe pod crasher` for exit code.
**Verify:** identify the failing command/config.
**Reset:** n/a.

### T3. ImagePullBackOff
**Task:** Pod won't pull its image. Fix the tag. *(3 min)*

**Solution:** `k describe pod <p>` shows the pull error; `k set image` or edit to a valid tag / add imagePullSecret.
**Verify:** pod Running.
**Reset:** n/a.

### T4. Node NotReady
**Task:** `node1` is NotReady. Restore it. *(6 min)*

**Solution:** `k describe node node1` for conditions; on the node `systemctl status kubelet`, `journalctl -u kubelet -f`, restart kubelet / runtime.
**Verify:** `k get nodes` -> Ready.
**Reset:** n/a.

### T5. API server down
**Task:** `kubectl` refuses to connect. Recover the control plane. *(6 min)*

**Solution:** on the control-plane node: `sudo crictl ps` for the apiserver container, `sudo crictl logs <id>`, inspect `/etc/kubernetes/manifests/kube-apiserver.yaml` for a bad edit, fix, kubelet recreates it.
**Verify:** `k get nodes` responds again.
**Reset:** n/a.

### T6. Full LEDGE sweep
**Task:** App in namespace `prod` returns 500s. Diagnose end to end. *(6 min)*

**Solution:** **L**ogs -> **E**vents -> **D**escribe -> **G**et -o wide -> **E**xec. Walk outside-in until the root cause surfaces.
**Verify:** app healthy.
**Reset:** n/a.

---

## Cluster Architecture (8)

### C1. etcd snapshot save
**Task:** Take an etcd snapshot to `/opt/snap.db`. *(4 min)*

**Solution:**
```bash
ETCDCTL_API=3 etcdctl snapshot save /opt/snap.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```
**Verify:** `etcdctl snapshot status /opt/snap.db`.
**Reset:** `rm /opt/snap.db`

### C2. etcd restore
**Task:** Restore that snapshot to `/var/lib/etcd-restore` and repoint etcd. *(6 min)*

**Solution:** `etcdctl snapshot restore /opt/snap.db --data-dir /var/lib/etcd-restore`, edit `/etc/kubernetes/manifests/etcd.yaml` data dir, kubelet restarts etcd.
**Verify:** cluster data intact after restart.
**Reset:** point manifest back to original data dir.

### C3. kubeadm upgrade (control plane)
**Task:** Upgrade the control-plane node one minor version. *(6 min)*

**Solution:** DUCK-U: drain -> upgrade kubeadm -> `kubeadm upgrade plan` + `apply` -> upgrade kubelet/kubectl + restart -> uncordon.
**Verify:** `k get nodes` shows the new version.
**Reset:** n/a (lab snapshot).

### C4. kubeadm upgrade (worker)
**Task:** Upgrade a worker node. *(5 min)*

**Solution:** drain from control plane; on worker: upgrade kubeadm, `sudo kubeadm upgrade node`, upgrade kubelet, restart; uncordon.
**Verify:** node version bumped, Ready.
**Reset:** n/a.

### C5. Join a node
**Task:** Generate and use a join command for a new worker. *(3 min)*

**Solution:** `kubeadm token create --print-join-command` on control plane; run output on the new node.
**Verify:** `k get nodes` lists the new node Ready.
**Reset:** `k drain <node> --ignore-daemonsets && k delete node <node>`

### C6. Cordon / drain / uncordon
**Task:** Safely take `node1` out for maintenance and back. *(3 min)*

**Solution:** `k drain node1 --ignore-daemonsets --delete-emptydir-data`; then `k uncordon node1`.
**Verify:** pods evicted then reschedulable.
**Reset:** `k uncordon node1`

### C7. RBAC role + binding
**Task:** Give ServiceAccount `dev:app` get/list on pods in `dev`. *(4 min)*

**Solution:**
```bash
k create role pod-reader --verb=get,list --resource=pods -n dev
k create rolebinding app-reader --role=pod-reader --serviceaccount=dev:app -n dev
```
**Verify:** `k auth can-i list pods --as=system:serviceaccount:dev:app -n dev` -> yes.
**Reset:** `k delete rolebinding app-reader role pod-reader -n dev`

### C8. ServiceAccount + token
**Task:** Create SA `ci` in `dev` and run a pod using it. *(3 min)*

**Solution:** `k create sa ci -n dev`; set `spec.serviceAccountName: ci` in the pod.
**Verify:** `k get pod <p> -n dev -o jsonpath='{.spec.serviceAccountName}'` -> `ci`.
**Reset:** `k delete sa ci -n dev`

---

## CKAD Bonus (3)

### B1. Kustomize overlay
**Task:** Build a base + overlay that sets `replicas: 3` and a name prefix `prod-`. *(5 min)*

**Solution:** base `kustomization.yaml` with the Deployment; overlay `kustomization.yaml` with `namePrefix: prod-` and a replicas patch. Preview `k kustomize overlay/`, apply `k apply -k overlay/`.
**Verify:** `k get deploy` shows `prod-...` at 3 replicas.
**Reset:** `k delete -k overlay/`

### B2. Helm install + upgrade
**Task:** Install a chart as release `demo`, then upgrade a value. *(4 min)*

**Solution:** `helm install demo <chart> --set replicaCount=1`; `helm upgrade demo <chart> --set replicaCount=3`.
**Verify:** `helm list` + `k get deploy`.
**Reset:** `helm uninstall demo`

### B3. Rollout undo drill
**Task:** Deploy, do two image updates, then roll back to revision 1. *(4 min)*

**Solution:** `k rollout history deploy/web`; `k rollout undo deploy/web --to-revision=1`.
**Verify:** image matches revision 1.
**Reset:** n/a.

---

## 6-Week Study Plan

| Week | Focus | Goal |
|------|-------|------|
| 1 | Cluster Arch (C1-C8) + kubeadm/etcd | Green on all C drills |
| 2 | Troubleshooting (T1-T6) + LEDGE | Green on all T drills; fast at CJK |
| 3 | Networking (N1-N6) + NetworkPolicy/DNS | Green on all N drills |
| 4 | Workloads & Scheduling (W1-W9) | Green on all W drills; imperative reflex |
| 5 | Storage (S1-S4) + CKAD bonus (B1-B3) | Green everywhere; mixed drilling |
| 6 | Full timed mocks (killer.sh x2) | Two clean run-throughs under time |

Daily: 30-60 min of drills. Re-drill every **red** same day, every **yellow** next day. End each session by updating your red/yellow/green table.

---

## Exam-Day Speed-Run Checklist

- [ ] Set `k`, `$do`, `$now` + bash completion.
- [ ] CREV on every task: **C**ontext first, **R**ead fully, **E**xecute imperative, **V**erify.
- [ ] Set namespace on the context per task; stop typing `-n`.
- [ ] Scaffold YAML with `$do`; edit; `k apply -f`.
- [ ] Flag/skip anything over budget; return later.
- [ ] Verify with `get`/`describe` before submit. Never leave a resource broken.

---

## Drill Index

| ID | Domain | Drill |
|----|--------|-------|
| S1-S4 | Storage | PV/PVC bind, consume PVC, default SC swap, resize PVC |
| W1-W9 | Workloads | deploy, image update, rollback, restart, scale, DaemonSet, CronJob, taint/toleration, nodeSelector |
| N1-N6 | Networking | ClusterIP, NodePort, broken selector, default-deny, allow-frontend, DNS |
| T1-T6 | Troubleshooting | Pending, CrashLoop, ImagePull, NotReady node, API down, LEDGE sweep |
| C1-C8 | Cluster Arch | etcd save, etcd restore, upgrade CP, upgrade worker, join, drain, RBAC, SA |
| B1-B3 | CKAD bonus | Kustomize, Helm, rollout undo |
