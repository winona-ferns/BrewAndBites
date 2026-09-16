CREATE DATABASE IF NOT EXISTS brew_bites;

USE brew_bites;


-- 1. Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL
);


-- 2. Menu items table
CREATE TABLE menu_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock INT DEFAULT 0,
    low_stock_limit INT DEFAULT 5,
    available BOOLEAN DEFAULT TRUE
);


-- 3. Customers table
CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100),
    loyalty_points INT DEFAULT 0
);


-- 4. Orders table
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    subtotal DECIMAL(10,2) NOT NULL,
    gst DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    status VARCHAR(30) DEFAULT 'Pending',

    FOREIGN KEY (customer_id)
        REFERENCES customers(id)
        ON DELETE SET NULL
);


-- 5. Order items table
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    menu_item_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,

    FOREIGN KEY (order_id)
        REFERENCES orders(id)
        ON DELETE CASCADE,

    FOREIGN KEY (menu_item_id)
        REFERENCES menu_items(id)
);


-- 6. Combos table
CREATE TABLE combos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    combo_price DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    available BOOLEAN DEFAULT TRUE
);


-- 7. Combo items table
CREATE TABLE combo_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    combo_id INT NOT NULL,
    menu_item_id INT NOT NULL,
    quantity INT DEFAULT 1,

    FOREIGN KEY (combo_id)
        REFERENCES combos(id)
        ON DELETE CASCADE,

    FOREIGN KEY (menu_item_id)
        REFERENCES menu_items(id)
        ON DELETE CASCADE
);


-- 8. Waste records table
CREATE TABLE waste_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    menu_item_id INT NOT NULL,
    quantity INT NOT NULL,
    reason VARCHAR(255),
    estimated_loss DECIMAL(10,2) DEFAULT 0,
    waste_date DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (menu_item_id)
        REFERENCES menu_items(id)
);


-- 9. Loyalty transactions table
CREATE TABLE loyalty_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    points INT NOT NULL,
    description VARCHAR(255),
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (customer_id)
        REFERENCES customers(id)
        ON DELETE CASCADE
);