# Laundry Management System

## Overview
The Laundry Management System is a modern web application designed to streamline the operations of a laundry service. It consists of a backend built with Flask and a frontend developed using React. The system includes various modules such as CRM, Order Management, Pickup, Delivery, Processing, Inventory, and Sales.

## Project Structure
The project is organized into two main directories: `backend` and `frontend`.

### Backend
- **app**: Contains the core application logic and modules.
  - **crm**: Manages customer relationships.
  - **order**: Handles order processing.
  - **pickup**: Manages pickup tasks and agents.
  - **delivery**: Handles delivery tasks and agents.
  - **processing**: Manages the processing of laundry items.
  - **inventory**: Handles stock management.
  - **sales**: Manages sales transactions and invoicing.
  - **models**: Contains shared data models.
- **config.py**: Configuration settings for the Flask application.
- **requirements.txt**: Lists the dependencies required for the backend.
- **run.py**: Entry point for running the Flask application.

### Frontend
- **public**: Contains static files, including the main HTML file.
- **src**: Contains the React application source code.
  - **components**: Contains React components for each module.
  - **services**: Contains API service functions for backend communication.
- **package.json**: Configuration file for npm, listing dependencies and scripts.
- **README.md**: Documentation for the frontend application.

## Setup Instructions

### Backend
1. Navigate to the `backend` directory.
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python run.py
   ```

### Frontend
1. Navigate to the `frontend` directory.
2. Install the required dependencies:
   ```
   npm install
   ```
3. Start the React application:
   ```
   npm start
   ```

## Features
- **CRM**: Manage customer information and interactions.
- **Order Management**: Create and track orders.
- **Pickup and Delivery**: Manage pickup and delivery tasks.
- **Processing**: Track the processing stages of laundry items.
- **Inventory Management**: Manage stock items and movements.
- **Sales**: Handle invoicing and payment tracking.

## Documentation
For detailed documentation on application flows and data models, refer to the `docs` directory:
- Flows: `docs/flows/process_flows.md`
- Data Models: `docs/models/data_models.md`

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.