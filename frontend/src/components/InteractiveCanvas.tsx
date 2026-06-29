"use client";

import React, { useEffect, useRef } from "react";

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  color: string;
  strokeColor: string;
  labelText: string | null;
}

interface Ripple {
  x: number;
  y: number;
  r: number;
  alpha: number;
}

interface InteractiveCanvasProps {
  isLoading: boolean;
}

export default function InteractiveCanvas({ isLoading }: InteractiveCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: -1000, y: -1000 });
  const ripplesRef = useRef<Ripple[]>([]);
  const gradientTimeRef = useRef(0);

  const colors = [
    "rgba(183, 234, 246, 0.35)",
    "rgba(250, 233, 255, 0.35)",
    "rgba(254, 243, 200, 0.35)",
    "rgba(210, 250, 229, 0.35)",
    "rgba(245, 209, 254, 0.35)",
  ];
  const strokeColors = ["#b7eaf6", "#fae9ff", "#fef3c8", "#d2fae5", "#f5d1fe"];
  const labels = ["RBI", "KYC", "SLA", "SEC", "GO", "MAP", "DONE", "100%", "90d", "AML"];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let nodes: Node[] = [];

    const initNodes = () => {
      nodes = [];
      const count = 32;
      const leftExcl = canvas.width * 0.28;
      const rightExcl = canvas.width * 0.72;

      for (let i = 0; i < count; i++) {
        let rx = Math.random() * canvas.width;
        if (rx > leftExcl && rx < rightExcl) {
          rx = Math.random() < 0.5 ? Math.random() * leftExcl : rightExcl + Math.random() * (canvas.width - rightExcl);
        }

        nodes.push({
          x: rx,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 0.8,
          vy: (Math.random() - 0.5) * 0.8,
          color: colors[i % colors.length],
          strokeColor: strokeColors[i % strokeColors.length],
          labelText: i < labels.length ? labels[i] : null,
        });
      }
    };

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      initNodes();
    };

    window.addEventListener("resize", resize);
    resize();

    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseLeave = () => {
      mouseRef.current = { x: -1000, y: -1000 };
    };

    const handleMouseClick = (e: MouseEvent) => {
      if (isLoading) {
        ripplesRef.current.push({
          x: e.clientX,
          y: e.clientY,
          r: 10,
          alpha: 1.0,
        });
      }
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseleave", handleMouseLeave);
    window.addEventListener("click", handleMouseClick);

    let animationId: number;

    const tick = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (isLoading) {
        // Draw background neobrutalist dynamic gradient
        gradientTimeRef.current += 0.0025;
        const grad = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
        const r1 = Math.floor(183 + Math.sin(gradientTimeRef.current) * 15);
        const g1 = Math.floor(234 + Math.cos(gradientTimeRef.current) * 15);
        const b1 = Math.floor(246 + Math.sin(gradientTimeRef.current + 1) * 10);
        const r2 = Math.floor(250 + Math.sin(gradientTimeRef.current * 1.5) * 5);
        const g2 = Math.floor(233 + Math.cos(gradientTimeRef.current * 1.2) * 10);
        const b2 = Math.floor(255 + Math.sin(gradientTimeRef.current * 0.8) * 5);
        grad.addColorStop(0, `rgb(${r1}, ${g1}, ${b1})`);
        grad.addColorStop(1, `rgb(${r2}, ${g2}, ${b2})`);
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Bounding parameters for center exclusion shield
        const leftExcl = canvas.width * 0.28;
        const rightExcl = canvas.width * 0.72;
        const topExcl = canvas.height * 0.16;
        const botExcl = canvas.height * 0.76;

        // 1. Process node updates
        nodes.forEach((n) => {
          n.x += n.vx;
          n.y += n.vy;

          // Mouse avoidance push
          const mx = mouseRef.current.x;
          const my = mouseRef.current.y;
          if (mx > 0 && my > 0) {
            const dx = n.x - mx;
            const dy = n.y - my;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 170 && dist > 0.1) {
              const force = (1.0 - dist / 170) * 0.55;
              n.vx += (dx / dist) * force;
              n.vy += (dy / dist) * force;
            }
          }

          n.vx *= 0.96;
          n.vy *= 0.96;

          const speed = Math.sqrt(n.vx * n.vx + n.vy * n.vy);
          if (speed < 0.25) {
            n.vx += (Math.random() - 0.5) * 0.35;
            n.vy += (Math.random() - 0.5) * 0.35;
          }
          if (speed > 1.8) {
            n.vx = (n.vx / speed) * 1.5;
            n.vy = (n.vy / speed) * 1.5;
          }

          // Window boundary bounce
          if (n.x < 15) { n.x = 15; n.vx *= -1; }
          if (n.x > canvas.width - 15) { n.x = canvas.width - 15; n.vx *= -1; }
          if (n.y < 15) { n.y = 15; n.vy *= -1; }
          if (n.y > canvas.height - 15) { n.y = canvas.height - 15; n.vy *= -1; }

          // Center Box deflector shield
          if (n.x > leftExcl && n.x < rightExcl && n.y > topExcl && n.y < botExcl) {
            const dL = n.x - leftExcl;
            const dR = rightExcl - n.x;
            const dT = n.y - topExcl;
            const dB = botExcl - n.y;
            const minDist = Math.min(dL, dR, dT, dB);

            if (minDist === dL) {
              n.x = leftExcl - 2;
              n.vx = -Math.abs(n.vx) * 0.9;
            } else if (minDist === dR) {
              n.x = rightExcl + 2;
              n.vx = Math.abs(n.vx) * 0.9;
            } else if (minDist === dT) {
              n.y = topExcl - 2;
              n.vy = -Math.abs(n.vy) * 0.9;
            } else {
              n.y = botExcl + 2;
              n.vy = Math.abs(n.vy) * 0.9;
            }
          }
        });

        // Helper to block lines crossing through the center area
        const isCrossingCenter = (p1: Node, p2: Node) => {
          const midX = (p1.x + p2.x) / 2;
          const midY = (p1.y + p2.y) / 2;
          const q1x = p1.x * 0.75 + p2.x * 0.25;
          const q1y = p1.y * 0.75 + p2.y * 0.25;
          const q2x = p1.x * 0.25 + p2.x * 0.75;
          const q2y = p1.y * 0.25 + p2.y * 0.75;

          const checkPt = (x: number, y: number) => x > leftExcl && x < rightExcl && y > topExcl && y < botExcl;
          return checkPt(midX, midY) || checkPt(q1x, q1y) || checkPt(q2x, q2y);
        };

        // 2. Draw crystal shard triangles
        const connectionLimit = 170;
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const dx1 = nodes[i].x - nodes[j].x;
            const dy1 = nodes[i].y - nodes[j].y;
            const dist1 = Math.sqrt(dx1 * dx1 + dy1 * dy1);

            if (dist1 < connectionLimit && !isCrossingCenter(nodes[i], nodes[j])) {
              for (let k = j + 1; k < nodes.length; k++) {
                const dx2 = nodes[j].x - nodes[k].x;
                const dy2 = nodes[j].y - nodes[k].y;
                const dist2 = Math.sqrt(dx2 * dx2 + dy2 * dy2);

                const dx3 = nodes[k].x - nodes[i].x;
                const dy3 = nodes[k].y - nodes[i].y;
                const dist3 = Math.sqrt(dx3 * dx3 + dy3 * dy3);

                if (
                  dist2 < connectionLimit &&
                  dist3 < connectionLimit &&
                  !isCrossingCenter(nodes[j], nodes[k]) &&
                  !isCrossingCenter(nodes[k], nodes[i])
                ) {
                  ctx.fillStyle = nodes[i].color;
                  ctx.beginPath();
                  ctx.moveTo(nodes[i].x, nodes[i].y);
                  ctx.lineTo(nodes[j].x, nodes[j].y);
                  ctx.lineTo(nodes[k].x, nodes[k].y);
                  ctx.closePath();
                  ctx.fill();

                  ctx.strokeStyle = "rgba(0, 0, 0, 0.04)";
                  ctx.lineWidth = 1.0;
                  ctx.stroke();
                }
              }
            }
          }
        }

        // 3. Draw connection lines
        ctx.strokeStyle = "rgba(0, 0, 0, 0.085)";
        ctx.lineWidth = 1.2;
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const dx = nodes[i].x - nodes[j].x;
            const dy = nodes[i].y - nodes[j].y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < connectionLimit && !isCrossingCenter(nodes[i], nodes[j])) {
              ctx.beginPath();
              ctx.moveTo(nodes[i].x, nodes[i].y);
              ctx.lineTo(nodes[j].x, nodes[j].y);
              ctx.stroke();
            }
          }
        }

        // 4. Draw node dots and float labels
        nodes.forEach((n) => {
          ctx.fillStyle = "#000000";
          ctx.beginPath();
          ctx.arc(n.x, n.y, 2.5, 0, Math.PI * 2);
          ctx.fill();

          if (n.labelText) {
            ctx.save();
            ctx.translate(n.x + 10, n.y - 12);

            const text = n.labelText;
            ctx.font = '800 8.5px "JetBrains Mono", monospace';
            const tw = ctx.measureText(text).width + 8;
            const th = 13;

            ctx.fillStyle = "#000000";
            ctx.fillRect(1.5, 1.5, tw, th);

            ctx.fillStyle = "#ffffff";
            ctx.strokeStyle = "#000000";
            ctx.lineWidth = 1.5;
            ctx.fillRect(0, 0, tw, th);
            ctx.strokeRect(0, 0, tw, th);

            ctx.fillStyle = "#000000";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(text, tw / 2, th / 2);
            ctx.restore();
          }
        });

        // 5. Draw mouse click ripple pings
        ripplesRef.current.forEach((rip, idx) => {
          rip.r += 3.5;
          rip.alpha = 1.0 - rip.r / 160;

          if (rip.alpha <= 0 || rip.r > 160) {
            ripplesRef.current.splice(idx, 1);
            return;
          }

          ctx.strokeStyle = `rgba(0, 0, 0, ${rip.alpha})`;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.arc(rip.x, rip.y, rip.r, 0, Math.PI * 2);
          ctx.stroke();
        });
      } else {
        // Draw clean light stone backdrop with neobrutalist grid pattern
        ctx.fillStyle = "#fafaf9";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.strokeStyle = "rgba(0, 0, 0, 0.035)";
        ctx.lineWidth = 1.0;
        const gridSpacing = 35;

        for (let x = 0; x < canvas.width; x += gridSpacing) {
          ctx.beginPath();
          ctx.moveTo(x, 0);
          ctx.lineTo(x, canvas.height);
          ctx.stroke();
        }

        for (let y = 0; y < canvas.height; y += gridSpacing) {
          ctx.beginPath();
          ctx.moveTo(0, y);
          ctx.lineTo(canvas.width, y);
          ctx.stroke();
        }
      }

      animationId = requestAnimationFrame(tick);
    };

    animationId = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseleave", handleMouseLeave);
      window.removeEventListener("click", handleMouseClick);
    };
  }, [isLoading]);

  return <canvas ref={canvasRef} className="fixed inset-0 w-full h-full -z-10 pointer-events-none" />;
}
