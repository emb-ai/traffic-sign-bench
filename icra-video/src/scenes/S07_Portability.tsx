import { Img, staticFile } from "remotion";
import { Fragment } from "react";
import { FLAGS } from "../config/assets";
import { COUNTRIES } from "../config/content";
import { COLORS, SIZE } from "../config/style";
import { T } from "../config/timing";
import { Headline, Reveal, Scene, Sub } from "../lib/ui";

const DISPLAY_COUNTRIES = [
  { key: "russia", label: "Russia", pct: null, vienna: true },
  ...COUNTRIES,
] as const;

export const S07_Portability: React.FC = () => {
  const tt = T.s07;
  return (
    <Scene>
      {/* Clean, authoritative header without awkward corner boxes */}
      <Reveal at={0.1} style={{ position: "absolute", left: SIZE.margin, right: SIZE.margin, top: 44 }}>
        <div>
          <div
            style={{
              display: "inline-block",
              padding: "4px 14px",
              borderRadius: 999,
              background: "#EEF4FC",
              border: "1.5px solid #C8DCF5",
              color: COLORS.blue,
              fontSize: 13,
              fontWeight: 900,
              letterSpacing: 2.2,
              textTransform: "uppercase",
              marginBottom: 8,
            }}
          >
            International Generalizability
          </div>
          <Headline size={50}>Traffic-Rule Semantics Generalize Internationally</Headline>
          <Sub size={24} style={{ marginTop: 6, fontWeight: 700, color: "#334155" }}>
            Legal semantics remain 92% invariant across jurisdictions — adapting to new countries requires changing visual appearance, not rule logic.
          </Sub>
        </div>
      </Reveal>

      {/* Integrated Metrics Belt: Hero Vienna Average (92%) + 6 Country Cards = Exactly 1740px (matching table below) */}
      <div style={{ position: "absolute", left: SIZE.margin, top: 240, display: "flex", gap: 15, width: 1740 }}>
        {/* Harmonious Hero KPI Card for Average Overlap (270px) */}
        <Reveal at={tt.flags} dy={10}>
          <div
            style={{
              width: 270,
              height: 104,
              padding: "12px 20px",
              boxSizing: "border-box",
              backgroundColor: "#EEF4FC",
              borderRadius: 16,
              border: "1.5px solid #C8DCF5",
              borderTop: `5px solid ${COLORS.blue}`,
              boxShadow: "0 6px 18px rgba(36, 88, 166, 0.06)",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div style={{ fontSize: 11, fontWeight: 900, letterSpacing: 1.5, textTransform: "uppercase", color: COLORS.blue }}>
              Mean Semantic Overlap
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <span style={{ fontSize: 14, fontWeight: 700, color: "#475569" }}>Vienna Signatories</span>
              <span style={{ fontSize: 32, fontWeight: 900, color: COLORS.blue, fontVariantNumeric: "tabular-nums" }}>
                92%
              </span>
            </div>
          </div>
        </Reveal>

        {/* 6 Country cards with national flags (230px each) */}
        {COUNTRIES.map((country, index) => (
          <Reveal key={country.key} at={tt.flags + (index + 1) * tt.flagStep} dy={10}>
            <div
              style={{
                width: 230,
                height: 104,
                padding: "12px 18px",
                boxSizing: "border-box",
                backgroundColor: "#FFFFFF",
                borderRadius: 16,
                border: "1.5px solid #E2E8F0",
                borderTop: country.vienna ? `5px solid ${COLORS.blue}` : `5px solid #94A3B8`,
                boxShadow: "0 6px 18px rgba(15, 23, 42, 0.04)",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Img
                  src={staticFile(FLAGS[country.key as keyof typeof FLAGS])}
                  style={{ width: 44, height: 28, objectFit: "cover", borderRadius: 4, boxShadow: "0 1px 4px rgba(0,0,0,0.12)" }}
                />
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 900,
                    color: country.vienna ? COLORS.blue : "#64748B",
                    letterSpacing: 0.8,
                    textTransform: "uppercase",
                    padding: "2px 8px",
                    borderRadius: 999,
                    background: country.vienna ? "#EFF6FF" : "#F1F5F9",
                  }}
                >
                  {country.vienna ? "Vienna" : "Non-Vienna"}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                <span style={{ fontSize: 17, color: "#334155", fontWeight: 700 }}>{country.label}</span>
                <span style={{ fontSize: 30, fontWeight: 900, color: COLORS.ink, fontVariantNumeric: "tabular-nums" }}>
                  {country.pct}%
                </span>
              </div>
            </div>
          </Reveal>
        ))}
      </div>

      {/* Visual comparison table */}
      <Reveal at={tt.figure} style={{ position: "absolute", left: SIZE.margin, top: 398 }}>
        <div style={{ color: COLORS.blue, fontSize: 13, fontWeight: 900, letterSpacing: 2, textTransform: "uppercase", marginBottom: 10 }}>
          Visual Equivalents Across Jurisdictions · Examples
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "140px repeat(7, 1fr)",
            width: 1740,
            borderRadius: 18,
            border: "1.5px solid #CBD5E1",
            boxShadow: "0 10px 30px rgba(15, 23, 42, 0.05)",
            overflow: "hidden",
            background: "#fff",
          }}
        >
          <div style={{ background: "#F1F5F9", display: "grid", placeItems: "center", fontSize: 14, fontWeight: 900, color: "#64748B", textTransform: "uppercase", letterSpacing: 1 }}>
            Sign Type
          </div>
          {DISPLAY_COUNTRIES.map((country) => (
            <div
              key={country.key}
              style={{
                height: 48,
                display: "grid",
                placeItems: "center",
                background: country.key === "russia" ? "#EEF6FF" : "#F8FAFC",
                borderLeft: "1px solid #E2E8F0",
                fontSize: 18,
                fontWeight: 900,
                color: country.key === "russia" ? COLORS.blue : COLORS.ink,
              }}
            >
              {country.key === "russia" ? "Russia (Ref)" : country.label}
            </div>
          ))}
          {[
            { key: "yield", label: "Yield" },
            { key: "direction_left", label: "Turn left" },
          ].map((row) => (
            <Fragment key={row.key}>
              <div
                style={{
                  height: 174,
                  display: "grid",
                  placeItems: "center",
                  background: "#F8FAFC",
                  borderTop: "1px solid #E2E8F0",
                  fontSize: 19,
                  color: COLORS.ink,
                  fontWeight: 900,
                }}
              >
                {row.label}
              </div>
              {DISPLAY_COUNTRIES.map((country) => (
                <div
                  key={`${row.key}-${country.key}`}
                  style={{
                    height: 174,
                    display: "flex",
                    alignItems: "flex-start",
                    justifyContent: "center",
                    paddingTop: 16,
                    boxSizing: "border-box",
                    borderLeft: "1px solid #E2E8F0",
                    borderTop: "1px solid #E2E8F0",
                    background: country.key === "russia" ? "#F6FAFF" : "#ffffff",
                  }}
                >
                  <Img
                    src={staticFile(`countries/${row.key}/${country.label}.png`)}
                    style={{ width: 124, height: 134, objectFit: "contain", objectPosition: "top center" }}
                  />
                </div>
              ))}
            </Fragment>
          ))}
        </div>
      </Reveal>

      {/* Bottom executive takeaway */}
      <Reveal at={tt.result} style={{ position: "absolute", left: 340, right: 340, top: 882 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 20 }}>
          <div
            style={{
              padding: "12px 24px",
              borderRadius: 14,
              background: "#EEF6FF",
              border: "1.5px solid #B8D4F4",
              boxShadow: "0 4px 14px rgba(36, 88, 166, 0.08)",
              color: COLORS.blue,
              fontSize: 23,
              fontWeight: 900,
            }}
          >
            Swap visual appearance
          </div>
          <div style={{ color: "#64748B", fontSize: 32, fontWeight: 900 }}>→</div>
          <div
            style={{
              padding: "12px 24px",
              borderRadius: 14,
              background: "#EAF7EF",
              border: "1.5px solid #B4E2C5",
              boxShadow: "0 4px 14px rgba(46, 139, 87, 0.08)",
              color: COLORS.green,
              fontSize: 23,
              fontWeight: 900,
            }}
          >
            Reuse rule-verification logic
          </div>
        </div>
        <Sub size={21} style={{ marginTop: 12, textAlign: "center", color: COLORS.muted }}>
          Modular benchmark architecture enables zero-effort adaptation to any international jurisdiction.
        </Sub>
      </Reveal>
    </Scene>
  );
};
