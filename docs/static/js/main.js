(() => {
  "use strict";

  const nav = document.querySelector(".nav");
  const menuButton = document.querySelector(".nav__menu");
  const mobileNav = document.querySelector(".mobile-nav");

  const updateNav = () => nav?.classList.toggle("is-scrolled", window.scrollY > 18);
  updateNav();
  window.addEventListener("scroll", updateNav, {passive: true});

  menuButton?.addEventListener("click", () => {
    const open = menuButton.getAttribute("aria-expanded") === "true";
    menuButton.setAttribute("aria-expanded", String(!open));
    mobileNav.hidden = open;
  });

  mobileNav?.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      menuButton.setAttribute("aria-expanded", "false");
      mobileNav.hidden = true;
    });
  });

  const reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    }, {threshold: 0.12, rootMargin: "0px 0px -30px"});
    reveals.forEach((element) => observer.observe(element));
  } else {
    reveals.forEach((element) => element.classList.add("is-visible"));
  }

  const copyButton = document.querySelector("#copy-citation");
  const citation = document.querySelector("#citation-code");
  copyButton?.addEventListener("click", async () => {
    const text = citation?.textContent?.trim() ?? "";
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const field = document.createElement("textarea");
      field.value = text;
      field.style.position = "fixed";
      field.style.opacity = "0";
      document.body.append(field);
      field.select();
      document.execCommand("copy");
      field.remove();
    }
    copyButton.textContent = "Copied ✓";
    window.setTimeout(() => { copyButton.textContent = "Copy BibTeX"; }, 1800);
  });

  const canvas = document.querySelector("#drive-canvas");
  if (!(canvas instanceof HTMLCanvasElement)) return;

  const ctx = canvas.getContext("2d");
  const sceneTitle = document.querySelector("#scene-title");
  const sceneRule = document.querySelector("#scene-rule");
  const sceneHelp = document.querySelector("#scene-help");
  const sceneSign = document.querySelector("#scene-sign");
  const stepCount = document.querySelector("#step-count");
  const status = document.querySelector("#verifier-status");
  const verifier = document.querySelector(".verifier");
  const liveRegion = document.querySelector("#sim-live");
  const tabs = [...document.querySelectorAll("[data-scene]")];
  const controls = [...document.querySelectorAll("[data-action]")];

  const WORLD = {width: 920, height: 560};
  const images = {};
  const imagePaths = {
    mandatory: "static/images/signs/4.2.1.png",
    "no-entry": "static/images/signs/3.1.png",
    crosswalk: "static/images/signs/5.19.png",
  };

  Object.entries(imagePaths).forEach(([key, src]) => {
    const image = new Image();
    image.src = src;
    images[key] = image;
  });

  const scenes = {
    mandatory: {
      title: "Keep right",
      rule: "Pass the traffic island on its right-hand side.",
      help: "Drive forward, move right before the island, then continue to the goal.",
      start: {x: 460, y: 492},
      draw: drawMandatory,
      evaluate: evaluateMandatory,
    },
    "no-entry": {
      title: "No entry",
      rule: "Do not enter the signed branch. Take the open road to the right.",
      help: "Reach the junction, then take the right branch. The left branch is prohibited.",
      start: {x: 460, y: 492},
      draw: drawNoEntry,
      evaluate: evaluateNoEntry,
    },
    crosswalk: {
      title: "Pedestrian crossing",
      rule: "Yield while a pedestrian occupies the crossing.",
      help: "Brake twice to let the pedestrian clear, then continue across the zebra.",
      start: {x: 460, y: 492},
      draw: drawCrosswalk,
      evaluate: evaluateCrosswalk,
    },
  };

  let sceneKey = "mandatory";
  let state = createState(sceneKey);
  let animationFrame = 0;

  function createState(key) {
    const start = scenes[key].start;
    return {
      x: start.x,
      y: start.y,
      previousY: start.y,
      heading: 0,
      step: 0,
      waits: 0,
      passedSide: null,
      terminal: false,
      result: "ready",
      message: "Ready to drive",
    };
  }

  function resetScene() {
    state = createState(sceneKey);
    syncInterface();
  }

  function selectScene(key) {
    sceneKey = key;
    tabs.forEach((tab) => tab.setAttribute("aria-selected", String(tab.dataset.scene === key)));
    resetScene();
  }

  function act(action) {
    if (state.terminal) return;
    state.previousY = state.y;
    state.step += 1;

    if (action === "forward") {
      state.y -= 46;
      state.heading = 0;
    } else if (action === "left") {
      state.x -= 54;
      state.heading = -1;
    } else if (action === "right") {
      state.x += 54;
      state.heading = 1;
    } else if (action === "brake") {
      state.heading = 0;
      if (sceneKey === "crosswalk") state.waits += 1;
    }

    scenes[sceneKey].evaluate(action);
    syncInterface();
    flashControl(action);
  }

  function setResult(result, message, terminal = false) {
    state.result = result;
    state.message = message;
    state.terminal = terminal;
  }

  function evaluateMandatory() {
    const offRoad = state.x < 340 || state.x > 580 || state.y > 525;
    const hitIsland = state.x > 404 && state.x < 516 && state.y > 202 && state.y < 354;
    if (offRoad) return setResult("violation", "Violation: left the drivable lane", true);
    if (hitIsland) return setResult("violation", "Collision with the traffic island", true);

    if (!state.passedSide && state.previousY > 200 && state.y <= 200) {
      state.passedSide = state.x > 516 ? "right" : "left";
      if (state.passedSide === "left") {
        return setResult("violation", "Violation: passed the island on the left", true);
      }
    }
    if (state.y < 65) {
      if (state.passedSide === "right") return setResult("safe", "Compliant destination reached ✓", true);
      return setResult("violation", "Violation: required side was not used", true);
    }
    setResult("safe", state.passedSide === "right" ? "Rule satisfied — reach the goal" : "No violation detected");
  }

  function evaluateNoEntry() {
    const onVertical = state.x >= 405 && state.x <= 515 && state.y >= 205 && state.y <= 525;
    const onHorizontal = state.y >= 185 && state.y <= 315 && state.x >= 130 && state.x <= 790;
    if (!onVertical && !onHorizontal) {
      return setResult("violation", "Violation: left the drivable road", true);
    }
    if (state.y <= 315 && state.x < 360) {
      return setResult("violation", "Violation: entered the prohibited road", true);
    }
    if (state.x > 735 && state.y <= 315) {
      return setResult("safe", "Compliant destination reached ✓", true);
    }
    setResult("safe", state.y <= 315 ? "No violation — continue right" : "No violation detected");
  }

  function evaluateCrosswalk(action) {
    const offRoad = state.x < 350 || state.x > 570 || state.y > 525;
    if (offRoad) return setResult("violation", "Violation: left the drivable lane", true);

    const enteredCrossing = state.previousY > 275 && state.y <= 275;
    if (enteredCrossing && state.waits < 2) {
      return setResult("violation", "Violation: failed to yield to pedestrian", true);
    }
    if (state.y < 65) return setResult("safe", "Compliant destination reached ✓", true);
    if (action === "brake" && state.waits < 2) return setResult("safe", "Holding — pedestrian is crossing");
    if (state.waits >= 2) return setResult("safe", "Crosswalk clear — proceed");
    setResult("safe", "Pedestrian detected — brake before the zebra");
  }

  function syncInterface() {
    const scene = scenes[sceneKey];
    sceneTitle.textContent = scene.title;
    sceneRule.textContent = scene.rule;
    sceneHelp.textContent = scene.help;
    sceneSign.src = imagePaths[sceneKey];
    sceneSign.alt = `${scene.title} traffic sign`;
    stepCount.textContent = String(state.step);
    status.textContent = state.message;
    verifier.dataset.state = state.result;
    liveRegion.textContent = `Step ${state.step}. ${state.message}`;
  }

  function flashControl(action) {
    const button = controls.find((item) => item.dataset.action === action);
    button?.classList.add("is-pressed");
    window.setTimeout(() => button?.classList.remove("is-pressed"), 120);
  }

  tabs.forEach((tab) => tab.addEventListener("click", () => selectScene(tab.dataset.scene)));
  controls.forEach((button) => button.addEventListener("click", () => act(button.dataset.action)));
  document.querySelector("#reset-scene")?.addEventListener("click", resetScene);

  window.addEventListener("keydown", (event) => {
    const target = event.target;
    if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement) return;
    const actions = {
      ArrowLeft: "left",
      ArrowUp: "forward",
      ArrowRight: "right",
      " ": "brake",
    };
    const action = actions[event.key];
    if (!action) return;
    const rect = canvas.getBoundingClientRect();
    if (rect.bottom < 0 || rect.top > window.innerHeight) return;
    event.preventDefault();
    act(action);
  });

  function roundedRect(x, y, width, height, radius) {
    const r = Math.min(radius, width / 2, height / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + width, y, x + width, y + height, r);
    ctx.arcTo(x + width, y + height, x, y + height, r);
    ctx.arcTo(x, y + height, x, y, r);
    ctx.arcTo(x, y, x + width, y, r);
    ctx.closePath();
  }

  function drawGround() {
    ctx.fillStyle = "#dce5d8";
    ctx.fillRect(0, 0, WORLD.width, WORLD.height);
    ctx.strokeStyle = "rgba(76, 98, 71, .08)";
    ctx.lineWidth = 1;
    for (let x = 20; x < WORLD.width; x += 36) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, WORLD.height);
      ctx.stroke();
    }
    for (let y = 20; y < WORLD.height; y += 36) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(WORLD.width, y);
      ctx.stroke();
    }
  }

  function drawRoadRect(x, y, width, height) {
    ctx.fillStyle = "#858a86";
    ctx.fillRect(x, y, width, height);
    ctx.strokeStyle = "#f5f4e9";
    ctx.lineWidth = 5;
    ctx.strokeRect(x + 4, y, width - 8, height);
  }

  function drawLaneLine(x1, y1, x2, y2) {
    ctx.save();
    ctx.strokeStyle = "rgba(255, 255, 255, .7)";
    ctx.lineWidth = 3;
    ctx.setLineDash([18, 18]);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.restore();
  }

  function drawSign(x, y, size = 54) {
    const image = images[sceneKey];
    ctx.save();
    ctx.fillStyle = "rgba(19, 23, 18, .22)";
    ctx.beginPath();
    ctx.ellipse(x + size / 2 + 5, y + size + 8, size * .43, 8, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#60655e";
    ctx.fillRect(x + size / 2 - 3, y + size - 2, 6, 42);
    if (image?.complete) {
      ctx.drawImage(image, x, y, size, size);
    }
    ctx.restore();
  }

  function drawGoal(x, y, width, height, label = "GOAL") {
    ctx.save();
    roundedRect(x, y, width, height, 10);
    ctx.fillStyle = "rgba(22, 121, 84, .22)";
    ctx.fill();
    ctx.strokeStyle = "#1c8f67";
    ctx.lineWidth = 2;
    ctx.setLineDash([7, 6]);
    ctx.stroke();
    ctx.fillStyle = "#116d4b";
    ctx.font = "700 11px DM Sans, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(label, x + width / 2, y + height / 2 + 4);
    ctx.restore();
  }

  function drawMandatory() {
    drawGround();
    drawRoadRect(330, 0, 260, 560);
    drawLaneLine(460, 0, 460, 185);
    drawLaneLine(460, 370, 460, 560);

    ctx.save();
    roundedRect(402, 196, 116, 165, 56);
    ctx.fillStyle = "#d6d9cd";
    ctx.fill();
    ctx.strokeStyle = "#f3f2e8";
    ctx.lineWidth = 5;
    ctx.stroke();
    ctx.fillStyle = "#79816f";
    for (let y = 220; y < 340; y += 24) {
      ctx.beginPath();
      ctx.arc(460 + Math.sin(y) * 17, y, 5, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();

    ctx.strokeStyle = "rgba(21, 87, 213, .68)";
    ctx.lineWidth = 5;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(475, 420);
    ctx.bezierCurveTo(555, 360, 564, 220, 526, 150);
    ctx.stroke();

    drawGoal(505, 20, 70, 47);
    drawSign(610, 326);
  }

  function drawNoEntry() {
    drawGround();
    drawRoadRect(400, 220, 120, 340);
    drawRoadRect(110, 170, 700, 160);
    drawLaneLine(460, 330, 460, 560);
    drawLaneLine(110, 250, 810, 250);

    ctx.save();
    ctx.fillStyle = "rgba(223, 75, 63, .2)";
    ctx.fillRect(110, 175, 255, 150);
    ctx.strokeStyle = "#df4b3f";
    ctx.lineWidth = 2;
    ctx.setLineDash([9, 7]);
    ctx.strokeRect(118, 183, 238, 134);
    ctx.fillStyle = "#a8322b";
    ctx.font = "700 11px DM Sans, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("PROHIBITED", 235, 206);
    ctx.restore();

    drawGoal(730, 188, 67, 124);
    drawSign(330, 337);
  }

  function drawCrosswalk(time) {
    drawGround();
    drawRoadRect(340, 0, 240, 560);
    drawLaneLine(460, 0, 460, 560);

    const stripeY = 212;
    ctx.fillStyle = "#f6f3df";
    for (let x = 348; x < 574; x += 30) {
      ctx.fillRect(x, stripeY, 18, 72);
    }

    const progress = Math.min(state.waits / 2, 1);
    const bob = Math.sin(time / 180) * 3;
    const pedestrianX = 382 + progress * 190;
    drawPedestrian(pedestrianX, 248 + bob, progress >= 1);
    drawGoal(385, 20, 150, 47);
    drawSign(606, 292);
  }

  function drawPedestrian(x, y, cleared) {
    ctx.save();
    ctx.translate(x, y);
    ctx.globalAlpha = cleared ? .42 : 1;
    ctx.strokeStyle = "#242823";
    ctx.fillStyle = "#f0b849";
    ctx.lineWidth = 5;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.arc(0, -18, 7, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(0, -10);
    ctx.lineTo(0, 11);
    ctx.moveTo(0, -2);
    ctx.lineTo(-10, 8);
    ctx.moveTo(0, -2);
    ctx.lineTo(10, 6);
    ctx.moveTo(0, 11);
    ctx.lineTo(-8, 24);
    ctx.moveTo(0, 11);
    ctx.lineTo(10, 23);
    ctx.stroke();
    ctx.restore();
  }

  function drawCar() {
    const lean = state.heading * .05;
    ctx.save();
    ctx.translate(state.x, state.y);
    ctx.rotate(lean);
    ctx.shadowColor = "rgba(20, 24, 19, .28)";
    ctx.shadowBlur = 14;
    ctx.shadowOffsetY = 7;
    roundedRect(-22, -38, 44, 76, 12);
    ctx.fillStyle = state.result === "violation" ? "#df4b3f" : "#f0b849";
    ctx.fill();
    ctx.shadowColor = "transparent";
    roundedRect(-16, -23, 32, 28, 7);
    ctx.fillStyle = "#2f4b58";
    ctx.fill();
    ctx.fillStyle = "#fbf9eb";
    ctx.fillRect(-17, 19, 34, 5);
    ctx.fillStyle = "#171916";
    ctx.fillRect(-26, -24, 5, 17);
    ctx.fillRect(21, -24, 5, 17);
    ctx.fillRect(-26, 13, 5, 17);
    ctx.fillRect(21, 13, 5, 17);
    ctx.restore();

    if (state.result === "violation") {
      ctx.save();
      ctx.strokeStyle = "rgba(223, 75, 63, .55)";
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.arc(state.x, state.y, 49 + Math.sin(animationFrame / 150) * 3, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    }
  }

  function drawHud() {
    ctx.save();
    roundedRect(16, 16, 151, 50, 10);
    ctx.fillStyle = "rgba(255, 255, 255, .86)";
    ctx.fill();
    ctx.fillStyle = "#676c65";
    ctx.font = "700 10px DM Sans, sans-serif";
    ctx.fillText(`STEP ${state.step}`, 30, 37);
    ctx.fillStyle = state.result === "violation" ? "#df4b3f" : "#167954";
    ctx.fillText(state.result === "violation" ? "VIOLATIONS 1" : "VIOLATIONS 0", 30, 53);
    ctx.restore();
  }

  function render(time = 0) {
    animationFrame = time;
    ctx.clearRect(0, 0, WORLD.width, WORLD.height);
    scenes[sceneKey].draw(time);
    drawCar();
    drawHud();
    window.requestAnimationFrame(render);
  }

  syncInterface();
  render();
})();
