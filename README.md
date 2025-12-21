# Indore Smart City Challan Chatbot

A modern, AI-powered chatbot application for managing and querying traffic challans in Indore Smart City. Built with React (Frontend) and FastAPI (Backend).

## 🚀 Features

- **AI-Powered Chatbot**: Intelligent conversation interface for challan queries
- **User Authentication**: Secure login and signup with MPIN verification
- **Profile Management**: User profile with personalized settings
- **Theme Support**: Light and dark mode toggle
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-time Messaging**: Interactive chat interface with message history

## 📁 Project Structure

```
Indore-Smart-City-Challan-Chatbot/
├── Client/                 # React Frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── context/       # React context providers
│   │   ├── hooks/         # Custom React hooks
│   │   ├── services/      # API service layer
│   │   └── config/        # Configuration files
│   └── package.json
│
└── Server/                # FastAPI Backend
    ├── modules/
    │   ├── Agent/        # Agent module
    │   └── Auth/         # Authentication module
    ├── database/         # Database models
    ├── utills/          # Utility functions
    ├── main.py          # FastAPI application
    └── requirements.txt
```

## 🛠️ Tech Stack

### Frontend
- **React** - UI library
- **Vite** - Build tool and dev server

### Backend
- **FastAPI** - Modern Python web framework
- **Python 3.x** - Programming language
- **SQLAlchemy** - ORM 
- **Docker** - Containerization

## 📋 Prerequisites
- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **Docker** (optional, for containerized deployment)
- **npm** or **yarn**

## 🚀 Getting Started

### Frontend Setup

1. Navigate to the Client directory:
```bash
cd Client
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Backend Setup

1. Navigate to the Server directory:
```bash
cd Server
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the FastAPI server:
```bash
uvicorn main:app --reload
```

The backend will be available at `http://localhost:8080`

### Docker Setup

Build and run the backend using Docker:

```bash
cd Server
docker build -t imc-server .
docker run -p 8000:8000 imc-server
```

## 🔧 Configuration

### Frontend Configuration
- Update API endpoints in `Client/src/config/constants.js`
- Customize theme variables in `Client/src/styles/variables.css`

### Backend Configuration
- Configure environment variables for database connection
- Set up email credentials for OTP/verification
- Configure authentication secrets

## 📚 API Documentation

Once the backend is running, access the interactive API documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔐 Authentication Flow

1. User signs up with required details
2. MPIN verification for secure access
3. Login with credentials
4. Session management with JWT/tokens

## 🎨 Key Components

### Frontend Components
- **ChatInput**: Message input with send functionality
- **MessageDisplay**: Chat message rendering
- **ProfileSection**: User profile display
- **SignUpModal**: User registration interface
- **MPINModal**: MPIN verification
- **Sidebar**: Navigation and menu

### Backend Modules
- **Auth**: User authentication and authorization
- **Agent**: AI chatbot logic and responses
- **Database**: Data models and persistence

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is part of the Indore Smart City initiative.

## 👥 Authors

- Development Team - Indore Smart City Project

## 📞 Support

For support and queries, please contact the Indore Smart City development team.

## 🙏 Acknowledgments

- Indore Municipal Corporation
- Smart City Mission
- All contributors and developers

---

**Note**: Make sure to configure all environment variables and secrets before deploying to production.
