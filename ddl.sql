CREATE TABLE IF NOT EXISTS `Staff` (
	`staff_id` INTEGER NOT NULL AUTO_INCREMENT,
	`staff_no` VARCHAR(9) UNIQUE COMMENT 'Format: CS-XXXXXX(6 Xs)',
	`name` VARCHAR(100) NOT NULL,
	`dept` VARCHAR(50) NOT NULL,
	`phone` VARCHAR(30),
	`is_active` BOOLEAN NOT NULL DEFAULT true,
	PRIMARY KEY(`staff_id`)
);


CREATE TABLE IF NOT EXISTS `Order` (
	`order_id` INTEGER NOT NULL AUTO_INCREMENT,
	`order_no` VARCHAR(50) UNIQUE COMMENT 'Format: INV-YEARXXXXXX(6 Xs)',
	`date` DATE NOT NULL,
	`reason` MEDIUMTEXT DEFAULT NULL COMMENT 'discount reason',
	`discount` INTEGER UNSIGNED DEFAULT NULL,
	`amount` INTEGER COMMENT '用 unit_price * unit 計算',
	`status` VARCHAR(255) NOT NULL DEFAULT 'processing' CHECK(status in ("processing", "shipped", "completed", "cancelled" )),
	`staff_id` INTEGER NOT NULL,
	`cust_id` INTEGER NOT NULL,
	PRIMARY KEY(`order_id`)
);


CREATE TABLE IF NOT EXISTS `Sequences` (
	`name` VARCHAR(50) NOT NULL,
	`year` YEAR NOT NULL,
	`last_num` INTEGER NOT NULL DEFAULT 0,
	PRIMARY KEY(`name`, `year`)
);


CREATE TABLE IF NOT EXISTS `login_info` (
	`staff_id` INTEGER NOT NULL,
	`pw_hash` VARCHAR(255) NOT NULL,
	`role` VARCHAR(255) NOT NULL CHECK(role in ( "admin", "staff")),
	PRIMARY KEY(`staff_id`)
);


CREATE TABLE IF NOT EXISTS `Order_details` (
	`order_id` INTEGER NOT NULL,
	`goods_id` INTEGER NOT NULL,
	`pro_id` INTEGER DEFAULT NULL,
	`unit` INTEGER UNSIGNED NOT NULL DEFAULT 0,
	`price` INTEGER UNSIGNED NOT NULL,
	`amount` INTEGER UNSIGNED,
	PRIMARY KEY(`order_id`, `goods_id`)
);


CREATE TABLE IF NOT EXISTS `Customer` (
	`cust_id` INTEGER NOT NULL AUTO_INCREMENT,
	`cust_no` VARCHAR(7) UNIQUE COMMENT 'Format: KXXXXXX',
	`co_name` VARCHAR(255) NOT NULL,
	`contact_name` VARCHAR(100),
	`phone` VARCHAR(30) NOT NULL,
	`staff_id` INTEGER NOT NULL,
	PRIMARY KEY(`cust_id`)
);


CREATE TABLE IF NOT EXISTS `Invertory` (
	`goods_id` INTEGER NOT NULL AUTO_INCREMENT,
	`name` VARCHAR(255) NOT NULL,
	`quantity` INTEGER  NOT NULL DEFAULT 0,
	`price` INTEGER NOT NULL DEFAULT 0,
	`sup_id` INTEGER NOT NULL,
	`stop_purchase` BOOLEAN NOT NULL DEFAULT False,
	PRIMARY KEY(`goods_id`),
	CONSTRAINT `invertory_chk_price` CHECK (`price` >= 0),
	CONSTRAINT `invertory_chk_quantity` CHECK (`quantity` >= 0)
);


CREATE TABLE IF NOT EXISTS `Supplier` (
	`sup_id` INTEGER NOT NULL AUTO_INCREMENT,
	`co_name` VARCHAR(255) NOT NULL,
	`contact_name` VARCHAR(100),
	`phone` VARCHAR(30) NOT NULL,
	PRIMARY KEY(`sup_id`)
);


CREATE TABLE IF NOT EXISTS `Purchase` (
	`pu_id` INTEGER NOT NULL AUTO_INCREMENT,
	`pu_no` VARCHAR(12) UNIQUE COMMENT 'Format: P-YEARXXXXXX',
	`date` DATE NOT NULL,
	`reason` MEDIUMTEXT DEFAULT NULL,
	`discount` INTEGER UNSIGNED DEFAULT NULL,
	`amount` INTEGER,
	`staff_id` INTEGER NOT NULL,
	PRIMARY KEY(`pu_id`)
);


CREATE TABLE IF NOT EXISTS `Purchase_details` (
	`pu_id` INTEGER NOT NULL,
	`goods_id` INTEGER NOT NULL,
	`unit` INTEGER UNSIGNED NOT NULL DEFAULT 0,
	`price` INTEGER UNSIGNED,
	`amount` INTEGER UNSIGNED,
	PRIMARY KEY(`pu_id`, `goods_id`)
);


CREATE TABLE IF NOT EXISTS `Promotion` (
	`pro_id` INTEGER NOT NULL AUTO_INCREMENT,
	`start_date` DATETIME NOT NULL,
	`end_date` DATETIME NOT NULL,
	`reason` MEDIUMTEXT NOT NULL,
	PRIMARY KEY(`pro_id`)
);


CREATE TABLE IF NOT EXISTS `Promotion_details` (
	`pro_id` INTEGER NOT NULL,
	`goods_id` INTEGER NOT NULL,
	`price` INTEGER UNSIGNED NOT NULL,
	PRIMARY KEY(`pro_id`, `goods_id`)
);


ALTER TABLE `Order`
ADD FOREIGN KEY(`staff_id`) REFERENCES `Staff`(`staff_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `Order_details`
ADD FOREIGN KEY(`order_id`) REFERENCES `Order`(`order_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `Customer`
ADD FOREIGN KEY(`staff_id`) REFERENCES `Staff`(`staff_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `Order`
ADD FOREIGN KEY(`cust_id`) REFERENCES `Customer`(`cust_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `Purchase_details`
ADD FOREIGN KEY(`pu_id`) REFERENCES `Purchase`(`pu_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `Promotion_details`
ADD FOREIGN KEY(`pro_id`) REFERENCES `Promotion`(`pro_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `Invertory`
ADD FOREIGN KEY(`sup_id`) REFERENCES `Supplier`(`sup_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `Purchase`
ADD FOREIGN KEY(`staff_id`) REFERENCES `Staff`(`staff_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `Promotion_details`
ADD FOREIGN KEY(`goods_id`) REFERENCES `Invertory`(`goods_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `Order_details`
ADD FOREIGN KEY(`goods_id`) REFERENCES `Invertory`(`goods_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `Purchase_details`
ADD FOREIGN KEY(`goods_id`) REFERENCES `Invertory`(`goods_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `Order_details`
ADD FOREIGN KEY(`pro_id`) REFERENCES `Promotion`(`pro_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE `login_info`
ADD FOREIGN KEY(`staff_id`) REFERENCES `Staff`(`staff_id`)
ON UPDATE NO ACTION ON DELETE NO ACTION;