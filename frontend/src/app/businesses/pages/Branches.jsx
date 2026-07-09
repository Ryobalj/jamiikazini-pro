// src/app/businesses/pages/Branches.jsx

import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import axios from "axios";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { useParams } from "react-router-dom";

function Branches() {
  const { t } = useTranslation();
  const { id: businessId } = useParams();

  const [branches, setBranches] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);

  const fetchBranches = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`/businesses/${businessId}/branches/`, {
        params: { search, page },
      });
      setBranches(res.data.results || []);
      setCount(res.data.count || 0);
      setErrorMsg("");
    } catch {
      setErrorMsg(t("errors.failed_to_fetch"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBranches();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchBranches();
  };

  const totalPages = Math.ceil(count / 10); // assuming page_size=10

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-semibold">{t("branches.title", "Matawi ya Biashara")}</h1>

      {/* Search Field */}
      <form onSubmit={handleSearch} className="flex gap-2 max-w-md">
        <Input
          placeholder={t("branches.search_placeholder", "Tafuta kwa jina...")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <Button type="submit">{t("buttons.search", "Tafuta")}</Button>
      </form>

      {/* Errors */}
      {errorMsg && (
        <div className="text-red-500 bg-red-100 p-2 rounded">{errorMsg}</div>
      )}

      {/* Loading */}
      {loading ? (
        <div className="flex items-center space-x-2 text-gray-500">
          <Loader2 className="animate-spin w-5 h-5" />
          <span>{t("loading", "Inapakia...")}</span>
        </div>
      ) : (
        <>
          {/* List */}
          <ul className="grid gap-3">
            {branches.map((branch) => (
              <li
                key={branch.id}
                className="border rounded-lg p-3 shadow-sm hover:shadow transition"
              >
                <h2 className="text-lg font-medium">{branch.name}</h2>
                {branch.address && <p className="text-sm text-gray-600">{branch.address}</p>}
              </li>
            ))}
          </ul>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-between items-center mt-4">
              <Button
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                disabled={page === 1}
              >
                {t("pagination.prev", "Kurasa iliyopita")}
              </Button>
              <span>
                {t("pagination.page", { page, totalPages }, `Uk. ${page} / ${totalPages}`)}
              </span>
              <Button
                onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                disabled={page === totalPages}
              >
                {t("pagination.next", "Kurasa inayofuata")}
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Branches;