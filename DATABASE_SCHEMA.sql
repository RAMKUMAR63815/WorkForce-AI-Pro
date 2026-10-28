-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: workforce_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `attendance`
--

DROP TABLE IF EXISTS `attendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attendance` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `check_in` datetime NOT NULL,
  `check_out` datetime DEFAULT NULL,
  `worked_minutes` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_attendance_employee_id` (`employee_id`),
  KEY `ix_attendance_id` (`id`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `attrition_alerts`
--

DROP TABLE IF EXISTS `attrition_alerts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attrition_alerts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `prediction_id` int NOT NULL,
  `employee_id` int NOT NULL,
  `risk_level` varchar(20) NOT NULL,
  `risk_percentage` float NOT NULL,
  `message` varchar(500) NOT NULL,
  `status` varchar(30) NOT NULL,
  `created_at` datetime NOT NULL,
  `acknowledged_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `prediction_id` (`prediction_id`),
  KEY `ix_attrition_alerts_employee_id` (`employee_id`),
  KEY `ix_attrition_alerts_id` (`id`),
  CONSTRAINT `attrition_alerts_ibfk_1` FOREIGN KEY (`prediction_id`) REFERENCES `attrition_predictions` (`id`),
  CONSTRAINT `attrition_alerts_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `attrition_datasets`
--

DROP TABLE IF EXISTS `attrition_datasets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attrition_datasets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dataset_name` varchar(150) NOT NULL,
  `version` int NOT NULL,
  `original_filename` varchar(255) NOT NULL,
  `stored_filename` varchar(255) NOT NULL,
  `uploaded_by` int NOT NULL,
  `total_rows` int NOT NULL,
  `valid_rows` int NOT NULL,
  `invalid_rows` int NOT NULL,
  `status` varchar(30) NOT NULL,
  `validation_report` text NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_attrition_dataset_version` (`dataset_name`,`version`),
  UNIQUE KEY `stored_filename` (`stored_filename`),
  KEY `uploaded_by` (`uploaded_by`),
  KEY `ix_attrition_datasets_id` (`id`),
  KEY `ix_attrition_datasets_dataset_name` (`dataset_name`),
  CONSTRAINT `attrition_datasets_ibfk_1` FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `attrition_models`
--

DROP TABLE IF EXISTS `attrition_models`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attrition_models` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dataset_id` int NOT NULL,
  `version` int NOT NULL,
  `artifact_filename` varchar(255) NOT NULL,
  `feature_columns` text NOT NULL,
  `target_column` varchar(100) NOT NULL,
  `trained_by` int NOT NULL,
  `training_rows` int NOT NULL,
  `accuracy` float DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `artifact_filename` (`artifact_filename`),
  KEY `trained_by` (`trained_by`),
  KEY `ix_attrition_models_dataset_id` (`dataset_id`),
  CONSTRAINT `attrition_models_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `attrition_datasets` (`id`),
  CONSTRAINT `attrition_models_ibfk_2` FOREIGN KEY (`trained_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `attrition_predictions`
--

DROP TABLE IF EXISTS `attrition_predictions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `attrition_predictions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `model_id` int NOT NULL,
  `dataset_id` int NOT NULL,
  `employee_id` int DEFAULT NULL,
  `predicted_label` varchar(10) NOT NULL,
  `risk_percentage` float NOT NULL,
  `confidence_score` float NOT NULL,
  `input_features` text NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_attrition_predictions_employee_id` (`employee_id`),
  KEY `ix_attrition_predictions_model_id` (`model_id`),
  KEY `ix_attrition_predictions_dataset_id` (`dataset_id`),
  CONSTRAINT `attrition_predictions_ibfk_1` FOREIGN KEY (`model_id`) REFERENCES `attrition_models` (`id`),
  CONSTRAINT `attrition_predictions_ibfk_2` FOREIGN KEY (`dataset_id`) REFERENCES `attrition_datasets` (`id`),
  CONSTRAINT `attrition_predictions_ibfk_3` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `chat_conversations`
--

DROP TABLE IF EXISTS `chat_conversations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chat_conversations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_one_id` int NOT NULL,
  `user_two_id` int NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_chat_conversations_user_one_id` (`user_one_id`),
  KEY `ix_chat_conversations_user_two_id` (`user_two_id`),
  CONSTRAINT `chat_conversations_ibfk_1` FOREIGN KEY (`user_one_id`) REFERENCES `users` (`id`),
  CONSTRAINT `chat_conversations_ibfk_2` FOREIGN KEY (`user_two_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `chat_messages`
--

DROP TABLE IF EXISTS `chat_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chat_messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `conversation_id` int NOT NULL,
  `sender_id` int NOT NULL,
  `message` text NOT NULL,
  `sent_at` datetime NOT NULL DEFAULT (now()),
  `read_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_chat_messages_sender_id` (`sender_id`),
  KEY `ix_chat_messages_conversation_id` (`conversation_id`),
  CONSTRAINT `chat_messages_ibfk_1` FOREIGN KEY (`conversation_id`) REFERENCES `chat_conversations` (`id`) ON DELETE CASCADE,
  CONSTRAINT `chat_messages_ibfk_2` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `departments`
--

DROP TABLE IF EXISTS `departments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `departments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_departments_name` (`name`),
  KEY `ix_departments_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `documents`
--

DROP TABLE IF EXISTS `documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `documents` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `uploaded_by` int NOT NULL,
  `file_name` varchar(255) NOT NULL,
  `stored_filename` varchar(100) NOT NULL,
  `category` varchar(50) NOT NULL,
  `content_type` varchar(100) NOT NULL,
  `size_bytes` int NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `stored_filename` (`stored_filename`),
  KEY `uploaded_by` (`uploaded_by`),
  KEY `ix_documents_id` (`id`),
  KEY `ix_documents_category` (`category`),
  KEY `ix_documents_employee_id` (`employee_id`),
  CONSTRAINT `documents_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`),
  CONSTRAINT `documents_ibfk_2` FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `employee_risk_alert_actions`
