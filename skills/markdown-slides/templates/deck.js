/* ===========================================
           SLIDE PRESENTATION CONTROLLER
           Keyboard, wheel, swipe; 1920×1080 stage scale.
           User zoom (pinch / Ctrl+wheel) sits on top of fit-to-viewport.
           =========================================== */
        class SlidePresentation {
            constructor() {
                this.slides = document.querySelectorAll(".slide");
                this.currentSlide = 0;
                this.stage = document.getElementById("deckStage");
                this.progress = document.getElementById("progressBar");
                this.touchStartX = 0;
                this.wheelLock = false;
                this.gotoBuffer = "";
                this.fitFactor = 1;
                this.userZoom = 1;
                this.panX = 0;
                this.panY = 0;
                this.minZoom = 1;
                this.maxZoom = 3;
                this.drag = null;
                this.setupStageScale();
                this.setupKeyboardNav();
                this.setupTouchNav();
                this.setupWheelNav();
                this.setupPanDrag();
                this.setupHashNav();
                this.showSlide(this.slideFromHash());
            }

            setupStageScale() {
                const onResize = () => {
                    this.applyStageTransform();
                };
                onResize();
                window.addEventListener("resize", onResize);
            }

            applyStageTransform() {
                this.fitFactor = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
                const scale = this.fitFactor * this.userZoom;
                // Center the unscaled stage, then apply user pan (screen px).
                const baseX = (window.innerWidth - 1920 * this.fitFactor) / 2;
                const baseY = (window.innerHeight - 1080 * this.fitFactor) / 2;
                this.clampPan();
                const x = baseX + this.panX;
                const y = baseY + this.panY;
                this.stage.style.transform = `translate(${x}px, ${y}px) scale(${scale})`;
                document.body.classList.toggle("deck-zoomed", this.userZoom > 1.001);
            }

            clampPan() {
                if (this.userZoom <= 1.001) {
                    this.panX = 0;
                    this.panY = 0;
                    return;
                }
                // Stage top-left on screen is (baseX + panX, baseY + panY) with
                // transform-origin 0 0 and scale = fitFactor * userZoom.
                // Allow panning until each stage edge can reach the viewport edge
                // (old clamp used half the overflow, so bottom-right stayed clipped).
                const baseX = (window.innerWidth - 1920 * this.fitFactor) / 2;
                const baseY = (window.innerHeight - 1080 * this.fitFactor) / 2;
                const stageW = 1920 * this.fitFactor * this.userZoom;
                const stageH = 1080 * this.fitFactor * this.userZoom;
                const minX = Math.min(0, window.innerWidth - baseX - stageW);
                const maxX = Math.max(0, -baseX);
                const minY = Math.min(0, window.innerHeight - baseY - stageH);
                const maxY = Math.max(0, -baseY);
                this.panX = Math.max(minX, Math.min(maxX, this.panX));
                this.panY = Math.max(minY, Math.min(maxY, this.panY));
            }

            setUserZoom(next, originX, originY) {
                const prev = this.userZoom;
                const zoom = Math.max(this.minZoom, Math.min(this.maxZoom, next));
                if (Math.abs(zoom - prev) < 0.0001) return;
                // Keep the point under the cursor stable when possible.
                if (originX != null && originY != null && prev > 0) {
                    const baseX = (window.innerWidth - 1920 * this.fitFactor) / 2;
                    const baseY = (window.innerHeight - 1080 * this.fitFactor) / 2;
                    const stageX = (originX - baseX - this.panX) / (this.fitFactor * prev);
                    const stageY = (originY - baseY - this.panY) / (this.fitFactor * prev);
                    this.userZoom = zoom;
                    this.panX = originX - baseX - stageX * this.fitFactor * zoom;
                    this.panY = originY - baseY - stageY * this.fitFactor * zoom;
                } else {
                    this.userZoom = zoom;
                }
                if (this.userZoom <= 1.001) {
                    this.userZoom = 1;
                    this.panX = 0;
                    this.panY = 0;
                }
                this.applyStageTransform();
            }

            resetZoom() {
                this.userZoom = 1;
                this.panX = 0;
                this.panY = 0;
                this.applyStageTransform();
            }

            setupKeyboardNav() {
                document.addEventListener("keydown", (e) => {
                    if (e.target && e.target.getAttribute("contenteditable") === "true") return;
                    if (["INPUT", "TEXTAREA"].includes(e.target.tagName)) return;
                    if (e.key === "ArrowRight" || e.key === "ArrowDown" || e.key === " " || e.key === "PageDown") {
                        e.preventDefault();
                        this.gotoBuffer = "";
                        this.next();
                    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp" || e.key === "PageUp") {
                        e.preventDefault();
                        this.gotoBuffer = "";
                        this.prev();
                    } else if (e.key === "Home") {
                        e.preventDefault();
                        this.gotoBuffer = "";
                        this.showSlide(0);
                    } else if (e.key === "End") {
                        e.preventDefault();
                        this.gotoBuffer = "";
                        this.showSlide(this.slides.length - 1);
                    } else if (/^[0-9]$/.test(e.key) && !e.metaKey && !e.ctrlKey && !e.altKey) {
                        // While zoomed, bare 0 resets zoom; otherwise digits build a page-goto buffer.
                        if (e.key === "0" && !this.gotoBuffer && this.userZoom > 1.001) {
                            e.preventDefault();
                            this.resetZoom();
                            return;
                        }
                        e.preventDefault();
                        this.gotoBuffer += e.key;
                    } else if (e.key === "Enter" && this.gotoBuffer) {
                        e.preventDefault();
                        this.showSlide(parseInt(this.gotoBuffer, 10) - 1);
                        this.gotoBuffer = "";
                    } else if (e.key === "Escape") {
                        this.gotoBuffer = "";
                        if (this.userZoom > 1.001) {
                            e.preventDefault();
                            this.resetZoom();
                        }
                    } else if (e.key === "f" || e.key === "F") {
                        e.preventDefault();
                        if (document.fullscreenElement) {
                            document.exitFullscreen();
                        } else {
                            document.documentElement.requestFullscreen();
                        }
                    } else if (e.key === "=" || e.key === "+") {
                        e.preventDefault();
                        this.setUserZoom(this.userZoom * 1.15, window.innerWidth / 2, window.innerHeight / 2);
                    } else if (e.key === "-" || e.key === "_") {
                        e.preventDefault();
                        this.setUserZoom(this.userZoom / 1.15, window.innerWidth / 2, window.innerHeight / 2);
                    }
                });
            }

            setupTouchNav() {
                document.addEventListener("touchstart", (e) => {
                    this.touchStartX = e.changedTouches[0].screenX;
                }, { passive: true });
                document.addEventListener("touchend", (e) => {
                    if (this.userZoom > 1.001) return;
                    const dx = e.changedTouches[0].screenX - this.touchStartX;
                    if (Math.abs(dx) < 50) {
                        if (e.changedTouches[0].clientX > window.innerWidth * 0.7) this.next();
                        else if (e.changedTouches[0].clientX < window.innerWidth * 0.3) this.prev();
                        return;
                    }
                    if (dx < 0) this.next();
                    else this.prev();
                }, { passive: true });
            }

            setupWheelNav() {
                // Non-passive so Ctrl/pinch zoom can preventDefault (Chrome trackpad pinch).
                window.addEventListener("wheel", (e) => {
                    const inScrollCard = e.target && e.target.closest && e.target.closest(".card.scroll");
                    // Pinch zoom / Ctrl+wheel → user zoom (never flip slides).
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        const intensity = Math.exp(-e.deltaY * 0.01);
                        this.setUserZoom(this.userZoom * intensity, e.clientX, e.clientY);
                        return;
                    }
                    // Zoomed in: pan with the wheel instead of changing slides.
                    if (this.userZoom > 1.001) {
                        if (inScrollCard) return;
                        e.preventDefault();
                        this.panX -= e.deltaX;
                        this.panY -= e.deltaY;
                        this.applyStageTransform();
                        return;
                    }
                    // Fit mode: scrollable cards keep the wheel; otherwise flip slides.
                    if (inScrollCard) return;
                    if (this.wheelLock) return;
                    if (Math.abs(e.deltaY) < 20) return;
                    this.wheelLock = true;
                    if (e.deltaY > 0) this.next();
                    else this.prev();
                    setTimeout(() => { this.wheelLock = false; }, 450);
                }, { passive: false });
            }

            setupPanDrag() {
                const onMove = (e) => {
                    if (!this.drag) return;
                    this.panX = this.drag.originPanX + (e.clientX - this.drag.startX);
                    this.panY = this.drag.originPanY + (e.clientY - this.drag.startY);
                    this.applyStageTransform();
                };
                const onUp = () => {
                    this.drag = null;
                    document.body.classList.remove("deck-panning");
                };
                window.addEventListener("pointerdown", (e) => {
                    if (this.userZoom <= 1.001) return;
                    if (e.button !== 0) return;
                    if (e.target && e.target.closest && e.target.closest(".card.scroll, a, button, [contenteditable='true']")) {
                        return;
                    }
                    this.drag = {
                        startX: e.clientX,
                        startY: e.clientY,
                        originPanX: this.panX,
                        originPanY: this.panY,
                    };
                    document.body.classList.add("deck-panning");
                });
                window.addEventListener("pointermove", onMove);
                window.addEventListener("pointerup", onUp);
                window.addEventListener("pointercancel", onUp);
            }

            next() { this.showSlide(this.currentSlide + 1); }
            prev() { this.showSlide(this.currentSlide - 1); }

            slideFromHash() {
                const n = parseInt(String(location.hash || "").replace(/^#/, ""), 10);
                if (!Number.isFinite(n) || n < 1) return 0;
                return n - 1;
            }

            setupHashNav() {
                window.addEventListener("hashchange", () => {
                    const index = this.slideFromHash();
                    if (index !== this.currentSlide) this.showSlide(index, { skipHash: true });
                });
            }

            showSlide(index, opts) {
                this.currentSlide = Math.max(0, Math.min(index, this.slides.length - 1));
                this.slides.forEach((slide, i) => {
                    slide.classList.toggle("active", i === this.currentSlide);
                    slide.classList.toggle("visible", i === this.currentSlide);
                });
                if (this.progress) {
                    this.progress.style.width = ((this.currentSlide + 1) / this.slides.length * 100) + "%";
                }
                if (!opts || !opts.skipHash) {
                    const hash = "#" + (this.currentSlide + 1);
                    if (location.hash !== hash) {
                        history.replaceState(null, "", hash);
                    }
                }
            }
        }

        /* ===========================================
           INLINE EDITOR
           Hover top-left or press E. Click text to edit.
           Ctrl/Cmd+S saves to localStorage and downloads.
           =========================================== */
        class InlineEditor {
            constructor() {
                this.isActive = false;
                this.storageKey = "markdown-slides:__DECK_NAME__";
                this.selectors = ".slide h1, .slide h2, .slide h3, .slide p, .slide li, .slide td, .slide th, .slide .overline, .slide .summary, .slide .sub, .slide .wk, .slide .foot span, .slide .num, .title-square, .slide .meta-row span, .slide .cover-session .lbl, .slide .cover-session .val";
                this.restore();
            }

            editableNodes() {
                return document.querySelectorAll(this.selectors);
            }

            toggleEditMode() {
                this.isActive = !this.isActive;
                document.body.classList.toggle("editing", this.isActive);
                document.getElementById("editToggle").classList.toggle("active", this.isActive);
                this.editableNodes().forEach((el) => {
                    el.setAttribute("contenteditable", this.isActive ? "true" : "false");
                });
            }

            persist() {
                const html = document.getElementById("deckStage").innerHTML;
                try { localStorage.setItem(this.storageKey, html); } catch (err) { /* ignore quota */ }
            }

            restore() {
                try {
                    const html = localStorage.getItem(this.storageKey);
                    if (!html) return;
                    const stage = document.getElementById("deckStage");
                    const liveCount = stage.querySelectorAll(".slide").length;
                    const probe = document.createElement("div");
                    probe.innerHTML = html;
                    if (probe.querySelectorAll(".slide").length !== liveCount) {
                        localStorage.removeItem(this.storageKey);
                        return;
                    }
                    stage.innerHTML = html;
                } catch (err) { /* ignore */ }
            }

            download() {
                this.persist();
                const blob = new Blob([document.documentElement.outerHTML], { type: "text/html" });
                const a = document.createElement("a");
                a.href = URL.createObjectURL(blob);
                a.download = "__DECK_NAME__.html";
                a.click();
                URL.revokeObjectURL(a.href);
            }
        }

        const editor = new InlineEditor();
        const deck = new SlidePresentation();

        document.getElementById("editToggle").addEventListener("click", () => editor.toggleEditMode());

        const hotzone = document.querySelector(".edit-hotzone");
        const editToggle = document.getElementById("editToggle");
        let hideTimeout = null;
        const showToggle = () => {
            clearTimeout(hideTimeout);
            editToggle.classList.add("show");
        };
        const hideToggle = () => {
            hideTimeout = setTimeout(() => {
                if (!editor.isActive) editToggle.classList.remove("show");
            }, 400);
        };
        hotzone.addEventListener("mouseenter", showToggle);
        hotzone.addEventListener("mouseleave", hideToggle);
        editToggle.addEventListener("mouseenter", showToggle);
        editToggle.addEventListener("mouseleave", hideToggle);
        hotzone.addEventListener("click", () => editor.toggleEditMode());

        document.addEventListener("keydown", (e) => {
            if ((e.key === "e" || e.key === "E") && !e.target.getAttribute("contenteditable")) {
                editor.toggleEditMode();
            }
            if ((e.metaKey || e.ctrlKey) && e.key === "s") {
                e.preventDefault();
                editor.download();
            }
        });
