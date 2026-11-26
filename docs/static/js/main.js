(() => {
  "use strict";

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const wait = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));
  const nextFrame = () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const easeOut = (t) => 1 - Math.pow(1 - t, 3);

  /* ---------------- Navigation ---------------- */
  const nav = $(".nav");
  const menuButton = $(".nav__menu");
  const mobileNav = $(".mobile-nav");

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

  /* ---------------- Helpers ---------------- */
  function onceVisible(elements, callback, options = {threshold: 0.2}) {
    const list = [...elements].filter(Boolean);
    if (!("IntersectionObserver" in window)) {
      list.forEach((element) => callback(element));
      return;
    }
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        callback(entry.target);
      });
    }, options);
    list.forEach((element) => observer.observe(element));
  }

  function formatNumber(element, value) {
    const decimals = Number(element.dataset.decimals || 0);
    if ("group" in element.dataset) return Math.round(value).toLocaleString("en-US");
    return value.toFixed(decimals);
  }

  function countUp(element, target, duration = 1400) {
    if (reduceMotion) {
      element.textContent = formatNumber(element, target);
      return;
    }
    const start = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      element.textContent = formatNumber(element, target * easeOut(t));
      if (t < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  function splitChars(element, offset = 0) {
    let index = offset;
    const walk = (node) => {
      [...node.childNodes].forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE) {
          const fragment = document.createDocumentFragment();
          for (const char of child.textContent) {
            if (char === " " || char === "\n") {
              fragment.append(document.createTextNode(" "));
              continue;
            }
            const span = document.createElement("span");
            span.className = "ch";
            span.style.setProperty("--i", String(index++));
            span.setAttribute("aria-hidden", "true");
            span.textContent = char;
            fragment.append(span);
          }
          child.replaceWith(fragment);
        } else if (child.nodeType === Node.ELEMENT_NODE) {
          walk(child);
        }
      });
    };
    walk(element);
    return index;
  }

  /* ---------------- Reveal on scroll ---------------- */
  onceVisible($$(".reveal"), (element) => element.classList.add("is-visible"), {
    threshold: 0.12,
    rootMargin: "0px 0px -40px",
  });

  onceVisible(
    $$("[data-count]").filter((element) => !element.closest(".hero")),
    (element) => countUp(element, Number(element.dataset.count)),
    {threshold: 0.6},
  );

  /* ---------------- Muted loops play only while visible ---------------- */
  const visibleVideos = new Set();
  let mosaicLive = false;

  function shouldPlay(video) {
    if (!visibleVideos.has(video)) return false;
    if (video.closest(".mosaic") && !mosaicLive) return false;
    const cycle = video.closest("[data-cycle]");
    if (cycle && !cycle.classList.contains("is-sim")) return false;
    return true;
  }

  function refreshVideo(video) {
    if (shouldPlay(video)) {
      video.play().catch(() => {});
    } else if (!video.paused) {
      video.pause();
    }
  }

  const loopVideos = $$("video[muted]").filter((video) => video.id !== "hero-video");
  if ("IntersectionObserver" in window) {
    const videoObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) visibleVideos.add(entry.target);
        else visibleVideos.delete(entry.target);
        refreshVideo(entry.target);
      });
    }, {threshold: 0.15});
    loopVideos.forEach((video) => videoObserver.observe(video));
  } else {
    loopVideos.forEach((video) => visibleVideos.add(video));
  }

  /* ---------------- Hero: scroll-scrubbed intro ---------------- */
  const heroScroll = $("[data-hero-scroll]");
  const heroAfter = $("[data-hero-after]");
  const hero = $(".hero");
  const stageElement = $(".hero__stage");
  const mosaic = $(".mosaic");
  const heroTile = $(".tile--hero");
  const heroVideo = $("#hero-video");
  const tagline = $("[data-type]");
  const heroMore = $(".hero__more");
  const moreHome = heroMore.parentElement;
  const scorecard = $(".scorecard", hero);
  const progressFill = $(".hero__progress-track", hero);
  const progressLabel = $(".hero__progress-label", hero);
  const tiles = $$(".tile", mosaic);
  const tileSigns = tiles.map((tile) => $(".tile__sign", tile));
  const heroIndex = tiles.indexOf(heroTile);
  const statElements = $$("[data-count]", heroMore);
  const narrowQuery = window.matchMedia("(max-width: 960px)");

  // The checker flags the crosswalk violation at simulator step 47 (25 fps);
  // freeze the opening clip a few frames later so the HUD lands on step 50.
  const VIOLATION_TIME = 47 / 25;
  const SCRUB_END = 50 / 25;

  // Story progress (0..1). Opening autoplays through AUTO_END; the rest is scroll-driven.
  const DRIVE = [0.02, 0.4];
  // Tagline types after the clip freezes; keep this span wide so letters appear slowly.
  const TYPE = [0.4, 0.62];
  const CARD_OUT = [0.64, 0.72];
  const ZOOM = [0.66, 0.86];
  const MORE = [0.84, 0.95];
  const LIVE_FROM = 0.84;
  const AUTO_END = TYPE[1];
  const TAGLINE_MS = 2800;

  const clamp01 = (t) => Math.min(1, Math.max(0, t));
  const span = (p, [a, b]) => clamp01((p - a) / (b - a));
  const lerp = (a, b, t) => a + (b - a) * t;
  const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

  let letterIndex = 0;
  $$("[data-split]", hero).forEach((element) => { letterIndex = splitChars(element, letterIndex); });
  const taglineLength = splitChars(tagline);
  const caret = document.createElement("span");
  caret.className = "caret";
  caret.setAttribute("aria-hidden", "true");
  tagline.append(caret);

  let focus = {x: 0, y: 0, s: 1};
  let ripple = tiles.map(() => 0);
  let introReady = false;
  let looping = false;
  let autoPlaying = false;
  let handoffP = 0;
  let targetP = 0;
  let shownP = 0;
  let videoTime = 0;
  let ticking = false;
  let scoresCounted = false;

  function measure() {
    const width = stageElement.clientWidth;
    const height = stageElement.clientHeight;
    const narrow = width < 560;
    const size = Math.min(height * 0.92, width * (narrow ? 0.54 : 0.58));
    const s = size / heroTile.offsetWidth;
    focus = {x: -s * heroTile.offsetLeft, y: (height - size) / 2 - s * heroTile.offsetTop, s};
    stageElement.style.setProperty("--card-left", `${size + (narrow ? 10 : 22)}px`);

    const cols = 4;
    const heroRow = Math.floor(heroIndex / cols);
    const heroCol = heroIndex % cols;
    const distances = tiles.map((_, index) => Math.hypot(Math.floor(index / cols) - heroRow, (index % cols) - heroCol));
    const maxDistance = Math.max(...distances);
    ripple = distances.map((distance) => distance / maxDistance);
  }

  function placeMore() {
    const target = narrowQuery.matches ? heroAfter : moreHome;
    if (heroMore.parentElement === target) return;
    target.append(heroMore);
    heroMore.style.opacity = "";
    heroMore.style.transform = "";
    statElements.forEach((element) => { element.textContent = formatNumber(element, Number(element.dataset.count)); });
  }

  function readScrollFrac() {
    const travel = heroScroll.offsetHeight - hero.offsetHeight;
    if (travel <= 0) return 1;
    return clamp01(-heroScroll.getBoundingClientRect().top / travel);
  }

  function mappedProgress() {
    return handoffP + (1 - handoffP) * readScrollFrac();
  }

  function setLive(live) {
    if (live === looping) return;
    looping = live;
    mosaicLive = live;
    loopVideos.filter((video) => video.closest(".mosaic")).forEach(refreshVideo);
    heroVideo.loop = live;
    if (live) {
      heroVideo.play().catch(() => {});
    } else {
      heroVideo.pause();
    }
  }

  let scrollEnabled = false;
  let videoReady = false;
  let videoReadyWaiters = [];
  let openingGen = 0;

  function whenVideoReady() {
    if (videoReady && heroVideo.readyState >= 2) return Promise.resolve();
    return new Promise((resolve) => videoReadyWaiters.push(resolve));
  }

  function markVideoReady() {
    if (videoReady) return;
    videoReady = true;
    videoReadyWaiters.splice(0).forEach((resolve) => resolve());
  }

  function seekVideo() {
    if (looping || heroVideo.readyState < 1 || heroVideo.seeking) return;
    if (Math.abs(heroVideo.currentTime - videoTime) > 0.02) heroVideo.currentTime = videoTime;
  }

  function render(p) {
    hero.dataset.stage = String(!introReady ? 0 : p < ZOOM[0] ? 1 : p < MORE[0] ? 2 : 3);

    hero.classList.toggle("is-violation", looping || videoTime >= VIOLATION_TIME);

    const typed = span(p, TYPE) * (taglineLength + 1);
    tagline.style.setProperty("--typed", typed.toFixed(2));
    tagline.classList.toggle("is-typed", typed > 0);

    const out = span(p, CARD_OUT);
    scorecard.style.opacity = String(1 - out);
    scorecard.style.transform = `translate(${out * 60}px, -50%) scale(${1 - out * 0.04})`;

    const z = easeInOut(span(p, ZOOM));
    const s = lerp(focus.s, 1, z);
    mosaic.style.transform = `translate(${lerp(focus.x, 0, z)}px, ${lerp(focus.y, 0, z)}px) scale(${s})`;
    mosaic.style.setProperty("--s", s.toFixed(3));
    tiles.forEach((tile, index) => {
      const delay = ripple[index] * 0.45;
      const sign = easeOut(span(z, [delay + 0.3, delay + 0.55]));
      tileSigns[index].style.opacity = String(sign);
      tileSigns[index].style.transform = `scale(${0.6 + 0.4 * sign})`;
      if (tile === heroTile) return;
      const shown = easeOut(span(z, [delay, delay + 0.5]));
      tile.style.opacity = String(shown);
      tile.style.transform = `scale(${0.86 + 0.14 * shown})`;
    });

    if (heroMore.parentElement === moreHome) {
      const more = easeOut(span(p, MORE));
      heroMore.style.opacity = String(more);
      heroMore.style.transform = `translateY(${18 * (1 - more)}px)`;
      const stats = easeOut(span(p, [MORE[0] + 0.02, MORE[1] + 0.04]));
      statElements.forEach((element) => { element.textContent = formatNumber(element, Number(element.dataset.count) * stats); });
    }

    progressFill.style.setProperty("--p", p.toFixed(3));
    if (autoPlaying) progressLabel.textContent = "Playing";
    else if (p < MORE[0]) progressLabel.textContent = "Scroll to continue";
    else progressLabel.textContent = "Scroll to explore";
  }

  function frame() {
    ticking = false;
    if (autoPlaying || !scrollEnabled) return;

    const delta = targetP - shownP;
    shownP = Math.abs(delta) < 0.0005 ? targetP : shownP + delta * 0.2;

    if (shownP >= LIVE_FROM) setLive(true);
    else if (shownP < LIVE_FROM - 0.03) setLive(false);

    if (!looping) {
      videoTime = span(shownP, DRIVE) * SCRUB_END;
      seekVideo();
    }
    render(shownP);

    const videoBehind = !looping && Math.abs(heroVideo.currentTime - videoTime) > 0.02;
    if (shownP !== targetP || videoBehind) schedule();
  }

  function schedule() {
    if (ticking || autoPlaying || !scrollEnabled) return;
    ticking = true;
    requestAnimationFrame(frame);
  }

  function countScores() {
    if (scoresCounted) return;
    scoresCounted = true;
    $$("[data-score]", hero).forEach((element) => countUp(element, Number(element.dataset.score), 1700));
  }

  function handOff(at = AUTO_END) {
    autoPlaying = false;
    handoffP = Math.max(at, AUTO_END);
    scrollEnabled = true;
    try { heroVideo.pause(); } catch { /* ignore */ }
    videoTime = Math.max(videoTime, SCRUB_END);
    seekVideo();
    targetP = shownP = Math.max(handoffP, mappedProgress());
    render(shownP);
    schedule();
  }

  function freezeOpeningClip() {
    try { heroVideo.pause(); } catch { /* ignore */ }
    videoTime = SCRUB_END;
    seekVideo();
  }

  function typeTagline(gen) {
    const from = DRIVE[1];
    const start = performance.now();
    const tick = (now) => {
      if (!autoPlaying || gen !== openingGen) return;
      const u = clamp01((now - start) / TAGLINE_MS);
      shownP = targetP = lerp(from, AUTO_END, u);
      videoTime = SCRUB_END;
      render(shownP);
      if (u < 1) requestAnimationFrame(tick);
      else handOff(AUTO_END);
    };
    requestAnimationFrame(tick);
  }

  async function startOpening() {
    if (autoPlaying || scrollEnabled) return;
    const gen = ++openingGen;
    autoPlaying = true;
    introReady = true;
    handoffP = 0;
    scrollEnabled = false;
    shownP = targetP = 0.04;
    videoTime = 0;
    measure();
    render(shownP);
    countScores();

    await whenVideoReady();
    if (!autoPlaying || gen !== openingGen) return;

    // One clean playback from the start — never scrub in parallel, never restart.
    try { heroVideo.pause(); } catch { /* ignore */ }
    try { heroVideo.currentTime = 0; } catch { /* ignore */ }
    await nextFrame();
    if (!autoPlaying || gen !== openingGen) return;

    let playing = false;
    try {
      await heroVideo.play();
      playing = !heroVideo.paused;
    } catch {
      playing = false;
    }

    if (playing) {
      const sync = () => {
        if (!autoPlaying || gen !== openingGen) return;
        videoTime = Math.min(heroVideo.currentTime || 0, SCRUB_END);
        shownP = targetP = DRIVE[0] + (DRIVE[1] - DRIVE[0]) * clamp01(videoTime / SCRUB_END);
        render(shownP);
        if (videoTime >= SCRUB_END - 0.02 || heroVideo.ended) {
          freezeOpeningClip();
          shownP = targetP = DRIVE[1];
          render(shownP);
          typeTagline(gen);
          return;
        }
        requestAnimationFrame(sync);
      };
      requestAnimationFrame(sync);
      return;
    }

    // Autoplay blocked: scrub once from 0 → SCRUB_END, then type.
    const start = performance.now();
    const duration = SCRUB_END * 1000;
    const scrub = (now) => {
      if (!autoPlaying || gen !== openingGen) return;
      const u = clamp01((now - start) / duration);
      videoTime = u * SCRUB_END;
      shownP = targetP = DRIVE[0] + (DRIVE[1] - DRIVE[0]) * u;
      seekVideo();
      render(shownP);
      if (u < 1) {
        requestAnimationFrame(scrub);
        return;
      }
      freezeOpeningClip();
      typeTagline(gen);
    };
    requestAnimationFrame(scrub);
  }

  function skipOpeningToScroll() {
    autoPlaying = false;
    introReady = true;
    handoffP = AUTO_END;
    scrollEnabled = true;
    videoTime = SCRUB_END;
    targetP = shownP = mappedProgress();
    countScores();
    $$("[data-score]", hero).forEach((element) => {
      element.textContent = formatNumber(element, Number(element.dataset.score));
    });
    render(shownP);
    schedule();
  }

  function prepareHeroVideo() {
    const src = heroVideo.currentSrc || heroVideo.src;

    // Blob URL makes scrubbing reliable even on servers without Range support.
    fetch(src)
      .then((response) => (response.ok ? response.blob() : Promise.reject()))
      .then((blob) => {
        heroVideo.src = URL.createObjectURL(blob);
        heroVideo.addEventListener("loadeddata", markVideoReady, {once: true});
        heroVideo.load();
      })
      .catch(() => {
        heroVideo.addEventListener("loadeddata", markVideoReady, {once: true});
        heroVideo.load();
        window.setTimeout(markVideoReady, 800);
      });
  }

  measure();
  placeMore();

  const deepLink = window.location.hash && window.location.hash !== "#top";
  const alreadyScrolled = readScrollFrac() > 0.02;

  if (reduceMotion) {
    introReady = true;
    handoffP = AUTO_END;
    scrollEnabled = true;
    videoTime = SCRUB_END;
    setLive(true);
    render(1);
    $$("[data-score]", hero).forEach((element) => {
      element.textContent = formatNumber(element, Number(element.dataset.score));
    });
  } else if (deepLink || alreadyScrolled) {
    prepareHeroVideo();
    skipOpeningToScroll();
  } else {
    prepareHeroVideo();
    // Start the opening on the next frame so layout/measure settle first.
    requestAnimationFrame(() => startOpening());
  }

  window.addEventListener("scroll", () => {
    if (reduceMotion) return;
    if (!scrollEnabled) {
      // Significant scroll skips the rest of the opening; tiny load noise is ignored.
      if (autoPlaying && readScrollFrac() > 0.04) handOff(Math.max(shownP, AUTO_END));
      return;
    }
    targetP = mappedProgress();
    schedule();
  }, {passive: true});

  heroVideo.addEventListener("loadedmetadata", () => { if (scrollEnabled) schedule(); });
  heroVideo.addEventListener("seeked", () => { if (scrollEnabled) schedule(); });

  window.addEventListener("resize", () => {
    measure();
    placeMore();
    if (reduceMotion) {
      render(1);
      return;
    }
    if (scrollEnabled) {
      targetP = mappedProgress();
      schedule();
    } else if (autoPlaying) {
      render(shownP);
    }
  });

  /* ---------------- Sign board: shuffle pile → semantic groups ---------------- */
  const board = $("[data-sort]");
  if (board) {
    const groups = $$(".sign-group", board);
    const icons = $$(".sign-group__icons img", board);
    const tooltip = document.createElement("div");
    tooltip.className = "sign-tip";
    document.body.append(tooltip);

    icons.forEach((icon) => {
      icon.addEventListener("mouseenter", () => {
        const rect = icon.getBoundingClientRect();
        tooltip.textContent = icon.dataset.tip;
        tooltip.style.left = `${rect.left + rect.width / 2}px`;
        tooltip.style.top = `${rect.top}px`;
        tooltip.classList.add("is-on");
      });
      icon.addEventListener("mouseleave", () => tooltip.classList.remove("is-on"));
    });
    window.addEventListener("scroll", () => tooltip.classList.remove("is-on"), {passive: true});

    if (reduceMotion) {
      board.classList.add("is-sorted");
    } else {
      board.classList.add("is-pile");
      icons.forEach((icon) => { icon.style.opacity = "0"; });

      onceVisible([board], async () => {
        const boardRect = board.getBoundingClientRect();
        const size = icons[0].getBoundingClientRect().width;
        const cols = boardRect.width > 900 ? 9 : boardRect.width > 560 ? 7 : 5;
        const gap = size * 0.4;
        const rows = Math.ceil(icons.length / cols);
        const originX = (boardRect.width - (cols * size + (cols - 1) * gap)) / 2;
        const originY = Math.max(0, Math.min(boardRect.height, window.innerHeight) - (rows * size + (rows - 1) * gap)) / 2;
        const slots = icons.map((_, index) => index).sort(() => Math.random() - 0.5);

        const pileTransforms = icons.map((icon, index) => {
          const rect = icon.getBoundingClientRect();
          const slot = slots[index];
          const dx = originX + (slot % cols) * (size + gap) - (rect.left - boardRect.left);
          const dy = originY + Math.floor(slot / cols) * (size + gap) - (rect.top - boardRect.top);
          const rotation = Math.random() * 24 - 12;
          return {dx, dy, rotation, slot};
        });

        icons.forEach((icon, index) => {
          const {dx, dy, rotation} = pileTransforms[index];
          icon.style.transition = "none";
          icon.style.transform = `translate(${dx}px, ${dy}px) rotate(${rotation}deg) scale(.2)`;
        });
        await nextFrame();

        icons.forEach((icon, index) => {
          const {dx, dy, rotation, slot} = pileTransforms[index];
          const delay = slot * 22;
          icon.style.transition = `transform .7s cubic-bezier(.2,.8,.2,1.2) ${delay}ms, opacity .3s ease ${delay}ms`;
          icon.style.opacity = "1";
          icon.style.transform = `translate(${dx}px, ${dy}px) rotate(${rotation}deg) scale(1)`;
        });

        await wait(700 + icons.length * 22 + 700);
        board.classList.remove("is-pile");
        board.classList.add("is-sorting");

        let maxDelay = 0;
        groups.forEach((group, groupIndex) => {
          $$(".sign-group__icons img", group).forEach((icon, index) => {
            const delay = groupIndex * 140 + index * 28;
            maxDelay = Math.max(maxDelay, delay);
            icon.style.transition = `transform 1.1s cubic-bezier(.65,0,.35,1) ${delay}ms`;
            icon.style.transform = "";
          });
        });

        await wait(1100 + maxDelay);
        board.classList.remove("is-sorting");
        board.classList.add("is-sorted");
        icons.forEach((icon) => {
          icon.style.transition = "";
          icon.style.transform = "";
          icon.style.opacity = "";
        });
      }, {threshold: 0.35});
    }
  }

  /* ---------------- Maps: pin → card links and crop → rollout cycles ---------------- */
  const maps = $("[data-maps]");
  if (maps) {
    const svg = $(".maps__links", maps);
    const pins = $$(".map-pin", maps);

    const drawLinks = () => {
      if (getComputedStyle(svg).display === "none") return;
      const mapsRect = maps.getBoundingClientRect();
      svg.setAttribute("viewBox", `0 0 ${mapsRect.width} ${mapsRect.height}`);
      svg.innerHTML = "";
      pins.forEach((pin, index) => {
        const card = $(`[data-card="${pin.dataset.pin}"]`, maps);
        if (!card) return;
        const p = pin.getBoundingClientRect();
        const c = card.getBoundingClientRect();
        const x1 = p.left + p.width / 2 - mapsRect.left;
        const y1 = p.top + p.height / 2 - mapsRect.top;
        const x2 = c.left - mapsRect.left;
        const y2 = c.top + c.height / 2 - mapsRect.top;
        const mid = x1 + (x2 - x1) * 0.55;
        const color = getComputedStyle(pin).backgroundColor;
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", `M${x1},${y1} C${mid},${y1} ${mid},${y2} ${x2},${y2}`);
        path.setAttribute("stroke", color);
        const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        dot.setAttribute("cx", String(x2));
        dot.setAttribute("cy", String(y2));
        dot.setAttribute("r", "4");
        dot.setAttribute("fill", color);
        svg.append(path, dot);
        const length = path.getTotalLength();
        path.style.setProperty("--len", String(length));
        path.style.setProperty("--delay", `${index * 220}ms`);
        dot.style.setProperty("--delay", `${index * 220}ms`);
      });
    };

    onceVisible([maps], async () => {
      await wait(reduceMotion ? 0 : 1000);
      drawLinks();
      await nextFrame();
      maps.classList.add("is-linked");
    }, {threshold: 0.3});

    let resizeTimer = 0;
    window.addEventListener("resize", () => {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(() => {
        if (maps.classList.contains("is-linked")) drawLinks();
      }, 150);
    });

    $$("[data-cycle]", maps).forEach((media, index) => {
      const video = $("video", media);
      let timer = 0;
      let active = false;
      const show = (sim) => {
        media.classList.toggle("is-sim", sim);
        if (sim) video.currentTime = 0;
        refreshVideo(video);
        timer = window.setTimeout(() => show(!sim), sim ? 6500 : 2200);
      };
      const observer = new IntersectionObserver(([entry]) => {
        if (entry.isIntersecting && !active) {
          active = true;
          timer = window.setTimeout(() => show(true), 1400 + index * 500);
        } else if (!entry.isIntersecting && active) {
          active = false;
          window.clearTimeout(timer);
          media.classList.remove("is-sim");
          refreshVideo(video);
        }
      }, {threshold: 0.4});
      observer.observe(media);
    });
  }

  /* ---------------- Equivalent signs across countries ---------------- */
  const equivalents = $("[data-equivalents]");
  if (equivalents) {
    const buttons = $$("[data-eq]", equivalents);
    const images = $$("img[data-country]", equivalents);
    const labels = {yield: "Yield", direction_left: "Turn left"};
    let current = "yield";
    let autoTimer = 0;
    let userPicked = false;

    const select = (type) => {
      if (type === current) return;
      current = type;
      buttons.forEach((button) => button.setAttribute("aria-selected", String(button.dataset.eq === type)));
      images.forEach((image, index) => {
        window.setTimeout(() => {
          image.classList.add("is-flipping");
          window.setTimeout(() => {
            const country = image.dataset.country;
            image.src = `static/site/countries/${type}/${country}.png`;
            image.alt = `${labels[type]} sign in ${image.closest("figure").querySelector("figcaption").firstChild.textContent.trim()}`;
            image.classList.remove("is-flipping");
          }, 260);
        }, index * 70);
      });
    };

    buttons.forEach((button) => button.addEventListener("click", () => {
      userPicked = true;
      window.clearInterval(autoTimer);
      select(button.dataset.eq);
    }));

    onceVisible([equivalents], () => {
      if (reduceMotion) return;
      autoTimer = window.setInterval(() => {
        if (userPicked) return;
        select(current === "yield" ? "direction_left" : "yield");
      }, 4200);
    }, {threshold: 0.5});
  }

  /* ---------------- Fine-tuning before / after ---------------- */
  const ft = $("[data-ft]");
  if (ft) {
    const captions = {
      direction: "PlanT-2 takes the prohibited branch; PlanT-2-FT reroutes.",
      speed: "PlanT-2 ignores the speed limit; PlanT-2-FT slows down.",
    };
    const tabs = $$("[data-ft-tab]", ft);
    const pair = $(".pair", ft);
    const caption = $("[data-ft-caption]", ft);
    const images = $$("[data-ft-image]", ft);
    let ftRequest = 0;

    const showFt = (name) => {
      const request = ++ftRequest;
      tabs.forEach((other) => other.setAttribute("aria-selected", String(other.dataset.ftTab === name)));
      pair.classList.add("is-switching");
      caption.textContent = captions[name];
      let pending = images.length;

      images.forEach((image) => {
        const variant = image.dataset.ftImage;
        const next = `static/site/ft/${name}-${variant}.gif`;
        const finish = () => {
          if (request !== ftRequest) return;
          pending -= 1;
          if (pending <= 0) pair.classList.remove("is-switching");
        };

        // Drop any in-flight load from a previous tab click.
        image.onload = null;
        image.onerror = null;

        if (image.getAttribute("src") === next && image.complete) {
          finish();
          return;
        }

        image.onload = finish;
        image.onerror = finish;
        // Clear first so a slow previous GIF cannot paint over the new tab.
        image.removeAttribute("src");
        image.src = next;
      });
    };

    tabs.forEach((tab) => tab.addEventListener("click", () => showFt(tab.dataset.ftTab)));
  }

  /* ---------------- Citation ---------------- */
  const copyButton = $("#copy-citation");
  const citation = $("#citation-code");
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
})();
