import React, { useState, useEffect } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert, AlertDescription } from "@/components/ui/Alert";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Textarea } from "@/components/ui/Textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/Select";
import { Switch } from "@/components/ui/Switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import { Progress } from "@/components/ui/Progress";
import {
  Heart,
  Star,
  RefreshCw,
  Search,
  Filter,
  TrendingUp,
  TrendingDown,
  Plus,
  Edit,
  Trash2,
  Eye,
  EyeOff,
  Target,
  Activity,
  BarChart3,
  PieChart,
  AlertTriangle,
} from "lucide-react";

interface UserInterestProfile {
  user_id: string;
  tenant_id: string;
  interests: Record<string, number>;
  keywords: Record<string, string[]>;
  interaction_history: Array<{
    type: string;
    category: string;
    content: string;
    timestamp: string;
    keywords: string[];
  }>;
  last_updated: string;
  created_at: string;
  updated_at: string;
}

interface InterestCategory {
  name: string;
  score: number;
  keywords: string[];
  trend: "up" | "down" | "stable";
  last_updated: string;
}

interface UserInteraction {
  id: string;
  user_id: string;
  tenant_id: string;
  interaction_type: string;
  content: string;
  category: string;
  timestamp: string;
  metadata: Record<string, unknown>;
  keywords?: string[];
}

