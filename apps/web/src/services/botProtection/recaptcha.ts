import { telemetry } from "../../lib/telemetry";

const RECAPTCHA_SITE_KEY = import.meta.env.VITE_RECAPTCHA_SITE_KEY as string;

async function getRecaptchaToken(action: string): Promise<string | null> {
  if (!RECAPTCHA_SITE_KEY) {
    console.warn("reCAPTCHA site key not found, skipping verification.");
    return null;
  }

  return new Promise((resolve) => {
    if (window.grecaptcha) {
      window.grecaptcha.ready(() => {
        window.grecaptcha
          .execute(RECAPTCHA_SITE_KEY, { action })
          .then((token) => {
            resolve(token);
          })
          .catch((err) => {
            console.error("reCAPTCHA execution error:", err);
            telemetry.track("recaptcha_error", { error: err.message, action });
            resolve(null);
          });
      });
    } else {
      console.error("reCAPTCHA script not loaded.");
      telemetry.track("recaptcha_error", { error: "script_not_loaded", action });
      resolve(null);
    }
  });
}

export const recaptcha = {
  getRecaptchaToken,
};
