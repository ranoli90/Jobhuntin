import { recaptcha } from "./recaptcha";

async function getBotProtectionToken(action: string): Promise<string | null> {
  return await recaptcha.getRecaptchaToken(action);
}

export const botProtection = {
  getBotProtectionToken,
};
