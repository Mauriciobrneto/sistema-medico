-- MySQL dump 10.13  Distrib 8.0.36, for Win64 (x86_64)
--
-- Host: localhost    Database: sistema
-- ------------------------------------------------------
-- Server version	8.4.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `anotacoes`
--

DROP TABLE IF EXISTS `anotacoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `anotacoes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `conteudo` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `data_criacao` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `anotacoes_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `usuarios` (`idusuarios`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `anotacoes`
--

LOCK TABLES `anotacoes` WRITE;
/*!40000 ALTER TABLE `anotacoes` DISABLE KEYS */;
INSERT INTO `anotacoes` VALUES (6,6,'teste','2024-06-26 02:10:32');
/*!40000 ALTER TABLE `anotacoes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `consultas`
--

DROP TABLE IF EXISTS `consultas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `consultas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `data` date NOT NULL,
  `horario` time NOT NULL,
  `paciente_id` int NOT NULL,
  `consultas_convenio` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `motivo` text COLLATE utf8mb4_unicode_ci,
  `diagnostico` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `paciente_id` (`paciente_id`),
  CONSTRAINT `consultas_ibfk_1` FOREIGN KEY (`paciente_id`) REFERENCES `pacientes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `consultas`
--

LOCK TABLES `consultas` WRITE;
/*!40000 ALTER TABLE `consultas` DISABLE KEYS */;
INSERT INTO `consultas` VALUES (29,'2024-06-25','13:00:00',35,'Unimed','Suspeita de Gripe','gripado, foi medicado'),(30,'2024-06-25','14:00:00',36,'SUS','Suspeita de gripe e febre','gripe, e foi medicado com multigrip'),(31,'2024-06-13','11:11:00',35,'teste','teste','teste'),(32,'2024-06-29','11:01:00',35,'teste','teste','teste');
/*!40000 ALTER TABLE `consultas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `logs`
--

DROP TABLE IF EXISTS `logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `acao` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_afetado` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `item_id` int NOT NULL,
  `usuario_id` int NOT NULL,
  `data_hora` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `logs`
--

LOCK TABLES `logs` WRITE;
/*!40000 ALTER TABLE `logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pacientes`
--

DROP TABLE IF EXISTS `pacientes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pacientes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `idade` int NOT NULL,
  `endereco` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `convenio` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `foto` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `last_modified` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `cpf` varchar(14) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `rua` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cidade` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `estado` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `pais` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `numero` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `historico` text COLLATE utf8mb4_unicode_ci,
  `telefone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pacientes`
--

LOCK TABLES `pacientes` WRITE;
/*!40000 ALTER TABLE `pacientes` DISABLE KEYS */;
INSERT INTO `pacientes` VALUES (35,'Mauricio Bittencourt Ribeiro Neto',27,NULL,'SUS','mauricio_neto.jpg','2024-06-26 00:06:37','988.923.472-89','234234234','234234234','234234234234','23423423','234234234','','(27) 83647-8234'),(36,'Jane Pacheco da Silva',57,NULL,'SUS','janepacheco.jpg','2024-06-26 00:12:41','234.238.947-23','adasdasd','asdasdasd','asdasda','asdasd','12312','','(23) 48729-3847');
/*!40000 ALTER TABLE `pacientes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `idusuarios` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `senha` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nivel_acesso` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`idusuarios`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (6,'Administrador','c4p1w5mn','mauriciobrn@hotmail.com','Administrador'),(13,'Tainara Santos','1234','tainara@uhasud','Usuário');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-06-26  0:04:16
