import confetti from 'canvas-confetti';

export function fireSuccessConfetti() {
  confetti({
    particleCount: 80,
    spread: 70,
    origin: { y: 0.6 },
    colors: ['#3b82f6', '#f59e0b', '#10b981', '#8b5cf6'],
    ticks: 120,
    gravity: 1.2,
    scalar: 0.9,
  });
}

export function fireUpgradeConfetti(): () => void {
  const end = Date.now() + 600;
  let cancelled = false;
  const frame = () => {
    if (cancelled) return;
    confetti({
      particleCount: 3,
      angle: 60,
      spread: 55,
      origin: { x: 0 },
      colors: ['#3b82f6', '#f59e0b'],
    });
    confetti({
      particleCount: 3,
      angle: 120,
      spread: 55,
      origin: { x: 1 },
      colors: ['#10b981', '#8b5cf6'],
    });
    if (Date.now() < end && !cancelled) requestAnimationFrame(frame);
  };
  frame();
  return () => { cancelled = true; };
}
