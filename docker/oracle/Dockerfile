# Oracle Free with a startup guard for hosts whose SysV IPC limits read as 2^64-1.
# On such hosts reading /proc/sys/kernel/shmmax fails with EOVERFLOW and Oracle dies
# (ORA-00600 [ksmcsg], ORA-27300 ... status 75). The guard only acts when that read
# fails; on a normal host it is a no-op and Oracle starts exactly as upstream.
FROM busybox:1.36.1-musl AS bb

FROM gvenzl/oracle-free:23-slim
USER root
COPY --from=bb /bin/busybox /usr/local/bin/busybox
COPY shmmax shmall /opt/shm-override/
COPY entrypoint.sh /usr/local/bin/sms-oracle-entrypoint.sh
RUN chmod 755 /usr/local/bin/sms-oracle-entrypoint.sh /usr/local/bin/busybox \
 && chmod 644 /opt/shm-override/shmmax /opt/shm-override/shmall
ENTRYPOINT ["/usr/local/bin/sms-oracle-entrypoint.sh"]
