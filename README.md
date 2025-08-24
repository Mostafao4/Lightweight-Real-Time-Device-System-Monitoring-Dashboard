# Lightweight Real-Time Device System Monitoring Dashboard

A lightweight, real-time monitoring solution for tracking the status of network devices and services. Built with Python and Flask, this application provides a clean web interface for monitoring ICMP (ping), HTTP, and TCP endpoints.

## Features

- **Multi-Protocol Monitoring**
  - ICMP (ping) checks
  - HTTP/HTTPS endpoint monitoring
  - TCP port checking
  - Response time tracking
  - Status classification (up/down/degraded)

- **Real-Time Dashboard**
  - Live status updates
  - Response time graphs
  - Historical data view
  - Device management interface

- **Alert System**
  - Telegram notifications
  - Email alerts
  - Configurable thresholds
  - Status change notifications

## Technologies

- **Backend**
  - Python 3.10+
  - Flask (Web Framework)
  - SQLAlchemy (Database ORM)
  - Flask-Login (Authentication)
  - SQLite (Database)

- **Frontend**
  - HTML5/CSS3
  - JavaScript
  - Chart.js (Graphs)
  - Bootstrap (Styling)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Lightweight-Real-Time-Device-System-Monitoring-Dashboard.git
cd Lightweight-Real-Time-Device-System-Monitoring-Dashboard
```

2. Create and activate virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables in `.env`:
```
FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URL=sqlite:///instance/monitor.db
SECRET_KEY=your-secret-key
TELEGRAM_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Usage

1. Start the web server:
```bash
python run.py
```

2. Start the monitoring service:
```bash
python monitor.py
```

3. Access the dashboard at `http://localhost:5000`

## Configuration

### Device Monitoring
- **Check Interval**: Configurable in seconds (default: 30)
- **Timeout Settings**:
  - PING: 1000ms
  - HTTP: 3s
  - TCP: 2s
- **Degraded Threshold**: 800ms for HTTP checks

### Alert Settings
- Configure SMTP settings for email alerts
- Set up Telegram bot token and chat ID
- Enable/disable recovery notifications

## Development

1. Run tests:
```bash
python -m pytest
```

2. Code style checks:
```bash
flake8 .
```

## Directory Structure

```
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── static/
│   └── templates/
├── instance/
├── tests/
├── .env
├── monitor.py
├── run.py
└── requirements.txt
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


## Acknowledgments

- Flask documentation and community
- Python requests library
- SQLAlchemy team