const UserInterests: React.FC = () => {
  const [profile, setProfile] = useState<UserInterestProfile | null>(null);
  const [topInterests, setTopInterests] = useState<InterestCategory[]>([]);
  const [interactionHistory, setInteractionHistory] = useState<
    UserInteraction[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showAddInterest, setShowAddInterest] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  // Add interest form state
  const [interestForm, setInterestForm] = useState({
    category: "",
    keywords: "",
    score_adjustment: 0.1,
  });

  useEffect(() => {
    fetchProfile();
    fetchTopInterests();
    fetchInteractionHistory();

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchProfile();
        fetchTopInterests();
        fetchInteractionHistory();
      }, 30_000);

      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchProfile = async () => {
    try {
      const data = await apiGet<UserInterestProfile>(
        "communications/interests",
      );
      setProfile(data);
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to fetch profile",
      );
    } finally {
      setLoading(false);
    }
  };

  const fetchTopInterests = async () => {
    try {
      const data = await apiGet<{
        top_interests: [string, number][];
      }>("communications/interests/top?limit=10&min_score=0.1");

      const interests = data.top_interests.map(
        ([category, score]: [string, number]) => ({
          name: category,
          score: score,
          keywords: [],
          trend: "stable" as const,
          last_updated: new Date().toISOString(),
        }),
      );

      setTopInterests(interests);
    } catch (error_) {
      setError(
        error_ instanceof Error
          ? error_.message
          : "Failed to fetch top interests",
      );
    }
  };

  const fetchInteractionHistory = async () => {
    try {
      // This would normally fetch from the API
      // For now, we'll simulate some interaction history
      const mockHistory: UserInteraction[] = [
        {
          id: "1",
          user_id: profile?.user_id || "",
          tenant_id: profile?.tenant_id || "",
          interaction_type: "view",
          content: "Viewed React documentation",
          category: "technology",
          timestamp: new Date(Date.now() - 86_400_000).toISOString(),
          metadata: {},
          keywords: ["react", "documentation", "frontend"],
        },
        {
          id: "2",
          user_id: profile?.user_id || "",
          tenant_id: profile?.tenant_id || "",
          interaction_type: "like",
          content: "Liked Python tutorial",
          category: "technology",
          timestamp: new Date(Date.now() - 172_800_000).toISOString(),
          metadata: {},
          keywords: ["python", "tutorial", "programming"],
        },
        {
          id: "3",
          user_id: profile?.user_id || "",
          tenant_id: profile?.tenant_id || "",
          interaction_type: "share",
          content: "Shared marketing campaign article",
          category: "marketing",
          timestamp: new Date(Date.now() - 259_200_000).toISOString(),
          metadata: {},
          keywords: ["marketing", "campaign", "social"],
        },
      ];

      setInteractionHistory(mockHistory);
    } catch (error_) {
      setError(
        error_ instanceof Error
          ? error_.message
          : "Failed to fetch interaction history",
      );
    }
  };

  const handleAddInterest = async () => {
    try {
      const keywords = interestForm.keywords
        .split(",")
        .map((k) => k.trim())
        .filter((k) => k.length > 0);

      if (!interestForm.category || keywords.length === 0) {
        setError("Please provide a category and at least one keyword");
        return;
      }

      await apiPost("communications/interests/update", {
        interactions: [
          {
            type: "manual",
            content:
              typeof interestForm.keywords === "string"
                ? interestForm.keywords
                : (interestForm.keywords as string[]).join(", "),
            category: interestForm.category,
            timestamp: new Date().toISOString(),
            metadata: {},
          },
        ],
      });

      await fetchProfile();
      await fetchTopInterests();
      setShowAddInterest(false);
      setInterestForm({
        category: "",
        keywords: "",
        score_adjustment: 0.1,
      });
      setError(null);
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to add interest",
      );
    }
  };

  const handleUpdateInterestScore = async (
    category: string,
    scoreAdjustment: number,
  ) => {
    try {
      await apiPost("communications/interests/update-score", {
        category: category,
        score_adjustment: scoreAdjustment,
      });

      await fetchProfile();
      await fetchTopInterests();
      setError(null);
    } catch (error_) {
      setError(
        error_ instanceof Error
          ? error_.message
          : "Failed to update interest score",
      );
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-yellow-600";
    if (score >= 0.4) return "text-orange-600";
    return "text-red-600";
  };

  const getScoreBackground = (score: number) => {
    if (score >= 0.8) return "bg-green-100";
    if (score >= 0.6) return "bg-yellow-100";
    if (score >= 0.4) return "bg-orange-100";
    return "bg-red-100";
  };

  const getTrendIcon = (trend: string) => {
    if (trend === "up")
      return <TrendingUp className="h-4 w-4 text-green-600" />;
    if (trend === "down")
      return <TrendingDown className="h-4 w-4 text-red-600" />;
    return <Activity className="h-4 w-4 text-gray-600" />;
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);

    if (diffSeconds < 60) return "Just now";
    if (diffSeconds < 3600)
      return `${Math.floor(diffSeconds / 60)} minutes ago`;
    if (diffSeconds < 86_400)
      return `${Math.floor(diffSeconds / 3600)} hours ago`;
    return `${Math.floor(diffSeconds / 86_400)} days ago`;
  };

  const getCategoryIcon = (category: string) => {
    const icons = {
      technology: <Star className="h-4 w-4" />,
      healthcare: <Heart className="h-4 w-4" />,
      finance: <Target className="h-4 w-4" />,
      education: <Star className="h-4 w-4" />,
      marketing: <Target className="h-4 w-4" />,
      design: <Star className="h-4 w-4" />,
      business: <Target className="h-4 w-4" />,
      science: <Star className="h-4 w-4" />,
      sports: <Heart className="h-4 w-4" />,
      travel: <Heart className="h-4 w-4" />,
    };
    return (
      icons[category as keyof typeof icons] || <Star className="h-4 w-4" />
    );
  };

  const getInteractionTypeColor = (type: string) => {
    const colors = {
      view: "bg-blue-100 text-blue-800",
      like: "bg-green-100 text-green-800",
      share: "bg-purple-100 text-purple-800",
      click: "bg-orange-100 text-orange-800",
      comment: "bg-pink-100 text-pink-800",
      bookmark: "bg-red-100 text-red-800",
      apply: "bg-indigo-100 text-indigo-800",
    };
    return colors[type as keyof typeof colors] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">User Interests</h1>
          <p className="text-gray-600">
            Manage user interests and interaction history
          </p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={() => setShowAddInterest(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Interest
          </Button>
          <Button variant="outline" onClick={() => setShowHistory(true)}>
            <Activity className="h-4 w-4 mr-2" />
            View History
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw
              className={`h-4 w-4 mr-2 ${autoRefresh ? "animate-spin" : ""}`}
            />
            {autoRefresh ? "Auto-refresh" : "Manual refresh"}
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Profile Overview */}
      {profile && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Total Interests</span>
                  <span className="text-2xl font-bold">
                    {Object.keys(profile.interests).length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Average Score</span>
                  <span className="text-2xl font-bold">
                    {Object.values(profile.interests).length > 0
                      ? (
                          Object.values(profile.interests).reduce(
                            (a, b) => a + b,
                            0,
                          ) / Object.values(profile.interests).length
                        ).toFixed(2)
                      : "0.00"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Total Keywords</span>
                  <span className="text-2xl font-bold">
                    {Object.values(profile.keywords).reduce(
                      (a, b) => a + b.length,
                      0,
                    )}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Interactions</span>
                  <span className="text-2xl font-bold">
                    {profile.interaction_history.length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Last Updated</span>
                  <span className="text-sm text-gray-500">
                    {formatTimeAgo(profile.last_updated)}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Top Interests</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {topInterests.map((interest, index) => (
                  <div
                    key={interest.name}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center space-x-3">
                      {getCategoryIcon(interest.name)}
                      <div className="flex-1">
                        <h4 className="font-medium capitalize">
                          {interest.name}
                        </h4>
                        <div className="flex items-center space-x-2">
                          <div
                            className={`w-24 h-2 rounded-full ${getScoreBackground(interest.score)}`}
                          />
                          <span
                            className={`text-sm font-medium ${getScoreColor(interest.score)}`}
                          >
                            {(interest.score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getTrendIcon(interest.trend)}
                      <span className="text-xs text-gray-500">
                        {interest.trend}
                      </span>
                    </div>
                  </div>
                ))}

                {topInterests.length === 0 && (
                  <div className="text-center py-4">
                    <Star className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">
                      No interests profiled yet
                    </p>
                    <p className="text-sm text-gray-400 mt-2">
                      Start adding interests to improve recommendations
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Interest Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(profile.interests)
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 5)
                  .map(([category, score]) => (
                    <div
                      key={category}
                      className="flex items-center justify-between"
                    >
                      <div className="flex items-center space-x-3">
                        {getCategoryIcon(category)}
                        <span className="text-sm font-medium capitalize">
                          {category}
                        </span>
                        <div className="flex items-center space-x-2">
                          <div
                            className={`w-20 h-2 rounded-full ${getScoreBackground(score)}`}
                          />
                          <span
                            className={`text-sm font-medium ${getScoreColor(score)}`}
                          >
                            {(score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}

                {Object.keys(profile.interests).length === 0 && (
                  <div className="text-center py-4">
                    <PieChart className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">
                      No interests profiled yet
                    </p>
                    <p className="text-sm text-gray-400 mt-2">
                      Start adding interests to see distribution
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Add Interest Modal */}
      {showAddInterest && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Add Interest</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="category">Category</Label>
                <Select
                  value={interestForm.category}
                  onValueChange={(value) =>
                    setInterestForm({ ...interestForm, category: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="technology">Technology</SelectItem>
                    <SelectItem value="healthcare">Healthcare</SelectItem>
                    <SelectItem value="finance">Finance</SelectItem>
                    <SelectItem value="education">Education</SelectItem>
                    <SelectItem value="marketing">Marketing</SelectItem>
                    <SelectItem value="design">Design</SelectItem>
                    <SelectItem value="business">Business</SelectItem>
                    <SelectItem value="science">Science</SelectItem>
                    <SelectItem value="sports">Sports</SelectItem>
                    <SelectItem value="travel">Travel</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="keywords">Keywords (comma-separated)</Label>
                <Input
                  id="keywords"
                  placeholder="react, python, javascript, design"
                  value={interestForm.keywords}
                  onChange={(e) =>
                    setInterestForm({
                      ...interestForm,
                      keywords: e.target.value,
                    })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="score-adjustment">Score Adjustment</Label>
                <Select
                  value={interestForm.score_adjustment.toString()}
                  onValueChange={(value) =>
                    setInterestForm({
                      ...interestForm,
                      score_adjustment: Number.parseFloat(value),
                    })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0.1">+0.1 (Small boost)</SelectItem>
                    <SelectItem value="0.2">+0.2 (Medium boost)</SelectItem>
                    <SelectItem value="0.3">+0.3 (Large boost)</SelectItem>
                    <SelectItem value="-0.1">-0.1 (Small decrease)</SelectItem>
                    <SelectItem value="-0.2">-0.2 (Medium decrease)</SelectItem>
                    <SelectItem value="-0.3">-0.3 (Large decrease)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex space-x-2">
                <Button
                  onClick={handleAddInterest}
                  disabled={!interestForm.category || !interestForm.keywords}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Interest
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowAddInterest(false)}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Interaction History Modal */}
      {showHistory && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Interaction History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {interactionHistory.slice(0, 20).map((interaction) => (
                <Card key={interaction.id} className="p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div
                        className={`px-2 py-1 rounded-full ${getInteractionTypeColor(interaction.interaction_type)}`}
                      >
                        <span className="text-xs font-medium">
                          {interaction.interaction_type}
                        </span>
                      </div>
                      <div className="flex-1">
                        <p className="text-sm line-clamp-2">
                          {interaction.content}
                        </p>
                        <div className="flex items-center space-x-2 mt-2">
                          <Badge variant="outline" className="text-xs">
                            {interaction.category}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {formatTimeAgo(interaction.timestamp)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {interaction.keywords &&
                      interaction.keywords.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {interaction.keywords
                            .slice(0, 3)
                            .map((keyword: string, index: number) => (
                              <Badge
                                key={index}
                                variant="outline"
                                className="text-xs"
                              >
                                {keyword}
                              </Badge>
                            ))}
                        </div>
                      )}
                  </div>
                </Card>
              ))}

              {interactionHistory.length === 0 && (
                <div className="text-center py-4">
                  <Activity className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">
                    No interaction history yet
                  </p>
                  <p className="text-sm text-gray-400 mt-2">
                    Your interaction history will appear here
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              variant="outline"
              className="h-20"
              onClick={() => setShowAddInterest(true)}
            >
              <Plus className="h-6 w-6 mx-auto mb-2" />
              Add Interest
            </Button>
            <Button
              variant="outline"
              className="h-20"
              onClick={() => setShowHistory(true)}
            >
              <Activity className="h-6 w-6 mx-auto mb-2" />
              View History
            </Button>
            <Button
              variant="outline"
              className="h-20"
              onClick={() => {
                // Export profile data
                const dataString = JSON.stringify(profile, null, 2);
                const blob = new Blob([dataString], {
                  type: "application/json",
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "user-interests-profile.json";
                a.click();
              }}
            >
              <BarChart3 className="h-6 w-6 mx-auto mb-2" />
              Export Profile
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default UserInterests;
