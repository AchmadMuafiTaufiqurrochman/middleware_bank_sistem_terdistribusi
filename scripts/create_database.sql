# scripts/create_database.sql
-- Script untuk membuat database middleware
-- Jalankan di MySQL sebelum menjalankan migration

-- Buat database jika belum ada
CREATE DATABASE IF NOT EXISTS middleware
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Gunakan database
USE middleware;

-- Tampilkan konfirmasi
SELECT 'Database middleware created successfully!' AS Status;
