import { useEffect, useState } from "react";
import api from "@/lib/axios";

export default function useUserBusiness() {
  const [loading, setLoading] = useState(true);
  const [business, setBusiness] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchBusiness = async () => {
      try {
        const res = await api.get("/businesses/my/");
        setBusiness(res.data); // au res.data[0] kama ni array
      } catch (err) {
        if (err.response?.status !== 404) {
          setError(err);
        }
        setBusiness(null);
      } finally {
        setLoading(false);
      }
    };

    fetchBusiness();
  }, []);

  return { loading, business, hasBusiness: !!business, error };
}