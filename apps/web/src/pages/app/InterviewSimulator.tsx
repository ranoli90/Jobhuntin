/**
 * Interview Simulator Page - AI-powered interview preparation
 * Microsoft-level implementation with real-time feedback and comprehensive session management
 */

import * as React from "react";
import { useTranslation } from "react-i18next";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiDelete } from "../../lib/api";
import { Button } from "../../components/ui/Button";

interface InterviewQuestion {
  question_text: string;
  difficulty?: string;
  options?: string[];
}

interface InterviewResponse {
  response_text?: string;
  feedback?: { feedback?: string; suggestions?: string[]; next_question?: string };
  next_question?: string;
}

interface InterviewSessionDetail {
  session_id: string;
  status: string;
  questions?: InterviewQuestion[];
  responses?: InterviewResponse[];
  total_score?: number;
  questions_answered?: number;
  top_strengths?: string[];
  top_improvements?: string[];
}
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { 
  Play, 
  Pause, 
  Square, 
  RotateCcw, 
  CheckCircle, 
  Clock, 
  Brain, 
  Target, 
  TrendingUp, 
  Award,
  MessageSquare,
  Send,
  Trash2
} from "lucide-react";

export default function InterviewSimulatorPage() {
  const { t } = useTranslation();
  const locale = localStorage.getItem("language") || "en";
  const queryClient = useQueryClient();

  // State
  const [selectedSession, setSelectedSession] = React.useState<string | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = React.useState(0);
  const [userAnswer, setUserAnswer] = React.useState("");
  const [responseTime, setResponseTime] = React.useState(0);
  const [startTime, setStartTime] = React.useState<number | null>(null);

  // Fetch sessions
  const {
    data: sessions = [],
    isLoading: sessionsLoading,
    error: sessionsError,
    refetch: refetchSessions,
  } = useQuery({
    queryKey: ["interview-sessions"],
    queryFn: async () => {
      return await apiGet<Array<{ id: string; job_title?: string; company?: string; status?: string; total_score?: number; duration_minutes?: number; difficulty?: string; created_at?: string }>>("interviews/sessions");
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });

  // Fetch current session details
  const {
    data: sessionDetail,
    isLoading: detailLoading,
    refetch: refetchDetail,
  } = useQuery({
    queryKey: ["interview-session", selectedSession],
    queryFn: async () => {
      if (!selectedSession) return null;
      return await apiGet<InterviewSessionDetail>(`interviews/sessions/${selectedSession}`);
    },
    enabled: !!selectedSession,
    staleTime: 30 * 1000, // 30 seconds
  });

  // Create session mutation
  const createSessionMutation = useMutation({
    mutationFn: async (sessionData: any) => {
      return await apiPost("interviews/sessions", sessionData);
    },
    onSuccess: (data) => {
      const d = data as { session_id: string };
      queryClient.invalidateQueries({ queryKey: ["interview-sessions"] });
      setSelectedSession(d.session_id);
    },
  });

  // Submit answer mutation
  const submitAnswerMutation = useMutation({
    mutationFn: async ({ sessionId, answer, timeSpent }: { sessionId: string; answer: string; timeSpent: number }) => {
      return await apiPost<{ is_complete?: boolean }>(`interviews/sessions/${sessionId}/answer`, {
        response_text: answer,
        response_time_seconds: timeSpent,
      });
    },
    onSuccess: (data) => {
      if (data.is_complete) {
        // Session completed, show summary
        queryClient.invalidateQueries({ queryKey: ["interview-session", selectedSession] });
      } else {
        // Move to next question
        setCurrentQuestionIndex(prev => prev + 1);
        setUserAnswer("");
        setResponseTime(0);
      }
    },
  });

  // Delete session mutation
  const deleteSessionMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      return await apiDelete(`interviews/sessions/${sessionId}`);
    },
    onSuccess: (_, deletedSessionId) => {
      queryClient.invalidateQueries({ queryKey: ["interview-sessions"] });
      if (selectedSession === deletedSessionId) {
        setSelectedSession(null);
      }
    },
  });

  // Handlers
  const handleCreateSession = () => {
    const sessionData = {
      job_id: "sample-job-id", // Would come from job selection
      company: "Sample Company",
      job_title: "Software Engineer",
      job_description: "We are looking for a skilled software engineer...",
      interview_type: "technical",
      difficulty: "medium",
      question_count: 10,
    };
    createSessionMutation.mutate(sessionData);
  };

  const handleSubmitAnswer = () => {
    if (!userAnswer.trim() || !selectedSession) return;
    
    const timeSpent = startTime ? (Date.now() - startTime) / 1000 : responseTime;
    submitAnswerMutation.mutate({
      sessionId: selectedSession,
      answer: userAnswer,
      timeSpent,
    });
    setUserAnswer("");
    setStartTime(Date.now());
  };

  const handleSkipQuestion = () => {
    if (!selectedSession) return;
    
    submitAnswerMutation.mutate({
      sessionId: selectedSession,
      answer: "SKIP",
      timeSpent: responseTime,
    });
    setUserAnswer("");
    setCurrentQuestionIndex(prev => prev + 1);
    setStartTime(Date.now());
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  if (sessionsLoading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (sessionsError) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <Card className="p-6 text-center">
          <MessageSquare className="w-12 h-12 mx-auto text-red-500 mb-4" />
          <h2 className="text-xl font-semibold text-red-600 mb-2">
            {t("interviewSimulator.errorLoading", locale) || "Error Loading Sessions"}
          </h2>
          <p className="text-slate-600">{sessionsError instanceof Error ? sessionsError.message : String(sessionsError)}</p>
          <Button onClick={() => refetchSessions()}>
            {t("common.retry", locale) || "Retry"}
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">
            {t("interviewSimulator.title", locale) || "Interview Simulator"}
          </h1>
          <p className="text-slate-500 font-medium">
            {t("interviewSimulator.description", locale) || "Practice interviews with AI-powered feedback and real-time coaching"}
          </p>
        </div>
        <Button onClick={handleCreateSession}>
          <Brain className="w-4 h-4 mr-2" />
          {t("interviewSimulator.newSession", locale) || "New Session"}
        </Button>
      </div>

      {/* Sessions List */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Sessions List */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">
            {t("interviewSimulator.mySessions", locale) || "My Sessions"}
          </h2>
          
          {sessions.length === 0 ? (
            <Card className="p-8 text-center">
              <Target className="w-12 h-12 mx-auto text-slate-300 mb-4" />
              <h3 className="text-xl font-semibold text-slate-900 mb-2">
                {t("interviewSimulator.noSessions", locale) || "No Sessions Yet"}
              </h3>
              <p className="text-slate-600 mb-4">
                {t("interviewSimulator.noSessionsDescription", locale) || "Start your first interview practice session to get personalized feedback"}
              </p>
              <Button onClick={handleCreateSession}>
                <Play className="w-4 h-4 mr-2" />
                {t("interviewSimulator.startFirstSession", locale) || "Start First Session"}
              </Button>
            </Card>
          ) : (
            sessions.map((session) => (
              <Card 
                key={session.id} 
                className={`p-4 cursor-pointer transition-all hover:shadow-lg ${
                  selectedSession === session.id ? 'ring-2 ring-primary-500' : ''
                }`}
                onClick={() => setSelectedSession(session.id)}
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900 mb-1">
                      {session.company} - {session.job_title}
                    </h3>
                    <div className="flex items-center gap-2 text-sm text-slate-500">
                      <Badge variant={session.status === 'completed' ? 'lagoon' : 'outline'}>
                        {session.status}
                      </Badge>
                      <Badge variant="outline">
                        {session.difficulty}
                      </Badge>
                      <span className="ml-2">
                        <Clock className="w-4 h-4" />
                        {session.created_at ? new Date(session.created_at).toLocaleDateString(locale) : ""}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteSessionMutation.mutate(session.id);
                      }}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                
                {session.total_score && (
                  <div className="mt-3 pt-3 border-t border-slate-200">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{t("interviewSimulator.overallScore", locale) || "Overall Score"}:</span>
                      <span className={`font-bold ${getScoreColor(session.total_score ?? 0)}`}>
                        {Math.round(session.total_score ?? 0)}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500">
                      {t("interviewSimulator.duration", locale) || "Duration"}: {formatTime((session.duration_minutes ?? 0) * 60)}
                    </div>
                  </div>
                )}
              </Card>
            ))
          )}
        </div>

        {/* Session Detail */}
        {selectedSession && sessionDetail && (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-slate-900">
                {t("interviewSimulator.sessionDetail", locale) || "Session Practice"}
              </h2>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setSelectedSession(null);
                    setCurrentQuestionIndex(0);
                    setUserAnswer("");
                    setResponseTime(0);
                    setStartTime(null);
                  }}
                >
                  {t("common.back", locale) || "Back"}
                </Button>
                {sessionDetail.status !== 'completed' && (
                  <Button
                    variant="outline"
                    onClick={() => deleteSessionMutation.mutate(selectedSession)}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    {t("common.delete", locale) || "Delete"}
                  </Button>
                )}
              </div>
            </div>

            {detailLoading ? (
              <Card className="p-6 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              </Card>
            ) : (
              <Card className="p-6">
                {/* Progress Bar */}
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-slate-700">
                      {t("interviewSimulator.progress", locale) || "Progress"}
                    </span>
                    <span className="text-sm text-slate-500">
                      {currentQuestionIndex + 1} / {sessionDetail.questions?.length || 0}
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div 
                      className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${((currentQuestionIndex + 1) / (sessionDetail.questions?.length || 1)) * 100}%` }}
                    ></div>
                  </div>
                </div>

                {/* Question */}
                {sessionDetail.questions && currentQuestionIndex < sessionDetail.questions.length && (
                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-lg font-semibold text-slate-900">
                        {t("interviewSimulator.question", locale) || "Question"} {currentQuestionIndex + 1}
                      </span>
                      <Badge variant="outline" className="ml-2">
                        {sessionDetail.questions[currentQuestionIndex]?.difficulty || "medium"}
                      </Badge>
                    </div>
                    
                    {sessionDetail.responses && sessionDetail.responses[currentQuestionIndex] && (
                      <div className="text-sm text-slate-500">
                        <span className="font-medium">{t("interviewSimulator.previousAnswer", locale) || "Previous answer"}:</span>
                        <span className="ml-2 italic">"{sessionDetail.responses[currentQuestionIndex]?.response_text}"</span>
                      </div>
                    )}

                    <div className="mb-4">
                      <div className="text-slate-900 mb-2">
                        {sessionDetail.questions[currentQuestionIndex]?.question_text}
                      </div>
                      
                      {/* Answer Options */}
                      {sessionDetail.questions[currentQuestionIndex]?.options && (
                        <div className="space-y-2 mb-4">
                          {sessionDetail.questions[currentQuestionIndex].options.map((option: string, index: number) => (
                            <button
                              key={index}
                              className="w-full text-left p-3 border border-slate-300 rounded-lg hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
                              onClick={() => setUserAnswer(option)}
                            >
                              {option}
                            </button>
                          ))}
                        </div>
                      )}
                      
                      {/* Text Answer */}
                      {!sessionDetail.questions[currentQuestionIndex]?.options && (
                        <div className="mb-4">
                          <textarea
                            value={userAnswer}
                            onChange={(e) => setUserAnswer(e.target.value)}
                            placeholder={t("interviewSimulator.typeYourAnswer", locale) || "Type your answer here..."}
                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                            rows={4}
                          />
                        </div>
                      )}
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        onClick={handleSkipQuestion}
                      >
                        <RotateCcw className="w-4 h-4 mr-2" />
                        {t("interviewSimulator.skip", locale) || "Skip"}
                      </Button>
                      <Button
                        onClick={handleSubmitAnswer}
                        disabled={!userAnswer.trim() || submitAnswerMutation.isPending}
                      >
                        {submitAnswerMutation.isPending ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                        ) : (
                          <Send className="w-4 h-4 mr-2" />
                        )}
                        {t("interviewSimulator.submit", locale) || "Submit"}
                      </Button>
                    </div>
                  </div>
                )}

                {/* AI Feedback */}
                {sessionDetail.responses && sessionDetail.responses[currentQuestionIndex] && (
                  <Card className="mt-4 p-4 bg-blue-50 border-blue-200">
                    <div className="flex items-center mb-2">
                      <Brain className="w-5 h-5 text-blue-600 mr-2" />
                      <h4 className="text-lg font-semibold text-blue-900">
                        {t("interviewSimulator.aiFeedback", locale) || "AI Feedback"}
                      </h4>
                    </div>
                    
                    <div className="text-sm text-slate-700">
                      <p className="mb-2">
                        <span className="font-medium">{t("interviewSimulator.feedback", locale) || "Feedback"}:</span>
                        {sessionDetail.responses[currentQuestionIndex]?.feedback?.feedback || 
                         t("interviewSimulator.goodAnswer", locale) || "Good answer! Consider the clarity and relevance."}
                      </p>
                      
                      {sessionDetail.responses[currentQuestionIndex]?.feedback?.suggestions && (
                        <div>
                          <span className="font-medium">{t("interviewSimulator.suggestions", locale) || "Suggestions"}:</span>
                          <ul className="list-disc list-inside ml-4 space-y-1">
                            {sessionDetail.responses[currentQuestionIndex].feedback.suggestions.map((suggestion: string, index: number) => (
                              <li key={index}>{suggestion}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {sessionDetail.responses[currentQuestionIndex]?.next_question && (
                        <div className="mt-3 pt-3 border-t border-blue-300">
                          <span className="font-medium">{t("interviewSimulator.nextQuestion", locale) || "Next Question"}:</span>
                          <p className="italic text-slate-600">"{sessionDetail.responses[currentQuestionIndex].next_question}"</p>
                        </div>
                      )}
                    </div>
                  </Card>
                )}

                {/* Session Summary */}
                {sessionDetail.status === 'completed' && (
                  <Card className="mt-6 p-6 bg-green-50 border-green-200">
                    <div className="flex items-center mb-4">
                      <CheckCircle className="w-6 h-6 text-green-600 mr-2" />
                      <h4 className="text-xl font-semibold text-green-900">
                        {t("interviewSimulator.sessionCompleted", locale) || "Session Completed"}
                      </h4>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h5 className="font-semibold text-slate-900 mb-2">
                          {t("interviewSimulator.performance", locale) || "Performance"}
                        </h5>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="font-medium">{t("interviewSimulator.overallScore", locale) || "Overall Score"}:</span>
                            <span className={`font-bold text-2xl ${getScoreColor(sessionDetail.total_score || 0)}`}>
                              {Math.round(sessionDetail.total_score || 0)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="font-medium">{t("interviewSimulator.questionsAnswered", locale) || "Questions Answered"}:</span>
                            <span className="font-bold">{sessionDetail.questions_answered || 0}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <h5 className="font-semibold text-slate-900 mb-2">
                          {t("interviewSimulator.strengths", locale) || "Strengths"}
                        </h5>
                        <div className="space-y-1">
                          {sessionDetail.top_strengths?.map((strength: string, index: number) => (
                            <div key={index} className="flex items-center gap-2">
                              <TrendingUp className="w-4 h-4 text-green-500" />
                              <span>{strength}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      <div>
                        <h5 className="font-semibold text-slate-900 mb-2">
                          {t("interviewSimulator.improvements", locale) || "Areas for Improvement"}
                        </h5>
                        <div className="space-y-1">
                          {sessionDetail.top_improvements?.map((improvement: string, index: number) => (
                            <div key={index} className="flex items-center gap-2">
                              <Award className="w-4 h-4 text-yellow-500" />
                              <span>{improvement}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </Card>
                )}
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
