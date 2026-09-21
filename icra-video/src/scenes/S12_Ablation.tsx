import { AbsoluteFill } from "remotion";
import { CLIPS } from "../config/assets";
import { TEXT } from "../config/content";
import { COLORS, SIZE } from "../config/style";
import { T } from "../config/timing";
import { Clip, Headline, Missing, Reveal, Scene, Sub } from "../lib/ui";

// Real footage exists only for the "sign input present" condition.
export const S12_Ablation: React.FC = () => {
  const c = TEXT.s12;
  const tt = T.s12;
  const S = 460;
  const Row: React.FC<{ label: string; from: string; to: string; at: number }> = ({ label, from, to, at }) => (
    <Reveal at={at} style={{ display: "flex", alignItems: "baseline", gap: 26, marginTop: 24 }}>
      <span style={{ width: 200, fontSize: 30, color: COLORS.muted }}>{label}</span>
      <span style={{ fontSize: 84, fontWeight: 900, color: COLORS.green, lineHeight: 1, fontVariantNumeric: "tabular-nums" }}>{from}</span>
      <span style={{ fontSize: 50, color: COLORS.faint }}>→</span>
      <span style={{ fontSize: 84, fontWeight: 900, color: COLORS.red, lineHeight: 1, fontVariantNumeric: "tabular-nums" }}>{to}</span>
    </Reveal>
  );
  return (
    <Scene>
      <Reveal at={0.1} style={{ position: "absolute", left: SIZE.margin, top: 50 }}>
        <Headline size={54}>{c.headline}</Headline>
        <Sub size={24}>{c.sub}</Sub>
      </Reveal>

      <Reveal at={tt.clips}>
        <Clip src={CLIPS.ablation_present} size={S} left={SIZE.margin} top={200} loop label={<b style={{ color: COLORS.green }}>{c.left}</b>} />
      </Reveal>
      <Reveal at={tt.clips + 0.3}>
        <Missing text={c.missing} left={SIZE.margin + S + 40} top={200} width={S} height={S} />
        <div style={{ position: "absolute", left: SIZE.margin + S + 40, top: 200 + S + 10, fontSize: 24, fontWeight: 700, color: COLORS.red }}>{c.right}</div>
      </Reveal>

      <AbsoluteFill style={{ left: 1100, width: 760, top: 210 }}>
        <Reveal at={tt.numbers - 0.4}><Sub size={30} style={{ fontWeight: 700, color: COLORS.ink }}>{c.episodes}</Sub></Reveal>
        <Row label={c.scd.label} from={c.scd.from} to={c.scd.to} at={tt.numbers} />
        <Row label={c.compliance.label} from={c.compliance.from} to={c.compliance.to} at={tt.compliance} />
        <Reveal at={tt.compliance + 1.5} style={{ marginTop: 40 }}>
          <Sub size={26}>Explicit sign identity is necessary for the learned behaviour — the gain is not generic fine-tuning.</Sub>
        </Reveal>
      </AbsoluteFill>
    </Scene>
  );
};
