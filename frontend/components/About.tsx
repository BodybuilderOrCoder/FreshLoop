export default function About() {
  return (
    <section className="about-section container" id="about">
      <span className="section-kicker">ABOUT FRESHLOOP</span>
      <h2>Fresh groceries. Smarter routines.</h2>

      <p>
        FreshLoop is a student-built grocery platform designed to connect households with
        nearby mini-marts in Ho Chi Minh City. Our goal is to make everyday grocery
        shopping simpler with up-to-date stock information and personalized reorder
        suggestions.
      </p>

      <div className="steps">
        <div>
          <span>01</span>
          <h3>Local convenience</h3>
          <p>Discover everyday essentials from stores in your neighborhood.</p>
        </div>

        <div>
          <span>02</span>
          <h3>Inventory visibility</h3>
          <p>
            We aim to help shoppers check availability and help stores keep their stock
            information up to date.
          </p>
        </div>

        <div>
          <span>03</span>
          <h3>Personalized shopping</h3>
          <p>
            Quick Reorder is designed to suggest familiar essentials based on purchase
            history.
          </p>
        </div>
      </div>
    </section>
  );
}