--

DROP TABLE IF EXISTS `employee_risk_alert_actions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `employee_risk_alert_actions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `alert_id` int NOT NULL,
  `user_id` int NOT NULL,
  `action` varchar(30) NOT NULL,
  `notes` text,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_employee_risk_alert_actions_id` (`id`),
  KEY `ix_employee_risk_alert_actions_alert_id` (`alert_id`),
  KEY `ix_employee_risk_alert_actions_user_id` (`user_id`),
  CONSTRAINT `employee_risk_alert_actions_ibfk_1` FOREIGN KEY (`alert_id`) REFERENCES `employee_risk_alerts` (`id`),
  CONSTRAINT `employee_risk_alert_actions_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `employee_risk_alerts`
--

DROP TABLE IF EXISTS `employee_risk_alerts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `employee_risk_alerts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `previous_risk` float NOT NULL,
  `current_risk` float NOT NULL,
  `risk_increase` float NOT NULL,
  `severity` varchar(20) NOT NULL,
  `status` varchar(20) NOT NULL,
  `detected_at` datetime NOT NULL,
  `resolved_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_employee_risk_alerts_id` (`id`),
  KEY `ix_employee_risk_alerts_status` (`status`),
  KEY `ix_employee_risk_alerts_employee_id` (`employee_id`),
  CONSTRAINT `employee_risk_alerts_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `employees`
--

DROP TABLE IF EXISTS `employees`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `employees` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_code` varchar(30) NOT NULL,
  `user_id` int NOT NULL,
  `department_id` int DEFAULT NULL,
  `designation` varchar(100) NOT NULL,
  `joining_date` date NOT NULL,
  `salary` decimal(12,2) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `address` text,
  `shift_id` int DEFAULT NULL,
  `manager_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `ix_employees_employee_code` (`employee_code`),
  KEY `ix_employees_id` (`id`),
  KEY `ix_employees_department_id` (`department_id`),
  KEY `ix_employees_shift_id` (`shift_id`),
  KEY `ix_employees_manager_id` (`manager_id`),
  CONSTRAINT `employees_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `employees_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`),
  CONSTRAINT `fk_employees_manager` FOREIGN KEY (`manager_id`) REFERENCES `employees` (`id`),
  CONSTRAINT `fk_employees_shift` FOREIGN KEY (`shift_id`) REFERENCES `shifts` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `hr_interventions`
