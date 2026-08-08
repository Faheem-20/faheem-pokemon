const particles = document.getElementById("particles");

if (particles) {
  for (let i = 0; i < 80; i++) {
    const s = document.createElement("span");
    s.className = "spark";
    s.style.left = Math.random() * 100 + "vw";
    s.style.animationDuration = (4 + Math.random() * 7) + "s";
    s.style.animationDelay = Math.random() * 5 + "s";
    s.style.opacity = 0.25 + Math.random() * 0.7;
    particles.appendChild(s);
  }
}

const cards = document.querySelectorAll(".card h3");
cards.forEach((card) => {
  const text = card.textContent;
  card.dataset.original = text;
});
