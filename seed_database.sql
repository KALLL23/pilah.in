-- Seed file untuk tabel waste_categories
-- Berguna jika database di-reset atau tabel dikosongkan.

INSERT INTO waste_categories (id, code, name, description) VALUES
(1, 'PLASTIC', 'Plastik', 'Kemasan dan benda berbahan plastik.'),
(2, 'PAPER_CARDBOARD', 'Kertas dan Kardus', 'Kertas, karton, dan kardus yang dapat dipilah.'),
(3, 'GLASS', 'Kaca', 'Botol, wadah, dan benda berbahan kaca.'),
(4, 'METAL', 'Logam', 'Kaleng dan benda berbahan logam.'),
(5, 'ORGANIC', 'Organik', 'Sisa makanan dan bahan organik yang dapat terurai.'),
(6, 'TEXTILE', 'Tekstil', 'Pakaian, kain, dan alas kaki.'),
(7, 'ELECTRONIC_SPECIAL', 'Elektronik dan Khusus', 'Elektronik, baterai, dan material yang membutuhkan penanganan khusus.'),
(8, 'RESIDUAL_MIXED', 'Residu Campuran', 'Sampah campuran atau residu yang tidak masuk kategori lain.')
ON CONFLICT (id) DO NOTHING;

-- Perbaikan tipe data ENUM (jika tipe di-generate tanpa garis bawah oleh SQLAlchemy)
-- Menyesuaikan nama tipe ENUM di PostgreSQL dengan yang diharapkan oleh SQLAlchemy Backend
ALTER TYPE wasteaction RENAME TO waste_action;
ALTER TYPE wastevolume RENAME TO waste_volume;
ALTER TYPE facilitytype RENAME TO facility_type;
ALTER TYPE userrole RENAME TO user_role;
ALTER TYPE reportstatus RENAME TO report_status;
ALTER TYPE risklevel RENAME TO risk_level;
