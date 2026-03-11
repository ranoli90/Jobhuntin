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
import { Progress } from "@/components/ui/Progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/Tabs";
import {
  Brain,
  Target,
  Search,
  RefreshCw,
  Filter,
  TrendingUp,
  TrendingDown,
  Zap,
  Eye,
  Settings,
  BarChart3,
  PieChart,
  Activity,
  Lightbulb,
  AlertTriangle,
} from "lucide-react";

interface UserProfile {
  user_id: string;
  tenant_id: string;
  interests: Record<string, number>;
  keywords: Record<string, string[]>;
  last_updated: string;
  created_at: string;
}

interface RelevanceScore {
  notification_id: string;
  user_id: string;
  relevance_score: number;
  category_scores: Record<string, number>;
  keyword_matches: string[];
  semantic_factors: Record<string, number>;
  calculated_at: string;
}

interface ContentRecommendation {
  id: string;
  title: string;
  content: string;
  category: string;
  similarity_score: number;
  metadata: Record<string, any>;
}

interface InterestCategory {
  name: string;
  score: number;
  keywords: string[];
  trend: "up" | "down" | "stable";
}

const SemanticMatcher: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [topInterests, setTopInterests] = useState<InterestCategory[]>([]);
  const [recommendations, setRecommendations] = useState<
    ContentRecommendation[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showProfile, setShowProfile] = useState(false);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);

  // Analysis form state
  const [analysisForm, setAnalysisForm] = useState({
    content: "",
    category: "general",
  });

  // Profile update form state
  const [profileForm, setProfileForm] = useState({
    interests: {} as Record<string, number>,
    keywords: {} as Record<string, string[]>,
  });

  useEffect(() => {
    fetchProfile();
    fetchTopInterests();

    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchProfile();
        fetchTopInterests();
      }, 30_000);

      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchProfile = async () => {
    try {
      const data = await apiGet<UserProfile>("communications/interests");
      setProfile(data);
      setProfileForm({
        interests: data.interests,
        keywords: data.keywords,
      });
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

  const handleUpdateProfile = async () => {
    try {
      await apiPost("communications/interests/update", {
        interactions: [
          {
            type: "view",
            content: analysisForm.content,
            category: analysisForm.category,
            timestamp: new Date().toISOString(),
            metadata: {},
          },
        ],
      });

      await fetchProfile();
      await fetchTopInterests();
      setShowAnalysis(false);
      setAnalysisForm({ content: "", category: "general" });
      setError(null);
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to update profile",
      );
    }
  };

  const handleCalculateMatch = async () => {
    try {
      const params = new URLSearchParams({
        content: analysisForm.content,
        category: analysisForm.category,
      });
      const data = await apiGet<{ similarity_score: number }>(
        `communications/semantic/match?${params}`,
      );

      alert(
        `Semantic Match Score: ${(data.similarity_score * 100).toFixed(1)}%`,
      );
    } catch (error_) {
      setError(
        error_ instanceof Error ? error_.message : "Failed to calculate match",
      );
    }
  };

  const handleGetRecommendations = async () => {
    setError(null);
    try {
      const data = await apiGet<{ recommendations?: ContentRecommendation[] }>(
        "communications/recommendations",
      );
      const recs = data?.recommendations ?? [];
      setRecommendations(recs);
      setShowRecommendations(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Content recommendations API not available.",
      );
      setRecommendations([]);
      setShowRecommendations(true);
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

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Semantic Matcher</h1>
          <p className="text-gray-600">
            AI-powered semantic notification matching and user profiling
          </p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={() => setShowAnalysis(true)}>
            <Brain className="h-4 w-4 mr-2" />
            Analyze Content
          </Button>
          <Button variant="outline" onClick={handleGetRecommendations}>
            <Target className="h-4 w-4 mr-2" />
            Get Recommendations
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
                      <span className="text-sm font-medium capitalize">
                        {interest.name}
                      </span>
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
                    <Lightbulb className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">
                      No interests profiled yet
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
                  ))}

                {Object.keys(profile.interests).length === 0 && (
                  <div className="text-center py-4">
                    <PieChart className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">
                      No interests profiled yet
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Content Analysis Modal */}
      {showAnalysis && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Content Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="content">Content</Label>
                  <Textarea
                    id="content"
                    placeholder="Enter content to analyze"
                    rows={4}
                    value={analysisForm.content}
                    onChange={(e) =>
                      setAnalysisForm({
                        ...analysisForm,
                        content: e.target.value,
                      })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Select
                    value={analysisForm.category}
                    onValueChange={(value) =>
                      setAnalysisForm({ ...analysisForm, category: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general">General</SelectItem>
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
              </div>

              <div className="flex space-x-2">
                <Button
                  onClick={handleCalculateMatch}
                  disabled={!analysisForm.content}
                >
                  <Brain className="h-4 w-4 mr-2" />
                  Calculate Match
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowAnalysis(false)}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recommendations Modal */}
      {showRecommendations && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>Content Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recommendations.map((rec) => (
                <Card key={rec.id} className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium">{rec.title}</h4>
                      <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                        {rec.content}
                      </p>
                      <div className="flex items-center space-x-2 mt-2">
                        <Badge variant="outline">{rec.category}</Badge>
                        <div
                          className={`px-2 py-1 rounded-full ${getScoreBackground(rec.similarity_score)}`}
                        >
                          <span
                            className={`text-xs font-medium ${getScoreColor(rec.similarity_score)}`}
                          >
                            {(rec.similarity_score * 100).toFixed(1)}% match
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button size="sm" variant="outline">
                        <Eye className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}

              {recommendations.length === 0 && (
                <div className="text-center py-4">
                  <Target className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">
                    No recommendations available
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Profile Details */}
      {showProfile && profile && (
        <Card className="p-6">
          <CardHeader>
            <CardTitle>User Interest Profile</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="interests" className="space-y-4">
              <TabsList>
                <TabsTrigger value="interests">Interests</TabsTrigger>
                <TabsTrigger value="keywords">Keywords</TabsTrigger>
              </TabsList>
              <TabsContent value="interests">
                <div className="space-y-4">
                  {Object.entries(profile.interests).map(
                    ([category, score]) => (
                      <div
                        key={category}
                        className="flex items-center justify-between"
                      >
                        <span className="font-medium capitalize">
                          {category}
                        </span>
                        <div className="flex items-center space-x-2">
                          <div
                            className={`w-24 h-2 rounded-full ${getScoreBackground(score)}`}
                          />
                          <span
                            className={`font-medium ${getScoreColor(score)}`}
                          >
                            {(score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    ),
                  )}
                </div>
              </TabsContent>
              <TabsContent value="keywords">
                <div className="space-y-4">
                  {Object.entries(profile.keywords).map(
                    ([category, keywords]) => (
                      <div key={category} className="space-y-2">
                        <h4 className="font-medium capitalize">{category}</h4>
                        <div className="flex flex-wrap gap-2">
                          {keywords.map((keyword, index) => (
                            <Badge
                              key={index}
                              variant="outline"
                              className="text-xs"
                            >
                              {keyword}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    ),
                  )}
                </div>
              </TabsContent>
            </Tabs>

            <div className="flex space-x-2 mt-6">
              <Button onClick={() => setShowProfile(false)}>Close</Button>
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
              onClick={() => setShowAnalysis(true)}
            >
              <Brain className="h-6 w-6 mx-auto mb-2" />
              Analyze Content
            </Button>
            <Button
              variant="outline"
              className="h-20"
              onClick={handleGetRecommendations}
            >
              <Target className="h-6 w-6 mx-auto mb-2" />
              Get Recommendations
            </Button>
            <Button
              variant="outline"
              className="h-20"
              onClick={() => setShowProfile(true)}
            >
              <BarChart3 className="h-6 w-6 mx-auto mb-2" />
              View Profile
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SemanticMatcher;
