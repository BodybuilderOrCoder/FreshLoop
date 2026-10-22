export default function Contact() {
  return (
    <section className="contact-section" id="contact">
      <div className="container">
        <span className="section-kicker">CONTACT US</span>
        <h2>Get in touch.</h2>
        <p className="contact-intro">
          Have a question or feedback about FreshLoop? We would love to hear from you.
        </p>

        <div className="contact-grid">
          <div className="contact-card">
            <h3>Our team</h3>
            <p>FreshLoop Project Team</p>
            <p>University of Information Technology — VNU-HCM</p>
          </div>

          <div className="contact-card">
            <h3>Location</h3>
            <p>Ho Chi Minh City, Vietnam</p>
          </div>

          <div className="contact-card">
            <h3>Explore our project</h3>
            <p>View our source code and project updates on GitHub.</p>
            <a
              href="https://github.com/BodybuilderOrCoder/FreshLoop"
              target="_blank"
              rel="noopener noreferrer"
            >
              Visit GitHub →
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
