import React, { useState } from "react";
import { cn } from "@/lib/utils";

interface SuccessStory {
  id: string;
  name: string;
  role: string;
  company: string;
  before: string;
  after: string;
  testimonial: string;
  avatar: string;
  timeToHire: string;
  salaryIncrease: string;
}

const successStories: SuccessStory[] = [
  {
    id: "1",
    name: "Sarah Chen",
    role: "Senior Software Engineer",
    company: "TechCorp",
    before: "Applied to 50+ jobs manually over 3 months, only got 2 interviews",
    after: "Applied to 15 targeted jobs, got 8 interviews and 4 offers",
    testimonial:
      "The AI resume optimization was a game-changer. My resume matched job descriptions perfectly.",
    avatar: "SC",
    timeToHire: "6 weeks",
    salaryIncrease: "35%",
  },
  {
    id: "2",
    name: "Michael Rodriguez",
    role: "Product Manager",
    company: "StartupXYZ",
    before: "Struggled to get noticed by recruiters despite strong experience",
    after:
      "Multiple companies reached out within 2 weeks of using the platform",
    testimonial:
      "The AI-powered matching found opportunities I never would have discovered.",
    avatar: "MR",
    timeToHire: "4 weeks",
    salaryIncrease: "28%",
  },
  {
    id: "3",
    name: "Emily Johnson",
    role: "UX Designer",
    company: "DesignStudio",
    before: "Spent hours customizing resumes for each application",
    after: "One-click resume generation with AI optimization",
    testimonial:
      "The tailored resumes helped me land my dream job at a top design firm.",
    avatar: "EJ",
    timeToHire: "3 weeks",
    salaryIncrease: "22%",
  },
  {
    id: "4",
    name: "David Kim",
    role: "Data Scientist",
    company: "DataCorp",
    before: "Applied to 30+ data science positions with generic resume",
    after: "AI-optimized resume and targeted applications led to 5 interviews",
    testimonial:
      "The skills validation and keyword optimization made all the difference.",
    avatar: "DK",
    timeToHire: "5 weeks",
    salaryIncrease: "40%",
  },
  {
    id: "5",
    name: "Lisa Thompson",
    role: "Marketing Manager",
    company: "BrandCo",
    before: "Traditional job hunting with low response rates",
    after: "AI-powered platform increased my response rate by 300%",
    testimonial:
      "I went from struggling to get responses to having multiple offers.",
    avatar: "LT",
    timeToHire: "4 weeks",
    salaryIncrease: "25%",
  },
  {
    id: "6",
    name: "James Wilson",
    role: "DevOps Engineer",
    company: "CloudTech",
    before: "Manual application tracking was overwhelming and inefficient",
    after: "Automated applications saved 20+ hours per week",
    testimonial:
      "The automation features allowed me to focus on interview preparation.",
    avatar: "JW",
    timeToHire: "3 weeks",
    salaryIncrease: "30%",
  },
];

const SuccessStories: React.FC = () => {
  const [activeStory, setActiveStory] = useState<number>(0);
  const [isAutoPlay, setIsAutoPlay] = useState(true);

  const nextStory = () => {
    setActiveStory((previous) => (previous + 1) % successStories.length);
  };

  const previousStory = () => {
    setActiveStory(
      (previous) =>
        (previous - 1 + successStories.length) % successStories.length,
    );
  };

  const goToStory = (index: number) => {
    setActiveStory(index);
    setIsAutoPlay(false);
  };

  React.useEffect(() => {
    if (isAutoPlay) {
      const interval = setInterval(() => {
        nextStory();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [isAutoPlay, activeStory]);

  const story = successStories[activeStory];

  return (
    <section className="py-16 bg-gray-50">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Success Stories
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            See how professionals like you transformed their job search with
            JobHuntin
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          {/* Main Story Display */}
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="grid md:grid-cols-2 gap-0">
              {/* Story Content */}
              <div className="p-8">
                <div className="flex items-center mb-6">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mr-4">
                    <span className="text-2xl font-bold text-blue-600">
                      {story.avatar}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">
                      {story.name}
                    </h3>
                    <p className="text-gray-600">
                      {story.role} at {story.company}
                    </p>
                  </div>
                </div>

                <div className="mb-6">
                  <div className="flex items-center mb-4">
                    <span className="bg-green-100 text-green-800 text-xs font-semibold px-3 py-1 rounded-full">
                      Before
                    </span>
                    <span className="mx-4 text-gray-400">→</span>
                    <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 rounded-full">
                      After
                    </span>
                  </div>
                  <p className="text-gray-700 mb-4">{story.before}</p>
                  <p className="text-gray-900 font-medium mb-4">
                    {story.after}
                  </p>
                  <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-700">
                    "{story.testimonial}"
                  </blockquote>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {story.timeToHire}
                    </div>
                    <div className="text-sm text-gray-600">Time to Hire</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {story.salaryIncrease}
                    </div>
                    <div className="text-sm text-gray-600">Salary Increase</div>
                  </div>
                </div>
              </div>

              {/* Story Image */}
              <div className="relative h-64 md:h-auto">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-purple-600 opacity-90"></div>
                <div className="relative h-full flex items-center justify-center">
                  <div className="text-center text-white">
                    <div className="text-6xl font-bold mb-2">
                      {story.avatar}
                    </div>
                    <div className="text-xl font-semibold">{story.name}</div>
                    <div className="text-lg opacity-90">{story.role}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-center space-x-4 mt-8">
            <button
              onClick={previousStory}
              className="p-2 rounded-full bg-white border border-gray-300 shadow-sm hover:shadow-md transition-shadow"
              aria-label="Previous story"
            >
              <svg
                className="w-5 h-5 text-gray-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7-7"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7-7"
                />
              </svg>
            </button>

            {/* Story Indicators */}
            <div className="flex space-x-2">
              {successStories.map((_, index) => (
                <button
                  key={index}
                  onClick={() => goToStory(index)}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    index === activeStory
                      ? "bg-blue-600"
                      : "bg-gray-300 hover:bg-gray-400"
                  }`}
                  aria-label={`Go to story ${index + 1}`}
                  aria-current={index === activeStory}
                />
              ))}
            </div>

            <button
              onClick={nextStory}
              className="p-2 rounded-full bg-white border border-gray-300 shadow-sm hover:shadow-md transition-shadow"
              aria-label="Next story"
            >
              <svg
                className="w-5 h-5 text-gray-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="m9 5l7 7-7 7"
                />
              </svg>
            </button>
          </div>

          {/* Story Thumbnails */}
          <div className="flex flex-wrap justify-center gap-4 mt-8">
            {successStories.map((story, index) => (
              <button
                key={story.id}
                onClick={() => goToStory(index)}
                className={`relative rounded-lg overflow-hidden transition-all ${
                  index === activeStory
                    ? "ring-2 ring-blue-600 ring-offset-2"
                    : "hover:ring-2 ring-gray-300 ring-offset-2"
                }`}
                aria-label={`View ${story.name}'s story`}
              >
                <div className="w-20 h-20 bg-gradient-to-br from-blue-400 to-purple-600 rounded-lg">
                  <div className="flex items-center justify-center h-full text-white font-bold">
                    {story.avatar}
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* Auto-play Toggle */}
          <div className="flex justify-center mt-8">
            <button
              onClick={() => setIsAutoPlay(!isAutoPlay)}
              className={`px-4 py-2 rounded-lg border ${
                isAutoPlay
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-700 border-gray-300"
              } transition-colors`}
            >
              {isAutoPlay ? "Pause" : "Auto-play"} Stories
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default SuccessStories;
