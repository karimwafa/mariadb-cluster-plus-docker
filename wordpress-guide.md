# Panduan Koneksi WordPress ke MariaDB Cluster

Cluster ini menggunakan **ProxySQL** sebagai gerbang utama database. Aplikasi Anda (WordPress) **tidak boleh** terhubung langsung ke container database (`db-master`, dll), melainkan harus melalui **ProxySQL**.

## Arsitektur Koneksi
- **Host**: `proxysql` (nama service di docker-compose) atau IP `127.0.0.1` jika dari localhost.
- **Port**: `6033` (Standard SQL Port ProxySQL).
- **Load Balancing**: Read query otomatis diarahkan ke Slaves, Write query ke Master.

## Langkah-Langkah Setup Database WordPress

### 1. Buat Database & User di Master
Anda perlu membuat database dan user di node Master. Data ini akan otomatis direplikasi ke Slave.

Jalankan command berikut di terminal:
```bash
# Masuk ke container Master
docker exec -it db-master mysql -u root -proot_password

# SQL Command (Ganti password dengan yang aman!)
CREATE DATABASE wordpress_db;
CREATE USER 'wp_user'@'%' IDENTIFIED BY 'wp_password_rahasia';
GRANT ALL PRIVILEGES ON wordpress_db.* TO 'wp_user'@'%';
FLUSH PRIVILEGES;
EXIT;
```

### 2. Daftarkan User di ProxySQL
ProxySQL perlu tahu user mana yang diizinkan lewat. Anda harus mendaftarkan user `wp_user` ke dalam konfigurasi ProxySQL.

Jalankan command berikut:
```bash
# Masuk ke admin interface ProxySQL
docker exec -it proxysql mysql -u admin -padmin -h 127.0.0.1 -P 6032

# SQL Command di Admin Interface
INSERT INTO mysql_users (username, password, default_hostgroup) VALUES ('wp_user', 'wp_password_rahasia', 10);
LOAD MYSQL USERS TO RUNTIME;
SAVE MYSQL USERS TO DISK;
EXIT;
```
> **Catatan**: `default_hostgroup=10` artinya Write query ke Master (HG 10). Read query akan otomatis dipisah ke Slave (HG 20) oleh Query Rules yang sudah aktif.

### 3. Konfigurasi `wp-config.php`
Saat menginstall WordPress, gunakan detail berikut:

- **Database Name**: `wordpress_db`
- **Username**: `wp_user`
- **Password**: `wp_password_rahasia`
- **Database Host**: 
    - Jika WordPress berjalan di **dalam Docker Network yang sama**: `proxysql:6033`
    - Jika WordPress berjalan di **Host Machine (XAMPP/Local)**: `127.0.0.1:6033`

## Verifikasi
Setelah installasi selesai, WordPress akan otomatis menggunakan cluster.
- Saat Anda menulis postingan baru -> Masuk ke Master.
- Saat pengunjung membaca web -> Masuk ke Slave (Load Balanced).
