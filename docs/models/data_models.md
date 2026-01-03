# Data Models Overview for Laundry Management System

## CRM Module
- **Customer**
  - Attributes:
    - `id`: Unique identifier for the customer
    - `name`: Name of the customer
    - `email`: Email address of the customer
    - `phone`: Phone number of the customer
    - `created_at`: Timestamp of when the customer was created
- **Contact**
  - Attributes:
    - `id`: Unique identifier for the contact
    - `customer_id`: Foreign key linking to the Customer
    - `contact_type`: Type of contact (e.g., phone, email)
    - `value`: Value of the contact (e.g., actual phone number or email)
- **Interaction**
  - Attributes:
    - `id`: Unique identifier for the interaction
    - `customer_id`: Foreign key linking to the Customer
    - `date`: Date of the interaction
    - `notes`: Notes regarding the interaction

## Order Module
- **Order**
  - Attributes:
    - `id`: Unique identifier for the order
    - `customer_id`: Foreign key linking to the Customer
    - `status`: Current status of the order
    - `created_at`: Timestamp of when the order was created
- **OrderItem**
  - Attributes:
    - `id`: Unique identifier for the order item
    - `order_id`: Foreign key linking to the Order
    - `service`: Type of service requested
    - `quantity`: Quantity of the service
- **OrderStatus**
  - Attributes:
    - `id`: Unique identifier for the order status
    - `status`: Description of the status (e.g., pending, completed)

## Pickup Module
- **PickupTask**
  - Attributes:
    - `id`: Unique identifier for the pickup task
    - `order_id`: Foreign key linking to the Order
    - `scheduled_time`: Scheduled time for the pickup
    - `status`: Current status of the pickup task
- **PickupAgent**
  - Attributes:
    - `id`: Unique identifier for the pickup agent
    - `name`: Name of the agent
    - `contact_info`: Contact information for the agent

## Delivery Module
- **DeliveryTask**
  - Attributes:
    - `id`: Unique identifier for the delivery task
    - `order_id`: Foreign key linking to the Order
    - `scheduled_time`: Scheduled time for the delivery
    - `status`: Current status of the delivery task
- **DeliveryAgent**
  - Attributes:
    - `id`: Unique identifier for the delivery agent
    - `name`: Name of the agent
    - `contact_info`: Contact information for the agent

## Processing Module
- **ProcessingStage**
  - Attributes:
    - `id`: Unique identifier for the processing stage
    - `order_id`: Foreign key linking to the Order
    - `stage_name`: Name of the processing stage
    - `status`: Current status of the processing stage
- **ProcessingItem**
  - Attributes:
    - `id`: Unique identifier for the processing item
    - `processing_stage_id`: Foreign key linking to the ProcessingStage
    - `description`: Description of the item being processed

## Inventory Module
- **StockItem**
  - Attributes:
    - `id`: Unique identifier for the stock item
    - `name`: Name of the stock item
    - `quantity`: Current quantity in stock
    - `reorder_level`: Level at which stock should be reordered
- **StockMovement**
  - Attributes:
    - `id`: Unique identifier for the stock movement
    - `stock_item_id`: Foreign key linking to the StockItem
    - `movement_type`: Type of movement (e.g., addition, subtraction)
    - `quantity`: Quantity moved
    - `date`: Date of the movement

## Sales Module
- **Invoice**
  - Attributes:
    - `id`: Unique identifier for the invoice
    - `order_id`: Foreign key linking to the Order
    - `amount`: Total amount of the invoice
    - `date`: Date of the invoice
- **Payment**
  - Attributes:
    - `id`: Unique identifier for the payment
    - `invoice_id`: Foreign key linking to the Invoice
    - `amount`: Amount paid
    - `payment_date`: Date of the payment
    - `payment_method`: Method of payment (e.g., credit card, cash)