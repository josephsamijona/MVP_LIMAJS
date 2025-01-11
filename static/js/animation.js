// Animation de la galaxie
const canvas = document.getElementById("galaxy");
const ctx = canvas.getContext("2d");

// Redimensionnement du canvas en plein écran
function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener("resize", resizeCanvas);

// Simulation du champ d'étoiles
const stars = Array(500).fill().map(() => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    size: Math.random() * 2,
    speed: Math.random() * 0.5 + 0.2
}));

function drawStars() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    stars.forEach(star => {
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
        ctx.fill();

        // Déplacement des étoiles
        star.y += star.speed;
        if (star.y > canvas.height) star.y = 0;
    });
}

function animate() {
    drawStars();
    requestAnimationFrame(animate);
}

animate();