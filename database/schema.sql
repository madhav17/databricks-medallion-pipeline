-- E-commerce relational schema for the Medallion Architecture assessment.
-- Derived from src/bronze/schemas.py and generated CSV column definitions.
-- Suitable for documentation and execution in a SQL engine with DATE/DECIMAL support.

CREATE TABLE customers (
    customer_id       INTEGER      NOT NULL,
    customer_name     VARCHAR(255),
    email             VARCHAR(255),
    country           VARCHAR(100),
    signup_date       DATE,
    customer_segment  VARCHAR(20),
    lifetime_value    DECIMAL(10, 2),
    CONSTRAINT pk_customers PRIMARY KEY (customer_id),
    CONSTRAINT chk_customer_segment CHECK (
        customer_segment IS NULL
        OR customer_segment IN ('Premium', 'Standard', 'Basic')
    ),
    CONSTRAINT chk_lifetime_value CHECK (
        lifetime_value IS NULL OR lifetime_value >= 0
    )
);

CREATE TABLE products (
    product_id      INTEGER      NOT NULL,
    product_name    VARCHAR(255),
    category        VARCHAR(100),
    price           DECIMAL(10, 2),
    cost            DECIMAL(10, 2),
    stock_quantity  INTEGER,
    reorder_level   INTEGER,
    CONSTRAINT pk_products PRIMARY KEY (product_id),
    CONSTRAINT chk_price CHECK (price IS NULL OR price >= 0),
    CONSTRAINT chk_cost CHECK (cost IS NULL OR cost >= 0),
    CONSTRAINT chk_stock_quantity CHECK (stock_quantity IS NULL OR stock_quantity >= 0),
    CONSTRAINT chk_reorder_level CHECK (reorder_level IS NULL OR reorder_level >= 0)
);

CREATE TABLE orders (
    order_id       INTEGER      NOT NULL,
    customer_id    INTEGER,
    order_date     DATE,
    product_id     INTEGER,
    quantity       INTEGER,
    unit_price     DECIMAL(10, 2),
    total_amount   DECIMAL(10, 2),
    order_status   VARCHAR(20),
    payment_date   DATE,
    CONSTRAINT pk_orders PRIMARY KEY (order_id),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
        REFERENCES customers (customer_id),
    CONSTRAINT fk_orders_product FOREIGN KEY (product_id)
        REFERENCES products (product_id),
    CONSTRAINT chk_order_status CHECK (
        order_status IS NULL
        OR order_status IN ('Pending', 'Completed', 'Cancelled')
    ),
    CONSTRAINT chk_quantity CHECK (quantity IS NULL OR quantity > 0),
    CONSTRAINT chk_unit_price CHECK (unit_price IS NULL OR unit_price >= 0)
);

-- Note: The assessment source CSV intentionally contains rows that violate
-- completeness, uniqueness, referential integrity, and (when injected)
-- business-logic constraints. Silver preserves those rows and flags them
-- instead of enforcing these constraints at load time.
