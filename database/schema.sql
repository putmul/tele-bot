CREATE DATABASE IF NOT EXISTS gymbuddy
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE gymbuddy;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    telegram_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(255) NULL,
    timezone VARCHAR(64) NOT NULL DEFAULT 'Asia/Jakarta',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS workout_splits (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    split_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_splits_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    UNIQUE KEY uq_user_split_name (user_id, split_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS exercises (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    exercise_name VARCHAR(255) NOT NULL,
    CONSTRAINT fk_exercises_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    UNIQUE KEY uq_user_exercise_name (user_id, exercise_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS split_exercises (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    split_id BIGINT UNSIGNED NOT NULL,
    exercise_id BIGINT UNSIGNED NOT NULL,
    exercise_order INT NOT NULL,
    CONSTRAINT fk_split_exercises_split FOREIGN KEY (split_id)
        REFERENCES workout_splits(id) ON DELETE CASCADE,
    CONSTRAINT fk_split_exercises_exercise FOREIGN KEY (exercise_id)
        REFERENCES exercises(id) ON DELETE CASCADE,
    UNIQUE KEY uq_split_exercise (split_id, exercise_id),
    UNIQUE KEY uq_split_exercise_order (split_id, exercise_order)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS workout_sessions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    split_id BIGINT UNSIGNED NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL,
    duration_seconds INT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_sessions_split FOREIGN KEY (split_id) REFERENCES workout_splits(id)
        ON DELETE RESTRICT,
    INDEX idx_sessions_user_status (user_id, status),
    INDEX idx_sessions_started_at (started_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS workout_sets (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT UNSIGNED NOT NULL,
    exercise_id BIGINT UNSIGNED NOT NULL,
    set_number INT NOT NULL,
    repetitions INT NOT NULL,
    weight_kg DECIMAL(8, 2) NOT NULL,
    CONSTRAINT fk_sets_session FOREIGN KEY (session_id) REFERENCES workout_sessions(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_sets_exercise FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS personal_records (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    exercise_id BIGINT UNSIGNED NOT NULL,
    weight_kg DECIMAL(8, 2) NOT NULL,
    repetitions INT NOT NULL,
    estimated_1rm DECIMAL(10, 2) NOT NULL,
    achieved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pr_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_pr_exercise FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        ON DELETE CASCADE,
    INDEX idx_pr_user_exercise (user_id, exercise_id, estimated_1rm)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS cardio_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    activity_type VARCHAR(100) NOT NULL,
    speed_kmh DECIMAL(8, 2) NOT NULL,
    duration_minutes DECIMAL(8, 2) NOT NULL,
    distance_km DECIMAL(10, 2) NOT NULL,
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cardio_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    INDEX idx_cardio_user_date (user_id, recorded_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS body_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    weight_kg DECIMAL(8, 2) NOT NULL,
    height_cm DECIMAL(8, 2) NOT NULL,
    bmi DECIMAL(6, 2) NOT NULL,
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_body_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    INDEX idx_body_user_date (user_id, recorded_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS gym_reminders (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    day_of_week TINYINT NOT NULL,
    reminder_time TIME NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_reminders_user FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    UNIQUE KEY uq_user_reminder (user_id, day_of_week, reminder_time)
) ENGINE=InnoDB;
