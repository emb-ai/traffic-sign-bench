(() => {
  "use strict";

  const canvas = document.querySelector("#sim-canvas");
  if (!(canvas instanceof HTMLCanvasElement)) return;

  const ctx = canvas.getContext("2d");
  const startOverlay = document.querySelector("#sim-start");
  const verifier = document.querySelector(".verifier");
  const status = document.querySelector("#verifier-status");
  const speedOutput = document.querySelector("#sim-speed");
  const distanceOutput = document.querySelector("#line-distance");
  const stopOutput = document.querySelector("#stop-state");
  const liveRegion = document.querySelector("#sim-live");
  const resetButton = document.querySelector("#reset-scene");
  const controlButtons = [...document.querySelectorAll("[data-control]")];

  const WIDTH = 920;
  const HEIGHT = 560;
  const STOP_LINE_Y = 10;
  const STOP_SPEED_MPS = 0.5;
  const WORLD_LIMIT = 80;
  const ROAD_HALF_WIDTH = 6;
  const input = {left: false, right: false, up: false, down: false};
  const pointers = new Map();

  const stopSign = new Image();
  stopSign.src = "static/images/signs/2.5.png";

  const trees = [
    [-15, 43, 5], [17, 35, 4], [-22, 18, 5], [20, 15, 4],
    [-19, -16, 4], [23, -23, 5], [-14, -46, 5], [17, -58, 4],
    [-38, 16, 4], [39, 17, 5], [-45, -15, 4], [48, -19, 5],
  ];

  let state;
  let previousTime = performance.now();
  let lastUiUpdate = 0;
  let lastAnnouncement = "";

  function initialState() {
    return {
      x: 2.55,
      y: 48,
      heading: 0,
      speed: 0,
      steering: 0,
      elapsed: 0,
      npcX: -39,
      started: false,
      stoppedBeforeLine: false,
      crossedStopLine: false,
      result: "ready",
      message: "Approach the stop line",
      terminal: false,
      offRoadTime: 0,
    };
  }

  function reset() {
    state = initialState();
    Object.keys(input).forEach((key) => { input[key] = false; });
    controlButtons.forEach((button) => button.classList.remove("is-pressed"));
    startOverlay?.classList.remove("is-hidden");
    previousTime = performance.now();
    lastAnnouncement = "";
    syncInterface(true);
  }

  function begin() {
    if (state.started) return;
    state.started = true;
    startOverlay?.classList.add("is-hidden");
    canvas.focus({preventScroll: true});
  }

  function isSimulatorVisible() {
    const rect = canvas.getBoundingClientRect();
    return rect.bottom > 0 && rect.top < window.innerHeight;
  }

  function setControl(control, pressed) {
    input[control] = pressed;
    const button = controlButtons.find((item) => item.dataset.control === control);
    button?.classList.toggle("is-pressed", pressed);
  }

  const keyControls = {
    ArrowLeft: "left",
    ArrowRight: "right",
    ArrowUp: "up",
    ArrowDown: "down",
  };

  window.addEventListener("keydown", (event) => {
    const control = keyControls[event.key];
    if (!control || !isSimulatorVisible()) return;
    const target = event.target;
    if (target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement) return;
    event.preventDefault();
    begin();
    setControl(control, true);
  });

  window.addEventListener("keyup", (event) => {
    const control = keyControls[event.key];
    if (!control) return;
    setControl(control, false);
  });

  window.addEventListener("blur", () => {
    Object.keys(input).forEach((key) => setControl(key, false));
  });

  controlButtons.forEach((button) => {
    button.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      begin();
      const control = button.dataset.control;
      pointers.set(event.pointerId, control);
      button.setPointerCapture(event.pointerId);
      setControl(control, true);
    });

    const release = (event) => {
      const control = pointers.get(event.pointerId);
      if (!control) return;
      pointers.delete(event.pointerId);
      const stillPressed = [...pointers.values()].includes(control);
      setControl(control, stillPressed);
    };

    button.addEventListener("pointerup", release);
    button.addEventListener("pointercancel", release);
    button.addEventListener("lostpointercapture", release);
  });

  startOverlay?.addEventListener("click", begin);
  canvas.addEventListener("pointerdown", begin);
  resetButton?.addEventListener("click", reset);

  function approach(value, target, amount) {
    if (value < target) return Math.min(value + amount, target);
    return Math.max(value - amount, target);
  }

  function frontOfVehicle() {
    return {
      x: state.x + Math.sin(state.heading) * 2.3,
      y: state.y - Math.cos(state.heading) * 2.3,
    };
  }

  function isOnRoad(x, y) {
    return Math.abs(x) <= ROAD_HALF_WIDTH || Math.abs(y) <= ROAD_HALF_WIDTH;
  }

  function setTerminal(result, message) {
    if (state.terminal) return;
    state.result = result;
    state.message = message;
    state.terminal = true;
    state.speed = 0;
    Object.keys(input).forEach((key) => setControl(key, false));
    syncInterface(true);
  }

  function updateRuleChecker(previousY) {
    const front = frontOfVehicle();
    const distance = front.y - STOP_LINE_Y;
    const inStopZone = distance > 0 && distance < 20;

    if (
      !state.stoppedBeforeLine &&
      inStopZone &&
      Math.abs(state.speed) < STOP_SPEED_MPS
    ) {
      state.stoppedBeforeLine = true;
      state.result = "safe";
      state.message = "Full stop registered — check for traffic";
    }

    if (!state.crossedStopLine && distance <= 0) {
      state.crossedStopLine = true;
      if (!state.stoppedBeforeLine) {
        setTerminal("violation", "Violation: crossed the line without stopping");
        return;
      }
    }

    const enteredJunction = previousY >= 6 && state.y < 6;
    if (enteredJunction && Math.abs(state.npcX) < 17) {
      setTerminal("violation", "Violation: failed to yield to main-road traffic");
      return;
    }

    const npcDistance = Math.hypot(state.x - state.npcX, state.y);
    if (npcDistance < 3.2) {
      setTerminal("violation", "Collision in the junction");
      return;
    }

    if (state.y < -39 && Math.abs(state.x) < ROAD_HALF_WIDTH) {
      setTerminal("safe", "Compliant destination reached ✓");
      return;
    }

    if (!isOnRoad(state.x, state.y)) {
      state.offRoadTime += 1 / 60;
      if (state.offRoadTime > 0.65) {
        setTerminal("violation", "Scenario failed: ego left the drivable road");
        return;
      }
    } else {
      state.offRoadTime = 0;
    }

    if (state.stoppedBeforeLine) {
      state.result = "safe";
      if (Math.abs(state.npcX) < 17 && state.y > 6) {
        state.message = "Hold — main-road vehicle is passing";
      } else if (state.y > STOP_LINE_Y) {
        state.message = "Full stop registered — safe to proceed";
      } else {
        state.message = "Stop satisfied — clear the junction";
      }
    } else if (distance < 18) {
      state.message = "Slow down and stop before the line";
    } else {
      state.message = "Approach the stop line";
    }
  }

  function update(dt) {
    if (!state.started || state.terminal) return;

    state.elapsed += dt;
    state.npcX = -42 + (state.elapsed * 6.5) % 84;

    const steeringTarget = input.left === input.right ? 0 : (input.left ? -1 : 1);
    state.steering = approach(state.steering, steeringTarget, dt * 4.8);

    let acceleration = 0;
    if (input.up && !input.down) {
      acceleration = state.speed < -0.25 ? 9 : 5.2;
    } else if (input.down && !input.up) {
      acceleration = state.speed > 0.35 ? -9.5 : -3.4;
    } else if (Math.abs(state.speed) > 0.01) {
      const resistance = 0.72 + 0.018 * state.speed * state.speed;
      acceleration = -Math.sign(state.speed) * resistance;
    }

    state.speed += acceleration * dt;
    state.speed = Math.max(-4.5, Math.min(15, state.speed));
    if (!input.up && !input.down && Math.abs(state.speed) < 0.12) state.speed = 0;

    if (Math.abs(state.speed) > 0.03) {
      const steerAngle = state.steering * 0.48;
      state.heading += (state.speed / 2.75) * Math.tan(steerAngle) * dt;
    }

    const previousY = state.y;
    state.x += Math.sin(state.heading) * state.speed * dt;
    state.y -= Math.cos(state.heading) * state.speed * dt;
    updateRuleChecker(previousY);
  }

  function cameraBasis() {
    const carForward = {
      x: Math.sin(state.heading),
      y: -Math.cos(state.heading),
    };
    const camera = {
      x: state.x - carForward.x * 10.5,
      y: state.y - carForward.y * 10.5,
      z: 7.8,
    };
    const target = {
      x: state.x + carForward.x * 11,
      y: state.y + carForward.y * 11,
      z: 0.6,
    };
    const rawForward = {
      x: target.x - camera.x,
      y: target.y - camera.y,
      z: target.z - camera.z,
    };
    const forwardLength = Math.hypot(rawForward.x, rawForward.y, rawForward.z);
    const forward = {
      x: rawForward.x / forwardLength,
      y: rawForward.y / forwardLength,
      z: rawForward.z / forwardLength,
    };
    const rightLength = Math.hypot(-forward.y, forward.x);
    const right = {
      x: -forward.y / rightLength,
      y: forward.x / rightLength,
      z: 0,
    };
    const up = {
      x: forward.y * right.z - forward.z * right.y,
      y: forward.z * right.x - forward.x * right.z,
      z: forward.x * right.y - forward.y * right.x,
    };
    return {camera, forward, right, up};
  }

  function makeProjector() {
    const basis = cameraBasis();
    return (point) => {
      const relative = {
        x: point.x - basis.camera.x,
        y: point.y - basis.camera.y,
        z: (point.z || 0) - basis.camera.z,
      };
      const depth =
        relative.x * basis.forward.x +
        relative.y * basis.forward.y +
        relative.z * basis.forward.z;
      if (depth < 1.2) return null;
      const horizontal =
        relative.x * basis.right.x +
        relative.y * basis.right.y +
        relative.z * basis.right.z;
      const vertical =
        relative.x * basis.up.x +
        relative.y * basis.up.y +
        relative.z * basis.up.z;
      const focal = 650;
      return {
        x: WIDTH / 2 + horizontal / depth * focal,
        y: HEIGHT * 0.47 - vertical / depth * focal,
        depth,
      };
    };
  }

  function polygon(points, fill, stroke = null, lineWidth = 1) {
    if (points.some((point) => !point)) return;
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    points.slice(1).forEach((point) => ctx.lineTo(point.x, point.y));
    ctx.closePath();
    if (fill) {
      ctx.fillStyle = fill;
      ctx.fill();
    }
    if (stroke) {
      ctx.strokeStyle = stroke;
      ctx.lineWidth = lineWidth;
      ctx.stroke();
    }
  }

  function drawWorldLine(project, start, end, color, width, dash = []) {
    const a = project(start);
    const b = project(end);
    if (!a || !b) return;
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.setLineDash(dash);
    ctx.stroke();
    ctx.restore();
  }

  function roadAt(x, y) {
    return Math.abs(x) < ROAD_HALF_WIDTH || Math.abs(y) < ROAD_HALF_WIDTH;
  }

  function drawTerrain(project) {
    const tiles = [];
    const tileSize = 4;
    for (let x = -WORLD_LIMIT; x < WORLD_LIMIT; x += tileSize) {
      for (let y = -WORLD_LIMIT; y < WORLD_LIMIT; y += tileSize) {
        if (Math.hypot(x + 2 - state.x, y + 2 - state.y) > 82) continue;
        const points = [
          project({x, y, z: 0}),
          project({x: x + tileSize, y, z: 0}),
          project({x: x + tileSize, y: y + tileSize, z: 0}),
          project({x, y: y + tileSize, z: 0}),
        ];
        if (points.some((point) => !point)) continue;
        const depth = points.reduce((sum, point) => sum + point.depth, 0) / 4;
        const road = roadAt(x + 2, y + 2);
        const variation = (Math.abs(x * 7 + y * 13) % 3) * 2;
        tiles.push({
          points,
          depth,
          color: road
            ? `rgb(${68 + variation}, ${73 + variation}, ${77 + variation})`
            : `rgb(${83 + variation}, ${110 + variation}, ${76 + variation})`,
        });
      }
    }
    tiles.sort((a, b) => b.depth - a.depth);
    tiles.forEach((tile) => polygon(tile.points, tile.color));

    const edge = "rgba(221, 224, 215, .88)";
    [-ROAD_HALF_WIDTH, ROAD_HALF_WIDTH].forEach((x) => {
      drawWorldLine(project, {x, y: 80}, {x, y: 6}, edge, 3);
      drawWorldLine(project, {x, y: -6}, {x, y: -80}, edge, 3);
    });
    [-ROAD_HALF_WIDTH, ROAD_HALF_WIDTH].forEach((y) => {
      drawWorldLine(project, {x: -80, y}, {x: -6, y}, edge, 3);
      drawWorldLine(project, {x: 6, y}, {x: 80, y}, edge, 3);
    });

    const laneColor = "rgba(244, 240, 205, .72)";
    for (let y = 76; y > 8; y -= 8) {
      drawWorldLine(project, {x: 0, y}, {x: 0, y: y - 4}, laneColor, 2);
    }
    for (let y = -8; y > -80; y -= 8) {
      drawWorldLine(project, {x: 0, y}, {x: 0, y: y - 4}, laneColor, 2);
    }
    for (let x = -76; x < -8; x += 8) {
      drawWorldLine(project, {x, y: 0}, {x: x + 4, y: 0}, laneColor, 2);
    }
    for (let x = 8; x < 76; x += 8) {
      drawWorldLine(project, {x, y: 0}, {x: x + 4, y: 0}, laneColor, 2);
    }

    drawWorldLine(
      project,
      {x: 0.25, y: STOP_LINE_Y},
      {x: 5.75, y: STOP_LINE_Y},
      "#f7f7ee",
      7,
    );
  }

  function drawTree(project, tree) {
    const [x, y, height] = tree;
    const base = project({x, y, z: 0});
    const crown = project({x, y, z: height});
    if (!base || !crown) return;
    const size = Math.max(3, Math.min(34, (base.y - crown.y) * 0.48));
    ctx.strokeStyle = "#443e31";
    ctx.lineWidth = Math.max(1, size * 0.16);
    ctx.beginPath();
    ctx.moveTo(base.x, base.y);
    ctx.lineTo(crown.x, crown.y + size * 0.4);
    ctx.stroke();
    ctx.fillStyle = "#355f39";
    ctx.beginPath();
    ctx.arc(crown.x, crown.y, size, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "rgba(122, 159, 92, .55)";
    ctx.beginPath();
    ctx.arc(crown.x - size * 0.28, crown.y - size * 0.25, size * 0.55, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawStopSign(project) {
    const base = project({x: 7.3, y: 10.5, z: 0});
    const signCenter = project({x: 7.3, y: 10.5, z: 3});
    if (!base || !signCenter) return;
    const visualHeight = Math.max(18, Math.min(76, base.y - signCenter.y));
    ctx.strokeStyle = "#c9ccc8";
    ctx.lineWidth = Math.max(2, visualHeight * 0.07);
    ctx.beginPath();
    ctx.moveTo(base.x, base.y);
    ctx.lineTo(signCenter.x, signCenter.y);
    ctx.stroke();

    const size = visualHeight * 0.72;
    if (stopSign.complete && stopSign.naturalWidth > 0) {
      ctx.drawImage(stopSign, signCenter.x - size / 2, signCenter.y - size / 2, size, size);
    } else {
      ctx.fillStyle = "#dd2b22";
      ctx.beginPath();
      for (let index = 0; index < 8; index += 1) {
        const angle = Math.PI / 8 + index * Math.PI / 4;
        const px = signCenter.x + Math.cos(angle) * size / 2;
        const py = signCenter.y + Math.sin(angle) * size / 2;
        if (index === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.fill();
    }
  }

  function carCorners(x, y, heading, length, width, z) {
    const forward = {x: Math.sin(heading), y: -Math.cos(heading)};
    const right = {x: Math.cos(heading), y: Math.sin(heading)};
    const point = (forwardScale, rightScale) => ({
      x: x + forward.x * forwardScale + right.x * rightScale,
      y: y + forward.y * forwardScale + right.y * rightScale,
      z,
    });
    return [
      point(length / 2, -width / 2),
      point(length / 2, width / 2),
      point(-length / 2, width / 2),
      point(-length / 2, -width / 2),
    ];
  }

  function drawCar(project, x, y, heading, color, isEgo = false) {
    const baseWorld = carCorners(x, y, heading, 4.5, 2.05, 0.18);
    const topWorld = carCorners(x, y, heading, 3.1, 1.72, 1.35);
    const base = baseWorld.map(project);
    const top = topWorld.map(project);
    if ([...base, ...top].some((point) => !point)) return;

    const shadow = carCorners(x + 0.12, y + 0.18, heading, 4.8, 2.25, 0.04).map(project);
    polygon(shadow, "rgba(10, 13, 14, .28)");
    polygon([base[0], base[1], top[1], top[0]], color);
    polygon([base[1], base[2], top[2], top[1]], shade(color, -26));
    polygon([base[3], base[0], top[0], top[3]], shade(color, -38));
    polygon(top, shade(color, 18), "rgba(255, 255, 255, .2)");

    const windshield = [
      interpolate(top[0], top[3], 0.2),
      interpolate(top[1], top[2], 0.2),
      interpolate(top[1], top[2], 0.48),
      interpolate(top[0], top[3], 0.48),
    ];
    polygon(windshield, "#263941");

    if (isEgo) {
      const rearLeft = interpolate(base[3], base[2], 0.18);
      const rearRight = interpolate(base[3], base[2], 0.82);
      [rearLeft, rearRight].forEach((light) => {
        ctx.fillStyle = input.down ? "#ff493f" : "#a92521";
        ctx.beginPath();
        ctx.arc(light.x, light.y, 2.8, 0, Math.PI * 2);
        ctx.fill();
      });
    }
  }

  function interpolate(a, b, amount) {
    return {
      x: a.x + (b.x - a.x) * amount,
      y: a.y + (b.y - a.y) * amount,
      depth: a.depth + (b.depth - a.depth) * amount,
    };
  }

  function shade(hex, amount) {
    const value = hex.replace("#", "");
    const number = Number.parseInt(value, 16);
    const red = Math.max(0, Math.min(255, (number >> 16) + amount));
    const green = Math.max(0, Math.min(255, ((number >> 8) & 255) + amount));
    const blue = Math.max(0, Math.min(255, (number & 255) + amount));
    return `rgb(${red}, ${green}, ${blue})`;
  }

  function roundedRect(x, y, width, height, radius) {
    ctx.beginPath();
    ctx.roundRect(x, y, width, height, radius);
  }

  function drawHud() {
    ctx.save();
    roundedRect(18, 18, 222, 48, 9);
    ctx.fillStyle = "rgba(17, 22, 25, .78)";
    ctx.fill();
    ctx.fillStyle = "#ffffff";
    ctx.font = "700 11px DM Sans, sans-serif";
    ctx.fillText("TRAFFICSIGNBENCH", 32, 38);
    ctx.fillStyle = "#aeb8b6";
    ctx.font = "600 9px DM Sans, sans-serif";
    ctx.fillText("MANUAL CONTROL  ·  STOP SCENE", 32, 53);

    roundedRect(WIDTH - 142, 18, 124, 62, 9);
    ctx.fillStyle = "rgba(17, 22, 25, .78)";
    ctx.fill();
    ctx.textAlign = "right";
    ctx.fillStyle = "#ffffff";
    ctx.font = "700 25px Manrope, sans-serif";
    ctx.fillText(String(Math.round(Math.abs(state.speed) * 3.6)), WIDTH - 50, 49);
    ctx.fillStyle = "#aeb8b6";
    ctx.font = "700 9px DM Sans, sans-serif";
    ctx.fillText("KM/H", WIDTH - 31, 49);
    ctx.fillText(state.speed < -0.1 ? "R" : "D", WIDTH - 31, 67);
    ctx.textAlign = "left";

    if (state.terminal) {
      roundedRect(WIDTH / 2 - 185, HEIGHT / 2 - 55, 370, 110, 14);
      ctx.fillStyle = "rgba(17, 22, 25, .9)";
      ctx.fill();
      ctx.strokeStyle = state.result === "safe" ? "#55c793" : "#f06b61";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.textAlign = "center";
      ctx.fillStyle = state.result === "safe" ? "#72d9aa" : "#ff8279";
      ctx.font = "700 12px DM Sans, sans-serif";
      ctx.fillText(state.result === "safe" ? "SCENARIO COMPLETE" : "RULE VIOLATION", WIDTH / 2, HEIGHT / 2 - 22);
      ctx.fillStyle = "#ffffff";
      ctx.font = "700 17px Manrope, sans-serif";
      ctx.fillText(state.message.replace("Violation: ", ""), WIDTH / 2, HEIGHT / 2 + 5);
      ctx.fillStyle = "#aeb8b6";
      ctx.font = "500 10px DM Sans, sans-serif";
      ctx.fillText("Restart the scenario to try again", WIDTH / 2, HEIGHT / 2 + 29);
    }
    ctx.restore();
  }

  function render() {
    const sky = ctx.createLinearGradient(0, 0, 0, HEIGHT);
    sky.addColorStop(0, "#9cb7c5");
    sky.addColorStop(0.48, "#d8ded9");
    sky.addColorStop(0.49, "#78936d");
    sky.addColorStop(1, "#526e4f");
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, WIDTH, HEIGHT);

    const project = makeProjector();
    drawTerrain(project);

    trees
      .map((tree) => ({tree, point: project({x: tree[0], y: tree[1], z: 0})}))
      .filter((item) => item.point)
      .sort((a, b) => b.point.depth - a.point.depth)
      .forEach((item) => drawTree(project, item.tree));

    drawStopSign(project);
    drawCar(project, state.npcX, 0, Math.PI / 2, "#d55243");
    drawCar(project, state.x, state.y, state.heading, "#e2b129", true);
    drawHud();
  }

  function syncInterface(force = false) {
    const now = performance.now();
    if (!force && now - lastUiUpdate < 80) return;
    lastUiUpdate = now;

    const distance = frontOfVehicle().y - STOP_LINE_Y;
    speedOutput.textContent = Math.abs(state.speed).toFixed(1);
    distanceOutput.textContent = distance > 0 ? `${distance.toFixed(1)} m` : "Passed";
    stopOutput.textContent = state.stoppedBeforeLine ? "Registered ✓" : "Not yet";
    status.textContent = state.message;
    verifier.dataset.state = state.result;

    if (state.message !== lastAnnouncement) {
      liveRegion.textContent = state.message;
      lastAnnouncement = state.message;
    }
  }

  function frame(time) {
    const dt = Math.min((time - previousTime) / 1000, 0.04);
    previousTime = time;
    update(dt);
    render();
    syncInterface();
    window.requestAnimationFrame(frame);
  }

  reset();
  window.requestAnimationFrame(frame);
})();
