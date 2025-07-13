#!/bin/bash

# RabbitMQ Setup Script for ALX Travel App
# This script helps set up RabbitMQ for Celery background tasks

echo "=========================================="
echo "RabbitMQ Setup for ALX Travel App"
echo "=========================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root"
   exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install RabbitMQ on Ubuntu/Debian
install_rabbitmq_ubuntu() {
    echo "Installing RabbitMQ on Ubuntu/Debian..."
    
    # Update package list
    sudo apt-get update
    
    # Install RabbitMQ
    sudo apt-get install -y rabbitmq-server
    
    # Start and enable RabbitMQ service
    sudo systemctl start rabbitmq-server
    sudo systemctl enable rabbitmq-server
    
    echo "✓ RabbitMQ installed and started"
}

# Function to install RabbitMQ on CentOS/RHEL
install_rabbitmq_centos() {
    echo "Installing RabbitMQ on CentOS/RHEL..."
    
    # Install EPEL repository
    sudo yum install -y epel-release
    
    # Install RabbitMQ
    sudo yum install -y rabbitmq-server
    
    # Start and enable RabbitMQ service
    sudo systemctl start rabbitmq-server
    sudo systemctl enable rabbitmq-server
    
    echo "✓ RabbitMQ installed and started"
}

# Function to install RabbitMQ on macOS
install_rabbitmq_macos() {
    echo "Installing RabbitMQ on macOS..."
    
    if ! command_exists brew; then
        echo "Homebrew is required. Please install it first:"
        echo "https://brew.sh/"
        exit 1
    fi
    
    # Install RabbitMQ
    brew install rabbitmq
    
    # Start RabbitMQ service
    brew services start rabbitmq
    
    echo "✓ RabbitMQ installed and started"
}

# Function to configure RabbitMQ
configure_rabbitmq() {
    echo "Configuring RabbitMQ..."
    
    # Enable management plugin
    sudo rabbitmq-plugins enable rabbitmq_management
    
    # Create a user (optional, for better security)
    read -p "Do you want to create a custom RabbitMQ user? (y/n): " create_user
    
    if [[ $create_user =~ ^[Yy]$ ]]; then
        read -p "Enter username for RabbitMQ: " rabbitmq_user
        read -s -p "Enter password for RabbitMQ: " rabbitmq_password
        echo
        
        # Create user
        sudo rabbitmqctl add_user "$rabbitmq_user" "$rabbitmq_password"
        sudo rabbitmqctl set_user_tags "$rabbitmq_user" administrator
        sudo rabbitmqctl set_permissions -p / "$rabbitmq_user" ".*" ".*" ".*"
        
        echo "✓ Custom user created: $rabbitmq_user"
        echo "Update your .env file with:"
        echo "CELERY_BROKER_URL=amqp://$rabbitmq_user:$rabbitmq_password@localhost:5672//"
    else
        echo "Using default guest:guest credentials"
        echo "CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//"
    fi
}

# Function to test RabbitMQ connection
test_rabbitmq() {
    echo "Testing RabbitMQ connection..."
    
    if command_exists rabbitmqctl; then
        # Check RabbitMQ status
        if sudo rabbitmqctl status >/dev/null 2>&1; then
            echo "✓ RabbitMQ is running"
            
            # Check if management plugin is enabled
            if sudo rabbitmq-plugins list | grep -q "rabbitmq_management.*enabled"; then
                echo "✓ Management plugin is enabled"
                echo "Management interface available at: http://localhost:15672"
                echo "Default credentials: guest/guest"
            else
                echo "⚠ Management plugin is not enabled"
            fi
        else
            echo "✗ RabbitMQ is not running"
            echo "Try starting it with: sudo systemctl start rabbitmq-server"
        fi
    else
        echo "✗ rabbitmqctl not found. RabbitMQ may not be installed properly."
    fi
}

# Main installation logic
main() {
    # Detect operating system
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command_exists apt-get; then
            # Ubuntu/Debian
            install_rabbitmq_ubuntu
        elif command_exists yum; then
            # CentOS/RHEL
            install_rabbitmq_centos
        else
            echo "Unsupported Linux distribution"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        install_rabbitmq_macos
    else
        echo "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    # Configure RabbitMQ
    configure_rabbitmq
    
    # Test installation
    test_rabbitmq
    
    echo ""
    echo "=========================================="
    echo "Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Update your .env file with the RabbitMQ connection URL"
    echo "2. Start your Django development server: python manage.py runserver"
    echo "3. Start Celery worker: celery -A alx_travel_app worker -l info"
    echo "4. Test the integration: python test_celery_integration.py"
    echo ""
    echo "For more information, see the README.md file."
}

# Run main function
main 