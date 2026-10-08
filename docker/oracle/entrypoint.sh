#!/bin/bash
# Runs as root only long enough to (optionally) overlay sane SysV IPC limits, then
# drops to the oracle user and hands over to the upstream entrypoint.
BB=/usr/local/bin/busybox
if ! cat /proc/sys/kernel/shmmax /proc/sys/kernel/shmall >/dev/null 2>&1; then
  echo "[shm-workaround] kernel.shmmax/shmall unreadable; bind-mounting sane values"
  for f in shmmax shmall; do
    $BB mount --bind "/opt/shm-override/$f" "/proc/sys/kernel/$f" \
      || echo "[shm-workaround] could not override $f (container needs cap SYS_ADMIN)"
  done
fi
args=""
for a in "$@"; do args="$args $(printf '%q' "$a")"; done
exec $BB su -s /bin/bash oracle -c "exec container-entrypoint.sh$args"
