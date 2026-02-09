-- MySQL 8 schema for the MVP platform.
-- If you use Alembic later, treat this as bootstrap-only.

CREATE TABLE IF NOT EXISTS users (
  id INT NOT NULL AUTO_INCREMENT,
  email VARCHAR(255) NOT NULL,
  username VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'user',
  rating INT NOT NULL DEFAULT 1000,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email),
  UNIQUE KEY uq_users_username (username),
  KEY ix_users_role (role),
  KEY ix_users_rating (rating)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE IF NOT EXISTS tasks (
  id INT NOT NULL AUTO_INCREMENT,
  title VARCHAR(255) NOT NULL,
  statement TEXT NOT NULL,
  subject VARCHAR(80) NOT NULL,
  topic VARCHAR(120) NOT NULL,
  difficulty INT NOT NULL DEFAULT 1,
  answer_type VARCHAR(20) NOT NULL DEFAULT 'text',
  correct_answer TEXT NOT NULL,
  hints_json JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_tasks_subject (subject),
  KEY ix_tasks_topic (topic),
  KEY ix_tasks_difficulty (difficulty)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE IF NOT EXISTS submissions (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  task_id INT NOT NULL,
  answer TEXT NOT NULL,
  is_correct BOOLEAN NOT NULL,
  duration_ms INT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_submissions_user_id (user_id),
  KEY ix_submissions_task_id (task_id),
  CONSTRAINT fk_submissions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_submissions_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE IF NOT EXISTS matches (
  id CHAR(36) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  canceled_reason VARCHAR(255) NULL,
  task_id INT NOT NULL,
  player1_id INT NOT NULL,
  player2_id INT NOT NULL,
  player1_score INT NOT NULL DEFAULT 0,
  player2_score INT NOT NULL DEFAULT 0,
  player1_rating_before INT NOT NULL,
  player2_rating_before INT NOT NULL,
  player1_rating_after INT NULL,
  player2_rating_after INT NULL,
  started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_matches_status (status),
  KEY ix_matches_player1_id (player1_id),
  KEY ix_matches_player2_id (player2_id),
  CONSTRAINT fk_matches_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE RESTRICT,
  CONSTRAINT fk_matches_player1 FOREIGN KEY (player1_id) REFERENCES users(id) ON DELETE RESTRICT,
  CONSTRAINT fk_matches_player2 FOREIGN KEY (player2_id) REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

CREATE TABLE IF NOT EXISTS match_answers (
  id INT NOT NULL AUTO_INCREMENT,
  match_id CHAR(36) NOT NULL,
  user_id INT NOT NULL,
  answer TEXT NOT NULL,
  is_correct BOOLEAN NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_match_answers_match_id (match_id),
  KEY ix_match_answers_user_id (user_id),
  CONSTRAINT fk_match_answers_match FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
  CONSTRAINT fk_match_answers_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;
