// src/hooks/useUserAndMenu.js
import { useState, useEffect } from 'react';
import axios from 'axios';
import { ALWAYS_AVAILABLE_APPS, USER_APPS } from '../config/apps';
import { useTranslation } from 'react-i18next';

export const useUserAndMenu = () => {
  const { t } = useTranslation(); // ✅ i18n hook
  const [user, setUser] = useState(null);
  const [menu, setMenu] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError('');

        const [userResponse, menuResponse] = await Promise.all([
          axios.get('/api/v1/auth/me'),
          axios.get('/api/v1/auth/menu'),
        ]);

        if (!isMounted) return;

        const userData = userResponse.data;
        const menuData = menuResponse.data;

        const finalMenu = menuData.filter(item => {
          const appAllowed =
            ALWAYS_AVAILABLE_APPS.includes(item.app) ||
            USER_APPS.includes(item.app);
          
          const roleAllowed =
            !item.roles || item.roles.some(r => userData.roles?.includes(r));

          return appAllowed && roleAllowed;
        });

        setUser({
          ...userData,
          roles: userData.roles || [],
          institution: userData.institution || {},
          domain: userData.institution?.domain || '',
        });
        setMenu(finalMenu);
      } catch (err) {
        if (isMounted) {
          setError(
            err.response?.data?.message || t('userandmenu.load_failed')
          );
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchData();

    return () => {
      isMounted = false;
    };
  }, [t]);

  return { user, menu, loading, error, setUser, setMenu };
};