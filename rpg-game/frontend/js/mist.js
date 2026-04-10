/**
 * Magic mist particle effect — creates floating arcane fog particles
 */
export function initMist(count = 12) {
  for (let i = 0; i < count; i++) {
    spawnParticle();
  }
}

function spawnParticle() {
  const el = document.createElement('div');
  el.className = 'mist-particle';

  const size = 60 + Math.random() * 140;
  const x = Math.random() * 100;
  const duration = 14 + Math.random() * 20;
  const delay = -(Math.random() * duration); // start mid-animation

  el.style.cssText = `
    width: ${size}px;
    height: ${size}px;
    left: ${x}%;
    bottom: ${-size}px;
    animation-duration: ${duration}s;
    animation-delay: ${delay}s;
    opacity: ${0.3 + Math.random() * 0.4};
  `;

  document.body.appendChild(el);

  // Respawn after animation ends
  el.addEventListener('animationiteration', () => {
    el.style.left = `${Math.random() * 100}%`;
    const newSize = 60 + Math.random() * 140;
    el.style.width = `${newSize}px`;
    el.style.height = `${newSize}px`;
  });
}