--

DROP TABLE IF EXISTS `hr_interventions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `hr_interventions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `intervention_type` varchar(100) NOT NULL,
  `action_plan` text NOT NULL,
  `notes` text,
  `status` varchar(30) NOT NULL,
  `follow_up_date` date DEFAULT NULL,
  `outcome` text,
  `created_by` int NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `created_by` (`created_by`),
  KEY `ix_hr_interventions_employee_id` (`employee_id`),
  KEY `ix_hr_interventions_id` (`id`),
  CONSTRAINT `hr_interventions_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`),
  CONSTRAINT `hr_interventions_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `leave_balances`
--

DROP TABLE IF EXISTS `leave_balances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leave_balances` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `leave_type` varchar(50) NOT NULL,
  `year` int NOT NULL,
  `total_days` int NOT NULL,
  `used_days` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_employee_leave_type_year` (`employee_id`,`leave_type`,`year`),
  KEY `ix_leave_balances_employee_id` (`employee_id`),
  KEY `ix_leave_balances_id` (`id`),
  CONSTRAINT `leave_balances_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `leaves`
--

DROP TABLE IF EXISTS `leaves`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `leaves` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `leave_type` varchar(50) NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `reason` text NOT NULL,
  `status` varchar(20) NOT NULL,
  `reviewed_by` int DEFAULT NULL,
  `review_remarks` text,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `reviewed_by` (`reviewed_by`),
  KEY `ix_leaves_id` (`id`),
  KEY `ix_leaves_status` (`status`),
  KEY `ix_leaves_employee_id` (`employee_id`),
  CONSTRAINT `leaves_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`),
  CONSTRAINT `leaves_ibfk_2` FOREIGN KEY (`reviewed_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `title` varchar(150) NOT NULL,
  `message` text NOT NULL,
  `notification_type` varchar(50) NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_notifications_user_id` (`user_id`),
  KEY `ix_notifications_id` (`id`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `password_reset_tokens`
--

DROP TABLE IF EXISTS `password_reset_tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `password_reset_tokens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `token_hash` varchar(64) NOT NULL,
  `expires_at` datetime NOT NULL,
  `used_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token_hash` (`token_hash`),
  KEY `ix_password_reset_tokens_user_id` (`user_id`),
  KEY `ix_password_reset_tokens_id` (`id`),
  CONSTRAINT `password_reset_tokens_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `payrolls`
--

DROP TABLE IF EXISTS `payrolls`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payrolls` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `year` int NOT NULL,
  `month` int NOT NULL,
  `basic_salary` decimal(12,2) NOT NULL,
  `allowance` decimal(12,2) NOT NULL,
  `deduction` decimal(12,2) NOT NULL,
  `net_salary` decimal(12,2) NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_employee_payroll_month` (`employee_id`,`year`,`month`),
  KEY `ix_payrolls_employee_id` (`employee_id`),
  KEY `ix_payrolls_id` (`id`),
  CONSTRAINT `payrolls_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `performance_reviews`
--

DROP TABLE IF EXISTS `performance_reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `performance_reviews` (
  `id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `reviewer_id` int NOT NULL,
  `review_period_start` date NOT NULL,
  `review_period_end` date NOT NULL,
  `rating` int NOT NULL,
  `strengths` text NOT NULL,
  `areas_for_improvement` text NOT NULL,
  `goals` text NOT NULL,
  `comments` text,
  `status` varchar(20) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_performance_reviews_reviewer_id` (`reviewer_id`),
  KEY `ix_performance_reviews_employee_id` (`employee_id`),
  KEY `ix_performance_reviews_id` (`id`),
  CONSTRAINT `performance_reviews_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`),
  CONSTRAINT `performance_reviews_ibfk_2` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `risk_monitoring_logs`
