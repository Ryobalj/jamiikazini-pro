// src/lib/auth.js
import api from "@/lib/axios";
import i18n from "@/i18n"; // ✅ i18n instance for direct translation

/**
 * Login wrapper
 */
export async function loginUser({ email, password, recaptcha_token, setUser, setUserMenu }) {
  try {
    const response = await api.post("/security/login/", {
      email,
      password,
      recaptcha_token,
    });

    const { access, refresh } = response.data;
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);

    if (setUser && setUserMenu) {
      const [userRes, menuRes] = await Promise.all([
        api.get("/auth/me/"),
        api.get("/kiini/user-menu/"),
      ]);

      const userData = userRes.data;
      if (!userData.full_name && userData.name) {
        userData.full_name = userData.name;
      }

      setUser(userData);
      setUserMenu(Array.isArray(menuRes.data) ? menuRes.data : []);
    }

    return { success: true };
  } catch (error) {
    const fallback = i18n.t("jamiiauth.login_failed");
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      fallback;

    return { success: false, message };
  }
}

/**
 * Register wrapper + auto-login
 */
export async function registerUser(data) {
  try {
    const { email, password, recaptcha_token, setUser, setUserMenu, ...rest } = data;

    await api.post("/auth/register/", {
      email,
      password,
      full_name: data.full_name,
      recaptcha_token,
      ...rest,
    });

    const res = await api.post("/security/login/", {
      email,
      password,
      recaptcha_token,
    });

    const { access, refresh } = res.data;
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);

    if (setUser && setUserMenu) {
      const [userRes, menuRes] = await Promise.all([
        api.get("/auth/me/"),
        api.get("/kiini/user-menu/"),
      ]);

      const userData = userRes.data;
      if (!userData.full_name && userData.name) {
        userData.full_name = userData.name;
      }

      setUser(userData);
      setUserMenu(Array.isArray(menuRes.data) ? menuRes.data : []);
    }

    return { success: true };
  } catch (error) {
    let message = i18n.t("jamiiauth.register_failed");
    const responseErrors = error.response?.data;

    if (responseErrors) {
      if (typeof responseErrors === "string") {
        message = responseErrors;
      } else {
        message = Object.values(responseErrors).flat().join(" ");
      }
    }

    return { success: false, message, raw: responseErrors };
  }
}

/**
 * Logout wrapper
 */
export function logoutUser({ setUser, setUserMenu, navigate } = {}) {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");

  if (typeof setUser === "function") setUser(null);
  if (typeof setUserMenu === "function") setUserMenu([]);
  if (typeof navigate === "function") navigate("/", { replace: true });
}