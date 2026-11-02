// SCR-00 Closed (placeholder until US31)
import i18n from "../i18n";

export function ClosedScreen() {
  return (
    <main>
      <p lang="en">{i18n.getFixedT("en")("closed.message")}</p>
      <p lang="vi">{i18n.getFixedT("vi")("closed.message")}</p>
    </main>
  );
}
