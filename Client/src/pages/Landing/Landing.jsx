import React from "react";
import { useNavigate } from "react-router-dom";
import {
  FaRobot,
  FaShieldAlt,
  FaClock,
  FaMobileAlt,
  FaFacebook,
  FaTwitter,
  FaLinkedin,
  FaInstagram,
  FaMapMarkerAlt,
  FaPhone,
  FaEnvelope,
} from "react-icons/fa";

const Landing = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <FaRobot />,
      title: "AI-Powered Chatbot",
      description:
        "Get instant answers to your challan queries with our intelligent chatbot assistant.",
    },
    {
      icon: <FaShieldAlt />,
      title: "Secure & Reliable",
      description:
        "Your data is protected with state-of-the-art security measures and encryption.",
    },
    {
      icon: <FaClock />,
      title: "24/7 Availability",
      description:
        "Access challan information anytime, anywhere, without waiting for office hours.",
    },
    {
      icon: <FaMobileAlt />,
      title: "Easy to Use",
      description:
        "Simple and intuitive interface designed for seamless user experience.",
    },
  ];

  return (
    <>
      {/* ================= CSS ================= */}
      <style>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
          font-family: Inter, system-ui, -apple-system;
        }

        body {
          background: #fbf6ee;
          color: #2b2b2b;
        }

        /* GLOBAL CONTAINER (🔥 MOST IMPORTANT FIX) */
        .container {
          max-width: 1280px;
          margin: 0 auto;
          width: 100%;
          padding: 0 24px;
        }

        /* PAGE STRUCTURE */
        .landing-page {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }

        /* Ensure content grows and footer stays at bottom */
        main {
          flex: 1;
        }


        /* HEADER */
        header {
          padding: 12px 0;
        }

        .header-inner {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .logo {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .logo img {
          height: 40px;
          width: auto;
        }

        .logo-text {
          display: flex;
          flex-direction: column;
        }

        .logo small {
          font-size: 12px;
          font-weight: 600;
        }

        .logo h1 {
          font-size: 26px;
          font-weight: 600;
        }

        .logo p {
          color: #555;
        }

        .login-btn {
          background: #d9823c;
          color: #fff;
          border: none;
          padding: 10px 22px;
          border-radius: 999px;
          cursor: pointer;
        }

        /* HERO */
        .hero {
          padding: 40px 0 40px;
        }

        .hero-grid {
          display: grid;
          grid-template-columns: 1.3fr 0.7fr;
          gap: clamp(40px, 6vw, 80px);
          align-items: center;
        }

        .hero h2 {
          font-size: 36px;
          margin-bottom: 16px;
        }

        .hero p {
          max-width: 640px;
          line-height: 1.6;
          margin-bottom: 28px;
          color: #444;
        }

        .hero-actions {
          display: flex;
          gap: 14px;
        }

        .btn {
          background: #1f1f1f;
          color: #fff;
          border: none;
          padding: 10px 22px;
          border-radius: 10px;
          cursor: pointer;
        }

        .chatbox {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        /* FEATURES */
        .features {
          padding: 40px 0 60px;
        }

        .features h3 {
          font-size: 24px;
          margin-bottom: 36px;
        }

        .features-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: 40px;
        }

        .feature {
          max-width: 280px;
        }

        .feature h4 {
          margin: 10px 0;
        }

        .feature p {
          font-size: 14px;
          color: #555;
          line-height: 1.5;
        }

        /* FOOTER */
        footer {
          background: #2b2b2b;
          color: #ccc;
          margin-top: auto;
        }

        .footer-top {
          padding: 48px 0;
          display: grid;
          grid-template-columns: 1.5fr 1fr 1fr;
          gap: 48px;
        }

        .footer-section-first {
          padding-left: 40px;
        }

        footer h4 {
          color: #fff;
          margin-bottom: 14px;
        }

        footer a {
          color: #aaa;
          text-decoration: none;
          display: block;
          margin-bottom: 8px;
        }

        .social {
          display: flex;
          gap: 14px;
          margin-top: 14px;
        }

        .footer-bottom {
          border-top: 1px solid #444;
          padding: 16px 0;
          text-align: center;
          font-size: 14px;
          color: #888;
        }

        /* RESPONSIVE */
        @media (max-width: 900px) {
          .container {
            padding: 0 16px;
          }

          header {
            padding: 16px 0;
          }

          .logo img {
            height: 45px;
          }

          .logo h1 {
            font-size: 24px;
          }

          .logo p {
            font-size: 12px;
          }

          .logo small {
            font-size: 10px;
          }

          .login-btn {
            padding: 8px 16px;
            font-size: 13px;
          }

          .hero {
            padding: 32px 0 32px;
          }

          .hero-grid {
            grid-template-columns: 1fr;
            gap: 32px;
          }

          .hero h2 {
            font-size: 28px;
          }

          .hero p {
            font-size: 15px;
          }

          .hero-actions {
            flex-direction: column;
          }

          .btn {
            width: 100%;
            text-align: center;
          }

          .features {
            padding: 32px 0 48px;
          }

          .features h3 {
            font-size: 20px;
            margin-bottom: 24px;
          }

          .features-grid {
            grid-template-columns: 1fr;
            gap: 28px;
          }

          .feature {
            max-width: 100%;
          }

          .footer-top {
            grid-template-columns: 1fr;
            gap: 32px;
            padding: 32px 0;
          }

          .footer-bottom {
            font-size: 13px;
          }
        }

        @media (max-width: 480px) {
          .logo {
            gap: 12px;
          }

          .logo img {
            height: 40px;
          }

          .logo h1 {
            font-size: 20px;
          }

          .logo p {
            font-size: 11px;
          }

          .hero h2 {
            font-size: 24px;
          }

          .hero p {
            font-size: 14px;
          }

          .btn {
            padding: 8px 18px;
            font-size: 13px;
          }
        }
      `}</style>

      {/* ================= JSX ================= */}
      <div className="landing-page">
        {/* HEADER */}
        <header>
          <div className="container header-inner">
            <div className="logo">
              <img src="/image/main_logo.png" alt="IMC Logo" />
              <div className="logo-text">
                <small>IMC</small>
                <h1>Smart City Indore</h1>
                <p>Challan Management System</p>
              </div>
            </div>
            <button className="login-btn" onClick={() => navigate("/login")}>
              Login
            </button>
          </div>
        </header>

        {/* HERO */}
        <section className="hero">
          <div className="container hero-grid">
            <div>
              <h2>
                Welcome to Indore <br /> Smart Challan System
              </h2>
              <p>
                Your intelligent assistant for managing traffic challans,
                checking violations, and staying updated with Indore’s smart
                city initiatives.
              </p>
              <div className="hero-actions">
                <button className="btn" onClick={() => navigate("/login")}>
                  Get Started
                </button>
               
              </div>
            </div>

            <div className="chatbox">
              <FaRobot />
              <h4>AI Chatbot Assistant</h4>
              <p>Smart, Fast, and Always Ready to Help</p>
            </div>
          </div>
        </section>

        {/* FEATURES */}
        <section className="features">
          <div className="container">
            <h3>Why Choose Us?</h3>
            <div className="features-grid">
              {features.map((f, i) => (
                <div key={i} className="feature">
                  {f.icon}
                  <h4>{f.title}</h4>
                  <p>{f.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* FOOTER */}
        <footer>
          <div className="container footer-top">
            <div className="footer-section-first">
              <h4>IMC Smart City Indore</h4>
              <p>
                Empowering citizens with smart solutions for traffic challan
                management.
              </p>
              <div className="social">
                <FaFacebook />
                <FaTwitter />
                <FaInstagram />
                <FaLinkedin />
              </div>
            </div>

            <div>
              <h4>Quick Links</h4>
              <a href="">About</a>
              <a href="">Services</a>
              <a href="">FAQ</a>
              <a href="">Privacy</a>
            </div>

            <div>
              <h4>Contact</h4>
              <p><FaMapMarkerAlt /> Indore, MP</p>
              <p><FaPhone /> +91 123 456 7890</p>
              <p><FaEnvelope /> support@imcindore.gov.in</p>
            </div>
          </div>

          <div className="footer-bottom">
            © 2025 IMC Smart City Indore. All rights reserved.
          </div>
        </footer>
      </div>
    </>
  );
};

export default Landing;
