import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getStatus, onSystemClosed } from "./api/client";
import { ClosedScreen } from "./screens/ClosedScreen";

export function App() {
  const { t } = useTranslation();
  const [state, setState] = useState<"loading" | "open" | "closed">("loading");

  useEffect(() => {
    let active = true;
    const unsubscribe = onSystemClosed(() => {
      if (active) setState("closed");
    });
    void getStatus().then(
      () => {
        if (active)
          setState((current) => (current === "closed" ? current : "open"));
      },
      () => {
        if (active) setState("closed");
      },
    );
    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  if (state === "closed") return <ClosedScreen />;
  if (state === "loading") return <main>{t("app.loading")}</main>;
  return (
    <main>
      <h1>{t("app.title")}</h1>
      <p>{t("home.running")}</p>
    </main>
  );
}
