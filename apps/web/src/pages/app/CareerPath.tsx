/**
 * Career Path Page - Visualize career analysis results
 * Microsoft-level implementation with interactive charts and comprehensive insights
 */

import * as React from "react";
import { useTranslation } from "react-i18next";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { 
  TrendingUp, 
  Target, 
  Award, 
  BookOpen, 
  Users, 
  Brain,
  Lightbulb,
  BarChart3,
  PieChart,
  Calendar,
  Clock,
  ArrowRight,
  Download,
  RefreshCw,
  Briefcase,
  GraduationCap,
  Star
} from "lucide-react";

export default function CareerPathPage() {
  const { t } = useTranslation();
  const locale = localStorage.getItem("language") || "en";
  const queryClient = useQueryClient();

  // State
  const [selectedView, setSelectedView] = React.useState<"overview" | "trajectory" | "recommendations" | "learning">("overview");
  const [timeRange, setTimeRange] = React.useState<"1year" | "3years" | "5years">("3years");

  // Mock data for demonstration (would come from API)
  const mockCareerData = {
    current_level: "Senior Software Engineer",
    current_track: "Technical Leadership",
    total_experience_years: 8,
    career_progression_score: 75,
    possible_next_roles: ["Principal Engineer", "Engineering Manager", "CTO"],
    current_skills: [
      "JavaScript", "TypeScript", "React", "Node.js", "Python", 
      "AWS", "Docker", "Kubernetes", "Team Leadership"
    ],
    trajectory: [
      {
        year: 2016,
        level: "Junior Developer",
        company: "TechCorp",
        description: "Started as frontend developer"
      },
      {
        year: 2018,
        level: "Mid-level Developer", 
        company: "StartupXYZ",
        description: "Promoted to mid-level, led key frontend projects"
      },
      {
        year: 2020,
        level: "Senior Developer",
        company: "Enterprise Corp",
        description: "Joined enterprise, worked on large-scale applications"
      },
      {
        year: 2022,
        level: "Lead Developer",
        company: "Current Company",
        description: "Leading development team, architecting microservices"
      }
    ],
    recommendations: {
      current_role: "Senior Software Engineer",
      target_role: "Engineering Manager",
      path_type: "advancement",
      steps: [
        "Develop leadership skills through team projects",
        "Take on technical mentorship roles",
        "Complete management training programs",
        "Gain experience in cross-functional collaboration"
      ],
      estimated_timeline_months: 18,
      potential_salary_increase_pct: 25,
      confidence: 0.85,
      skill_gaps: [
        {
          skill: "Project Management",
          importance: "high",
          acquisition_method: "certification"
        },
        {
          skill: "People Management",
          importance: "medium",
          acquisition_method: "on-the-job training"
        },
        {
          skill: "Cloud Architecture",
          importance: "high",
          acquisition_method: "certification"
        }
      ]
    },
    learning_path: {
      recommended_pace: "aggressive",
      total_weeks: 52,
      milestones: [
        {
          title: "Advanced React Patterns",
          description: "Master advanced React design patterns and state management",
          estimated_weeks: 8,
          resources: ["Advanced React Patterns Course", "React Documentation"]
        },
        {
          title: "Cloud Architecture Certification",
          description: "Get AWS Solutions Architect certification",
          estimated_weeks: 12,
          resources: ["AWS Training", "Practice Exams", "Study Materials"]
        },
        {
          title: "Leadership Development",
          description: "Complete management training and take on leadership roles",
          estimated_weeks: 16,
          resources: ["Management Courses", "Leadership Books", "Mentorship Program"]
        },
        {
          title: "Technical Blogging",
          description: "Build technical presence through writing and presentations",
          estimated_weeks: 24,
          resources: ["Personal Blog", "Tech Meetups", "Conference Speaking"]
        }
      ]
    }
  };

  // Fetch career data (would be from API)
  const {
    data: careerData = mockCareerData,
    isLoading,
    error,
    refetch: refetchCareerData,
  } = useQuery({
    queryKey: ["career-path"],
    queryFn: async () => {
      // return await apiGet("career/analyze");
      return mockCareerData; // Mock for demo
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Analyze mutation
  const analyzeMutation = useMutation({
    mutationFn: async (data: any) => {
      // return await apiPost("career/analyze", data);
      console.log("Career analysis requested:", data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["career-path"] });
    },
  });

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getLevelColor = (level: string) => {
    const levelColors: Record<string, string> = {
      "Junior": "text-blue-600",
      "Mid-level": "text-yellow-600", 
      "Senior": "text-green-600",
      "Lead": "text-purple-600",
      "Principal": "text-indigo-600"
    };
    return levelColors[level] || "text-slate-600";
  };

  const generateCareerTimeline = () => {
    const timeline = document.createElement('div');
    timeline.className = 'relative';
    
    // Create timeline line
    const timelineLine = document.createElement('div');
    timelineLine.className = 'absolute left-8 top-1/2 bottom-0 w-0.5 h-px bg-slate-300';
    
    return { timeline, timelineLine };
  };

  const handleExportReport = () => {
    // Export career analysis report
    const data = {
      format: "pdf",
      sections: ["overview", "trajectory", "recommendations", "learning_path"]
    };
    console.log("Exporting career report:", data);
    // Would call API to generate and download report
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <Card className="p-6 text-center">
          <BarChart3 className="w-12 h-12 mx-auto text-red-500 mb-4" />
          <h2 className="text-xl font-semibold text-red-600 mb-2">
            {t("careerPath.errorLoading", locale) || "Error Loading Career Data"}
          </h2>
          <p className="text-slate-600">{error}</p>
          <Button onClick={() => refetchCareerData()}>
            {t("common.retry", locale) || "Retry"}
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">
            {t("careerPath.title", locale) || "Career Path Analysis"}
          </h1>
          <p className="text-slate-500 font-medium">
            {t("careerPath.description", locale) || "Visualize your career progression and get personalized recommendations for advancement"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={selectedView === "overview" ? "default" : "outline"}
            onClick={() => setSelectedView("overview")}
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            {t("careerPath.overview", locale) || "Overview"}
          </Button>
          <Button
            variant={selectedView === "trajectory" ? "default" : "outline"}
            onClick={() => setSelectedView("trajectory")}
          >
            <TrendingUp className="w-4 h-4 mr-2" />
            {t("careerPath.trajectory", locale) || "Trajectory"}
          </Button>
          <Button
            variant={selectedView === "recommendations" ? "default" : "outline"}
            onClick={() => setSelectedView("recommendations")}
          >
            <Lightbulb className="w-4 h-4 mr-2" />
            {t("careerPath.recommendations", locale) || "Recommendations"}
          </Button>
          <Button
            variant={selectedView === "learning" ? "default" : "outline"}
            onClick={() => setSelectedView("learning")}
          >
            <BookOpen className="w-4 h-4 mr-2" />
            {t("careerPath.learning", locale) || "Learning Path"}
          </Button>
          <Button onClick={handleExportReport}>
            <Download className="w-4 h-4 mr-2" />
            {t("careerPath.export", locale) || "Export Report"}
          </Button>
        </div>
      </div>

      {/* Overview View */}
      {selectedView === "overview" && (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Current Status */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">
              {t("careerPath.currentStatus", locale) || "Current Status"}
            </h2>
            <div className="grid grid-cols-2 gap-6">
              <div className="text-center">
                <div className="text-4xl font-bold text-slate-900 mb-2">
                  {careerData.current_level}
                </div>
                <p className="text-sm text-slate-600">{t("careerPath.currentLevel", locale) || "Current Level"}</p>
                <div className={`text-2xl font-bold ${getLevelColor(careerData.current_level)}`}>
                  {careerData.career_progression_score}
                </div>
                <p className="text-sm text-slate-600">{t("careerPath.progressionScore", locale) || "Progression Score"}</p>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-slate-900 mb-2">
                  {careerData.total_experience_years}
                </div>
                <p className="text-sm text-slate-600">{t("careerPath.yearsExperience", locale) || "Years Experience"}</p>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                {t("careerPath.skills", locale) || "Top Skills"}
              </h3>
              <div className="flex flex-wrap gap-2">
                {careerData.current_skills.slice(0, 8).map((skill, index) => (
                  <Badge key={index} variant="outline" className="mb-2">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          </Card>

          {/* Career Trajectory */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">
              {t("careerPath.careerTrajectory", locale) || "Career Trajectory"}
            </h2>
            <div className="space-y-4">
              {careerData.trajectory.map((item, index) => (
                <div key={index} className="flex items-start gap-4 pb-4 border-b border-slate-200 last:border-b-0">
                  <div className="flex-shrink-0 w-16 text-center">
                    <div className="text-sm text-slate-500 mb-1">{item.year}</div>
                    <div className={`w-3 h-3 rounded-full ${getLevelColor(item.level)} mx-auto`}></div>
                  </div>
                  <div className="flex-1">
                    <div>
                      <h4 className="font-semibold text-slate-900">{item.level}</h4>
                      <span className={`ml-2 text-sm ${getLevelColor(item.level)}`}>{item.company}</span>
                    </div>
                      <p className="text-sm text-slate-600 mt-1">{item.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Potential Next Roles */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">
              {t("careerPath.potentialRoles", locale) || "Potential Next Roles"}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {careerData.possible_next_roles.map((role, index) => (
                <div key={index} className="p-4 border border-slate-200 rounded-lg hover:shadow-md">
                  <div className="flex items-center mb-2">
                    <Target className="w-6 h-6 text-primary-600 mr-2" />
                    <h4 className="font-semibold text-slate-900">{role}</h4>
                  </div>
                  <p className="text-sm text-slate-600">{t("careerPath.readyIn", locale) || "Ready in"} {careerData.estimated_timeline_months} {t("careerPath.months", locale) || "months"}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Trajectory View */}
      {selectedView === "trajectory" && (
        <div className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">
              {t("careerPath.careerProgression", locale) || "Career Progression"}
            </h2>
            <div className="relative">
              <div className="absolute left-8 top-1/2 transform -translate-y-1/2">
                <Users className="w-6 h-6 text-slate-400" />
              </div>
              <div className="ml-12 pl-20 border-l-4 border-slate-200">
                {careerData.trajectory.map((item, index) => (
                  <div key={index} className="relative">
                    <div className="absolute left-0 top-0 w-2 h-2 bg-primary-600 rounded-full"></div>
                    <div className="ml-4 pl-8 pb-4">
                      <div className="font-semibold text-slate-900">{item.year}</div>
                      <div className={`text-sm ${getLevelColor(item.level)}`}>{item.level}</div>
                      <div className="text-sm text-slate-600 mt-1">{item.company}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Recommendations View */}
      {selectedView === "recommendations" && (
        <div className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">
              {t("careerPath.recommendations", locale) || "Career Recommendations"}
            </h2>
            <div className="bg-blue-50 border-blue-200 rounded-lg p-4 mb-4">
              <div className="flex items-center mb-2">
                <Target className="w-6 h-6 text-blue-600 mr-2" />
                <div>
                  <h3 className="text-lg font-semibold text-blue-900">
                    {careerData.recommendations.target_role}
                  </h3>
                  <span className="ml-2 text-blue-600">→</span>
                  <span className="text-lg text-blue-900">{careerData.recommendations.current_role}</span>
                </div>
              </div>
              <div className="text-sm text-blue-700">
                <p className="font-medium">{t("careerPath.pathType", locale) || "Path Type"}:</p>
                <span className="ml-2">{careerData.recommendations.path_type}</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <h4 className="font-semibold text-slate-900 mb-2">
                  {t("careerPath.timeline", locale) || "Timeline"}
                </h4>
                <p className="text-sm text-slate-600 mb-2">
                  {careerData.recommendations.estimated_timeline_months} {t("careerPath.months", locale) || "months"}
                </p>
              </div>
              
              <div>
                <h4 className="font-semibold text-slate-900 mb-2">
                  {t("careerPath.confidence", locale) || "Confidence"}
                </h4>
                <div className="flex items-center gap-2">
                  <div className="text-sm text-slate-600">{Math.round(careerData.recommendations.confidence * 100)}%</div>
                  <div className="w-32 bg-slate-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${careerData.recommendations.confidence * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <h4 className="font-semibold text-slate-900 mb-2">
                  {t("careerPath.salaryIncrease", locale) || "Potential Salary Increase"}
                </h4>
                <p className="text-sm text-slate-600 mb-2">
                  +{careerData.recommendations.potential_salary_increase_pct}%
                </p>
              </div>
            </div>
          </Card>

          {/* Skill Gaps */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">
              {t("careerPath.skillGaps", locale) || "Skill Gaps to Address"}
            </h2>
            <div className="space-y-3">
              {careerData.recommendations.skill_gaps.map((gap, index) => (
                <div key={index} className="p-4 border border-slate-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <h4 className="font-semibold text-slate-900">{gap.skill}</h4>
                      <Badge variant={gap.importance === "high" ? "lagoon" : "outline"}>
                        {gap.importance}
                      </Badge>
                    </div>
                    <span className="text-sm text-slate-600">{gap.acquisition_method}</span>
                  </div>
                  <p className="text-sm text-slate-600 mt-2">{gap.resources?.join(", ") || "Self-study recommended"}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Learning Path View */}
      {selectedView === "learning" && (
        <div className="space-y-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-slate-900 mb-4">
              {t("careerPath.learningPath", locale) || "Learning Path"}
            </h2>
            <div className="text-sm text-slate-600 mb-4">
              {t("careerPath.recommendedPace", locale) || "Recommended Pace"}: {careerData.learning_path.recommended_pace}
            </div>
            <div className="text-sm text-slate-600">
              {t("careerPath.totalWeeks", locale) || "Total Duration"}: {careerData.learning_path.total_weeks}
            </div>
          </Card>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">
              {t("careerPath.milestones", locale) || "Key Milestones"}
            </h3>
            <div className="space-y-3">
              {careerData.learning_path.milestones.map((milestone, index) => (
                <div key={index} className="flex items-start gap-4 p-4 border border-slate-200 rounded-lg">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 font-bold">{index + 1}</span>
                  </div>
                  <div className="flex-1">
                    <div>
                      <h4 className="font-semibold text-slate-900">{milestone.title}</h4>
                      <p className="text-sm text-slate-600 mt-1">{milestone.description}</p>
                    </div>
                    <div className="text-sm text-slate-600 mt-2">
                      <span className="font-medium">{t("careerPath.estimatedWeeks", locale) || "Estimated"}:</span> {milestone.estimated_weeks} {t("careerPath.weeks", locale) || "weeks"}
                    </div>
                    <div className="text-sm text-slate-600 mt-2">
                      <span className="font-medium">{t("careerPath.resources", locale) || "Resources"}:</span> {milestone.resources?.join(", ") || "Self-study materials"}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">
              {t("careerPath.nextSteps", locale) || "Next Steps"}
            </h3>
            <div className="space-y-2">
              <Button className="w-full justify-start" variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                {t("careerPath.refreshAnalysis", locale) || "Refresh Analysis"}
              </Button>
              <Button className="w-full" variant="default">
                <ArrowRight className="w-4 h-4 mr-2" />
                {t("careerPath.startLearning", locale) || "Start Learning Path"}
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
