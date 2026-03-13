import React from "react";
import {
  SkillGapAnalysis as SkillGapAnalysisType,
  SkillRecommendation,
  calculateReadinessScore,
  getReadinessLevel,
  getPriorityColor,
  formatLearningTime,
} from "../hooks/useSkillGapAnalysis";

interface SkillGapAnalysisProps {
  analysis: SkillGapAnalysisType;
}

export function SkillGapAnalysisView({ analysis }: SkillGapAnalysisProps) {
  const readinessScore = calculateReadinessScore(analysis);
  const readinessLevel = getReadinessLevel(analysis.gap_score);

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Skill Gap Analysis
            </h2>
            <p className="text-gray-600 mt-1">
              Target Role: <span className="font-medium">{analysis.target_role}</span>
            </p>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-blue-600">{readinessScore}%</div>
            <div className="text-sm text-gray-600 mt-1">{readinessLevel}</div>
          </div>
        </div>
      </div>

      {/* Skills Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="text-2xl font-bold text-green-600">
            {analysis.matched_skills.length}
          </div>
          <div className="text-sm text-gray-600">Matched Skills</div>
          <div className="mt-2 flex flex-wrap gap-1">
            {analysis.matched_skills.slice(0, 5).map((skill) => (
              <span
                key={skill}
                className="text-xs px-2 py-1 bg-green-50 text-green-700 rounded"
              >
                {skill}
              </span>
            ))}
            {analysis.matched_skills.length > 5 && (
              <span className="text-xs px-2 py-1 text-gray-500">
                +{analysis.matched_skills.length - 5} more
              </span>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="text-2xl font-bold text-red-600">
            {analysis.missing_skills.length}
          </div>
          <div className="text-sm text-gray-600">Missing Skills</div>
          <div className="mt-2 flex flex-wrap gap-1">
            {analysis.missing_skills.slice(0, 5).map((skill) => (
              <span
                key={skill}
                className="text-xs px-2 py-1 bg-red-50 text-red-700 rounded"
              >
                {skill}
              </span>
            ))}
            {analysis.missing_skills.length > 5 && (
              <span className="text-xs px-2 py-1 text-gray-500">
                +{analysis.missing_skills.length - 5} more
              </span>
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="text-2xl font-bold text-gray-900">
            {analysis.required_skills.length}
          </div>
          <div className="text-sm text-gray-600">Total Required</div>
          <div className="mt-2 text-sm text-gray-500">
            {analysis.current_skills.length} current skills analyzed
          </div>
        </div>
      </div>

      {/* Market Insights */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Market Insights
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm text-gray-600">Demand Growth</div>
            <div className="text-lg font-semibold text-green-600">
              +{Math.round(analysis.market_insights.role_demand_growth * 100)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Experience Level</div>
            <div className="text-lg font-semibold text-gray-900">
              {analysis.market_insights.experience_level}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Job Postings</div>
            <div className="text-lg font-semibold text-gray-900">
              ~{analysis.market_insights.total_job_postings_estimate.toLocaleString()}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Competition</div>
            <div className="text-lg font-semibold text-gray-900 capitalize">
              {analysis.market_insights.competition_level}
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Learning Recommendations
        </h3>
        <div className="space-y-4">
          {analysis.recommendations.map((rec, index) => (
            <SkillRecommendationCard
              key={rec.skill}
              recommendation={rec}
              index={index}
            />
          ))}
        </div>
      </div>

      {/* Category Breakdown */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Category Breakdown
        </h3>
        <div className="space-y-3">
          {Object.entries(analysis.category_breakdown).map(
            ([category, data]) => (
              <div key={category} className="flex items-center">
                <div className="w-32 text-sm font-medium text-gray-700 capitalize">
                  {category.replace("_", " ")}
                </div>
                <div className="flex-1 mx-4">
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-600 rounded-full"
                      style={{ width: `${data.match_rate * 100}%` }}
                    />
                  </div>
                </div>
                <div className="w-20 text-sm text-gray-600 text-right">
                  {Math.round(data.match_rate * 100)}%
                </div>
                <div className="w-16 text-sm text-gray-500 text-right">
                  {data.matched.length}/{data.total}
                </div>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}

interface SkillRecommendationCardProps {
  recommendation: SkillRecommendation;
  index: number;
}

function SkillRecommendationCard({
  recommendation,
  index,
}: SkillRecommendationCardProps) {
  const priorityClass = getPriorityColor(recommendation.priority);

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-lg font-semibold text-gray-900">
              {index + 1}. {recommendation.skill}
            </span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full border ${priorityClass}`}
            >
              {recommendation.priority}
            </span>
          </div>
          <p className="text-sm text-gray-600 mt-1">{recommendation.reason}</p>
          <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              {formatLearningTime(recommendation.estimated_learning_weeks)}
            </span>
            <span className="flex items-center gap-1">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                />
              </svg>
              {Math.round(recommendation.demand_score * 100)}% demand
            </span>
          </div>
        </div>
      </div>

      {/* Resources */}
      {recommendation.resources.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="text-xs font-medium text-gray-500 mb-2">
            Learning Resources:
          </div>
          <div className="flex flex-wrap gap-2">
            {recommendation.resources.map((resource, i) => (
              <a
                key={i}
                href="#"
                className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100"
              >
                {resource.name} ({resource.provider})
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Related Skills */}
      {recommendation.related_skills.length > 0 && (
        <div className="mt-2">
          <div className="flex flex-wrap gap-1">
            {recommendation.related_skills.map((skill) => (
              <span
                key={skill}
                className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Simple loading skeleton for skill gap analysis
 */
export function SkillGapAnalysisSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-4"
          >
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
          </div>
        ))}
      </div>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-gray-100 rounded"></div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default SkillGapAnalysisView;
