"use client";
import { useEffect, useRef, useState } from "react";
import Mark from "./Mark";
import { faqs, site } from "@/lib/site";
const arrow = (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    aria-hidden="true"
  >
    <path
      d="M5 12h14m-6-6 6 6-6 6"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);
function Download({ small = false }: { small?: boolean }) {
  return (
    <a
      className={`button primary ${small ? "small" : ""}`}
      href="/api/download"
    >
      <svg
        width="15"
        height="18"
        viewBox="0 0 24 24"
        fill="currentColor"
        aria-hidden="true"
      >
        <path d="M17.1 12.5c0-2.2 1.8-3.3 1.9-3.4-1-1.5-2.6-1.7-3.2-1.7-1.4-.1-2.7.8-3.4.8-.7 0-1.8-.8-3-.8-1.6 0-3 .9-3.8 2.3-1.6 2.8-.4 7 1.1 9.3.8 1.1 1.6 2.2 2.8 2.1 1.1 0 1.5-.7 2.9-.7 1.3 0 1.7.7 2.9.7 1.2 0 2-1.1 2.7-2.1.9-1.3 1.2-2.6 1.2-2.7-.1 0-2.1-.8-2.1-3.8ZM14.8 5.9c.6-.8 1.1-1.8 1-2.9-1 .1-2.1.7-2.8 1.5-.6.7-1.2 1.8-1.1 2.8 1.1.1 2.2-.6 2.9-1.4Z" />
      </svg>
      {small ? "Download" : "Download for Mac"}
    </a>
  );
}
function Demo() {
  const a = useRef<HTMLAudioElement>(null);
  const b = useRef<HTMLAudioElement>(null);
  const [enhanced, setEnhanced] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(8.69);
  const [error, setError] = useState("");
  const [peaks, setPeaks] = useState<number[]>([]);
  useEffect(() => {
    fetch("/audio/peaks.json")
      .then((r) => r.json())
      .then((x) => setPeaks(x))
      .catch(() => {});
    return () => {
      a.current?.pause();
      b.current?.pause();
    };
  }, []);
  const switchTo = (v: boolean) => {
    const from = enhanced ? b.current : a.current,
      to = v ? b.current : a.current;
    if (!from || !to || v === enhanced) return;
    to.currentTime = from.currentTime;
    from.pause();
    setEnhanced(v);
    if (playing)
      to.play().catch(() => {
        setPlaying(false);
        setError("Tap play to continue.");
      });
  };
  const toggle = async () => {
    const audio = enhanced ? b.current : a.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
      setPlaying(false);
    } else {
      try {
        await audio.play();
        setPlaying(true);
        setError("");
      } catch {
        setError("Audio could not play. Please try again.");
      }
    }
  };
  return (
    <div className="demo-wrap" id="demo">
      <div className="demo-top">
        <span className="demo-title">
          <Mark size={18} />
          voicy
        </span>
        <span className="demo-file">A little less noise.wav</span>
        <span className="demo-meta">00:08</span>
      </div>
      <div className="demo-body">
        <div className="demo-copy">
          <span>{enhanced ? "Just the voice." : "Hear the difference."}</span>
          <p>
            {enhanced
              ? "Enhanced with Voicy"
              : "A voice, a fan, a little echo."}
          </p>
        </div>
        <div
          className={`wave ${playing ? "playing" : ""} ${enhanced ? "enhanced" : ""}`}
          aria-hidden="true"
        >
          {Array.from({ length: 96 }, (_, i) => (
            <i
              key={i}
              className={i / 96 <= time / duration ? "heard" : ""}
              style={{
                height: `${12 + (peaks[i] ?? Math.abs(Math.sin(i * 0.7))) * 75}%`,
                animationDelay: `${i * 13}ms`,
              }}
            />
          ))}
        </div>
        <div className="player">
          <button
            className="play"
            onClick={toggle}
            aria-label={playing ? "Pause demo" : "Play demo"}
          >
            {playing ? (
              <svg viewBox="0 0 20 20">
                <path
                  d="M7 4v12M13 4v12"
                  stroke="currentColor"
                  strokeWidth="3"
                />
              </svg>
            ) : (
              <svg viewBox="0 0 20 20">
                <path d="m7 4 9 6-9 6Z" fill="currentColor" />
              </svg>
            )}
          </button>
          <input
            aria-label="Seek demo"
            type="range"
            min="0"
            max={duration}
            step=".01"
            value={time}
            onChange={(e) => {
              const t = Number(e.target.value);
              if (a.current) a.current.currentTime = t;
              if (b.current) b.current.currentTime = t;
              setTime(t);
            }}
          />
          <span className="time">
            0:{Math.floor(time).toString().padStart(2, "0")} / 0:08
          </span>
          <div
            className="ab"
            role="group"
            aria-label="Compare original and enhanced audio"
          >
            <button aria-pressed={!enhanced} onClick={() => switchTo(false)}>
              Original
            </button>
            <button aria-pressed={enhanced} onClick={() => switchTo(true)}>
              Voicy <span>✦</span>
            </button>
          </div>
        </div>
        {error && (
          <p role="alert" className="audio-error">
            {error}
          </p>
        )}
      </div>
      <audio
        ref={a}
        src="/audio/before.wav"
        preload="metadata"
        onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
        onTimeUpdate={(e) => {
          if (!enhanced) setTime(e.currentTarget.currentTime);
        }}
        onEnded={() => setPlaying(false)}
      />
      <audio
        ref={b}
        src="/audio/after.wav"
        preload="metadata"
        onTimeUpdate={(e) => {
          if (enhanced) setTime(e.currentTarget.currentTime);
        }}
        onEnded={() => setPlaying(false)}
      />
    </div>
  );
}
export default function Landing() {
  const [scrolled, setScrolled] = useState(false);
  const hero = useRef<HTMLElement>(null);
  useEffect(() => {
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    let ticking = false;
    const update = () => {
      setScrolled(scrollY > 120);
      if (!reduced)
        hero.current?.style.setProperty(
          "--scroll",
          String(Math.min(scrollY / 700, 1)),
        );
      ticking = false;
    };
    const scroll = () => {
      if (!ticking) {
        requestAnimationFrame(update);
        ticking = true;
      }
    };
    window.addEventListener("scroll", scroll, { passive: true });
    update();
    const observer = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("visible");
            observer.unobserve(e.target);
          }
        }),
      { threshold: 0.12 },
    );
    document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));
    fetch("/api/event", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event: "pageview" }),
    }).catch(() => {});
    return () => {
      window.removeEventListener("scroll", scroll);
      observer.disconnect();
    };
  }, []);
  return (
    <>
      <a href="#demo" className="skip">
        Skip to audio demo
      </a>
      <header className={scrolled ? "nav scrolled" : "nav"}>
        <a href="#" className="brand" aria-label="Voicy home">
          <Mark size={20} />
          <span>voicy</span>
        </a>
        <nav aria-label="Main navigation">
          <a href="#demo">Demo</a>
          <a href="#how-it-works">How it works</a>
          <a href={site.github}>GitHub</a>
        </nav>
        <Download small />
      </header>
      <main>
        <section className="hero" ref={hero}>
          <div className="hero-wave" aria-hidden="true">
            {Array.from({ length: 81 }, (_, i) => (
              <i
                key={i}
                style={{
                  height:
                    18 +
                    180 *
                      Math.exp(-1 * Math.pow((i - 40) / 21, 2)) *
                      Math.abs(Math.sin(i * 0.51)) +
                    "px",
                  animationDelay: `${i * -90}ms`,
                }}
              />
            ))}
          </div>
          <div className="hero-content">
            <h1>
              Your voice.
              <br />
              <span>In the clear.</span>
            </h1>
            <p>
              Free AI speech enhancement.
              <br />
              <span>Fully on your Mac.</span>
            </p>
            <div className="hero-actions">
              <Download />
              <a className="text-link" href="#demo">
                Hear the difference {arrow}
              </a>
            </div>
            <span className="requirements">
              Apple Silicon · macOS 14+ · No account
            </span>
          </div>
          <a href="#demo" className="scroll-cue">
            Scroll to listen
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 4v16m-5-5 5 5 5-5"
                stroke="currentColor"
                strokeWidth="1.5"
              />
            </svg>
          </a>
        </section>
        <section className="demo-section shell">
          <Demo />
          <p className="demo-note">
            Real Voicy output. Synthetic voice with simulated fan noise. Switch
            while it plays.
          </p>
        </section>
        <section className="statement shell reveal">
          <h2>
            A good recording.
            <br />
            <span>Without the perfect room.</span>
          </h2>
          <p>
            Bring your voice forward. Reduce background noise
            <br className="desktop" /> and room echo with AI that runs right on
            your Mac.
          </p>
        </section>
        <section id="how-it-works" className="workflow shell">
          <div className="workflow-visual reveal">
            <div className="file-stack">
              <div className="file-back"></div>
              <div className="file-front">
                <Mark size={44} />
                <span>Recording.wav</span>
                <small>Drop it into Voicy</small>
              </div>
              <span className="cursor">↖</span>
            </div>
          </div>
          <div className="workflow-copy reveal">
            <h2>
              Drop. Enhance.
              <br />
              <span>That’s it.</span>
            </h2>
            <ol>
              <li>
                <span>01</span>
                <div>
                  <h3>Bring your recording.</h3>
                  <p>
                    Voice memos, interviews, podcasts.
                    <br />
                    Open a file or drop it in.
                  </p>
                </div>
              </li>
              <li>
                <span>02</span>
                <div>
                  <h3>Let Voicy do the cleanup.</h3>
                  <p>
                    Noise and echo, handled locally.
                    <br />
                    Your original stays untouched.
                  </p>
                </div>
              </li>
              <li>
                <span>03</span>
                <div>
                  <h3>Listen. Compare. Export.</h3>
                  <p>
                    Switch between both versions.
                    <br />
                    Save the result as a 24-bit WAV.
                  </p>
                </div>
              </li>
            </ol>
          </div>
        </section>
        <section className="local-section shell">
          <div className="local-copy reveal">
            <h2>
              Your Mac.
              <br />
              <span>Your audio.</span>
            </h2>
            <p>
              No uploads. No accounts. No credits.
              <br />
              The models come with the app.
              <br />
              Even your Wi-Fi can take a break.
            </p>
            <a className="text-link" href="/privacy">
              How privacy works {arrow}
            </a>
          </div>
          <div className="local-visual reveal" aria-hidden="true">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="chip">
              <Mark size={42} />
              <span>ON DEVICE</span>
            </div>
            <span className="local-label">Made for Apple Silicon</span>
          </div>
        </section>
        <section className="open-section shell reveal">
          <div className="source-mark" aria-hidden="true">
            &lt;/&gt;
          </div>
          <h2>
            Free to use.
            <br />
            <span>Open to everyone.</span>
          </h2>
          <p>
            A free Adobe Podcast alternative for Mac.
            <br />
            Read the code. Make it yours. Help it get better.
          </p>
          <a href={site.github} className="button secondary">
            Explore on GitHub {arrow}
          </a>
          <span className="fine">
            MIT application code · Open-source models
          </span>
        </section>
        <section id="faq" className="faq shell reveal">
          <h2>A few good questions.</h2>
          <div className="faq-layout">
            <div>
              {faqs.map(([q, a]) => (
                <details key={q}>
                  <summary>
                    {q}
                    <svg width="16" height="16" viewBox="0 0 16 16">
                      <path
                        d="M3 6l5 5 5-5"
                        fill="none"
                        stroke="currentColor"
                      />
                    </svg>
                  </summary>
                  <p>{a}</p>
                </details>
              ))}
            </div>
            <aside>
              <Mark size={28} />
              <p>Something else on your mind?</p>
              <a className="text-link" href={`${site.github}/issues`}>
                Ask on GitHub {arrow}
              </a>
            </aside>
          </div>
        </section>
        <section className="closing shell reveal">
          <Mark size={36} />
          <h2>
            Let your voice
            <br />
            <span>come through.</span>
          </h2>
          <Download />
          <p className="requirements">Free · Local · Open source</p>
        </section>
      </main>
      <footer className="shell">
        <div className="footer-top">
          <a className="brand" href="#">
            <Mark size={22} />
            voicy
          </a>
          <span>© {new Date().getFullYear()} Voicy</span>
          <a href={site.github}>GitHub {arrow}</a>
        </div>
        <div className="footer-links">
          <a href="#demo">Speech enhancement demo</a>
          <a href={`${site.github}#getting-started`}>Documentation</a>
          <a href="/privacy">Privacy</a>
          <a href={`${site.github}/blob/main/LICENSE`}>License</a>
          <a href="/llms.txt">For AI readers</a>
        </div>
        <p className="fine">
          Independent software. Not affiliated with Adobe or Apple.
        </p>
      </footer>
    </>
  );
}
