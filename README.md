# ALX Travel App - Background Task Management with Celery

This project implements background task management using Celery with RabbitMQ as the message broker, along with email notifications for bookings.

## Features

- **Background Task Management**: Celery configured with RabbitMQ for asynchronous task processing
- **Email Notifications**: Automatic booking confirmation emails sent asynchronously
- **Payment Integration**: Chapa payment gateway integration with email confirmations
- **RESTful API**: Django REST Framework with comprehensive endpoints
- **User Authentication**: Secure user management and booking system

## Prerequisites

- Python 3.8+
- MySQL Database
- RabbitMQ Server
- Virtual Environment

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd alx_travel_app_0x03
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root with the following variables:
   ```env
   # Database Configuration
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=localhost
   DB_PORT=3306

   # Celery Configuration
   CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
   CELERY_RESULT_BACKEND=rpc://

   # Email Configuration
   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
   EMAIL_HOST=localhost
   EMAIL_PORT=1025
   EMAIL_USE_TLS=False
   EMAIL_HOST_USER=
   EMAIL_HOST_PASSWORD=
   DEFAULT_FROM_EMAIL=noreply@alxtravel.com

   # Chapa API Configuration
   CHAPA_SECRET_KEY=your_chapa_secret_key
   CHAPA_BASE_URL=https://api.chapa.co/v1
   ```

5. **Set up RabbitMQ**
   ```bash
   # Install RabbitMQ (Ubuntu/Debian)
   sudo apt-get install rabbitmq-server
   
   # Start RabbitMQ service
   sudo systemctl start rabbitmq-server
   sudo systemctl enable rabbitmq-server
   
   # Create a user (optional, default guest:guest works for development)
   sudo rabbitmqctl add_user myuser mypassword
   sudo rabbitmqctl set_user_tags myuser administrator
   sudo rabbitmqctl set_permissions -p / myuser ".*" ".*" ".*"
   ```

6. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

## Running the Application

### 1. Start Django Development Server
```bash
python manage.py runserver
```

### 2. Start Celery Worker
In a new terminal:
```bash
celery -A alx_travel_app worker -l info
```

### 3. Start Celery Beat (for scheduled tasks)
In another terminal:
```bash
celery -A alx_travel_app beat -l info
```

### 4. Start RabbitMQ (if not running)
```bash
sudo systemctl start rabbitmq-server
```

## Background Task Management

### Celery Configuration

The project is configured with Celery using RabbitMQ as the message broker:

- **Broker**: RabbitMQ (`amqp://guest:guest@localhost:5672//`)
- **Result Backend**: RPC (`rpc://`)
- **Task Serializer**: JSON
- **Result Serializer**: JSON

### Available Tasks

The following background tasks are implemented in `listings/tasks.py`:

1. **`send_booking_confirmation_email(booking_id)`**
   - Sends booking confirmation email to user
   - Triggered automatically when a booking is created

2. **`send_payment_confirmation_email(payment_id)`**
   - Sends payment confirmation email to user
   - Triggered when payment status is updated to 'completed'

3. **`send_payment_failed_email(payment_id)`**
   - Sends payment failed notification email to user
   - Triggered when payment status is updated to 'failed'

4. **`update_payment_status(payment_id)`**
   - Updates payment status by verifying with Chapa API
   - Can be scheduled or triggered manually

5. **`cleanup_expired_payments()`**
   - Cleans up payments that have been pending for too long
   - Scheduled task to run periodically

### Email Templates

Email templates are located in `listings/templates/listings/email/`:
- `booking_confirmation.html` - Booking confirmation email
- `payment_confirmation.html` - Payment confirmation email
- `payment_failed.html` - Payment failed notification email

## Testing Background Tasks

### 1. Test Email Task Manually

Create a booking through the API and check the console output for email messages (since we're using console backend for development).

### 2. Test Celery Worker

```bash
# Start the worker
celery -A alx_travel_app worker -l info

# In another terminal, test the debug task
python manage.py shell
```

```python
from alx_travel_app.celery import debug_task
result = debug_task.delay()
print(result.id)
```

### 3. Test Booking Email Task

```python
from listings.tasks import send_booking_confirmation_email
# Assuming you have a booking with ID 1
send_booking_confirmation_email.delay(1)
```

### 4. Monitor Task Execution

You can monitor task execution in the Celery worker terminal. Tasks will show:
- Task received
- Task started
- Task succeeded/failed
- Any errors or exceptions

## API Endpoints

### Listings
- `GET /api/listings/` - List all listings
- `GET /api/listings/{id}/` - Get listing details
- `POST /api/listings/` - Create new listing (authenticated)
- `PUT /api/listings/{id}/` - Update listing (authenticated)
- `DELETE /api/listings/{id}/` - Delete listing (authenticated)

### Bookings
- `GET /api/bookings/` - List user's bookings (authenticated)
- `POST /api/bookings/` - Create new booking (authenticated)
- `GET /api/bookings/{id}/` - Get booking details (authenticated)
- `PUT /api/bookings/{id}/` - Update booking (authenticated)
- `DELETE /api/bookings/{id}/` - Cancel booking (authenticated)

### Payments
- `GET /api/payments/` - List user's payments (authenticated)
- `POST /api/payments/` - Create new payment (authenticated)
- `POST /api/payments/{id}/initiate_payment/` - Initiate payment with Chapa
- `POST /api/payments/{id}/verify_payment/` - Verify payment status

### Reviews
- `GET /api/reviews/` - List all reviews
- `POST /api/reviews/` - Create new review (authenticated)
- `GET /api/reviews/{id}/` - Get review details
- `PUT /api/reviews/{id}/` - Update review (authenticated)
- `DELETE /api/reviews/{id}/` - Delete review (authenticated)

## Email Configuration

For production, update the email settings in `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

## Troubleshooting

### Common Issues

1. **RabbitMQ Connection Error**
   - Ensure RabbitMQ is running: `sudo systemctl status rabbitmq-server`
   - Check if port 5672 is accessible
   - Verify credentials in CELERY_BROKER_URL

2. **Celery Worker Not Starting**
   - Check if Django settings are properly configured
   - Ensure all dependencies are installed
   - Verify the Celery app is imported in `__init__.py`

3. **Tasks Not Executing**
   - Check if the worker is running and connected to the broker
   - Verify task registration with `celery -A alx_travel_app inspect active`
   - Check task logs for errors

4. **Email Not Sending**
   - Verify email configuration in settings
   - Check if email backend is properly configured
   - For console backend, check terminal output

### Useful Commands

```bash
# Check Celery worker status
celery -A alx_travel_app inspect active

# Check registered tasks
celery -A alx_travel_app inspect registered

# Monitor Celery events
celery -A alx_travel_app events

# Check RabbitMQ status
sudo rabbitmqctl status

# List RabbitMQ queues
sudo rabbitmqctl list_queues
```

## Development

### Adding New Tasks

1. Create the task function in `listings/tasks.py`:
```python
@shared_task
def my_new_task(param1, param2):
    # Task logic here
    pass
```

2. Import and call the task:
```python
from .tasks import my_new_task
my_new_task.delay(param1, param2)
```

### Scheduled Tasks

To add scheduled tasks, update `celery.py`:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'cleanup-expired-payments': {
        'task': 'listings.tasks.cleanup_expired_payments',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
}
```

## License

This project is part of the ALX Software Engineering program.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
