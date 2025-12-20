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

        .container {
          max-width: 1280px;
          margin: 0 auto;
          padding: 0 24px;
          width: 100%;
        }

        .landing-page {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }

        main {
          flex: 1;
        }

        /* ================= HEADER ================= */
        header {
          padding: 16px 0;
        }

        .header-inner {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .logo {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .logo img {
          height: 42px;
        }

        .logo-text small {
          font-size: 12px;
          font-weight: 600;
        }

        .logo-text h1 {
          font-size: 24px;
          font-weight: 600;
        }

        .logo-text p {
          font-size: 13px;
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

        /* ================= HERO ================= */
        .hero {
          padding: 48px 0;
        }

        .hero-grid {
          display: grid;
          grid-template-columns: 1.3fr 0.7fr;
          gap: 64px;
          align-items: center;
        }

        .hero-left {
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          text-align: center;
        }

        .hero h2 {
          font-size: 36px;
          margin-bottom: 16px;
        }

        .hero p {
          max-width: 620px;
          line-height: 1.6;
          margin-bottom: 28px;
          color: #444;
          margin-left: auto;
          margin-right: auto;
        }

        .hero-actions {
          display: flex;
          gap: 14px;
          justify-content: center;
        }

        .btn {
          background: #1f1f1f;
          color: #fff;
          border: none;
          padding: 10px 22px;
          border-radius: 10px;
          cursor: pointer;
        }

        /* CHATBOX */
        .chatbox {
          background: #fff;
          border-radius: 18px;
          padding: 32px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.08);
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
        }

        .chatbox svg {
          font-size: 48px;
        }

        .chatbox h4 {
          font-size: 18px;
        }

        .chatbox p {
          font-size: 14px;
          color: #555;
        }

        /* ================= FEATURES ================= */
        .features {
          padding: 56px 0;
        }

        .features h3 {
          font-size: 24px;
          margin-bottom: 36px;
          text-align: center;
        }

        .features-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: 32px;
        }

        .feature {
          background: #fff;
          padding: 26px;
          border-radius: 18px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.06);
          text-align: center;
        }

        .feature svg {
          font-size: 32px;
          margin-bottom: 12px;
        }

        .feature h4 {
          margin-bottom: 8px;
        }

        .feature p {
          font-size: 14px;
          color: #555;
          line-height: 1.5;
        }

        /* ================= ABOUT US ================= */
        .about-us {
          padding: 64px 0;
          background: #fff;
        }

        .about-content {
          max-width: 900px;
          margin: 0 auto;
          text-align: center;
        }

        .about-us h3 {
          font-size: 32px;
          margin-bottom: 24px;
          color: #2b2b2b;
        }

        .about-us p {
          font-size: 16px;
          line-height: 1.8;
          color: #444;
          margin-bottom: 20px;
        }

        .about-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 32px;
          margin-top: 48px;
        }

        .stat-card {
          background: #fbf6ee;
          padding: 28px;
          border-radius: 16px;
          text-align: center;
        }

        .stat-card h4 {
          font-size: 36px;
          color: #d9823c;
          margin-bottom: 8px;
        }

        .stat-card p {
          font-size: 14px;
          color: #555;
          margin: 0;
        }

        /* ================= FOOTER ================= */
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

        footer p {
          display: flex;
          align-items: center;
          gap: 8px;
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

        /* ================= RESPONSIVE ================= */
        @media (max-width: 900px) {
          .hero-grid {
            grid-template-columns: 1fr;
            gap: 36px;
          }

          .hero h2 {
            font-size: 28px;
          }

          .hero-actions {
            flex-direction: column;
          }

          .btn {
            width: 100%;
          }

          .chatbox {
            max-width: 360px;
            margin: 0 auto;
          }

          .footer-top {
            grid-template-columns: 1fr;
            gap: 32px;
          }
        }

        @media (max-width: 480px) {
          .hero h2 {
            font-size: 24px;
          }
        }
      `}</style>

      {/* ================= JSX ================= */}
      <div className="landing-page">
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

        <section className="hero">
          <div className="container h">
            <div className="hero-left">
              <h2>
                Welcome to Indore  Smart Challan System
              </h2>
              <p>
                Your intelligent assistant for managing traffic challans,
                checking violations, and staying updated with Indore’s smart city
                initiatives.
              </p>
              <div className="hero-actions">
                <button className="btn" onClick={() => navigate("/login")}>
                  Get Started
                </button>
              </div>
            </div>

           
          </div>
        </section>

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

        <section className="about-us">
          <div className="container">
            <div className="about-content">
              <h3>About IMC Smart City Indore</h3>
              <p>
                Indore Municipal Corporation is committed to transforming Indore
                into a world-class smart city. Our Smart Challan Management System
                is a step towards digitization and transparency in traffic
                enforcement.
              </p>
              <p>
                We leverage cutting-edge AI technology to provide citizens with
                instant access to challan information, payment options, and
                real-time assistance through our intelligent chatbot.
              </p>

              
            
            </div>
          </div>
        </section>

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
              <a href="#">About</a>
              <a href="#">Services</a>
              <a href="#">FAQ</a>
              <a href="#">Privacy</a>
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
