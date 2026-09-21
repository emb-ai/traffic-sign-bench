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
      <Reveal at={0.1} style={{ position: "absolute", left: SIZE.margin, right: SIZE.margin, top: 48 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <Headline>Shared rules transcend visual borders.</Headline>
            <Sub size={27} style={{ marginTop: 8 }}>TrafficSignBench separates legal semantics from sign appearance.</Sub>
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 14, padding: "14px 22px", borderRadius: 16, background: "#EEF6FF", border: "2px solid #B8D4F4" }}>
            <span style={{ color: COLORS.blue, fontSize: 54, lineHeight: 1, fontWeight: 900 }}>92%</span>
            <span style={{ color: COLORS.ink, fontSize: 21, lineHeight: 1.2, fontWeight: 700 }}>average semantic overlap<br />across Vienna signatories</span>
          </div>
        </div>
      </Reveal>

      <div style={{ position: "absolute", left: SIZE.margin, top: 168, display: "flex", gap: 14 }}>
        {COUNTRIES.map((country, index) => (
          <Reveal key={country.key} at={tt.flags + index * tt.flagStep} dy={10}>
            <div style={{ width: 232, height: 112, padding: "13px 16px", boxSizing: "border-box", backgroundColor: COLORS.panel, borderRadius: 14, borderTop: `6px solid ${country.vienna ? COLORS.blue : COLORS.faint}`, display: "flex", alignItems: "center", gap: 14 }}>
              <Img src={staticFile(FLAGS[country.key as keyof typeof FLAGS])} style={{ width: 46, maxHeight: 31, objectFit: "cover", borderRadius: 4, boxShadow: "0 0 0 1px rgba(0,0,0,0.08)" }} />
              <div>
                <div style={{ fontSize: 18, color: COLORS.muted, fontWeight: 700 }}>{country.label}</div>
                <div style={{ fontSize: 35, lineHeight: 1.05, fontWeight: 900, fontVariantNumeric: "tabular-nums" }}>{country.pct}%</div>
              </div>
            </div>
          </Reveal>
        ))}
        <Reveal at={tt.flags + 6 * tt.flagStep} style={{ alignSelf: "center", marginLeft: 8, fontSize: 18, color: COLORS.muted, lineHeight: 1.55 }}>
          <div><span style={{ display: "inline-block", width: 13, height: 13, backgroundColor: COLORS.blue, borderRadius: 3, marginRight: 7 }} />Vienna</div>
          <div><span style={{ display: "inline-block", width: 13, height: 13, backgroundColor: COLORS.faint, borderRadius: 3, marginRight: 7 }} />Non-Vienna</div>
        </Reveal>
      </div>

      <Reveal at={tt.figure} style={{ position: "absolute", left: SIZE.margin, top: 330 }}>
        <div style={{ color: COLORS.muted, fontSize: 18, fontWeight: 900, letterSpacing: 1.8, textTransform: "uppercase", marginBottom: 10 }}>
          Visual equivalents · examples
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "130px repeat(7, 1fr)", width: 1740, borderRadius: 18, border: `2px solid ${COLORS.border}`, overflow: "hidden", background: "#fff" }}>
          <div style={{ background: COLORS.panel }} />
          {DISPLAY_COUNTRIES.map((country) => (
            <div key={country.key} style={{ height: 48, display: "grid", placeItems: "center", background: country.key === "russia" ? "#EEF6FF" : COLORS.panel, borderLeft: `1px solid ${COLORS.border}`, fontSize: 19, fontWeight: 900 }}>
              {country.label}
            </div>
          ))}
          {[
            { key: "yield", label: "Yield" },
            { key: "direction_left", label: "Turn left" },
          ].map((row) => (
            <Fragment key={row.key}>
              <div style={{ height: 178, display: "grid", placeItems: "center", background: COLORS.panel, borderTop: `1px solid ${COLORS.border}`, fontSize: 20, color: COLORS.muted, fontWeight: 900 }}>{row.label}</div>
              {DISPLAY_COUNTRIES.map((country) => (
                <div key={`${row.key}-${country.key}`} style={{ height: 178, display: "flex", alignItems: "flex-start", justifyContent: "center", paddingTop: 18, boxSizing: "border-box", borderLeft: `1px solid ${COLORS.border}`, borderTop: `1px solid ${COLORS.border}`, background: country.key === "russia" ? "#F8FBFF" : "#fff" }}>
                  <Img
                    src={staticFile(`countries/${row.key}/${country.label}.png`)}
                    style={{ width: 128, height: 137, objectFit: "contain", objectPosition: "top center" }}
                  />
                </div>
              ))}
            </Fragment>
          ))}
        </div>
      </Reveal>

      <Reveal at={tt.result} style={{ position: "absolute", left: 360, right: 360, top: 850 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 22 }}>
          <div style={{ padding: "13px 22px", borderRadius: 14, background: "#EEF6FF", color: COLORS.blue, fontSize: 25, fontWeight: 900 }}>Swap visual appearance</div>
          <div style={{ color: COLORS.faint, fontSize: 38 }}>→</div>
          <div style={{ padding: "13px 22px", borderRadius: 14, background: "#EAF7EF", color: COLORS.green, fontSize: 25, fontWeight: 900 }}>Reuse rule-verification logic</div>
        </div>
        <Sub size={22} style={{ marginTop: 12, textAlign: "center" }}>
          Modular semantics enable low-cost adaptation to new jurisdictions.
        </Sub>
      </Reveal>
    </Scene>
  );
};
