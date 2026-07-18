// src/app/accounts/pages/ProfilePage.jsx

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import { useAppContext } from "@/context/AppContext";
import {
  User,
  Mail,
  Phone,
  Shield,
  Building2,
  Calendar,
  Edit3,
  Key,
  LogOut,
  Award,
  Loader2,
  CheckCircle,
  XCircle,
  Copy,
  Eye,
  EyeOff,
  Briefcase,
  MessageCircle,
  Clock,
  ArrowRight,
  Plus,
  Store,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { toast } from "react-toastify";

// Simple Tabs Context
const TabsContext = React.createContext(null);

function Tabs({ defaultValue, value, onValueChange, children, className }) {
  const [internalValue, setInternalValue] = useState(defaultValue);
  const currentValue = value !== undefined ? value : internalValue;
  
  const handleValueChange = (newValue) => {
    if (onValueChange) {
      onValueChange(newValue);
    } else {
      setInternalValue(newValue);
    }
  };
  
  return (
    <TabsContext.Provider value={{ value: currentValue, onValueChange: handleValueChange }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

function TabsList({ className, children }) {
  return (
    <div className="relative">
      <div className={cn(
        "flex items-center gap-1 p-1 bg-white dark:bg-gray-800 shadow-sm overflow-x-auto scrollbar-hide",
        "scroll-smooth snap-x snap-mandatory",
        className
      )}>
        {children}
      </div>
    </div>
  );
}

function TabsTrigger({ value, className, children }) {
  const { value: selectedValue, onValueChange } = React.useContext(TabsContext);
  const isActive = selectedValue === value;
  
  return (
    <button
      type="button"
      onClick={() => onValueChange(value)}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-md px-4 py-2 text-sm font-medium transition-all",
        "snap-start flex-shrink-0",
        isActive 
          ? "bg-blue-600 text-white shadow-sm" 
          : "text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700",
        className
      )}
    >
      {children}
    </button>
  );
}

function TabsContent({ value, className, children }) {
  const { value: selectedValue } = React.useContext(TabsContext);
  if (selectedValue !== value) return null;
  return <div className={cn("mt-6", className)}>{children}</div>;
}

function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

export default function ProfilePage() {
  const { t } = useTranslation("accounts");
  const navigate = useNavigate();
  const { user, setUser } = useAppContext();
  const [loading, setLoading] = useState(true);
  const [profileData, setProfileData] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [showSensitive, setShowSensitive] = useState(false);
  
  const [institutions, setInstitutions] = useState([]);
  const [businesses, setBusinesses] = useState([]);
  const [recentChats, setRecentChats] = useState([]);
  const [activities, setActivities] = useState([]);
  const [loadingInstitutions, setLoadingInstitutions] = useState(false);
  const [loadingBusinesses, setLoadingBusinesses] = useState(false);
  const [loadingChats, setLoadingChats] = useState(false);
  const [loadingActivities, setLoadingActivities] = useState(false);

  useEffect(() => {
    fetchProfileData();
  }, []);

  useEffect(() => {
    if (activeTab === "institutions") {
      fetchInstitutions();
    }
    if (activeTab === "businesses") {
      fetchBusinesses();
    }
    if (activeTab === "chat") {
      fetchRecentChats();
    }
    if (activeTab === "activity") {
      fetchActivities();
    }
  }, [activeTab]);

  const fetchProfileData = async () => {
    try {
      setLoading(true);
      const res = await api.get("/auth/me/");
      setProfileData(res.data);
    } catch (error) {
      console.error("Failed to fetch profile:", error);
      toast.error(t("errors.failed_to_load_profile"));
    } finally {
      setLoading(false);
    }
  };

  const fetchInstitutions = async () => {
    try {
      setLoadingInstitutions(true);
      const res = await api.get("/institutions/my/");
      setInstitutions(Array.isArray(res.data) ? res.data : res.data.results || []);
    } catch (error) {
      console.error("Failed to fetch institutions:", error);
      setInstitutions([]);
    } finally {
      setLoadingInstitutions(false);
    }
  };

  const fetchBusinesses = async () => {
    try {
      setLoadingBusinesses(true);
      const res = await api.get("/businesses/");
      const businessList = Array.isArray(res.data) 
        ? res.data 
        : res.data.results || [];
      setBusinesses(businessList);
    } catch (error) {
      console.error("Failed to fetch businesses:", error);
      setBusinesses([]);
    } finally {
      setLoadingBusinesses(false);
    }
  };

  const fetchRecentChats = async () => {
    try {
      setLoadingChats(true);
      const mockChats = [
        { id: 1, name: "Jamiikazini Support", lastMessage: "Habari, tunawezaje kukusaidia?", time: "10:30", unread: 2 },
        { id: 2, name: "Business Team", lastMessage: "Biashara yako imeidhinishwa", time: "Jana", unread: 0 },
        { id: 3, name: "Mteja - John", lastMessage: "Nahitaji huduma ya nywele", time: "Jana", unread: 1 },
      ];
      setRecentChats(mockChats);
    } catch (error) {
      console.error("Failed to fetch chats:", error);
      setRecentChats([]);
    } finally {
      setLoadingChats(false);
    }
  };

  const fetchActivities = async () => {
    try {
      setLoadingActivities(true);
      const mockActivities = [
        { id: 1, action: "Umejisajili kwenye Jamiikazini", time: "Wiki 2 zilizopita", icon: User },
        { id: 2, action: "Umeunda taasisi yako ya kwanza", time: "Wiki 1 iliyopita", icon: Building2 },
        { id: 3, action: "Umeunda biashara yako", time: "Siku 3 zilizopita", icon: Briefcase },
        { id: 4, action: "Umebadilisha maelezo ya wasifu", time: "Saa 2 zilizopita", icon: Edit3 },
      ];
      setActivities(mockActivities);
    } catch (error) {
      console.error("Failed to fetch activities:", error);
      setActivities([]);
    } finally {
      setLoadingActivities(false);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    setUser(null);
    navigate("/security/login");
    toast.success(t("logout_success"));
  };

  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} ${t("copied")}`);
  };

  const maskSensitive = (value, type = "text") => {
    if (!value) return "-";
    if (showSensitive) return value;
    
    if (type === "email") {
      const [name, domain] = value.split("@");
      if (!domain) return value;
      return name.substring(0, 3) + "***@" + domain;
    }
    
    if (type === "phone") {
      return value.substring(0, 6) + "****" + value.slice(-2);
    }
    
    return "••••••••";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const userData = profileData || user || {};

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Profile Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-900 dark:to-indigo-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 sm:gap-6">
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-white/20 flex items-center justify-center text-2xl sm:text-3xl font-bold">
              {userData.full_name?.charAt(0)?.toUpperCase() || "U"}
            </div>
            
            <div className="flex-1">
              <h1 className="text-xl sm:text-2xl font-bold">
                {showSensitive ? userData.full_name : maskSensitive(userData.full_name, "text")}
              </h1>
              <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-white/80 text-sm">
                <span className="flex items-center gap-1">
                  <Mail className="w-3.5 h-3.5" />
                  {maskSensitive(userData.email, "email")}
                </span>
                {userData.phone_number && (
                  <span className="flex items-center gap-1">
                    <Phone className="w-3.5 h-3.5" />
                    {maskSensitive(userData.phone_number, "phone")}
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <Award className="w-3.5 h-3.5" />
                  {userData.role || "CLIENT"}
                </span>
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setShowSensitive(!showSensitive)}
                className="bg-white/20 hover:bg-white/30 text-white border-0 h-8 w-8 p-0"
              >
                {showSensitive ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => navigate("/accounts/edit")}
                className="bg-white/20 hover:bg-white/30 text-white border-0 h-8 px-3"
              >
                <Edit3 className="w-4 h-4 mr-1" />
                {t("edit")}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs - Scrollable */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-4 pb-12">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="rounded-xl">
            <TabsTrigger value="overview">{t("tabs.overview")}</TabsTrigger>
            <TabsTrigger value="institutions">{t("tabs.institutions")}</TabsTrigger>
            <TabsTrigger value="businesses">{t("tabs.businesses")}</TabsTrigger>
            <TabsTrigger value="chat">
              <MessageCircle className="w-4 h-4 mr-1" />
              {t("tabs.chat")}
            </TabsTrigger>
            <TabsTrigger value="activity">{t("tabs.activity")}</TabsTrigger>
            <TabsTrigger value="security">{t("tabs.security")}</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader title={t("personal_info")} icon={<User className="w-5 h-5" />} divider />
                <CardContent>
                  <div className="space-y-4">
                    <InfoRow icon={User} label={t("full_name")} value={maskSensitive(userData.full_name)} showSensitive={showSensitive} originalValue={userData.full_name} />
                    <InfoRow icon={Mail} label={t("email")} value={maskSensitive(userData.email, "email")} verified={userData.is_verified} onCopy={() => copyToClipboard(userData.email, t("email"))} showSensitive={showSensitive} originalValue={userData.email} />
                    <InfoRow icon={Phone} label={t("phone")} value={userData.phone_number ? maskSensitive(userData.phone_number, "phone") : "-"} verified={userData.is_phone_verified} showSensitive={showSensitive} originalValue={userData.phone_number} />
                    <InfoRow icon={Shield} label={t("national_id")} value={maskSensitive(userData.national_id)} showSensitive={showSensitive} originalValue={userData.national_id} />
                    <InfoRow icon={Calendar} label={t("member_since")} value={userData.created_at ? new Date(userData.created_at).toLocaleDateString() : "-"} />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader title={t("account_status")} icon={<Shield className="w-5 h-5" />} divider />
                <CardContent>
                  <div className="space-y-4">
                    <StatusRow label={t("email_verified")} status={userData.is_verified} />
                    <StatusRow
                      label={t("phone_verified")}
                      status={userData.is_phone_verified}
                      actionLabel={t("settings.verify_phone", "Thibitisha")}
                      onAction={() => navigate("/accounts/settings")}
                    />
                    <StatusRow label={t("2fa_enabled")} status={userData.is_2fa_enabled} />
                    <StatusRow label={t("account_active")} status={userData.is_active} />
                    <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                      <Button variant="outline" className="w-full" onClick={() => setActiveTab("security")}>
                        <Key className="w-4 h-4 mr-2" />{t("manage_security")}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Institutions Tab */}
          <TabsContent value="institutions">
            <Card>
              <CardHeader 
                title={t("your_institutions")}
                icon={<Building2 className="w-5 h-5" />}
                divider
                actions={
                  <Button size="sm" onClick={() => navigate("/institutions/create")}>
                    <Plus className="w-4 h-4 mr-1" />{t("create")}
                  </Button>
                }
              />
              <CardContent>
                {loadingInstitutions ? (
                  <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-blue-600" /></div>
                ) : institutions.length > 0 ? (
                  <div className="space-y-3">
                    {institutions.map((inst) => (
                      <div key={inst.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors" onClick={() => navigate(`/kiini/institutions/${inst.id}`)}>
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                            <Building2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-gray-100">{inst.name}</p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">{inst.domain || "-"}</p>
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-gray-400" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Building2 className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-500 dark:text-gray-400 mb-4">{t("no_institutions_yet")}</p>
                    <Button onClick={() => navigate("/institutions/create")}>
                      <Plus className="w-4 h-4 mr-2" />{t("create_institution")}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Businesses Tab */}
          <TabsContent value="businesses">
            <Card>
              <CardHeader 
                title={t("your_businesses")}
                icon={<Store className="w-5 h-5" />}
                divider
                actions={
                  <Button size="sm" onClick={() => navigate("/businesses/register/")}>
                    <Plus className="w-4 h-4 mr-1" />{t("create")}
                  </Button>
                }
              />
              <CardContent>
                {loadingBusinesses ? (
                  <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-blue-600" /></div>
                ) : businesses.length > 0 ? (
                  <div className="space-y-3">
                    {businesses.map((biz) => (
                      <div key={biz.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors" onClick={() => navigate(`/businesses/dashboard/${biz.id}/overview`)}>
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                            <Store className="w-5 h-5 text-green-600 dark:text-green-400" />
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-gray-100">{biz.name}</p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">{biz.category_name || biz.description?.substring(0, 50) || "-"}</p>
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-gray-400" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Store className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-500 dark:text-gray-400 mb-4">{t("no_businesses_yet")}</p>
                    <Button onClick={() => navigate("/businesses/register/")}>
                      <Plus className="w-4 h-4 mr-2" />{t("create_business")}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Chat Tab */}
          <TabsContent value="chat">
            <Card>
              <CardHeader 
                title={t("recent_conversations")}
                icon={<MessageCircle className="w-5 h-5" />}
                divider
                actions={
                  <Button size="sm" onClick={() => navigate("/jamiichat")}>
                    {t("open_chat")}<ArrowRight className="w-4 h-4 ml-1" />
                  </Button>
                }
              />
              <CardContent>
                {loadingChats ? (
                  <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-blue-600" /></div>
                ) : recentChats.length > 0 ? (
                  <div className="space-y-2">
                    {recentChats.map((chat) => (
                      <div key={chat.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors" onClick={() => navigate(`/jamiichat/${chat.id}`)}>
                        <div className="flex items-center gap-3">
                          <div className="relative">
                            <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
                              <MessageCircle className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                            </div>
                            {chat.unread > 0 && (
                              <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">{chat.unread}</span>
                            )}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-gray-100">{chat.name}</p>
                            <p className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-[200px]">{chat.lastMessage}</p>
                          </div>
                        </div>
                        <div className="text-right"><p className="text-xs text-gray-400">{chat.time}</p></div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <MessageCircle className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-500 dark:text-gray-400 mb-4">{t("no_conversations_yet")}</p>
                    <Button onClick={() => navigate("/jamiichat")}>
                      <MessageCircle className="w-4 h-4 mr-2" />{t("start_chat")}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Activity Tab */}
          <TabsContent value="activity">
            <Card>
              <CardHeader title={t("recent_activity")} icon={<Clock className="w-5 h-5" />} divider />
              <CardContent>
                {loadingActivities ? (
                  <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-blue-600" /></div>
                ) : activities.length > 0 ? (
                  <div className="space-y-3">
                    {activities.map((activity) => {
                      const IconComponent = activity.icon || Clock;
                      return (
                        <div key={activity.id} className="flex items-start gap-3 p-3">
                          <div className="w-8 h-8 rounded-full bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
                            <IconComponent className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                          </div>
                          <div className="flex-1">
                            <p className="text-gray-900 dark:text-gray-100">{activity.action}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{activity.time}</p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Clock className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-500 dark:text-gray-400">{t("no_recent_activity")}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security">
            <div className="space-y-6">
              <Card>
                <CardHeader title={t("two_factor_authentication")} divider />
                <CardContent>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{t("2fa_status")}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{userData.is_2fa_enabled ? t("2fa_enabled_desc") : t("2fa_disabled_desc")}</p>
                    </div>
                    <Button variant={userData.is_2fa_enabled ? "destructive" : "default"} onClick={() => navigate("/security/2fa/setup")}>
                      {userData.is_2fa_enabled ? t("disable_2fa") : t("enable_2fa")}
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader title={t("change_password")} divider />
                <CardContent>
                  <Button variant="outline" onClick={() => navigate("/accounts/change-password")}>
                    <Key className="w-4 h-4 mr-2" />{t("update_password")}
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader title={t("danger_zone")} divider />
                <CardContent>
                  <Button variant="destructive" onClick={handleLogout} className="w-full sm:w-auto">
                    <LogOut className="w-4 h-4 mr-2" />{t("logout")}
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function InfoRow({ icon: Icon, label, value, verified, onCopy, showSensitive, originalValue }) {
  const displayValue = showSensitive && originalValue ? originalValue : value;
  return (
    <div className="flex items-start gap-3">
      <Icon className="w-5 h-5 text-gray-400 dark:text-gray-500 mt-0.5 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
        <div className="flex items-center gap-2 flex-wrap">
          <p className="font-medium text-gray-900 dark:text-gray-100 truncate">{displayValue || "-"}</p>
          {verified !== undefined && (verified ? <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" /> : <XCircle className="w-4 h-4 text-yellow-500 flex-shrink-0" />)}
          {onCopy && showSensitive && originalValue && (
            <button onClick={onCopy} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 flex-shrink-0">
              <Copy className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusRow({ label, status, actionLabel, onAction }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-600 dark:text-gray-300">{label}</span>
      {status ? (
        <span className="flex items-center gap-1 text-green-600 dark:text-green-400"><CheckCircle className="w-4 h-4" />Active</span>
      ) : actionLabel && onAction ? (
        <button
          onClick={onAction}
          className="flex items-center gap-1 text-yellow-600 dark:text-yellow-400 hover:underline"
        >
          <XCircle className="w-4 h-4" />{actionLabel}
        </button>
      ) : (
        <span className="flex items-center gap-1 text-yellow-600 dark:text-yellow-400"><XCircle className="w-4 h-4" />Inactive</span>
      )}
    </div>
  );
}