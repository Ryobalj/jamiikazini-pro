// src/app/businesses/pages/NearbyBusinessesPage.jsx

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import api from "@/lib/axios";
import {
  Store,
  MapPin,
  Loader2,
  Search,
  Navigation,
  Phone,
  Mail,
  Star,
  ChevronRight,
  X,
  SlidersHorizontal,
  MessageCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { toast } from "react-toastify";

// Helper function to calculate distance between two coordinates (Haversine formula)
function calculateDistance(lat1, lon1, lat2, lon2) {
  if (!lat1 || !lon1 || !lat2 || !lon2) return 0;
  const R = 6371; // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

export default function NearbyBusinessesPage() {
  const { t } = useTranslation("businesses");
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [userLocation, setUserLocation] = useState(null);
  const [businesses, setBusinesses] = useState([]);
  const [filteredBusinesses, setFilteredBusinesses] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [maxDistance, setMaxDistance] = useState(5); // 5km default
  const [categories, setCategories] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [locationError, setLocationError] = useState(null);
  const [messagingId, setMessagingId] = useState(null);

  const handleMessageBusiness = async (e, business) => {
    e.stopPropagation();
    setMessagingId(business.id);
    try {
      const res = await api.post("/jamiichat/conversations/start-with-business/", {
        business_id: business.id,
        message: "Habari, ningependa kupata maelezo zaidi.",
      });
      navigate(`/jamiichat/${res.data.id}`);
    } catch (err) {
      toast.error(err.response?.data?.business_id?.[0] || "Imeshindwa kuanzisha mazungumzo.");
    } finally {
      setMessagingId(null);
    }
  };

  useEffect(() => {
    getUserLocation();
    fetchCategories();
  }, []);

  useEffect(() => {
    if (userLocation) {
      fetchNearbyBusinesses();
    }
  }, [userLocation, maxDistance]);

  useEffect(() => {
    filterBusinesses();
  }, [businesses, searchQuery, selectedCategory]);

  const getUserLocation = () => {
    if (!navigator.geolocation) {
      setLocationError(t("nearby.location_required"));
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setUserLocation({ lat: latitude, lng: longitude });
        setLocationError(null);
      },
      (error) => {
        console.error("Geolocation error:", error);
        let errorMessage;
        if (error.code === 1) {
          errorMessage = t("nearby.location_permission_denied");
        } else if (error.code === 2) {
          errorMessage = t("nearby.location_unavailable");
        } else if (error.code === 3) {
          errorMessage = t("nearby.location_timeout");
        } else {
          errorMessage = t("nearby.location_required");
        }
        setLocationError(errorMessage);
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  const fetchCategories = async () => {
    try {
      const res = await api.get("/categories/");
      const cats = Array.isArray(res.data) ? res.data : res.data.results || [];
      setCategories(cats);
    } catch (error) {
      console.error("Failed to fetch categories:", error);
    }
  };

  const fetchNearbyBusinesses = async () => {
    if (!userLocation) return;

    try {
      setLoading(true);
      
      const params = {
        lat: userLocation.lat,
        lng: userLocation.lng,
        radius: maxDistance,
        type: "business",
        page_size: 50,
      };
      
      console.log("Fetching nearby with params:", params);
      
      const res = await api.get("/businesses/nearby/", { params });
      
      const businessList = res.data.businesses || [];
      
      const businessesWithDistance = businessList.map(b => ({
        ...b,
        distance: b.distance ? b.distance / 1000 : calculateDistance(
          userLocation.lat,
          userLocation.lng,
          b.location?.latitude || b.lat,
          b.location?.longitude || b.lng || b.lon
        )
      })).sort((a, b) => a.distance - b.distance);
      
      setBusinesses(businessesWithDistance);
    } catch (error) {
      console.error("Failed to fetch nearby businesses:", error);
      
      // Fallback: fetch all and filter client-side
      try {
        const res = await api.get("/businesses/");
        const businessList = Array.isArray(res.data) 
          ? res.data 
          : res.data.results || [];
        
        const nearbyWithDistance = businessList
          .filter(b => b.location?.latitude || b.lat)
          .map(b => ({
            ...b,
            distance: calculateDistance(
              userLocation.lat,
              userLocation.lng,
              b.location?.latitude || b.lat,
              b.location?.longitude || b.lng || b.lon
            )
          }))
          .filter(b => b.distance <= maxDistance)
          .sort((a, b) => a.distance - b.distance);
        
        setBusinesses(nearbyWithDistance);
      } catch (fallbackError) {
        console.error("Fallback also failed:", fallbackError);
        setBusinesses([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const filterBusinesses = () => {
    let filtered = [...businesses];
    
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(b => 
        b.name?.toLowerCase().includes(query) ||
        b.description?.toLowerCase().includes(query) ||
        b.category_name?.toLowerCase().includes(query)
      );
    }
    
    if (selectedCategory !== "all") {
      filtered = filtered.filter(b => 
        b.category === selectedCategory || b.category_id === selectedCategory
      );
    }
    
    setFilteredBusinesses(filtered);
  };

  const handleRetryLocation = () => {
    setLocationError(null);
    setLoading(true);
    getUserLocation();
  };

  const getCategoryName = (categoryId) => {
    const cat = categories.find(c => c.id === categoryId);
    return cat?.name || t("nearby.unknown_category");
  };

  const formatDistance = (distance) => {
    if (distance < 1) {
      return t("nearby.distance_meters", { distance: Math.round(distance * 1000) });
    }
    return t("nearby.distance_kilometers", { distance: distance.toFixed(1) });
  };

  if (locationError) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="text-center py-8">
            <MapPin className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
              {t("nearby.location_required")}
            </h2>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              {locationError}
            </p>
            <Button onClick={handleRetryLocation} className="w-full">
              <Navigation className="w-4 h-4 mr-2" />
              {t("nearby.try_again")}
            </Button>
            <Button 
              variant="outline" 
              onClick={() => navigate("/home")} 
              className="w-full mt-2"
            >
              {t("nearby.go_back_home")}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(-1)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full"
            >
              <ChevronRight className="w-5 h-5 rotate-180 text-gray-600 dark:text-gray-400" />
            </button>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              {t("nearby.title")}
            </h1>
          </div>
          
          {/* Search Bar */}
          <div className="mt-3 flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder={t("nearby.search_placeholder")}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              <SlidersHorizontal className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
          </div>
          
          {/* Filters Panel */}
          {showFilters && (
            <div className="mt-3 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium text-gray-900 dark:text-gray-100">
                  {t("nearby.filters")}
                </h3>
                <button onClick={() => setShowFilters(false)}>
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              </div>
              
              <div className="space-y-4">
                {/* Category Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t("nearby.category")}
                  </label>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="w-full p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-gray-100"
                  >
                    <option value="all">{t("nearby.all_categories")}</option>
                    {categories.map(cat => (
                      <option key={cat.id} value={cat.id}>{cat.name}</option>
                    ))}
                  </select>
                </div>
                
                {/* Distance Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {t("nearby.maximum_distance")}: {maxDistance} km
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    value={maxDistance}
                    onChange={(e) => setMaxDistance(parseInt(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>1 km</span>
                    <span>10 km</span>
                    <span>20 km</span>
                  </div>
                </div>
                
                <Button 
                  onClick={() => {
                    fetchNearbyBusinesses();
                    setShowFilters(false);
                  }}
                  className="w-full"
                >
                  {t("nearby.apply_filters")}
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Location Info */}
      {userLocation && (
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <MapPin className="w-4 h-4 text-green-500" />
            <span>
              {t("nearby.showing_businesses", { distance: maxDistance })}
            </span>
          </div>
        </div>
      )}

      {/* Business List */}
      <div className="max-w-7xl mx-auto px-4 pb-8">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : filteredBusinesses.length > 0 ? (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {filteredBusinesses.length === 1 
                ? t("nearby.found_businesses", { count: filteredBusinesses.length })
                : t("nearby.found_businesses_plural", { count: filteredBusinesses.length })
              }
            </p>
            
            {filteredBusinesses.map((business) => (
              <Card 
                key={business.id}
                className="hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => navigate(`/store/${business.id}`)}
              >
                <CardContent className="p-0">
                  <div className="p-4">
                    <div className="flex items-start gap-3">
                      <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900 flex items-center justify-center flex-shrink-0">
                        <Store className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                              {business.name}
                            </h3>
                            <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                              {business.category_name || getCategoryName(business.category)}
                            </p>
                          </div>
                          
                          {business.distance !== undefined && (
                            <span className="ml-2 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-medium rounded-full">
                              {formatDistance(business.distance)}
                            </span>
                          )}
                        </div>
                        
                        {business.description && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 line-clamp-2">
                            {business.description}
                          </p>
                        )}
                        
                        <div className="flex flex-wrap gap-3 mt-3 text-sm text-gray-500 dark:text-gray-400">
                          {business.phone && (
                            <span className="flex items-center gap-1">
                              <Phone className="w-3.5 h-3.5" />
                              {business.phone}
                            </span>
                          )}
                          {business.email && (
                            <span className="flex items-center gap-1">
                              <Mail className="w-3.5 h-3.5" />
                              {business.email}
                            </span>
                          )}
                        </div>
                        
                        {business.average_rating && (
                          <div className="flex items-center gap-1 mt-2">
                            <Star className="w-4 h-4 text-yellow-400 fill-current" />
                            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                              {business.average_rating.toFixed(1)}
                            </span>
                            <span className="text-xs text-gray-500">
                              ({business.reviews_count === 1 
                                ? t("nearby.reviews", { count: business.reviews_count || 0 })
                                : t("nearby.reviews_plural", { count: business.reviews_count || 0 })
                              })
                            </span>
                          </div>
                        )}

                        <Button
                          size="sm"
                          className="mt-3 bg-purple-600 hover:bg-purple-700"
                          disabled={messagingId === business.id}
                          onClick={(e) => handleMessageBusiness(e, business)}
                        >
                          {messagingId === business.id ? (
                            <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                          ) : (
                            <MessageCircle className="w-4 h-4 mr-1" />
                          )}
                          Wasiliana na Muuzaji
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Store className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              {t("nearby.no_businesses_found")}
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              {searchQuery || selectedCategory !== "all" 
                ? t("nearby.try_adjusting")
                : t("nearby.no_businesses_message", { distance: maxDistance })
              }
            </p>
            {searchQuery || selectedCategory !== "all" ? (
              <Button 
                variant="outline"
                onClick={() => {
                  setSearchQuery("");
                  setSelectedCategory("all");
                }}
              >
                {t("nearby.clear_filters")}
              </Button>
            ) : (
              <Button onClick={() => setMaxDistance(maxDistance + 5)}>
                {t("nearby.expand_to", { distance: maxDistance + 5 })}
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}