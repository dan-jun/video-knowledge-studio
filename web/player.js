/* ══════════════════════════════════════════════════════════════
   VIDEO FORGE PLAYER — 对标 YouTube 播放器（结构 / 交互 / 视觉 1:1）

   用法：
     const p = new VP(document.getElementById('vp'), {
       src: '/media/video?id=xxx',
       title: '片名',
       sub: '2.4 min · 9 页',
       chapters: [{start:0, label:'P01'}, ...],
       frameAt: (t) => '/media/frame?id=xxx&at=' + t,   // 可选，进度条悬停预览
       next: () => {...},                               // 可选，片尾/下一集
     });

   快捷键（YouTube 同款）：空格/K 播放暂停，J/L ±10s，←/→ ±5s，↑/↓ 音量，
   M 静音，F 全屏，C 字幕，0-9 跳百分比，Shift+,/. 调速，? 显示快捷键。
   ══════════════════════════════════════════════════════════════ */
(function (global) {
  'use strict';

  const ICON = {
    play: '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>',
    pause: '<svg viewBox="0 0 24 24"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>',
    next: '<svg viewBox="0 0 24 24"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>',
    prev: '<svg viewBox="0 0 24 24"><path d="M6 6h2v12H6zM18 6l-8.5 6L18 18V6z"/></svg>',
    vol: '<svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3a4.5 4.5 0 0 0-2.5-4v8a4.5 4.5 0 0 0 2.5-4z"/></svg>',
    volLow: '<svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm11 3a2.5 2.5 0 0 1-1 2v-4a2.5 2.5 0 0 1 1 2z"/></svg>',
    mute: '<svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.6 3l2.6-2.6-1.4-1.4L15.2 10.6 12.6 8 11.2 9.4 13.8 12l-2.6 2.6 1.4 1.4 2.6-2.6 2.6 2.6 1.4-1.4L16.6 12z"/></svg>',
    gear: '<svg viewBox="0 0 24 24"><path d="M19.4 13a7.6 7.6 0 0 0 0-2l2-1.6a.5.5 0 0 0 .1-.6l-1.9-3.3a.5.5 0 0 0-.6-.2l-2.4 1a7.3 7.3 0 0 0-1.7-1L14.5 2.4a.5.5 0 0 0-.5-.4h-4a.5.5 0 0 0-.5.4L9.1 5a7.3 7.3 0 0 0-1.7 1l-2.4-1a.5.5 0 0 0-.6.2L2.5 8.5a.5.5 0 0 0 .1.6L4.6 11a7.6 7.6 0 0 0 0 2l-2 1.6a.5.5 0 0 0-.1.6l1.9 3.3a.5.5 0 0 0 .6.2l2.4-1c.5.4 1.1.8 1.7 1l.4 2.5a.5.5 0 0 0 .5.4h4a.5.5 0 0 0 .5-.4l.4-2.5c.6-.2 1.2-.6 1.7-1l2.4 1a.5.5 0 0 0 .6-.2l1.9-3.3a.5.5 0 0 0-.1-.6L19.4 13zM12 15.5A3.5 3.5 0 1 1 15.5 12 3.5 3.5 0 0 1 12 15.5z"/></svg>',
    full: '<svg viewBox="0 0 24 24"><path d="M7 14H5v5h5v-2H7v-3zm0-4h2V7h3V5H5v5zm10 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>',
    exitFull: '<svg viewBox="0 0 24 24"><path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/></svg>',
    pip: '<svg viewBox="0 0 24 24"><path d="M19 11h-8v6h8v-6zm4 8V5a2 2 0 0 0-2-2H3a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h18a2 2 0 0 0 2-2zm-2 .02H3V4.98h18v14.04z"/></svg>',
    theater: '<svg viewBox="0 0 24 24"><path d="M3 5h18v14H3V5zm2 2v10h14V7H5z"/></svg>',
    cover: '<svg viewBox="0 0 24 24"><path d="M21 3H3a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h18a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1zm-1 15.6l-4.6-4.6-3.1 3.1-2.2-2.2L5 19V5h15v13.6z"/></svg>',
    shot: '<svg viewBox="0 0 24 24"><path d="M9 3l-1.8 2H4a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-3.2L15 3H9zm3 5.5A5.5 5.5 0 1 1 6.5 14 5.5 5.5 0 0 1 12 8.5zm0 2A3.5 3.5 0 1 0 15.5 14 3.5 3.5 0 0 0 12 10.5z"/></svg>',
    cc: '<svg viewBox="0 0 24 24"><path d="M19 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm-8 7H9.5v-.5h-2v3h2V13H11v1a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1zm7 0h-1.5v-.5h-2v3h2V13H18v1a1 1 0 0 1-1 1h-3a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v1z"/></svg>',
    back10: '<svg viewBox="0 0 24 24"><path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z"/></svg>',
    fwd10: '<svg viewBox="0 0 24 24"><path d="M13 6v12l8.5-6L13 6zM4 18l8.5-6L4 6v12z"/></svg>',
  };

  const RATES = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];

  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const fmt = (t) => {
    if (!isFinite(t) || t < 0) t = 0;
    const s = Math.floor(t % 60);
    const m = Math.floor(t / 60) % 60;
    const h = Math.floor(t / 3600);
    const two = (n) => String(n).padStart(2, '0');
    return h > 0 ? `${h}:${two(m)}:${two(s)}` : `${m}:${two(s)}`;
  };

  class VP {
    constructor(root, opt = {}) {
      this.root = root;
      this.opt = opt;
      this.root.classList.add('vp');
      if (!this.root.dataset.skin) this.root.dataset.skin = opt.skin || 'forge';
      this.root.tabIndex = 0;
      this.build();
      this.bind();
      this.attach(opt.src);
      if (opt.title) this.setTitle(opt.title, opt.sub);
      this.setChapters(opt.chapters || []);
    }

    /* ── 结构 ───────────────────────────────────────── */
    build() {
      this.root.innerHTML = `
        <video playsinline preload="metadata"></video>
        <div class="vp-top"><div><div class="vp-title"></div><div class="vp-sub"></div></div></div>
        <div class="vp-center">
          <div class="vp-bigplay" role="button" aria-label="播放">${ICON.play}</div>
          <div class="vp-spinner"></div>
        </div>
        <div class="vp-ripple left"><span>${ICON.back10}<b>10 秒</b></span></div>
        <div class="vp-ripple right"><span>${ICON.fwd10}<b>10 秒</b></span></div>
        <div class="vp-toast"></div>
        <div class="vp-endcard"><div class="card"><b>播放完毕</b><span>可以继续看下一段</span><br><button>重新播放</button></div></div>
        <div class="vp-bottom">
          <div class="vp-progress" role="slider" aria-label="进度" tabindex="0">
            <div class="vp-track">
              <div class="vp-loaded"></div>
              <div class="vp-played"></div>
              <div class="vp-chapters"></div>
            </div>
            <div class="vp-knob"></div>
            <div class="vp-tip noimg"><img alt=""><span>0:00</span></div>
          </div>
          <div class="vp-row">
            <button class="vp-btn" data-act="prev" title="上一段 (Shift+P)" aria-label="上一段">${ICON.prev}</button>
            <button class="vp-btn" data-act="play" title="播放/暂停 (K)" aria-label="播放">${ICON.play}</button>
            <button class="vp-btn" data-act="next" title="下一段 (Shift+N)" aria-label="下一段">${ICON.next}</button>
            <div class="vp-vol">
              <button class="vp-btn" data-act="mute" title="静音 (M)" aria-label="静音">${ICON.vol}</button>
              <div class="vp-vol-slider"><input type="range" min="0" max="1" step="0.01" value="1" aria-label="音量"></div>
            </div>
            <div class="vp-time"><span class="cur">0:00</span> <em>/</em> <span class="dur">0:00</span></div>
            <div class="vp-spacer"></div>
            <button class="vp-btn" data-act="cover" title="存为封面 (C 已占用→用 Shift+C)" aria-label="封面">${ICON.cover || ''}</button>
            <button class="vp-btn" data-act="shot" title="截取当前帧 (S)" aria-label="截图">${ICON.shot || ''}</button>
            <button class="vp-btn" data-act="cc" title="字幕 (C)" aria-label="字幕">${ICON.cc}</button>
            <button class="vp-btn" data-act="gear" title="设置" aria-label="设置">${ICON.gear}</button>
            <button class="vp-btn" data-act="pip" title="画中画 (I)" aria-label="画中画">${ICON.pip}</button>
            <button class="vp-btn" data-act="theater" title="剧场模式 (T)" aria-label="剧场模式">${ICON.theater}</button>
            <button class="vp-btn" data-act="full" title="全屏 (F)" aria-label="全屏">${ICON.full}</button>
          </div>
        </div>
        <div class="vp-menu" role="menu"></div>
      `;
      const q = (s) => this.root.querySelector(s);
      this.video = q('video');
      this.$ = q;
      this.el = {
        top: q('.vp-top'), title: q('.vp-title'), sub: q('.vp-sub'),
        bigplay: q('.vp-bigplay'), spinner: q('.vp-spinner'),
        bottom: q('.vp-bottom'), progress: q('.vp-progress'), track: q('.vp-track'),
        loaded: q('.vp-loaded'), played: q('.vp-played'), knob: q('.vp-knob'),
        chapters: q('.vp-chapters'), tip: q('.vp-tip'), tipImg: q('.vp-tip img'), tipTxt: q('.vp-tip span'),
        cur: q('.cur'), dur: q('.dur'), menu: q('.vp-menu'),
        toast: q('.vp-toast'), endcard: q('.vp-endcard'),
        rippleL: q('.vp-ripple.left'), rippleR: q('.vp-ripple.right'),
        volSlider: q('.vp-vol-slider input'),
        btnPlay: q('[data-act="play"]'), btnMute: q('[data-act="mute"]'), btnCC: q('[data-act="cc"]'),
      };
      this.rate = 1;
      this.ccOn = false;
      this.posKey = 'vf_pos_' + (this.opt.key || '');
      this.qualities = (this.opt && this.opt.qualities) || {};   // {"1440p":{w,h,upscaled}}
      this.quality = (this.opt && this.opt.quality) || null;      // 当前档位（null=母片）
      this.hideTimer = null;
      this.menuView = null;
    }

    /* ── 事件 ───────────────────────────────────────── */
    bind() {
      const v = this.video, e = this.el, R = this.root;

      v.addEventListener('loadedmetadata', () => {
        e.dur.textContent = fmt(v.duration);
        this.sync();
        this._restorePos();
      });
      v.addEventListener('timeupdate', () => { this.sync(); this._savePos(); });
      v.addEventListener('progress', () => this.syncBuffer());
      v.addEventListener('waiting', () => R.classList.add('buffering'));
      v.addEventListener('playing', () => {
        R.classList.remove('buffering', 'paused', 'ended');
        this.setPlayIcon(true);
        this.armHide();
      });
      v.addEventListener('pause', () => {
        R.classList.add('paused');
        this.setPlayIcon(false);
        this.showControls(true);
      });
      v.addEventListener('ended', () => {
        R.classList.add('ended');
        this.showControls(true);
      });
      v.addEventListener('volumechange', () => this.syncVolume());
      v.addEventListener('error', () => {
        this.toast('视频加载失败');
        R.classList.remove('buffering');
      });

      // 中央大按钮
      e.bigplay.addEventListener('click', () => this.toggle());
      e.endcard.querySelector('button').addEventListener('click', () => {
        v.currentTime = 0; this.play();
      });

      // 点击画面：单击播放/暂停，双击全屏；左右双击快进
      let lastTap = 0, tapTimer = null;
      R.addEventListener('click', (ev) => {
        if (ev.target.closest('.vp-bottom, .vp-menu, .vp-top, .vp-endcard, .vp-bigplay')) return;
        const rect = R.getBoundingClientRect();
        const x = (ev.clientX - rect.left) / rect.width;
        const now = Date.now();
        if (now - lastTap < 260) {                 // 双击
          clearTimeout(tapTimer);
          lastTap = 0;
          if (x < 0.3) { this.seekBy(-10, 'left'); }
          else if (x > 0.7) { this.seekBy(10, 'right'); }
          else { this.toggleFull(); }
          return;
        }
        lastTap = now;
        tapTimer = setTimeout(() => {
          if (this.isEnded()) { v.currentTime = 0; this.play(); } else { this.toggle(); }
        }, 250);
      });

      // 控制条按钮
      R.addEventListener('click', (ev) => {
        const b = ev.target.closest('.vp-btn');
        if (!b) return;
        this.act(b.dataset.act);
      });

      // 音量
      e.volSlider.addEventListener('input', () => {
        v.volume = Number(e.volSlider.value);
        v.muted = v.volume === 0;
      });

      // 进度条：拖动 + 悬停预览
      let dragging = false;
      const seekTo = (clientX) => {
        const r = e.track.getBoundingClientRect();
        const p = clamp((clientX - r.left) / r.width, 0, 1);
        if (isFinite(v.duration)) v.currentTime = p * v.duration;
        this.sync();
      };
      e.progress.addEventListener('pointerdown', (ev) => {
        dragging = true;
        R.classList.add('scrubbing');
        seekTo(ev.clientX);                          // 先跳，再尝试捕获指针
        try { e.progress.setPointerCapture(ev.pointerId); } catch (_) { /* 合成事件无活动指针 */ }
      });
      // 兼容只发 mouse 事件的场景
      e.progress.addEventListener('mousedown', (ev) => { if (!dragging) seekTo(ev.clientX); });
      e.progress.addEventListener('pointermove', (ev) => {
        if (dragging) seekTo(ev.clientX);
        this.showTip(ev.clientX);
      });
      e.progress.addEventListener('pointerup', () => {
        dragging = false;
        R.classList.remove('scrubbing');
      });
      e.progress.addEventListener('pointerleave', () => e.tip.classList.remove('show'));
      e.progress.addEventListener('keydown', (ev) => {
        if (ev.key === 'ArrowRight') { this.seekBy(5); ev.preventDefault(); }
        if (ev.key === 'ArrowLeft') { this.seekBy(-5); ev.preventDefault(); }
      });

      // 自动隐藏
      R.addEventListener('pointermove', () => { this.showControls(); this.armHide(); });
      R.addEventListener('pointerleave', () => this.armHide());
      R.addEventListener('focusin', () => this.showControls(true));

      // 全屏状态
      document.addEventListener('fullscreenchange', () => this.syncFullIcon());

      // 键盘
      document.addEventListener('keydown', (ev) => this.onKey(ev));
    }

    onKey(ev) {
      // 焦点在输入框里时不抢键
      const tag = (ev.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea' || ev.target.isContentEditable) return;
      if (!this.root.isConnected) return;
      const near = this.root.getBoundingClientRect();
      const inView = near.bottom > 0 && near.top < innerHeight;
      if (!inView && !this.root.contains(document.activeElement)) return;

      const k = ev.key, v = this.video;
      const shift = ev.shiftKey;
      let handled = true;
      if (k === ' ' || k === 'k' || k === 'K') this.toggle();
      else if (k === 'j' || k === 'J') this.seekBy(-10);
      else if (k === 'l' || k === 'L') this.seekBy(10);
      else if (k === 'ArrowLeft') this.seekBy(shift ? -1 : -5);
      else if (k === 'ArrowRight') this.seekBy(shift ? 1 : 5);
      else if (k === 'ArrowUp') this.nudgeVolume(0.05);
      else if (k === 'ArrowDown') this.nudgeVolume(-0.05);
      else if (k === 'm' || k === 'M') this.act('mute');
      else if (k === 'f' || k === 'F') this.toggleFull();
      else if (k === 't' || k === 'T') this.act('theater');
      else if (k === 'Escape' && document.body.classList.contains('vp-theater')) {
        document.body.classList.remove('vp-theater');
        this.toast('退出剧场模式');
      }
      else if (k === 'i' || k === 'I') this.act('pip');
      else if (k === 's' || k === 'S') this.act('shot');
      else if (k === 'C') this.act('cover');
      else if (k === 'c' || k === 'C') this.act('cc');
      else if (k === 'Home') v.currentTime = 0;
      else if (k === 'End') v.currentTime = Math.max(0, v.duration - 0.1);
      else if (/^[0-9]$/.test(k)) v.currentTime = v.duration * (Number(k) / 10);
      else if (k === '?' || (k === '/' && shift)) this.shortcuts();
      else if (k === '.' && shift) this.setRate(this.nextRate(1));
      else if (k === ',' && shift) this.setRate(this.nextRate(-1));
      else handled = false;
      if (handled) { ev.preventDefault(); this.showControls(); this.armHide(); }
    }

    /* ── 播放控制 ───────────────────────────────────── */
    toggle() { this.video.paused ? this.play() : this.video.pause(); }
    play() { this.video.play().catch(() => {}); }
    isEnded() { return this.root.classList.contains('ended'); }
    seekBy(sec, side) {
      const v = this.video;
      v.currentTime = clamp(v.currentTime + sec, 0, v.duration || 0);
      this.flashRipple(side);
      this.toast((sec > 0 ? '+' : '') + sec + 's');
    }
    nudgeVolume(d) {
      const v = this.video;
      v.volume = clamp(v.volume + d, 0, 1);
      v.muted = v.volume === 0;
      this.toast('音量 ' + Math.round(v.volume * 100) + '%');
    }
    act(a) {
      const v = this.video;
      switch (a) {
        case 'play': this.toggle(); break;
        case 'next': this.jumpChapter(1); break;
        case 'prev': this.jumpChapter(-1); break;
        case 'mute':
          v.muted = !v.muted;
          if (!v.muted && v.volume === 0) v.volume = 0.6;
          break;
        case 'cover': this.opt.onCover && this.opt.onCover(); break;
        case 'shot': this.screenshot(); break;
        case 'cc':
          this.ccOn = !this.ccOn;
          this.el.btnCC.classList.toggle('on', this.ccOn);
          this.toast(this.ccOn ? '字幕：开（本片为硬字幕）' : '字幕：关（硬字幕无法关闭）');
          break;
        case 'gear': this.openMenu('settings'); break;
        case 'pip': this.togglePip(); break;
        case 'theater': this.toggleTheater(); break;
        case 'full': this.toggleFull(); break;
      }
    }

    jumpChapter(dir) {
      const chs = this.chapters || [];
      const t = this.video.currentTime;
      if (!chs.length) { this.seekBy(dir > 0 ? 30 : -30); return; }
      if (dir > 0) {
        const nxt = chs.find((c) => c.start > t + 0.5);
        if (nxt) { this.video.currentTime = nxt.start + 0.05; this.toast(nxt.label || ''); }
        else if (this.opt.next) this.opt.next();
      } else {
        const cur = [...chs].reverse().find((c) => c.start < t - 1.2);
        this.video.currentTime = (cur ? cur.start : 0) + 0.05;
        this.toast(cur ? cur.label : '开头');
      }
    }

    nextRate(dir) {
      const i = RATES.indexOf(this.rate);
      const n = clamp((i < 0 ? RATES.indexOf(1) : i) + dir, 0, RATES.length - 1);
      return RATES[n];
    }
    setRate(r) {
      this.rate = r;
      this.video.playbackRate = r;
      this.toast('速度 ' + r + '×');
      this.syncMenu();
    }

    /** 截取当前帧为 PNG（做封面 / 对稿留证） */
    screenshot() {
      const v = this.video;
      if (!v.videoWidth) { this.toast('画面还没就绪'); return; }
      const c = document.createElement('canvas');
      c.width = v.videoWidth; c.height = v.videoHeight;
      const ctx = c.getContext('2d');
      ctx.drawImage(v, 0, 0, c.width, c.height);
      const t = Math.floor(v.currentTime);
      const name = (this.opt.key || 'frame') + '_' + String(Math.floor(t / 60)).padStart(2, '0')
        + String(t % 60).padStart(2, '0') + '.png';
      c.toBlob((blob) => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = name;
        a.click();
        setTimeout(() => URL.revokeObjectURL(a.href), 4000);
      }, 'image/png');
      this.toast('已截取 ' + fmt(t));
    }

    _restorePos() {
      const v = this.video;
      if (this._posRestored) return;
      this._posRestored = true;
      if (!this.posKey || !this.opt.key) return;
      try {
        const raw = localStorage.getItem(this.posKey);
        if (!raw) return;
        const t = Number(raw);
        if (!isFinite(t) || t < 5) return;
        if (v.duration && t > v.duration - 8) return;   // 快看完了就别恢复
        v.currentTime = t;
        this.toast('从 ' + fmt(t) + ' 继续');
      } catch (e) {}
    }
    _savePos() {
      if (!this.opt.key) return;
      const v = this.video;
      if (!v.duration) return;
      try { localStorage.setItem(this.posKey, String(Math.floor(v.currentTime))); } catch (e) {}
    }

    qualityLabel() {
      const q = this.quality;
      if (!q) return '母片';
      const v = (this.qualities || {})[q];
      return v ? `${v.h}p` : q;
    }

    /** 切画质：记住播放位置与播放状态，换源后恢复 */
    switchQuality(q) {
      if (q === this.quality) return;
      const v = this.video;
      const t = v.currentTime;
      const playing = !v.paused;
      const base = this.opt.srcBase;
      if (!base) { this.toast('缺少 srcBase，无法切档'); return; }
      this.quality = q;
      v.src = base + (q ? (base.includes('?') ? '&' : '?') + 'q=' + encodeURIComponent(q) : '');
      const resume = () => {
        try { v.currentTime = t; } catch (e) {}
        if (playing) v.play().catch(() => {});
        v.removeEventListener('loadedmetadata', resume);
      };
      v.addEventListener('loadedmetadata', resume);
      v.load();
      this.toast('画质：' + this.qualityLabel());
      this.syncMenu();
    }

    togglePip() {
      const v = this.video;
      if (document.pictureInPictureElement) document.exitPictureInPicture().catch(() => {});
      else if (v.requestPictureInPicture) v.requestPictureInPicture().catch(() => this.toast('画中画不可用'));
      else this.toast('浏览器不支持画中画');
    }

    toggleTheater() {
      const on = !document.body.classList.contains('vp-theater');
      document.body.classList.toggle('vp-theater', on);
      const b = this.root.querySelector('[data-act="theater"]');
      if (b) b.classList.toggle('on', on);
      this.toast(on ? '剧场模式（Esc 退出）' : '退出剧场模式');
    }

    toggleFull() {
      const R = this.root;
      if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
      else if (R.requestFullscreen) R.requestFullscreen().catch(() => {});
      else if (R.webkitRequestFullscreen) R.webkitRequestFullscreen();
    }

    /* ── 同步画面 ───────────────────────────────────── */
    sync() {
      const v = this.video, e = this.el;
      const d = isFinite(v.duration) ? v.duration : 0;
      const p = d ? (v.currentTime / d) * 100 : 0;
      e.played.style.width = p + '%';
      e.knob.style.left = p + '%';
      e.cur.textContent = fmt(v.currentTime);
      if (d) e.dur.textContent = fmt(d);
    }
    syncBuffer() {
      const v = this.video;
      if (!v.buffered.length || !isFinite(v.duration)) return;
      let end = 0;
      for (let i = 0; i < v.buffered.length; i++) {
        if (v.buffered.start(i) <= v.currentTime + 0.25) end = Math.max(end, v.buffered.end(i));
      }
      this.el.loaded.style.width = (v.duration ? (end / v.duration) * 100 : 0) + '%';
    }
    syncVolume() {
      const v = this.video, e = this.el;
      const val = v.muted ? 0 : v.volume;
      e.volSlider.value = String(val);
      e.btnMute.innerHTML = v.muted || v.volume === 0 ? ICON.mute : v.volume < 0.5 ? ICON.volLow : ICON.vol;
    }
    setPlayIcon(playing) {
      this.el.btnPlay.innerHTML = playing ? ICON.pause : ICON.play;
      this.el.btnPlay.setAttribute('aria-label', playing ? '暂停' : '播放');
      this.root.classList.toggle('paused', !playing);
    }
    syncFullIcon() {
      const b = this.root.querySelector('[data-act="full"]');
      b.innerHTML = document.fullscreenElement ? ICON.exitFull : ICON.full;
    }

    /* ── 控件显隐 ───────────────────────────────────── */
    armHide() {
      clearTimeout(this.hideTimer);
      if (this.video.paused) { this.root.classList.remove('autohide'); return; }
      this.hideTimer = setTimeout(() => this.root.classList.add('autohide'), 2600);
    }
    showControls(force) {
      this.root.classList.remove('autohide');
      if (!force && this.video.paused) return;
    }
    flashRipple(side) {
      const el = side === 'left' ? this.el.rippleL : side === 'right' ? this.el.rippleR : null;
      if (!el) return;
      el.classList.add('show');
      setTimeout(() => el.classList.remove('show'), 620);
    }
    toast(msg) {
      const t = this.el.toast;
      t.textContent = msg;
      t.classList.add('show');
      clearTimeout(this.tTimer);
      this.tTimer = setTimeout(() => t.classList.remove('show'), 900);
    }
    shortcuts() {
      this.toast('空格/K 播放 · J/L ±10s · ←/→ ±5s · ↑/↓ 音量 · M 静音 · F 全屏 · T 剧场 · I 画中画 · 0-9 跳段 · >/< 调速');
    }

    /* ── 进度条悬停预览 ─────────────────────────────── */
    showTip(clientX) {
      const v = this.video, e = this.el;
      if (!isFinite(v.duration) || !v.duration) return;
      const r = e.track.getBoundingClientRect();
      const p = clamp((clientX - r.left) / r.width, 0, 1);
      const t = p * v.duration;
      e.tip.style.left = clientX - r.left + 'px';
      e.tipTxt.textContent = fmt(t);
      e.tip.classList.add('show');
      if (this.opt.frameAt) {
        const url = this.opt.frameAt(t);
        if (url && this._tipUrl !== url) {
          this._tipUrl = url;
          e.tipImg.src = url;
          e.tipImg.onload = () => e.tip.classList.remove('noimg');
          e.tipImg.onerror = () => e.tip.classList.add('noimg');
        }
      } else {
        e.tip.classList.add('noimg');
      }
    }

    /* ── 菜单 ───────────────────────────────────────── */
    openMenu(view) {
      this.menuView = view || 'settings';
      this.renderMenu();
      this.el.menu.classList.add('open');
    }
    closeMenu() { this.el.menu.classList.remove('open'); }
    renderMenu() {
      const m = this.el.menu;
      const v = this.video;
      const mi = (lab, val, act, sel) =>
        `<div class="vp-mi${sel ? ' sel' : ''}" data-m="${act}">${lab}${val ? `<span class="v">${val}</span>` : ''}</div>`;
      if (this.menuView === 'speed') {
        m.innerHTML = `<h4>播放速度</h4>` +
          RATES.map((r) => mi((r === 1 ? '正常' : r + '×'), '', 'rate:' + r, this.rate === r)).join('');
      } else if (this.menuView === 'quality') {
        const qs = this.qualities || {};
        const keys = Object.keys(qs).sort((a, b) => qs[b].h - qs[a].h);
        if (!keys.length) {
          m.innerHTML = `<h4>画质</h4>` + mi('母片（未转多档）', '', 'noop', true) +
            `<div class="vp-mi" data-m="noop" style="padding-left:14px;color:var(--vp-dim);font-size:12px">跑 tools/make_variants.py 可生成多档</div>`;
        } else {
          m.innerHTML = `<h4>画质</h4>` +
            keys.map((k) => {
              const v = qs[k];
              const tag = v.upscaled ? ' · 放大' : '';
              return mi(`${v.h}p${tag}`, `${v.w}×${v.h}`, 'q:' + k, this.quality === k);
            }).join('') +
            mi('母片', '', 'q:', !this.quality);
        }
      } else if (this.menuView === 'captions') {
        m.innerHTML = `<h4>字幕</h4>` +
          mi('关闭', '', 'cc:off', !this.ccOn) + mi('打开（硬字幕）', '', 'cc:on', this.ccOn);
      } else {
        m.innerHTML = `<h4>设置</h4>` +
          mi('播放速度', this.rate + '×', 'view:speed') +
          mi('画质', this.qualityLabel(), 'view:quality') +
          mi('字幕', this.ccOn ? '开' : '关', 'view:captions') +
          `<hr>` +
          mi('键盘快捷键', '?', 'shortcuts') +
          mi('从头播放', '', 'restart');
      }
      m.querySelectorAll('[data-m]').forEach((el) => {
        el.addEventListener('click', (ev) => {
          ev.stopPropagation();
          const a = el.dataset.m;
          if (a.startsWith('view:')) { this.menuView = a.slice(5); this.renderMenu(); return; }
          if (a.startsWith('rate:')) { this.setRate(Number(a.slice(5))); this.openMenu('settings'); return; }
          if (a === 'shortcuts') { this.shortcuts(); this.closeMenu(); return; }
          if (a === 'restart') { v.currentTime = 0; this.play(); this.closeMenu(); return; }
          if (a.startsWith('q:')) {
            this.switchQuality(a.slice(2) || null);
            this.openMenu('settings');
            return;
          }
          if (a.startsWith('cc:')) { this.ccOn = a.endsWith('on'); this.el.btnCC.classList.toggle('on', this.ccOn); this.openMenu('settings'); return; }
          this.closeMenu();
        });
      });
    }
    syncMenu() { if (this.el.menu.classList.contains('open')) this.renderMenu(); }

    /* ── 对外接口 ───────────────────────────────────── */
    attach(src) {
      this.opt.srcBase = src;        // 切档时在它后面拼 &q=
      this.video.src = src;
      this.video.load();
      this.syncVolume();
      this.setPlayIcon(false);
      this.root.classList.add('paused');
      this.el.loaded.style.width = '0';
    }
    setTitle(t, sub) {
      this.el.title.textContent = t || '';
      this.el.sub.textContent = sub || '';
      this.el.title.title = t || '';
    }
    setChapters(list) {
      this.chapters = (list || []).slice().sort((a, b) => a.start - b.start);
      const box = this.el.chapters;
      box.innerHTML = '';
      const d = this.video.duration;
      if (!d || !isFinite(d)) { this._pendingChapters = list; return; }
      this.chapters.forEach((c) => {
        if (c.start <= 0) return;
        const i = document.createElement('i');
        i.style.left = (c.start / d) * 100 + '%';
        i.title = c.label || '';
        box.appendChild(i);
      });
    }
    destroy() { this.root.innerHTML = ''; this.root.classList.remove('vp'); }
  }

  // 元数据到位后补画章节刻度
  const origAttach = VP.prototype.attach;
  VP.prototype.attach = function (src) {
    origAttach.call(this, src);
    this.video.addEventListener('loadedmetadata', () => {
      if (this._pendingChapters) { const p = this._pendingChapters; this._pendingChapters = null; this.setChapters(p); }
      else this.setChapters(this.chapters || []);
    }, { once: false });
  };

  global.VP = VP;
  if (typeof module !== 'undefined' && module.exports) module.exports = VP;
})(typeof window !== 'undefined' ? window : globalThis);
