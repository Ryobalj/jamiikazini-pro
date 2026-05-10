// src/hooks/useRecaptcha.js
import { useEffect } from "react";

export const useRecaptchaV3 = () => {
  useEffect(() => {
    const scriptId = "recaptcha-script";
    if (document.getElementById(scriptId)) return;

    const script = document.createElement("script");
    script.id = scriptId;
    script.src = `https://www.google.com/recaptcha/api.js?render=${import.meta.env.VITE_RECAPTCHA_SITE_KEY}`;
    script.async = true;
    document.body.appendChild(script);
  }, []);

  const execute = async (action = "submit") => {
    return new Promise((resolve, reject) => {
      if (!window.grecaptcha) return reject("reCAPTCHA not loaded");

      window.grecaptcha.ready(() => {
        window.grecaptcha
          .execute(import.meta.env.VITE_RECAPTCHA_SITE_KEY, { action })
          .then(resolve)
          .catch(reject);
      });
    });
  };

  return { execute };
};