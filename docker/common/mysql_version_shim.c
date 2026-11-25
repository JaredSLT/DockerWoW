/* Trinity Legion DatabaseWorkerPool.cpp checks mysql_get_client_version()
 * against MYSQL_VERSION_ID (8.0.42 / 80042) and MIN_MYSQL_CLIENT_VERSION
 * (50100). The OpenSSL-1.0.2-safe MariaDB Connector/C 3.3.11 drop-in reports
 * 30311 and fails both checks. Report the compile-time MySQL 8 client.
 * mysql_get_server_* is also faked so MariaDB 11 is accepted as >= 5.1. */
const char *mysql_get_client_info(void) {
  return "8.0.42";
}

unsigned long mysql_get_client_version(void) {
  return 80042UL;
}

const char *mysql_get_server_info(void *mysql) {
  (void)mysql;
  return "8.0.42";
}

unsigned long mysql_get_server_version(void *mysql) {
  (void)mysql;
  return 80042UL;
}
