-- Jalankan file ini jika database sudah dibuat dari schema versi awal.
-- Jika tabel sudah memiliki kolom tersebut, lewati statement yang terkait.

ALTER TABLE workout_splits
    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE workout_sessions
    ADD COLUMN current_exercise_order INT NOT NULL DEFAULT 1;