--

DROP TABLE IF EXISTS `risk_monitoring_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `risk_monitoring_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `prediction_id` int NOT NULL,
  `employee_id` int DEFAULT NULL,
  `previous_risk` float DEFAULT NULL,
  `current_risk` float NOT NULL,
  `risk_change` float DEFAULT NULL,
  `risk_level` varchar(20) NOT NULL,
  `alert_generated` tinyint(1) NOT NULL,
  `notes` text,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_risk_monitoring_logs_id` (`id`),
  KEY `ix_risk_monitoring_logs_risk_level` (`risk_level`),
  KEY `ix_risk_monitoring_logs_prediction_id` (`prediction_id`),
  KEY `ix_risk_monitoring_logs_employee_id` (`employee_id`),
  CONSTRAINT `risk_monitoring_logs_ibfk_1` FOREIGN KEY (`prediction_id`) REFERENCES `attrition_predictions` (`id`),
  CONSTRAINT `risk_monitoring_logs_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(30) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `ix_roles_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `shifts`
--

DROP TABLE IF EXISTS `shifts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shifts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL,
  `break_minutes` int NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `ix_shifts_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `hashed_password` varchar(255) NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `role_id` int NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_email` (`email`),
  KEY `ix_users_role_id` (`role_id`),
  KEY `ix_users_id` (`id`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `workforce_forecasts`
--

DROP TABLE IF EXISTS `workforce_forecasts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workforce_forecasts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `forecast_months` int NOT NULL,
  `current_headcount` int NOT NULL,
  `employees_with_predictions` int NOT NULL,
  `expected_attrition_12_months` float NOT NULL,
  `projected_attrition` float NOT NULL,
  `projected_headcount` float NOT NULL,
  `projected_retention_rate` float NOT NULL,
  `assumptions` text NOT NULL,
  `generated_by` int NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `generated_by` (`generated_by`),
  KEY `ix_workforce_forecasts_id` (`id`),
  CONSTRAINT `workforce_forecasts_ibfk_1` FOREIGN KEY (`generated_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `workforce_kpi_breaches`
--

DROP TABLE IF EXISTS `workforce_kpi_breaches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workforce_kpi_breaches` (
  `id` int NOT NULL AUTO_INCREMENT,
  `metric_key` varchar(100) NOT NULL,
  `current_value` float NOT NULL,
  `target_value` float NOT NULL,
  `severity` varchar(20) NOT NULL,
  `status` varchar(20) NOT NULL,
  `message` varchar(255) NOT NULL,
  `detected_at` datetime NOT NULL,
  `resolved_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_workforce_kpi_breaches_id` (`id`),
  KEY `ix_workforce_kpi_breaches_status` (`status`),
  KEY `ix_workforce_kpi_breaches_metric_key` (`metric_key`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `workforce_kpi_targets`
--

DROP TABLE IF EXISTS `workforce_kpi_targets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workforce_kpi_targets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `metric_key` varchar(100) NOT NULL,
  `target_value` float NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_workforce_kpi_targets_metric_key` (`metric_key`),
  KEY `ix_workforce_kpi_targets_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `workforce_monitoring`
--

DROP TABLE IF EXISTS `workforce_monitoring`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workforce_monitoring` (
  `id` int NOT NULL AUTO_INCREMENT,
  `active_headcount` int NOT NULL,
  `employees_with_predictions` int NOT NULL,
  `high_risk_employees` int NOT NULL,
  `open_alerts` int NOT NULL,
  `snapshot_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_workforce_monitoring_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=61 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'workforce_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-28 10:05:21
