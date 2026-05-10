// src/hooks/useBusinessCategories.js

import { useEffect, useState } from "react";
import api from "@/lib/axios";

export default function useBusinessCategories() {
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;

    async function fetchCategories() {
      setLoading(true);
      try {
        const res = await api.get("/businesses/categories/");
        if (active) {
          const formatted = res.data.map((cat) => ({
            label: cat.name,
            value: cat.id,
          }));
          setOptions(formatted);
        }
      } catch (err) {
        if (active) setError(err);
      } finally {
        if (active) setLoading(false);
      }
    }

    fetchCategories();
    return () => {
      active = false;
    };
  }, []);

  return { options, loading, error };
}